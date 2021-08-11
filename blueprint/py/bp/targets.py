"""The Blueprint targets file format."""

import json

from dataclasses import asdict, dataclass, field as dc_field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .extraction import Extraction, Field
from .geometry import BBox
from .instantiate import instantiate


@dataclass
class TargetWord:
  """A word which is part of a target value.

  Attributes:
    text: The text of the word.
    bbox: The word's bounding box. The x and y units are percentages of document
      width and height respectively.
  """
  text: str
  bbox: BBox


@dataclass
class TargetValue:
  """A target value for some field in some doc.

  Attributes:
    text: Some text, if the field's value is expected to contain text. If text
      is None, there should explicitly not be an assignment in the document for
      the field with this target value.
    words: The individual words that make up this target value. You should not
      assume that these are in any particular order.
    geometry_validated: Whether the bounding boxes / target words of this target
      value have been validated, typically by a human. (We sometimes guess at
      which OCRed words in a document are represented by a text-only target
      value. If the words are obtained by guessing, the validated attribute will
      be false.)
  """

  text: Optional[str] = None
  words: Optional[List[TargetWord]] = None
  geometry_validated: bool = False


@dataclass
class TargetAssignment:
  field: str
  value: TargetValue


@dataclass
class DocTargets:
  """The targets for a given doc.

  Within a targets file, every doc must have the same set of fields.

  Attributes:
    doc_name: A document's name.
    assignments: A tuple of target assignments.
    doc_tags: This document's tags.
    notes: An arbitrary string, used for storing notes in targets files.
  """

  doc_name: str
  assignments: Tuple[TargetAssignment, ...]
  doc_tags: List[str] = dc_field(default_factory=list)
  notes: Optional[str] = None

  @property
  def fields(self) -> Tuple[Field, ...]:
    return tuple(assignment.field for assignment in self.assignments)


@dataclass
class Slice:
  """A slice of the documents.

  This is used for grouping related docs together, to report stats specific to
  that slice.

  This can/should be extended to allow also slicing the fields.

  Attributes:
    description: Description of this slice, for use in stats tables, etc.
    include_doc_tags: If this is nonempty, then for a doc to be considered part
      of this slice, it must have at least one of these tags.
    require_doc_tags: For a doc to be considered part of this slice, it must
      have all of these tags.
    exclude_doc_tags: For a doc to be considered part of this slice, it must not
      have any of these tags.
    notes: An arbitrary string, used for storing notes in targets files.
  """

  description: str
  include_doc_tags: List[str] = dc_field(default_factory=list)
  require_doc_tags: List[str] = dc_field(default_factory=list)
  exclude_doc_tags: List[str] = dc_field(default_factory=list)
  notes: Optional[str] = None


@dataclass
class OutputConfig:
  """Configuration for what kinds of accuracy stats to report.

  If there are subsets of your documents or of your fields that you would like
  accuracy stats for specifically, you can add them here.

  Attributes:
    doc_tags: Doc tags to include as a row.
    field_groups: Field tags to include as a row. We automatically have a row
      for every field by default.
    slices: Slices to include as a row. See docs for `Slice`.
  """
  doc_tags: List[str] = dc_field(default_factory=list)
  field_groups: List[str] = dc_field(default_factory=list)
  slices: Dict[str, Slice] = dc_field(default_factory=dict)


@dataclass
class FieldGroup:
  """Field groups.

  Attributes:
    fields: Fields which are in this grouping.
    description: String description of the field group.
  """
  fields: List[str] = dc_field(default_factory=list)
  description: str = ""


@dataclass(frozen=True)
class Entry:
  field: str
  type: str
  is_label: bool


TargetsSchema = Tuple[Entry, ...]


def schema_fields(schema: TargetsSchema) -> Tuple[str, ...]:
  return tuple(entry.field for entry in schema)


def get_entry_from_schema(field: str, schema: TargetsSchema) -> Entry:
  if field not in schema_fields(schema):
    raise ValueError(f'field {field} not in schema')
  entry = tuple(filter(lambda E: E.field == field, schema))
  if len(entry) != 1:
    raise ValueError(f'multiple entries for field {field} in schema')
  return entry[0]


def get_entry_type_from_schema(field: str, schema: TargetsSchema) -> str:
  return get_entry_from_schema(field, schema).type


def is_label(field: str, schema: TargetsSchema) -> bool:
  return get_entry_from_schema(field, schema).is_label


def get_labels_from_schema(schema: TargetsSchema) -> Tuple[str, ...]:
  return tuple(map(lambda E: E.field,
    filter(lambda E: is_label(E.field, schema), schema)))


def schema_type_map(schema: TargetsSchema) -> Dict[str, str]:
  return {entry.field: entry.type for entry in schema}


def validate_extraction(
  extraction: Extraction, schema: TargetsSchema) -> Extraction:
  schema_map = schema_type_map(schema)
  for point in extraction.assignments:
    if schema_map[point.field] != point.entity.type:
      raise TypeError(f'entity type {point.entity.type} for does not match '
                      f'type {schema_map[point.field]} for field {point.field} '
                      f'in schema')
  return extraction


@dataclass(frozen=True)
class Targets:
  """A targets file for a collection of documents.

  Attributes:
    doc_targets: A tuple of targets for docuemnts.
    schema: A dictionary from field to field type.
    output_config: Configuration for what kinds of accuracy stats to report.
    doc_tags: Descriptions of all doc tags that appear in these targets.
    field_groups: A dictionary from field group name to that group of fields.
      This is for accuracy scoring, to get accuracy data for specific groups of
      fields.
  """
  doc_targets: Tuple[DocTargets, ...]
  schema: TargetsSchema
  output_config: OutputConfig = OutputConfig()
  doc_tags: Dict[str, str] = dc_field(default_factory=dict)
  field_groups: Dict[str, FieldGroup] = dc_field(default_factory=dict)

  @lru_cache(maxsize=None)
  def build_doc_map(self) -> Dict[str, DocTargets]:
    return {doc_targets.doc_name: doc_targets
        for doc_targets in self.doc_targets}

  def get_by_doc_name(self, doc_name: str) -> DocTargets:
    doc_map = self.build_doc_map()
    if doc_name not in doc_map:
      raise ValueError(f'doc {doc_name} missing from targets')
    return doc_map[doc_name]


def validate(targets: Targets,
             silent: bool = False) \
               -> Targets:
  """Validate these targets.

  Args:
    targets: The targets to validate.
    silent: Don't print warnings to stdout.

  Returns:
    The input targets.
  """

  for doc_targets in targets.doc_targets:
    for doc_tag in doc_targets.doc_tags:
      if doc_tag not in targets.doc_tags:
        raise ValueError(
          f'unrecognized doc tag {doc_tag} in doc {doc_targets.doc_name} -- '
          f'please add a description for {doc_tag}')

  for doc_targets in targets.doc_targets:
    for field in doc_targets.fields:
      if field not in targets.schema:
        raise ValueError(
          f'field {field} in doc {doc_targets.doc_name} is missing from schema')

  for doc_tag in targets.doc_tags:
    if not any(doc_tag in doc_targets.doc_tags
               for doc_targets in targets.doc_targets):
      if not silent:
        print(f'Warning: unused doc tag {doc_tag}')

  for doc_tag in targets.output_config.doc_tags:
    if doc_tag not in targets.doc_tags:
      raise ValueError(
        f'unrecognized doc tag {doc_tag} in output config')

  for field_group in targets.output_config.field_groups:
    if field_group not in targets.field_groups:
      raise ValueError(
        f'unrecognized field group {field_group} in output config')

  for slice_name, slice in targets.output_config.slices.items():
    for doc_tag in slice.include_doc_tags + \
                   slice.require_doc_tags + \
                   slice.exclude_doc_tags:
      if doc_tag not in targets.doc_tags:
        raise ValueError(
          f'unrecognized doc tag {doc_tag} in output config slice {slice_name}')

  return targets


def load_targets(path: Path,
                 silent: bool = False) \
                   -> Targets:
  with path.open() as f:
    return load_targets_from_json(json.load(f), silent)


def load_targets_from_json(blob: Dict,
                           silent: bool = False) \
                             -> Targets:
  return validate(instantiate(Targets, blob),
                  silent)


def load_doc_targets_from_json(blob: Dict) -> DocTargets:
  return instantiate(DocTargets, blob)


def load_schema(path: Path) -> TargetsSchema:
  with path.open() as f:
    return load_schema_from_json(json.load(f))


def load_schema_from_json(blob: Dict) -> TargetsSchema:
  return instantiate(TargetsSchema, blob)


def save_targets(targets: Targets, path: Path, silent: bool = False) -> None:
  s = json.dumps(asdict(validate(targets, silent=silent)),
                 indent=2, sort_keys=True)
  with path.open('w') as f:
    f.write(s + '\n')
