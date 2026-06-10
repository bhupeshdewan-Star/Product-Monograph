from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import requests

from config import FDA_API, FDA_TIMEOUT
from .schemas import EvidenceRecord, EvidenceSourceResult


@dataclass
class FDAClient:
    timeout: int = FDA_TIMEOUT

    def fetch(self, molecule: str, max_results: int = 30) -> EvidenceSourceResult:
        start = datetime.now()
        url = f"{FDA_API}/label.json"
        try:
            response = requests.get(
                url,
                params={
                    "search": f'openfda.generic_name:"{molecule.lower()}"',
                    "limit": min(max_results, 10),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            records: list[EvidenceRecord] = []
            for result in results[:max_results]:
                openfda = result.get("openfda", {}) or {}
                generic = (openfda.get("generic_name") or [molecule])[0]
                brand_names = ", ".join(openfda.get("brand_name", []) or [])
                indications = self._first_text(result.get("indications_and_usage"))
                warnings = self._first_text(result.get("warnings"))
                contraindications = self._first_text(result.get("contraindications"))
                dosage = self._first_text(result.get("dosage_and_administration"))
                adverse = self._first_text(result.get("adverse_reactions"))
                interactions = self._first_text(result.get("drug_interactions"))
                pharmacology = self._first_text(result.get("clinical_pharmacology"))
                record = EvidenceRecord(
                    source="fda",
                    title=f"FDA label for {generic}",
                    summary=indications[:500],
                    indications=indications,
                    warnings=warnings,
                    contraindications=contraindications,
                    dosage=dosage,
                    adverse_reactions=adverse,
                    pharmacology=pharmacology,
                    identifier=generic,
                    url="https://www.accessdata.fda.gov/scripts/cder/daf/",
                    metadata={
                        "brand_names": brand_names,
                        "effective_time": result.get("effective_time", ""),
                        "sections": [
                            section_name
                            for section_name, section_value in (
                                ("indications_and_usage", indications),
                                ("warnings", warnings),
                                ("contraindications", contraindications),
                                ("dosage_and_administration", dosage),
                                ("adverse_reactions", adverse),
                                ("drug_interactions", interactions),
                                ("clinical_pharmacology", pharmacology),
                            )
                            if section_value
                        ],
                    },
                )
                if interactions:
                    record.metadata["drug_interactions"] = interactions
                records.append(record)

            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            if not records:
                return EvidenceSourceResult(source="fda", status="empty", count=0, request_url=url, elapsed_ms=elapsed)
            return EvidenceSourceResult(
                source="fda",
                status="found",
                count=len(records),
                records=records,
                elapsed_ms=elapsed,
                request_url=url,
            )
        except Exception as exc:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return EvidenceSourceResult(
                source="fda",
                status="failed",
                error=str(exc),
                elapsed_ms=elapsed,
                request_url=url,
            )

    @staticmethod
    def _first_text(values) -> str:
        if not values:
            return ""
        if isinstance(values, list):
            for item in values:
                if item:
                    return str(item).strip()
            return ""
        return str(values).strip()
