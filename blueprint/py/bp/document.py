import json

from functools import lru_cache
from dataclasses import asdict, dataclass, field, replace
from itertools import chain
from pathlib import Path
from typing import (
  Any,
  Callable,
  Dict,
  Generator,
  Generic,
  Iterable,
  List,
  Optional,
  Tuple,
  Type,
  TypeVar,
)

from .entity import Entity, Page, Text, Word, entity_resolver
from .ez_box import EZBox
from .functional import all_equal, arg_max, comma_sep, pairs
from .geometry import BBox, Interval
from .instantiate import instantiate
from .typing_utils import unwrap


E = TypeVar('E', bound=Entity)
T = TypeVar('T')
Field = str


@dataclass(frozen=True)
class Document:
  """A Document is a collection of Entities of varying type."""
  bbox: BBox
  entities: Tuple[Entity, ...]
  name: str

  @staticmethod
  def from_entities(
    entities: Iterable[Entity], name: str) -> 'Document':
    """Construct a Document from entities."""
    entities = tuple(entities)
    bbox = unwrap(BBox.union(e.bbox for e in entities))
    return Document(bbox, entities, name)

  def with_entities(self, entities: Iterable[Entity]) -> 'Document':
    """Returns a copy of this Document with given entities added and bbox
    adjusted to include the new entities."""
    return Document.from_entities(
      tuple(chain(self.entities, entities)), self.name)

  def filter_entities(self, entity_type: Type[E]) -> Iterable[E]:
    yield from (e for e in self.entities if isinstance(e, entity_type))

  @lru_cache(maxsize=None)
  def median_line_height(self) -> float:
    return median_word_height(
      chain.from_iterable(
        E.entity_words() for E in self.entities))

  def __hash__(self) -> int:
    return id(self)

  def __eq__(self, other: Any) -> bool:
    return id(self) == id(other)


def median_word_height(words: Iterable[Word]) -> float:
  L = sorted(words, key=lambda W: W.height)
  if not L:
    return 0
  n = len(L)
  if n % 2 == 0:
    return 0.5 * (L[n // 2 - 1].height + L[n // 2].height)
  return L[(n - 1) // 2].height


@dataclass(frozen=True)
class DocRegion:
  """A region of a document.

  Attributes:
    document: A document.
    bbox: A bounding box on the document.
  """

  document: Document
  bbox: BBox

  def contains_doc_region(self, other: Optional['DocRegion']) -> bool:
    if other is None:
      return True
    return self.bbox.contains_bbox(other.bbox)

  def intersects_doc_region(self, other: Optional['DocRegion']) -> bool:
    if other is None:
      return False
    return self.bbox.intersects_bbox(other.bbox)

  @staticmethod
  def build(document: Optional[Document], bbox: Optional[BBox]) \
      -> Optional['DocRegion']:
    return DocRegion(document, bbox) \
      if document is not None and bbox is not None \
      else None

  @staticmethod
  def intersection(drs: Iterable[Optional['DocRegion']]) \
      -> Optional['DocRegion']:
    drs_: List['DocRegion'] = []
    for dr in drs:
      if dr is None:
        return None
      else:
        drs_.append(dr)
    if not drs_:
      return None # This is not really right, I guess.
    return DocRegion.build(
      drs_[0].document,
      BBox.intersection(dr.bbox for dr in drs_))

  def __str__(self) -> str:
    return 'DocRegion(region_in_percent={})'.format(
        self.document.bbox.percentages_overlapping(self.bbox))


class EZDocRegion(Generic[T]):

  def __init__(self, doc_region_getter: Callable[[T], DocRegion]):
    self.doc_region_getter = doc_region_getter
    self.ez_box: Optional[EZBox] = None

  def insert(self, t: T) -> None:
    doc_region = self.doc_region_getter(t)
    document = doc_region.document
    if self.ez_box is None:
      bbox_getter = lambda t_: self.doc_region_getter(t_).bbox
      self.ez_box = EZBox(document.bbox, bbox_getter)
    self.ez_box.insert(t)

  def ts(self) -> Generator[T, None, None]:
    if self.ez_box is not None:
      yield from self.ez_box.ts()

  def ts_contained_in(self, doc_region: DocRegion) -> Generator[T, None, None]:
    if self.ez_box is not None:
      yield from self.ez_box.ts_contained_in(doc_region.bbox)

  def ts_intersecting(self, doc_region: DocRegion) -> Generator[T, None, None]:
    if self.ez_box is not None:
      yield from self.ez_box.ts_intersecting(doc_region.bbox)


@lru_cache(maxsize=None)
def get_document_pages(document: Document) -> Tuple[Page, ...]:
  return tuple(filter(lambda E: isinstance(E, Page), document.entities)) # type: ignore


def get_pages(entity: Entity, document: Document) -> Tuple[Page, ...]:
  doc_pages = get_document_pages(document)
  return tuple(filter(lambda P: P.bbox.intersects_bbox(entity.bbox), doc_pages))


@lru_cache(maxsize=None)
def build_words_ez_doc_region(document: Document) -> EZDocRegion[Entity]:
  def build_doc_region(E: Entity) -> DocRegion:
    doc_region = DocRegion.build(document, E.bbox)
    assert doc_region
    return doc_region
  ez_doc_region: EZDocRegion[Entity] = EZDocRegion(build_doc_region)
  for word in filter(lambda E: isinstance(E, Text)
                                and len(E.words) == 1, document.entities):
    ez_doc_region.insert(word)
  return ez_doc_region


@lru_cache(maxsize=None)
def get_page_containing_entity(document: Document, entity: Entity) -> Page:
  return arg_max(
    lambda page: entity.bbox.percentage_contained_in(page.bbox),
    get_document_pages(document),
  )


def load_doc_from_json(blob: Dict) -> Document:
  return instantiate(
    Document,
    blob,
    base_classes={Entity},
    derived_class_resolver=entity_resolver)


def load_doc(path: Path) -> Document:
  with path.open() as f:
    return load_doc_from_json(json.load(f))


def dump_to_json(root: Document) -> str:
  return json.dumps(asdict(root))


def save_doc(root: Document, path: Path) -> None:
  with path.open('w') as f:
    f.write(dump_to_json(root) + '\n')
