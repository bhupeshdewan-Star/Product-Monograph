from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

import requests

from config import PUBMED_API, PUBMED_TIMEOUT
from .schemas import EvidenceRecord, EvidenceSourceResult


@dataclass
class PubMedClient:
    timeout: int = PUBMED_TIMEOUT

    def fetch(self, molecule: str, max_results: int = 30) -> EvidenceSourceResult:
        start = datetime.now()
        search_url = f"{PUBMED_API}/esearch.fcgi"
        summary_url = f"{PUBMED_API}/esummary.fcgi"
        fetch_url = f"{PUBMED_API}/efetch.fcgi"
        query = f'({molecule}[Title/Abstract] OR {molecule}[MeSH Terms])'
        try:
            search = requests.get(
                search_url,
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance",
                },
                timeout=self.timeout,
            )
            search.raise_for_status()
            pmids = search.json().get("esearchresult", {}).get("idlist", [])[:max_results]
            if not pmids:
                return EvidenceSourceResult(source="pubmed", status="empty", count=0, request_url=search_url)

            summary = requests.get(
                summary_url,
                params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
                timeout=self.timeout,
            )
            summary.raise_for_status()
            summary_data = summary.json().get("result", {})

            abstract_map = self._fetch_abstracts(fetch_url, pmids)
            records: list[EvidenceRecord] = []
            for pmid in pmids:
                item = summary_data.get(pmid, {})
                authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
                record = EvidenceRecord(
                    source="pubmed",
                    title=item.get("title", "").strip(),
                    abstract=abstract_map.get(pmid, ""),
                    journal=item.get("source", "").strip(),
                    year=(item.get("pubdate", "") or "").split(" ")[0],
                    identifier=pmid,
                    doi=self._extract_doi(item),
                    authors=authors,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    metadata={"pmid": pmid},
                )
                records.append(record)

            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return EvidenceSourceResult(
                source="pubmed",
                status="found",
                count=len(records),
                records=records,
                elapsed_ms=elapsed,
                request_url=search_url,
            )
        except Exception as exc:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return EvidenceSourceResult(
                source="pubmed",
                status="failed",
                error=str(exc),
                elapsed_ms=elapsed,
                request_url=search_url,
            )

    def _fetch_abstracts(self, fetch_url: str, pmids: list[str]) -> dict[str, str]:
        if not pmids:
            return {}
        response = requests.get(
            fetch_url,
            params={"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
        abstracts: dict[str, str] = {}
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//MedlineCitation/PMID", default="").strip()
            abstract_parts = [part.text or "" for part in article.findall(".//Article/Abstract/AbstractText")]
            abstracts[pmid] = " ".join(part.strip() for part in abstract_parts if part.strip())
        return abstracts

    @staticmethod
    def _extract_doi(item: dict[str, Any]) -> str:
        for article_id in item.get("articleids", []) or []:
            if article_id.get("idtype", "").lower() == "doi" and article_id.get("value"):
                return article_id["value"]
        return ""
