from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class NewsSource:
    name: str
    base_url: str
    path: str
    priority: int = -10

    @property
    def seed_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.path.lstrip('/')}"


DEFAULT_NEWS_SOURCES: List[NewsSource] = [
    NewsSource("Moneycontrol", "https://www.moneycontrol.com/", "/"),
    NewsSource("Economic Times", "https://economictimes.indiatimes.com/", "/"),
    NewsSource("Business Standard", "https://www.business-standard.com/", "/"),
    NewsSource("Mint (LiveMint)", "https://www.livemint.com/", "/"),
    NewsSource("CNBC-TV18", "https://www.cnbctv18.com/", "/"),
    NewsSource("NDTV Profit", "https://www.ndtvprofit.com/", "/"),
    NewsSource("PIB (Press Information Bureau)", "https://pib.gov.in/", "/AllRelease.aspx", priority=-15),
    NewsSource("Ministry of Finance", "https://finmin.gov.in/", "/press-releases", priority=-15),
    NewsSource(
        "SEBI (Securities & Exchange Board)",
        "https://www.sebi.gov.in/",
        "/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0",
        priority=-15
    ),
    NewsSource("RBI (Reserve Bank of India)", "https://www.rbi.org.in/", "/Scripts/BS_PressReleaseDisplay.aspx", priority=-15),
    NewsSource("GST Council", "https://gstcouncil.gov.in/", "/press-release", priority=-15),
]


def get_default_news_sources() -> List[NewsSource]:
    return list(DEFAULT_NEWS_SOURCES)
