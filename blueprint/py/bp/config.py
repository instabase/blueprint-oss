"""Blueprint configuration."""

import json

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .instantiate import instantiate


@dataclass(frozen=True)
class Config:
  """Configuration for Blueprint extraction.

  Args:
    num_samples: The number of samples to take from the extraction tree. A value
      of 0 means to take no samples. A negative value means to sample the
      extraction tree until we exhaust it.
    timeout: Timeout in seconds for a model run. To indicate no timeout, set
      to -1.
  """

  num_samples: int = 1
  timeout: int = -1


def load_config(path: Path) -> Config:
  with path.open() as f:
    return load_config_from_json(json.load(f))


def load_config_from_json(blob: Dict) -> Config:
  return instantiate(Config, blob)
