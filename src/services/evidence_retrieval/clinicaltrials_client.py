from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

import requests

from .schemas import EvidenceRecord, EvidenceSourceResult


@dataclass
class ClinicalTrialsClient:
    timeout: int = 25

    def fetch(self, molecule: str, max_results: int = 30) -> EvidenceSourceResult:
        start = datetime.now()
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.term": molecule,
            "pageSize": max_results,
        }
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json() if response.content else {}
            studies = self._study_list(payload)
            records: list[EvidenceRecord] = []
            for study in studies[:max_results]:
                record = self._study_to_record(study, molecule=molecule, request_url=getattr(response, "url", url))
                if record.identifier or record.title:
                    records.append(record)

            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            if not records:
                return EvidenceSourceResult(
                    source="clinicaltrials",
                    status="empty",
                    count=0,
                    error="No ClinicalTrials.gov studies found.",
                    elapsed_ms=elapsed,
                    request_url=getattr(response, "url", url),
                )
            return EvidenceSourceResult(
                source="clinicaltrials",
                status="found",
                count=len(records),
                records=records,
                elapsed_ms=elapsed,
                request_url=getattr(response, "url", url),
            )
        except requests.exceptions.HTTPError as exc:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return EvidenceSourceResult(
                source="clinicaltrials",
                status="unavailable",
                error=str(exc),
                elapsed_ms=elapsed,
                request_url=url,
            )
        except requests.exceptions.RequestException as exc:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return EvidenceSourceResult(
                source="clinicaltrials",
                status="unavailable",
                error=str(exc),
                elapsed_ms=elapsed,
                request_url=url,
            )
        except Exception as exc:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return EvidenceSourceResult(
                source="clinicaltrials",
                status="failed",
                error=str(exc),
                elapsed_ms=elapsed,
                request_url=url,
            )

    def _study_to_record(self, study: dict[str, Any], *, molecule: str, request_url: str) -> EvidenceRecord:
        protocol = study.get("protocolSection", {}) or {}
        identification = protocol.get("identificationModule", {}) or {}
        status_module = protocol.get("statusModule", {}) or {}
        design_module = protocol.get("designModule", {}) or {}
        conditions_module = protocol.get("conditionsModule", {}) or {}
        interventions_module = protocol.get("armsInterventionsModule", {}) or {}
        outcomes_module = protocol.get("outcomesModule", {}) or {}
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {}) or {}

        nct_id = self._first_non_empty(
            identification.get("nctId"),
            study.get("nctId"),
            study.get("NCTId"),
        )
        title = self._first_non_empty(
            identification.get("briefTitle"),
            identification.get("officialTitle"),
            study.get("briefTitle"),
            study.get("officialTitle"),
        )
        recruitment_status = self._first_non_empty(
            status_module.get("overallStatus"),
            status_module.get("recruitmentStatus"),
            study.get("overallStatus"),
        )
        phase = self._join_values(
            design_module.get("phases"),
            design_module.get("phase"),
            study.get("phase"),
        )
        conditions = self._as_list(conditions_module.get("conditions") or study.get("conditions"))
        interventions = self._flatten_interventions(interventions_module.get("interventions") or study.get("interventions"))
        primary_outcomes = self._outcomes_to_text(outcomes_module.get("primaryOutcomes") or study.get("primaryOutcomes"))
        secondary_outcomes = self._outcomes_to_text(outcomes_module.get("secondaryOutcomes") or study.get("secondaryOutcomes"))
        sponsor = self._first_non_empty(
            (sponsor_module.get("leadSponsor") or {}).get("name"),
            (sponsor_module.get("responsibleParty") or {}).get("name"),
            study.get("sponsorName"),
        )
        enrollment = self._first_non_empty(
            self._extract_enrollment(design_module.get("enrollmentInfo")),
            study.get("enrollmentCount"),
        )
        start_date = self._first_non_empty(
            self._extract_date(status_module.get("startDateStruct")),
            status_module.get("startDate"),
            study.get("startDate"),
        )
        completion_date = self._first_non_empty(
            self._extract_date(status_module.get("completionDateStruct")),
            status_module.get("completionDate"),
            study.get("completionDate"),
        )
        location_path = f"/api/v2/studies/{nct_id}" if nct_id else request_url

        metadata = {
            "database": "ClinicalTrials.gov",
            "source_section": "protocolSection",
            "query_term": molecule,
            "request_url": request_url,
            "study_keys": sorted(list(protocol.keys())),
        }
        if primary_outcomes:
            metadata["primary_outcome"] = primary_outcomes[0]
        if secondary_outcomes:
            metadata["secondary_outcomes"] = secondary_outcomes

        return EvidenceRecord(
            source="clinicaltrials",
            source_type="online",
            source_name="ClinicalTrials.gov",
            source_path=location_path,
            retrieved_at=datetime.now().isoformat(),
            title=title,
            status=recruitment_status,
            phase=phase,
            conditions=conditions,
            interventions=interventions,
            outcomes=primary_outcomes + secondary_outcomes,
            sponsor=sponsor,
            enrollment=enrollment,
            start_date=start_date,
            completion_date=completion_date,
            identifier=nct_id,
            url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "https://clinicaltrials.gov/",
            summary=title or nct_id or molecule,
            metadata=metadata,
        )

    @staticmethod
    def _study_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
        if not payload:
            return []
        studies = payload.get("studies")
        if isinstance(studies, list):
            return [item for item in studies if isinstance(item, dict)]
        return []

    @staticmethod
    def _first_non_empty(*values: Any) -> str:
        for value in values:
            if value is None:
                continue
            if isinstance(value, list):
                for item in value:
                    text = ClinicalTrialsClient._normalize_scalar(item)
                    if text:
                        return text
                continue
            if isinstance(value, dict):
                text = ClinicalTrialsClient._normalize_scalar(value.get("date") or value.get("value") or value.get("text"))
                if text:
                    return text
                continue
            text = ClinicalTrialsClient._normalize_scalar(value)
            if text:
                return text
        return ""

    @staticmethod
    def _normalize_scalar(value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        return text if text and text.lower() != "none" else ""

    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, list):
            result: list[str] = []
            for item in value:
                if isinstance(item, dict):
                    for candidate in (item.get("name"), item.get("description"), item.get("measure"), item.get("timeFrame")):
                        text = ClinicalTrialsClient._normalize_scalar(candidate)
                        if text:
                            result.append(text)
                            break
                else:
                    text = ClinicalTrialsClient._normalize_scalar(item)
                    if text:
                        result.append(text)
            return result
        text = ClinicalTrialsClient._normalize_scalar(value)
        return [text] if text else []

    @staticmethod
    def _join_values(*values: Any) -> str:
        items: list[str] = []
        for value in values:
            items.extend(ClinicalTrialsClient._as_list(value))
        seen = set()
        deduped = []
        for item in items:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return ", ".join(deduped)

    @staticmethod
    def _flatten_interventions(value: Any) -> list[str]:
        if not value:
            return []
        items: list[str] = []
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, dict):
                for candidate in (item.get("name"), item.get("description"), item.get("interventionName")):
                    text = ClinicalTrialsClient._normalize_scalar(candidate)
                    if text:
                        items.append(text)
                        break
            else:
                text = ClinicalTrialsClient._normalize_scalar(item)
                if text:
                    items.append(text)
        return items

    @staticmethod
    def _outcomes_to_text(value: Any) -> list[str]:
        if not value:
            return []
        if not isinstance(value, list):
            value = [value]
        results: list[str] = []
        for item in value:
            if not isinstance(item, dict):
                text = ClinicalTrialsClient._normalize_scalar(item)
                if text:
                    results.append(text)
                continue
            measure = ClinicalTrialsClient._normalize_scalar(item.get("measure"))
            time_frame = ClinicalTrialsClient._normalize_scalar(item.get("timeFrame"))
            description = ClinicalTrialsClient._normalize_scalar(item.get("description"))
            parts = [part for part in [measure, time_frame, description] if part]
            if parts:
                results.append("; ".join(parts))
        return results

    @staticmethod
    def _extract_enrollment(value: Any) -> str:
        if isinstance(value, dict):
            return ClinicalTrialsClient._first_non_empty(value.get("count"), value.get("type"))
        return ClinicalTrialsClient._normalize_scalar(value)

    @staticmethod
    def _extract_date(value: Any) -> str:
        if isinstance(value, dict):
            for key in ("date", "dateString", "raw", "value"):
                text = ClinicalTrialsClient._normalize_scalar(value.get(key))
                if text:
                    return text
        return ClinicalTrialsClient._normalize_scalar(value)
