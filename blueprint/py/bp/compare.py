"""Utilities for generating comparison tables.

We use this for comparing targets to extracted values, and also for comparing
different revisions of Blueprint for overall runtime and accuracy.
"""

import dataclasses

from functools import reduce
from itertools import count
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .functional import all_equal, nonempty


def tabulate(rows_: Iterable[Iterable[Any]]) -> str:
  def render(t: Any) -> str:
    return str(t) if t is not None else ''
  rows = tuple(tuple(render(t) for t in row) for row in rows_)
  nonempty_rows = tuple(filter(nonempty, rows))
  maximal_rows = tuple(row for row in rows
    if len(row) == max(map(len, rows)))
  if not nonempty_rows: return ''
  widths = tuple(max(len(entry) for entry in col) for col in zip(*maximal_rows))
  def make_line(row: Tuple[str, ...]) -> str:
    return '  '.join(word.ljust(width) for word, width in zip(row, widths))
  return '\n'.join(make_line(row) for row in rows)


@dataclasses.dataclass(frozen=True)
class Row:
  """A single tabular row in a comparison table.

  For example, in targets comparison, this is either the "extracted" row or the
  "targets" row.

  Args:
    name: In targets comparison, this is either "extracted" or "targets".
    dictionary: Key-to-value dictionary.
  """

  name: str
  dictionary: Dict[str, str]


@dataclasses.dataclass(frozen=True)
class Cluster:
  """A "cluster" of rows in a comparison table.

  For example, in targets comparison, we have one "cluster" per document.

  Args:
    heading: For example, in targets comparison, this consists of ('doc name',
      <doc-name>) and sometimes ('notes', <some notes>).
    rows: See the Row docs.
    checkmarks: Whether to put a checkmark in the given column.
  """

  heading: Tuple[Tuple[str, str], ...]
  rows: Tuple[Row, ...]
  checkmarks: Dict[str, bool]


def render_cluster(cluster: Cluster, keys: Iterable[str]) -> List[List[str]]:
  keys = tuple(keys)
  def key_str(key: str) -> str:
    return key + (' ✓' if cluster.checkmarks.get(key, False) else ' ✗')
  table_rows: List[List[str]] = []
  table_rows += [[k, v] for k, v in cluster.heading]
  table_rows += [[''] + list(map(key_str, keys))]
  table_rows += [[row.name] + [str(row.dictionary[key]) for key in keys]
    for row in cluster.rows]
  table_rows += [[]]
  return table_rows


def render_clusters(clusters: Iterable[Cluster], keys: Iterable[str]) -> str:
  keys = tuple(keys)
  rows: List[List[str]] = reduce(
    list.__add__, (render_cluster(cluster, keys) for cluster in clusters), [])
  return tabulate(rows)


def draw_table(rows: Sequence[Sequence[str]]) -> str:
  if not all_equal(map(len, rows)):
    raise ValueError('all rows must have same number of entries')

  cols = tuple(zip(*rows))
  col_widths = tuple(max(len(entry) for entry in col) for col in cols)

  def draw_row(row: Sequence[str]) -> str:
    def justify(s: str, width: int, index: int) -> str:
      return s.ljust(width) if index == 0 else s.rjust(width)
    return ' '.join(justify(s, width, i) for s, width, i in
                    zip(row, col_widths, count()))

  return '\n'.join(draw_row(row) for row in rows) + '\n'
