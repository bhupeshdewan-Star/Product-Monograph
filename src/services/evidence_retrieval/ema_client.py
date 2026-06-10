from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .schemas import EvidenceRecord, EvidenceSourceResult


@dataclass
class EMAClient:
    timeout: int = 25

    def fetch(self, molecule: str, max_results: int = 30) -> EvidenceSourceResult:
        start = datetime.now()
        search_url = "https://www.ema.europa.eu/en/search/search"
        try:
            response = requests.get(
                search_url,
                params={"search_api_fulltext": molecule},
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            records: list[EvidenceRecord] = []
            for link in soup.select('a[href*="/en/medicines/"], a[href*="/medicines/"]')[:max_results]:
                title = link.get_text(" ", strip=True)
                href = link.get("href", "")
                if not title or not href:
                    continue
                url = href if href.startswith("http") else f"https://www.ema.europa.eu{href}"
                records.append(
                    EvidenceRecord(
                        source="ema",
                        title=title,
                        url=url,
                        summary=title,
                        metadata={"search_term": molecule},
                    )
                )

            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            if not records:
                return EvidenceSourceResult(
                    source="ema",
                    status="unavailable",
                    count=0,
                    error="No structured EMA results were found.",
                    elapsed_ms=elapsed,
                    request_url=search_url,
                )
            return EvidenceSourceResult(
                source="ema",
                status="found",
                count=len(records),
                records=records,
                elapsed_ms=elapsed,
                request_url=search_url,
            )
        except Exception as exc:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return EvidenceSourceResult(
                source="ema",
                status="unavailable",
                error=str(exc),
                elapsed_ms=elapsed,
                request_url=search_url,
            )
