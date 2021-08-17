from unittest import TestCase

from bp.rules.textual import text_equals
from bp.tree import (
  CombineNode,
  LeafNode,
  PickBestNode,
  combine,
  extract,
  optimize_rule_distribution,
  pick_best,
)


class TestOptimizeRuleDistribution(TestCase):

  def test_leaf_rules(self) -> None:
    """Leaf rules stay at leaves."""

    r1 = text_equals('Rule 1')('f1')
    l1 = LeafNode('f1', 'Text').with_extra_rules(r1)

    self.assertIn(r1, frozenset(optimize_rule_distribution(l1).all_rules()))

    r2 = text_equals('Rule 2')('f2')
    l2 = LeafNode('f2', 'Text').with_extra_rules(r2)

    m = combine(l1, l2)
    o = optimize_rule_distribution(m)

    self.assertNotIn(r1, frozenset(o.rules))
    self.assertNotIn(r2, frozenset(o.rules))
    self.assertIn(r1, frozenset(o.all_rules()))
    self.assertIn(r2, frozenset(o.all_rules()))

  def test_combine(self) -> None:
    """Degree-1 rules migrate to leaves."""

    l1 = extract(field_types={'f1': 'Text'})
    l2 = extract(field_types={'f2': 'Text'})

    r1 = text_equals('Rule 1')('f1')
    r2 = text_equals('Rule 2')('f2')

    m = combine(l1, l2).with_extra_rules(r1, r2)
    o = optimize_rule_distribution(m)

    self.assertNotIn(r1, frozenset(o.rules))
    self.assertNotIn(r2, frozenset(o.rules))

    self.assertIn(r1, frozenset(o.all_rules()))
    self.assertIn(r2, frozenset(o.all_rules()))

    assert isinstance(o, CombineNode)

    self.assertIn(r1, o.node1.rules)
    self.assertIn(r2, o.node2.rules)

  def test_pick_best(self) -> None:
    """Degree-1 rules migrate to leaves."""

    l1 = extract(field_types={'f1': 'Text'})
    l2 = extract(field_types={'f2': 'Text'})

    r1 = text_equals('Rule 1')('f1')
    r2 = text_equals('Rule 2')('f2')

    m = pick_best(l1, l2).with_extra_rules(r1, r2)
    o = optimize_rule_distribution(m)

    self.assertNotIn(r1, frozenset(o.rules))
    self.assertNotIn(r2, frozenset(o.rules))

    self.assertIn(r1, frozenset(o.all_rules()))
    self.assertIn(r2, frozenset(o.all_rules()))

    assert isinstance(o, PickBestNode) and len(o.children) == 2

    self.assertIn(r1, o.children[0].rules)
    self.assertIn(r2, o.children[1].rules)
