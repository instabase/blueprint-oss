import json

from dataclasses import dataclass, replace
from functools import reduce
from itertools import chain, combinations
from mypy_extensions import VarArg
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple, Type

from ..document import Document
from ..entity import Entity
from ..extraction import Extraction, ExtractionPoint, Field
from ..functional import arg_min, adjacent_pairs
from ..graphs import components as graph_components
from ..rule import Atom, Conjunction, Predicate, Rule
from ..targets import TargetsSchema, get_labels_from_schema, schema_type_map

from ..rules.impingement import (
  NothingBetweenHorizontally,
  NothingBetweenVertically,
)
from ..rules.semantic import (
  IsAddress,
  IsDate,
  IsDollarAmount,
  IsEntirePhrase,
  IsPersonName,
)
from ..rules.spatial import (
  AlignmentLine,
  BottomAligned,
  LeftAligned,
  LeftToRight,
  RightAligned,
  TopDown,
  bottom_aligned,
  left_aligned,
  left_to_right,
  right_aligned,
  top_down,
)
from ..rules.textual import TextEquals


MINIMUM_SCORE = 0.8


@dataclass(frozen=True)
class SynthesizedRules:
  textual: Tuple[Rule, ...]
  type: Tuple[Rule, ...]
  spatial: Tuple[Rule, ...]

  @property
  def rules(self) -> Tuple[Rule, ...]:
    return tuple(chain(self.textual, self.type, self.spatial))


def text_equals(text: str) -> Predicate:
  # FIXME: Should be able to escape these instead of removing them, but I
  # couldn't get it to work properly.
  text = text.replace('"', '')
  tolerance = 0 if len(text) < 4 else 1
  return TextEquals((text,), tolerance=tolerance)


def find_spatial_rules(extraction: Extraction, doc: Document) \
    -> Tuple[Rule, ...]:

  Component = Tuple[ExtractionPoint, ...]

  def get_tabular_components(predicate: Predicate) -> Tuple[Component, ...]:
    def check_rule(component: Component) -> bool:
      rule = Atom(tuple(point.field for point in component), predicate)
      entities: Tuple[Entity, ...] = tuple(point.entity for point in component)
      return rule.predicate.score(entities, doc).score >= MINIMUM_SCORE

    if isinstance(predicate, BottomAligned):
      sorting_key: Callable[[Entity], float] = lambda p: p.bbox.ix.a
    else:
      assert isinstance(predicate, LeftAligned) \
          or isinstance(predicate, RightAligned)
      sorting_key = lambda p: p.bbox.iy.a
    def key(point: ExtractionPoint) -> float:
      return sorting_key(point.entity)
    sorted_extraction_points = sorted(tuple(extraction.points()), key=key)
    extraction_point_pairs = tuple(combinations(sorted_extraction_points, 2))
    tabular_pairs = tuple(filter(check_rule, extraction_point_pairs))

    components = graph_components(tabular_pairs)
    ordered_components = tuple(tuple(sorted(component,
      key=lambda p: sorting_key(extraction[p.field])))
      for component in components)
    return ordered_components

  rows = get_tabular_components(BottomAligned())
  left_columns = get_tabular_components(LeftAligned())
  right_columns = get_tabular_components(RightAligned())

  def trim_components(components: Tuple[Component, ...],
                      alignment: AlignmentLine) -> Tuple[Component, ...]:
    edgepoint_getter: Callable[[ExtractionPoint], float] = \
        lambda P: P.entity.bbox.ix.a \
        if alignment == AlignmentLine.LEFT_SIDES \
        else P.entity.bbox.ix.b
    def trim_component(component: Component) -> Component:
      for row_ in rows:
        column_edgepoint = sum(
          edgepoint_getter(P) for P in component) / len(component)
        def offset(point: ExtractionPoint) -> float:
          return abs(column_edgepoint - point.entity.bbox.center.x)
        if frozenset(point.field for point in row_).issubset(
            frozenset(point.field for point in component)):
          component = tuple(filter(
            lambda p: p not in row_ or p == arg_min(offset, row_), component))
      return component

    trimmed_components = (trim_component(component) for component in components)
    return tuple(component for component in trimmed_components \
        if len(component) > 0)

  left_columns = trim_components(left_columns, AlignmentLine.LEFT_SIDES)
  right_columns = trim_components(right_columns, AlignmentLine.RIGHT_SIDES)

  def eliminate_subsets(C1: Tuple[Component, ...],
                        C2: Tuple[Component, ...]) -> Tuple[Component, ...]:
    return tuple(filter(
      lambda C1_: all(not frozenset(C2_).issuperset(frozenset(C1_))
        for C2_ in C2), C1))

  left_columns = eliminate_subsets(left_columns, right_columns)
  right_columns = eliminate_subsets(right_columns, left_columns)

  RuleBuilder = Callable[[VarArg(Field)], Rule]

  def get_component_rules(component: Component,
                          rule_builder: RuleBuilder) -> Tuple[Rule, ...]:
    if rule_builder == bottom_aligned:
      order_rule_builder: RuleBuilder = left_to_right
      order_checker: Predicate = LeftToRight()
    else:
      assert rule_builder in (left_aligned, right_aligned)
      order_rule_builder = top_down
      order_checker = TopDown()

    validated_fields = frozenset(tuple(chain.from_iterable((p1.field, p2.field)
      for (p1, p2) in adjacent_pairs(component)
      if order_checker.score(
        (p1.entity, p2.entity), doc).score > MINIMUM_SCORE)))
    fields = tuple(point.field for point in component
      if point.field in validated_fields)
    if len(fields) < 2:
      return tuple()
    return (rule_builder(*fields), order_rule_builder(*fields))

  def get_impingement_rules(components: Tuple[Component, ...],
                            impingement_predicate: Predicate) \
                                -> Tuple[Rule, ...]:
    def not_impinged(points: Tuple[ExtractionPoint, ExtractionPoint]) -> bool:
      score = impingement_predicate.score(
        (points[0].entity, points[1].entity), doc).score
      return score >= MINIMUM_SCORE

    adjacent_component_pairs = tuple(filter(lambda p: not_impinged(p),
      chain.from_iterable(adjacent_pairs(component)
      for component in components)))

    return tuple(Atom((P1.field, P2.field), impingement_predicate)
        for P1, P2 in adjacent_component_pairs)

  row_rules = tuple(chain.from_iterable(
    get_component_rules(component, bottom_aligned)
    for component in rows))
  left_column_rules = tuple(chain.from_iterable(
    get_component_rules(component, left_aligned)
    for component in left_columns))
  right_column_rules = tuple(chain.from_iterable(
    get_component_rules(component, right_aligned)
    for component in right_columns))
  impingement_rules = chain(
    get_impingement_rules(
      tuple(chain(left_columns, right_columns)),
      NothingBetweenVertically()),
    get_impingement_rules(rows, NothingBetweenHorizontally()))
  return validate_rules(tuple(chain(
      row_rules,
      left_column_rules,
      right_column_rules,
      impingement_rules)),
    extraction, doc)


def validate_rules(
  rules: Tuple[Rule, ...],
  extraction: Extraction,
  doc: Document) -> Tuple[Rule, ...]:

  assert all(isinstance(R, Atom) or isinstance(R, Conjunction) for R in rules)

  def validate_atom(atom: Rule) -> Optional[Rule]:
    assert isinstance(atom, Atom)
    return atom if atom.predicate.score(tuple(extraction[field]
      for field in atom.fields), doc).score > MINIMUM_SCORE else None

  def validate_conjunction(conjunction: Rule) -> Optional[Rule]:
    assert isinstance(conjunction, Conjunction)
    # We only currently create simple conjunctions during synthesis.
    assert all(isinstance(atom, Atom) for atom in conjunction.rules)
    valid_atoms = tuple(filter(lambda A: A is not None,
      (validate_atom(atom) for atom in conjunction.rules)))
    return replace(conjunction, rules=valid_atoms) if valid_atoms else None

  valid_atoms = tuple(map(validate_atom,
    filter(lambda R: isinstance(R, Atom), rules)))
  valid_conjunctions = tuple(map(validate_conjunction,
    filter(lambda R: isinstance(R, Conjunction), rules)))
  return tuple(R for R in valid_atoms + valid_conjunctions if R is not None)


def get_schema_rules(type_map: Dict[str, str]) -> Tuple[Rule, ...]:
  type_predicates = {
    'Date': IsDate(),
    'DollarAmount': IsDollarAmount(),
    'PersonName': IsPersonName(),
    'Address': IsAddress(),
  }
  return tuple(Atom((field,), type_predicates[type_map[field]])
    for field in filter(lambda F: type_map[F] in type_predicates, type_map))


def find_type_rules(extraction: Extraction,
                    schema: TargetsSchema,
                    doc: Document) -> Tuple[Rule, ...]:
  entire_phrase_rules = list(Atom((field,), IsEntirePhrase())
    for field in filter(lambda F: IsEntirePhrase().score(
      (extraction[F],), doc).score >= MINIMUM_SCORE, extraction.fields))
  type_map = {entry.field: entry.type
    for entry in schema if entry.field in extraction.fields}
  return tuple(chain(entire_phrase_rules, get_schema_rules(type_map)))


def find_textual_rules(extraction: Extraction, labels: Tuple[Field, ...]) \
    -> Tuple[Rule, ...]:
  return tuple(Atom((field,),
    text_equals(extraction[field].entity_text or ''))
    for field in filter(lambda F: F in labels, extraction.fields))


def find_rules_for_extraction(extraction: Extraction, schema: TargetsSchema,
                              doc: Document) -> SynthesizedRules:
  labels = get_labels_from_schema(schema)
  return SynthesizedRules(
    textual=find_textual_rules(extraction, labels),
    type=find_type_rules(extraction, schema, doc),
    spatial=find_spatial_rules(extraction, doc))
