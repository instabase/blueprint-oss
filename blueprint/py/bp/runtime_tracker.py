"""Track how long Blueprint takes to do various things."""

import dataclasses, datetime

from enum import Enum
from typing import Dict, Optional


class Step(Enum):
  TOTAL = 'total' # This isn't really a step...
  BINDING = 'binding'
  PUMPING = 'pumping'


class _Timer:

  def __init__(self) -> None:
    self.start = datetime.datetime.now()
    self.end: Optional[datetime.datetime] = None

  @property
  def duration(self) -> datetime.timedelta:
    if not self.done:
      raise RuntimeError('cannot get duration of running timer')
    assert self.end is not None
    return self.end - self.start

  @property
  def duration_ms(self) -> int:
    return self.duration.seconds * 1000 \
         + self.duration.microseconds // 1000

  def finish(self) -> None:
    if self.done:
      raise RuntimeError('cannot finish timer twice')
    self.end = datetime.datetime.now()

  @property
  def done(self) -> bool:
    return self.end is not None


class RuntimeTracker:
  """This is only for logging."""

  def __init__(self) -> None:
    self.timers: Dict[Step, _Timer] = {}

  def start(self, step: Step) -> None:
    if step in self.timers:
      raise RuntimeError(f'cannot start step {step} twice')
    self.timers[step] = _Timer()

  def end(self, step: Step) -> None:
    if step not in self.timers:
      raise RuntimeError(f'cannot end step {step} which was never started')
    self.timers[step].finish()

  def duration_ms(self, step: Step) -> Optional[int]:
    if step not in self.timers:
      return None
    return self.timers[step].duration_ms

  def finish(self) -> None:
    """End any steps that are still running. Janky."""
    for timer in self.timers.values():
      if not timer.done:
        timer.finish()


@dataclasses.dataclass
class DocRuntimeInfo:
  """"How long did this doc take to process?"""

  binding_ms: Optional[int]
  pumping_ms: Optional[int]
  total_ms: Optional[int]

  timed_out: bool
