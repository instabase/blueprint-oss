"""OCR types wrappers."""

from dataclasses import dataclass
from typing import Optional, Iterable, Tuple

from .geometry import BBox


@dataclass(frozen=True)
class CharConfidence:
  percentage: float
  unsure: Optional[bool]


@dataclass(frozen=True)
class WordConfidence:
  word_confidence: Optional[float]
  low_confidence: Optional[bool]
  char_confidences: Optional[Tuple[CharConfidence, ...]]


@dataclass(frozen=True)
class InputWord:
  bbox: BBox
  text: str
  confidence: Optional[WordConfidence] = None

  char_width: Optional[float] = None
  rotation_angle: Optional[float] = None

  @property
  def height(self) -> float:
    return self.bbox.height

  @property
  def width(self) -> float:
    return self.bbox.width

  def __str__(self) -> str:
    return 'InputWord("{}", bbox={})'.format(self.text, self.bbox)
