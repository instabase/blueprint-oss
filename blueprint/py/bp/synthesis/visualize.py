from dataclasses import dataclass
from itertools import chain
from typing import Dict, List, Tuple

from ..extraction import Field


TabularComponent = Tuple[Field, ...]
TabularComponents = List[TabularComponent]


@dataclass
class VisualTemplate:
  rows: TabularComponents
  columns: TabularComponents

  @property
  def max_width(self) -> int:
    return max(len(row) for row in self.rows) if len(self.rows) > 0 else 0

  @property
  def max_height(self) -> int:
    return max(len(col) for col in self.columns) if len(self.columns) > 0 else 0

  @property
  def max_field_width(self) -> int:
    row_fields = chain(*self.rows)
    return max(len(field)
      for field in chain(tuple(chain(*self.rows)), tuple(chain(*self.columns))))

  def print_template(self) -> None:

    def get_ranks(components: TabularComponents) -> Dict[int, TabularComponent]:
      assert components in (self.rows, self.columns)
      counterpart = self.columns if components == self.rows else self.rows
      field_ranks = {field: index for index, field in chain.from_iterable(
        enumerate(component) for component in counterpart)}
      return {max(field_ranks[field]
          for field in component if field in field_ranks): component
        for component in components}

    row_ranks = get_ranks(self.rows)
    column_ranks = get_ranks(self.columns)

    def get_element(index: int) -> TabularComponent:
      if index not in row_ranks:
        return tuple()
      return row_ranks[index]
    row_components = [get_element(i) for i in range(self.max_height)]
    cell_size = self.max_field_width
    for row in row_components:
      def get_grid_text(index: int) -> str:
        overlap = tuple(frozenset(column_ranks[index]) & frozenset(row)) \
          if index in column_ranks else None
        def get_padded_text(text: str) -> str:
          return text + ' ' * (cell_size - len(text))
        if overlap:
          # Think this through
          assert len(overlap) == 1
          text = overlap[0]
        else:
          text = ''
        return get_padded_text(text)
      spaced_row = tuple(get_grid_text(i) for i in range(self.max_width))
      print('  '.join(spaced_row))
