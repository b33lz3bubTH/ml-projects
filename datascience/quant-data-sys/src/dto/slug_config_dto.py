from dataclasses import dataclass
from typing import Set, Optional


@dataclass
class SlugDetectionConfig:
    """Configuration for slug-based article link detection"""
    min_slug_length: int = 30
    min_hyphen_count: int = 3
    min_path_depth: int = 1
    min_total_path_length: int = 50
    exclude_paths: Optional[Set[str]] = None
    require_lowercase: bool = True
    min_hyphen_ratio: float = 0.05
    
    def __post_init__(self):
        if self.exclude_paths is None:
            self.exclude_paths = set()
