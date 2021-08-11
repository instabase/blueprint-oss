from dataclasses import dataclass, replace
from itertools import chain
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple
from uuid import uuid4

from ..synthesis.rules import find_spatial_rules

from ..document import DocRegion, Document, EZDocRegion
from ..entity import Entity, Page, Text, Word
from ..extraction import Extraction, ExtractionPoint, Field
from ..functional import arg_max, pairs
from ..geometry import BBox, Interval
from ..graphs import Graph
from ..model import Predicate, Rule
from ..targets import DocTargets, TargetAssignment, TargetValue, TargetWord, Targets, TargetsSchema, get_labels_from_schema, schema_type_map

from ..rules.impingement import NothingBetweenHorizontally, NothingBetweenVertically
from ..rules.textual import TextEquals


def is_word(e: Entity) -> bool:
  return isinstance(e, Text) and len(e.words) == 1 \
      or isinstance(e, Word) # XXX: FIXME(ddanco)


def generate_target_extraction(
  targets: DocTargets,
  schema: TargetsSchema,
  document: Document) -> Optional[Extraction]:

  def find_entity(field: Field, target: TargetValue) \
      -> Optional[ExtractionPoint]:
    if not target.words:
      return None
    percentages_bbox = BBox.spanning(tuple(
      chain.from_iterable(word.bbox.corners() for word in target.words)))
    assert percentages_bbox is not None
    pixels_bbox = BBox.build(
      Interval(percentages_bbox.ix.a * doc_width,
              percentages_bbox.ix.b * doc_width),
      Interval(percentages_bbox.iy.a * doc_height,
              percentages_bbox.iy.b * doc_height))
    doc_region = DocRegion.build(document, pixels_bbox)
    assert doc_region is not None
    target_words = frozenset(word.text for word in target.words)
    found_words: FrozenSet[Word] = frozenset()

    intersecting_entities = tuple(ez_doc_region.ts_intersecting(doc_region))
    for E in intersecting_entities:
      if frozenset(W.entity_text or '' for W in E.entity_words()) \
          == target_words and E.type == schema_type_map(schema)[field]:
        return ExtractionPoint(field=field, entity=E)
    return None

  doc_width = document.bbox.width
  doc_height = document.bbox.height
  def build_doc_region(entity: Entity) -> DocRegion:
    doc_region = DocRegion.build(document, entity.bbox)
    assert doc_region
    return doc_region
  ez_doc_region: EZDocRegion[Entity] = EZDocRegion(build_doc_region)
  for entity in filter(lambda E: not isinstance(E, Page), document.entities):
    ez_doc_region.insert(entity)
  extraction_points = tuple(find_entity(assignment.field, assignment.value)
    for assignment in targets.assignments)
  if any(point is None for point in extraction_points):
    return None
  return Extraction(tuple(point for point in extraction_points
    if point is not None))


def find_entities_from_targets(
  target_assignments: Tuple[TargetAssignment, ...],
  document: Document,
  fields: Tuple[Field, ...],
  labels: Tuple[Field, ...]) -> Extraction:

  def get_entity_candidates(field: Field, target_value: Optional[TargetValue]) \
      -> FrozenSet[Entity]:
    if target_value is None or target_value.text is None:
      return frozenset()
    # This is somewhat arbitrary.
    tolerance: Callable[[Entity], int] = \
        lambda E: 0 if len(E.entity_text or '') < 4 else 1
    text_scores = {
      E: TextEquals(
        texts=(target_value.text,),
        tolerance=tolerance(E),
        taper=1).score((E,), document).score
      for E in document.entities}
    best_matches = frozenset(entity for entity, _ in tuple(filter(
      lambda V: V[1] == 1, text_scores.items())))
    # Best matches (tolerance=1) get preference over less good matches. TBD
    # if we should adjust this a bit.
    if best_matches:
      return best_matches
    partial_matches = frozenset(entity for entity, _ in tuple(filter(
      lambda V: V[1] > 0, text_scores.items())))
    return partial_matches

  def choose_best_candidates(candidates: Dict[Field, FrozenSet[Entity]]) \
      -> Extraction:

    def ordering_attempt(field_order: Tuple[Field, ...]) \
        -> Graph[ExtractionPoint]:
      # Entity IDs will be used as temporary field names for finding rules
      # between all possible entities
      entity_id_extraction = Extraction(tuple(
          ExtractionPoint(str(id(entity)), entity)
        for entity in entity_key))
      entity_id_map = entity_id_extraction.build_dictionary()
      spatial_rules = find_spatial_rules(entity_id_extraction, document)

      # Split col/row segments by labels
      split_spatial_rules: List[Rule] = []
      for rule in spatial_rules:
        cur_fields: List[Field] = []
        for field in rule.fields:
          if entity_key[entity_id_map[field]] in labels:
            if len(cur_fields) > 1:
              split_spatial_rules += [replace(rule, fields=cur_fields)]
            cur_fields = [field]
          else:
            cur_fields += [field]
        if len(cur_fields) > 1:
          split_spatial_rules += [replace(rule, fields=cur_fields)]

      edges = frozenset(tuple(chain.from_iterable(
          ((ExtractionPoint(entity_key[entity_id_map[F1]], entity_id_map[F1]),
          ExtractionPoint(entity_key[entity_id_map[F2]], entity_id_map[F2]))
        for F1, F2 in pairs(rule.fields)) for rule in split_spatial_rules)))

      graph = Graph(
        vertices=frozenset(ExtractionPoint(field, entity)
          for entity, field in entity_key.items()),
        edges=edges)

      for field in field_order:
        field_vertices = frozenset(
          tuple(filter(lambda V: V.field == field, graph.vertices)))
        def relevant_neighbor(neighbor: ExtractionPoint) -> bool:
          # There's a lot more work to be done here, labels should be good lined
          # up, but NOT when there are labels in a row/col with other labels AND
          # non-labels
          return neighbor.field != field and \
             not (field in labels and neighbor.field in labels)

        if field_vertices:
          most_neighbors = arg_max(lambda V: len(tuple(filter(
            relevant_neighbor, graph.neighbors(V)))), field_vertices)
          graph = graph.with_vertices_removed(
            field_vertices - frozenset((most_neighbors,)))
      return graph

    selected_orderings = (tuple(candidates), tuple(reversed(tuple(candidates))))
    attempts = (ordering_attempt(ordering)
      for ordering in selected_orderings)
    best_attempt = arg_max(lambda G: len(G.edges), attempts)
    return Extraction(tuple(ExtractionPoint(point.field, point.entity)
      for point in best_attempt.vertices))

  entity_candidates = {assignment.field: get_entity_candidates(
    assignment.field, assignment.value) for assignment in target_assignments}

  entity_key: Dict[Entity, Field] = {}
  for field in entity_candidates:
    for entity in entity_candidates[field]:
      entity_key[entity] = field

  best_candidates = choose_best_candidates(entity_candidates)
  return best_candidates


def get_target_spatial_info_for_all_docs(
  targets: Targets,
  documents: List[Document],
  fields: List[Field]) -> Dict[Document, DocTargets]:
  doc_targets_map = targets.build_doc_map()
  return {document: get_target_spatial_info_for_doc(
    doc_targets_map[f'{document.name}'], targets.schema, document,
    fields) for document in filter(
      lambda p: p.name in doc_targets_map, documents)}


def get_target_spatial_info_for_doc(
  doc_targets: DocTargets, schema: TargetsSchema, document: Document,
  fields: List[Field]) -> DocTargets:

  def create_target(field: Field, entity: Optional[Entity]) \
      -> Optional[TargetValue]:
    if entity is None:
      return None

    def build_target_word(word: Entity) -> TargetWord:
      assert isinstance(word, Word)
      bbox = word.bbox
      percentages_bbox = BBox(
        Interval(bbox.ix.a / document.bbox.width,
                  bbox.ix.b / document.bbox.width),
        Interval(bbox.iy.a / document.bbox.height,
                  bbox.iy.b / document.bbox.height))
      return TargetWord(word.text, percentages_bbox)
    target_words = [build_target_word(word) for word in entity.entity_words()]
    return TargetValue(entity.entity_text, target_words, False)

  labels = get_labels_from_schema(schema)
  target_assignments = tuple(filter(
    lambda A: A.field in fields, doc_targets.assignments))

  validated_targets = tuple(filter(
    lambda A: A.value.geometry_validated, target_assignments))
  unvalidated_targets = tuple(filter(
    lambda A: not A.value.geometry_validated, target_assignments))

  best_candidates = find_entities_from_targets(
    unvalidated_targets, document, tuple(fields), labels)
  estimated_targets = {point.field: create_target(point.field, point.entity)
    for point in best_candidates.assignments}

  return DocTargets(
    doc_name=doc_targets.doc_name,
    assignments=tuple(chain(validated_targets, unvalidated_targets)))
