from itertools import chain
from typing import Dict, FrozenSet, Generator, List, Optional

from .doc_region_restriction import get_doc_region_restriction
from .document import DocRegion, Document, EZDocRegion
from .extraction import Field
from .scoring import ScoredExtraction
from .spatial_formula import DNF, Formula, doc_region_terms_with_multiplicity, simplify


class DocRegionPrefilter:

  def __init__(
      self, field: Field,
      phi: Formula, document: Document):
    self.field = field
    self.phi = DNF(simplify(phi))
    self.document = document

    def get_doc_region(extraction: ScoredExtraction) -> DocRegion:
      doc_region = DocRegion.build(self.document, extraction[field].bbox)
      assert doc_region
      return doc_region

    self.ez_doc_region = EZDocRegion(get_doc_region)
    self.nones: List[ScoredExtraction] = []

    self.doc_region_terms = frozenset(doc_region_terms_with_multiplicity(phi))
    fields = frozenset(
        term.field for term in self.doc_region_terms if term.field != field)

    # FIXME: It's a bit janky to have this 'top-scoring' logic here.
    self.best: Optional[ScoredExtraction] = None

  def add(self, M_target: ScoredExtraction) -> None:
    # FIXME: It's a bit janky to have this 'top-scoring' logic here.
    if self.best is None or M_target < self.best:
      self.best = M_target

    if self.field not in M_target.fields:
      self.nones.append(M_target)
    else:
      self.ez_doc_region.insert(M_target)

  def get(self,
          M_feeder: ScoredExtraction) -> Generator[ScoredExtraction, None, None]:
    yield from self._get_from_ez_doc_region(M_feeder)
    yield from self.nones

  def _get_from_ez_doc_region(
      self, M_feeder: ScoredExtraction) -> Generator[ScoredExtraction, None, None]:
    dnf = get_doc_region_restriction(
      self.field, M_feeder, self.phi, self.document)

    if dnf == False:
      return

    if dnf == True:
      yield from self.ez_doc_region.ts()

    else:
      M_targets = set()

      assert not isinstance(dnf, bool)
      for conjunction in dnf.conjunctions:
        if conjunction.superset is None:
          assert conjunction.intersection_sets is not None
          intersecting_ts = tuple(frozenset(
              self.ez_doc_region.ts_intersecting(intersection_set))
            for intersection_set in conjunction.intersection_sets)
          if len(intersecting_ts) == 0:
            continue
          for M0 in frozenset.intersection(*intersecting_ts):
            M_targets.add(M0)
        elif conjunction.intersection_sets is None:
          assert conjunction.superset is not None
          for M0 in self.ez_doc_region.ts_contained_in(conjunction.superset):
            M_targets.add(M0)
        else:
          assert all(conjunction.superset.contains_doc_region(intersection_set)
              for intersection_set in conjunction.intersection_sets)
          for M0 in self.ez_doc_region.ts_contained_in(conjunction.superset):
            doc_region = DocRegion.build(self.document, M0[self.field].bbox)
            assert doc_region
            if all(intersection_set.intersects_doc_region(doc_region)
                for intersection_set in conjunction.intersection_sets):
              M_targets.add(M0)

      yield from M_targets
