from unittest import TestCase

from bp.rule import Atom
from bp.tree import CombineNode, LeafNode, PatternNode, distribute_rules

from bp.rules.textual import TextEquals


class TestTree(TestCase):

  def test_leaf_rules_staying_at_leaf_nodes(self) -> None:
    r1 = Atom(('f1', ), TextEquals(('Rule 1', )))
    l1 = LeafNode('f1', 'Text').with_rules((r1, ))

    self.assertIn(r1, frozenset(distribute_rules(l1, tuple()).all_rules()))

    r2 = Atom(('f2',), TextEquals(('Rule 2', )))
    l2 = LeafNode('f2', 'Text').with_rules((r2, ))

    m = CombineNode(node1=l1, node2=l2)
    o = distribute_rules(m, tuple())

    self.assertNotIn(r1, frozenset(o.rules))
    self.assertNotIn(r2, frozenset(o.rules))
    self.assertIn(r1, frozenset(o.all_rules()))
    self.assertIn(r2, frozenset(o.all_rules()))

  def test_degree_1_rules_migrating_to_leaf_nodes(self) -> None:

    r1 = Atom(('f1', ), TextEquals(('Rule 1', )))
    l1 = LeafNode('f1', 'Text')

    self.assertIn(r1, frozenset(distribute_rules(l1, (r1,)).all_rules()))

    r2 = Atom(('f2',), TextEquals(('Rule 2', )))
    l2 = LeafNode('f2', 'Text')

    m = CombineNode(node1=l1, node2=l2)
    o = distribute_rules(m, (r1, r2))

    self.assertNotIn(r1, frozenset(o.rules))
    self.assertNotIn(r2, frozenset(o.rules))
    self.assertIn(r1, frozenset(o.all_rules()))
    self.assertIn(r2, frozenset(o.all_rules()))
