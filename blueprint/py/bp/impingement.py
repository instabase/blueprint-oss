from .geometry import Interval


class Impingement():

  def __init__(self, I: Interval):
    if not I.valid:
      raise ValueError(f'impingement interval {I} cannot be invalid')
    if not I.non_empty:
      raise ValueError(f'impingement interval {I} cannot be empty')
    self._I = I
    self._opacities = {I: 0.0}

  @property
  def total_impingement(self) -> float:
    """Return weighted average of all sub-divisions."""
    return sum(
        opacity * interval.length
        for interval, opacity in self._opacities.items()) / self._I.length

  def incorporate_subdivision(self, I: Interval, new_opacity: float) -> None:
    if not 0 <= new_opacity <= 1:
      raise ValueError(f'subdivision opacity must be in [0,1], not {new_opacity}')
    if not I.valid:
      raise ValueError(f'subdivision {I} cannot be invalid')
    if not I.non_empty:
      # A zero-length subdivision cannot contribute to impingement -- do nothing.
      return

    intersecting_subdivisions = tuple(
        filter(I.intersects_interval, self._opacities))
    for subdivision in intersecting_subdivisions:
      old_opacity = self._opacities[subdivision]
      if new_opacity <= old_opacity:
        continue
      del self._opacities[subdivision]

      # new: -----
      # old:  ---
      if I.a <= subdivision.a and I.b >= subdivision.b:
        self._opacities[Interval(subdivision.a, subdivision.b)] = new_opacity

      # ----
      #   ----
      elif I.a <= subdivision.a and I.b < subdivision.b:
        self._opacities[Interval(subdivision.a, I.b)] = new_opacity
        self._opacities[Interval(I.b, subdivision.b)] = old_opacity

      #   ----
      # ----
      elif I.a > subdivision.a and I.b >= subdivision.b:
        self._opacities[Interval(subdivision.a, I.a)] = old_opacity
        self._opacities[Interval(I.a, subdivision.b)] = new_opacity

      #  ---
      # -----
      else:
        assert I.a > subdivision.a and I.b < subdivision.b
        self._opacities[Interval(subdivision.a, I.a)] = old_opacity
        self._opacities[Interval(I.a, I.b)] = new_opacity
        self._opacities[Interval(I.b, subdivision.b)] = old_opacity
