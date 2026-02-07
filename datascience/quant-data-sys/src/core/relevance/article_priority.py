import re
from typing import Iterable, List, Optional


DEFAULT_EXCLUDE_URL_PATTERNS = [
    r"/sports?/",
    r"/sport/",
    r"/cricket/",
    r"/football/",
    r"/tennis/",
    r"/basketball/",
    r"/olympics?/",
    r"/entertainment/",
    r"/bollywood/",
    r"/hollywood/",
    r"/celebrity/",
    r"/movie/",
    r"/music/",
    r"/tv/",
    r"/lifestyle/",
    r"/fashion/",
    r"/beauty/",
    r"/travel/",
    r"/food/",
    r"/recipe/",
    r"/horoscope/",
    r"/astrology/",
]

DEFAULT_HIGH_PRIORITY_PATTERNS = [
    r"/business/",
    r"/markets?/",
    r"/economy/",
    r"/economics/",
    r"/finance/",
    r"/stocks?/",
    r"/companies?/",
    r"/industry/",
    r"/bank(s|ing)/",
    r"/commodities?/",
    r"/ipo/",
    r"/earnings?/",
    r"/results?/",
    r"/policy/",
    r"/regulator/",
    r"/rbi/",
    r"/sebi/",
    r"/government/",
]

DEFAULT_LOW_PRIORITY_PATTERNS = [
    r"/opinion/",
    r"/editorial/",
    r"/feature/",
    r"/analysis/",
    r"/interview/",
]


class ArticlePriorityPolicy:
    """Heuristic URL-based priority policy for news articles."""

    def __init__(
        self,
        exclude_url_patterns: Optional[Iterable[str]] = None,
        high_priority_patterns: Optional[Iterable[str]] = None,
        low_priority_patterns: Optional[Iterable[str]] = None,
        case_sensitive: bool = False
    ):
        flags = 0 if case_sensitive else re.IGNORECASE
        exclude_patterns = list(exclude_url_patterns or DEFAULT_EXCLUDE_URL_PATTERNS)
        high_patterns = list(high_priority_patterns or DEFAULT_HIGH_PRIORITY_PATTERNS)
        low_patterns = list(low_priority_patterns or DEFAULT_LOW_PRIORITY_PATTERNS)

        self._exclude_patterns = [re.compile(p, flags) for p in exclude_patterns]
        self._high_patterns = [re.compile(p, flags) for p in high_patterns]
        self._low_patterns = [re.compile(p, flags) for p in low_patterns]

    def should_exclude_url(self, url: str) -> bool:
        return any(pattern.search(url) for pattern in self._exclude_patterns)

    def get_priority(self, url: str) -> int:
        if any(pattern.search(url) for pattern in self._high_patterns):
            return -10
        if any(pattern.search(url) for pattern in self._low_patterns):
            return 10
        return 0
