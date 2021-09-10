from typing import Optional
from .hocr_node import HOCRNode

class HOCRDocument:
  def __init__(self, filename: str, encoding: str = "utf-8"): ...

  @property
  def body(self) -> Optional[HOCRNode]: ...
