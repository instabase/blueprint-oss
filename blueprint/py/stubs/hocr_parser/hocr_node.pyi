from typing import List, Optional
from .bbox import BBox

class HOCRNode:
  @property
  def bbox(self) -> Optional[BBox]: ...

  @property
  def parent_bbox(self) -> Optional[BBox]: ...

  @property
  def paragraphs(self) -> List["HOCRNode"]: ...

  @property
  def ocr_text(self) -> str: ...

  @property
  def confidence(self) -> Optional[float]: ...

  @property
  def words(self) -> List["HOCRNode"]: ...

  @property
  def pages(self) -> List["HOCRNode"]: ...