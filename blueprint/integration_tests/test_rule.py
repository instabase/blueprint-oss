from unittest import TestCase

from .mock_doc import mock_doc
from .testing import ExpectedExtraction

from bp.rule import Disjunction
from bp.tree import extract

from bp.rules.logical import *
from bp.rules.spatial import *
from bp.rules.textual import *


class TestRule(TestCase):

  def test_rule_score_bounds(self) -> None:
    doc = mock_doc([
      'OK      Good      Bad'
    ])

    expected_extraction = ExpectedExtraction(doc, {'good': 'Good'})

    # This test won't pass until we check degree-1 non-Atoms at leaf-binding
    """
    self.assertTrue(
      expected_extraction.is_exactly_best_extraction_from(
        PatternNode(
          fields={
            'good': 'Text',
          },
          rules=((
            Disjunction(
              rules=(
                Atom(('good',), TextEquals(('Good', ))),
                Atom(('good',), Penalize(TextEquals(('OK', )), 0.8)),
                Atom(('good',), Penalize(TextEquals(('Bad', )), 0.4)),
              ),
            ),)
          )
        )
      )
    )
    """

    self.assertTrue(
      expected_extraction.is_contained_in_best_extraction_from(
        extract(
            text_equals('Good')('good'),
            text_equals('OK')('ok'),
            non_fatal(left_aligned_pair())('good', 'ok'),
          field_types={
            'good': 'Text',
            'ok': 'Text',
          },
        )
      )
    )
