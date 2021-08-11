from dataclasses import dataclass, field
from itertools import chain
from typing import Collection, Dict, FrozenSet, Generic, Iterable, Tuple, TypeVar

from .extraction import Field
from .functional import empty

T = TypeVar('T')

Component = FrozenSet[T]
Edge = Tuple[T, T]


@dataclass(frozen=True)
class Graph(Generic[T]):

  vertices: FrozenSet[T] = frozenset()
  edges: FrozenSet[Edge] = frozenset()

  def degree(self, vertex: T) -> int:
    return len(tuple(filter(lambda p: vertex in p, self.edges)))

  def indegree(self, vertex: T) -> int:
    def _filter(edge: Edge) -> bool:
      assert len(edge) == 2
      return vertex == edge[1]
    return len(tuple(filter(_filter, self.edges)))

  def outdegree(self, vertex: T) -> int:
    def _filter(edge: Edge) -> bool:
      assert len(edge) == 2
      return vertex == edge[0]
    return len(tuple(filter(_filter, self.edges)))

  @property
  def maximum_vertex_degree(self) -> int:
    if empty(self.vertices):
      raise ValueError('Null graph, no maximum vertex degree')
    return max(self.degree(v) for v in self.vertices)

  def neighbors(self, vertex: T) -> FrozenSet[T]:
    edges = tuple(filter(lambda p: vertex in p, self.edges))
    return frozenset(chain.from_iterable(edges)) - frozenset((vertex,))

  def restricted_to(self, fields: FrozenSet[Field]) -> 'Graph':
    return Graph(
      vertices=fields,
      edges=frozenset(filter(
        lambda p: fields.issuperset(frozenset(p)), self.edges)))

  def with_vertices_collapsed(self,
                              old_vertices: Collection[T],
                              new_vertex: T) \
                                -> 'Graph':
    """Return a new graph, where all of the `old_vertices` have been collapsed
    to a single `new_vertex`.

    Args:
      old_vertices: Vertices to delete from the graph. Any edge that had an old
        vertex as an end will have that end replaced with the new vertex. If
        there are any `old_vertices` which are not in the graph, they are
        silently ignored.
      new_vertex: A vertex to add to the graph.
    """
    old_vertices = frozenset(old_vertices)
    def new_edge(old_edge: Edge) -> Edge:
      def new_edge_vertex(vertex: T) -> T:
        return new_vertex if vertex in old_vertices else vertex
      return (new_edge_vertex(old_edge[0]),
              new_edge_vertex(old_edge[1]))
    return Graph(self.vertices - old_vertices | frozenset({new_vertex}),
                 frozenset(map(new_edge, self.edges)))

  def with_vertices_removed(self, vertices: Collection[T]) -> 'Graph':
    vertices = frozenset(vertices)
    remaining_edges = frozenset(filter(
      lambda E: all(V not in E for V in vertices), self.edges))
    return Graph(self.vertices - vertices, remaining_edges)


def components(
    complete_graphs: Iterable[Iterable[T]]) -> FrozenSet[Component[T]]:
  """Given a set of complete graphs, return the connected components of their
  union.

  Args:
    complete_graphs: Iterable of iterables, each of which lists the vertices of
      a complete graph.
  """

  components: Dict[T, Component] = {}

  for K in complete_graphs:
    ts = frozenset(K)
    existing_components = frozenset(
        components[t] for t in ts if t in components)
    new_component = ts.union(*existing_components)

    for t in new_component:
      components[t] = new_component

  return frozenset(components.values())

@dataclass(frozen=True)
class WeightedMultiGraph(Graph[T]):
  """A graph with edge multiplicity and numerical weights.

  Attributes:
    vertices: The set of vertices.
    edges: A set containing a tuple of two vertices if there is at least one edge between those vertices.
    weights: Associates each member of edges with a tuple of the weights of the edges between those vertices.
  """

  weights: Dict[Edge,Tuple[float,...]] = \
    field(default_factory=Dict[Edge,Tuple[float,...]])

  def __post_init__(self) -> None:
    assert(frozenset(self.weights.keys()) == frozenset(self.edges))

  def degree(self, vertex: T) -> int:
    return sum(tuple(len(self.weights[p]) for p in self.edges if vertex in p))

  def indegree(self, vertex: T) -> int:
    def _filter(edge: Edge) -> bool:
      assert len(edge) == 2
      return vertex == edge[1]
    return sum(tuple(len(self.weights[p]) for p in filter(_filter, self.edges)))

  def outdegree(self, vertex: T) -> int:
    def _filter(edge: Edge) -> bool:
      assert len(edge) == 2
      return vertex == edge[0]
    return sum(tuple(len(self.weights[p]) for p in filter(_filter, self.edges)))

  def restricted_to(self, fields: FrozenSet[Field]) -> 'WeightedMultiGraph':
    remaining_edges = frozenset(filter(
        lambda p: fields.issuperset(frozenset(p)), self.edges))
    return WeightedMultiGraph(
      vertices = fields,
      edges = remaining_edges,
      weights = dict(filter(
        lambda e: e[0] in remaining_edges, self.weights.items())))

  def with_vertices_collapsed(self,
                              old_vertices: Collection[T],
                              new_vertex: T
  ) -> 'WeightedMultiGraph':
    old_vertices = frozenset(old_vertices)
    def new_edge(old_edge: Edge) -> Edge:
      def new_edge_vertex(vertex: T) -> T:
        return new_vertex if vertex in old_vertices else vertex
      return (new_edge_vertex(old_edge[0]),
              new_edge_vertex(old_edge[1]))
    new_weights: Dict[Edge,Tuple[float,...]] = {}
    for edge, edgeweights in self.weights.items():
      new_weights[new_edge(edge)] = edgeweights + new_weights[new_edge(edge)] \
        if new_edge(edge) in new_weights else edgeweights

    return WeightedMultiGraph(
      self.vertices - old_vertices | frozenset({new_vertex}),
      frozenset(map(new_edge, self.edges)),
      new_weights)

  def with_vertices_removed(
    self,
    vertices: Collection[T]
  ) -> 'WeightedMultiGraph':
    vertices = frozenset(vertices)
    remaining_edges = frozenset(filter(
      lambda E: all(V not in E for V in vertices), self.edges))
    remaining_weights = dict(filter(
      lambda e: e[0] in remaining_edges, self.weights.items()))
    return WeightedMultiGraph(self.vertices - vertices,
      remaining_edges,
      remaining_weights)
