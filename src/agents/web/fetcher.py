from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class FetchedPage:
    url: str
    final_url: str
    status_code: int
    html: str
    content_type: str = ""


def fetch_url(url: str, timeout: float = 20.0, user_agent: Optional[str] = None) -> FetchedPage:
    headers = {
        "User-Agent": user_agent
        or "Mozilla/5.0 (compatible; MedicoExpressGlobalAgents/0.1; +https://localhost)"
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    logger.info("Fetched %s with status %s", url, response.status_code)
    return FetchedPage(
        url=url,
        final_url=str(response.url),
        status_code=response.status_code,
        html=response.text,
        content_type=response.headers.get("content-type", ""),
    )

