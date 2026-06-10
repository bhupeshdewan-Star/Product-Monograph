from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .schemas import EvidencePackage, EvidenceRecord, EvidenceSourceResult, EvidenceSummary


def normalize_evidence_package(
    molecule: str,
    source_results: dict[str, EvidenceSourceResult],
    *,
    cache_status: dict[str, Any] | None = None,
    retrieved_with: dict[str, Any] | None = None,
) -> EvidencePackage:
    sources: dict[str, list[EvidenceRecord]] = {}
    source_errors: list[str] = []
    limitations: list[str] = []
    summary = EvidenceSummary()

    order = [source_name for source_name in ("local", "pubmed", "fda", "ema", "clinicaltrials") if source_name in source_results]
    if not order:
        order = ["pubmed", "fda", "ema", "clinicaltrials"]

    for source_name in order:
        result = source_results.get(source_name)
        records = list(result.records) if result else []
        sources[source_name] = records
        count = len(records)
        setattr(summary, f"{source_name}_count", count)
        summary.total_records += count
        if result and result.error:
            source_errors.append(f"{source_name.upper()}: {result.error}")
        if result and result.status in {"failed", "unavailable"} and not records:
            limitations.append(f"{source_name.upper()} evidence unavailable.")
        if result and result.status == "empty":
            limitations.append(f"{source_name.upper()} returned no matching records.")

    if summary.total_records == 0:
        limitations.append("No live evidence retrieved. Review generated draft with extra caution.")

    package = EvidencePackage(
        molecule=molecule,
        retrieved_at=datetime.now(timezone.utc),
        sources=sources,
        summary=summary,
        limitations=_dedupe(limitations),
        source_errors=_dedupe(source_errors),
        source_status=source_results,
        cache_status=cache_status or {},
        retrieved_with=retrieved_with or {},
    )
    package.evidence_context = build_evidence_context(package)
    package.evidence_references = build_vancouver_references(package)
    return package


def build_evidence_context(package: EvidencePackage, max_items_per_source: int = 5, max_chars: int = 10000) -> str:
    lines: list[str] = []
    lines.append("STRUCTURED EVIDENCE PACKAGE")
    lines.append(f"Molecule: {package.molecule}")
    lines.append(f"Retrieved at (UTC): {package.retrieved_at.isoformat()}")
    lines.append(
        "Summary: "
        f"local={package.summary.local_count}; "
        f"total={package.summary.total_records}; "
        f"pubmed={package.summary.pubmed_count}; "
        f"fda={package.summary.fda_count}; "
        f"ema={package.summary.ema_count}; "
        f"clinicaltrials={package.summary.clinicaltrials_count}"
    )

    for source_name in ("local", "pubmed", "fda", "ema", "clinicaltrials"):
        if source_name not in package.sources:
            continue
        records = package.sources.get(source_name, [])
        status = package.source_status.get(source_name)
        lines.append("")
        lines.append(f"[{source_name.upper()}] status={status.status if status else 'unknown'} count={len(records)}")
        if status and status.error:
            lines.append(f"Error: {status.error}")
        if not records:
            lines.append("No records available.")
            continue
        for idx, record in enumerate(records[:max_items_per_source], start=1):
            lines.append(f"{idx}. {record.title}".strip())
            if record.abstract:
                lines.append(f"   Abstract: {record.abstract[:700]}")
            meta_bits = []
            if record.journal:
                meta_bits.append(f"Journal: {record.journal}")
            if record.year:
                meta_bits.append(f"Year: {record.year}")
            if record.identifier:
                meta_bits.append(f"ID: {record.identifier}")
            if record.doi:
                meta_bits.append(f"DOI: {record.doi}")
            if record.status:
                meta_bits.append(f"Status: {record.status}")
            if record.phase:
                meta_bits.append(f"Phase: {record.phase}")
            if record.conditions:
                meta_bits.append(f"Conditions: {', '.join(record.conditions[:5])}")
            if record.interventions:
                meta_bits.append(f"Interventions: {', '.join(record.interventions[:5])}")
            if record.outcomes:
                meta_bits.append(f"Outcomes: {', '.join(record.outcomes[:5])}")
            if record.sponsor:
                meta_bits.append(f"Sponsor: {record.sponsor}")
            if record.indications:
                meta_bits.append(f"Indications: {record.indications[:500]}")
            if record.warnings:
                meta_bits.append(f"Warnings: {record.warnings[:500]}")
            if record.contraindications:
                meta_bits.append(f"Contraindications: {record.contraindications[:500]}")
            if record.dosage:
                meta_bits.append(f"Dosage: {record.dosage[:500]}")
            if record.adverse_reactions:
                meta_bits.append(f"Adverse reactions: {record.adverse_reactions[:500]}")
            if record.pharmacology:
                meta_bits.append(f"Pharmacology: {record.pharmacology[:500]}")
            if record.source_path:
                meta_bits.append(f"Source path: {record.source_path[:500]}")
            if record.url:
                meta_bits.append(f"URL: {record.url}")
            for bit in meta_bits:
                lines.append(f"   {bit}")
    if package.limitations:
        lines.append("")
        lines.append("Limitations:")
        for limitation in package.limitations:
            lines.append(f"- {limitation}")
    if package.source_errors:
        lines.append("")
        lines.append("Source errors:")
        for error in package.source_errors:
            lines.append(f"- {error}")

    context = "\n".join(lines).strip()
    if len(context) > max_chars:
        context = context[: max_chars - 80].rstrip() + "\n[Evidence context truncated for prompt size.]"
    return context


def build_vancouver_references(package: EvidencePackage, max_items_per_source: int = 5) -> str:
    refs: list[str] = []
    index = 1
    include_local = bool((package.retrieved_with or {}).get("include_local_evidence_in_references", False))
    if include_local and "local" in package.sources:
        for record in package.sources.get("local", [])[:max_items_per_source]:
            label = record.source_name or record.title or package.molecule
            local_bits = []
            page = record.metadata.get("page") if record.metadata else ""
            section = record.metadata.get("section") if record.metadata else ""
            if page:
                local_bits.append(f"page {page}")
            if section:
                local_bits.append(f"section {section}")
            suffix = f" ({', '.join(local_bits)})" if local_bits else ""
            refs.append(f"{index}. Local Evidence: {label}{suffix}.")
            index += 1
    for record in package.sources.get("pubmed", [])[:max_items_per_source]:
        author_text = _format_authors(record.authors)
        title = record.title or package.molecule
        journal = record.journal or ""
        year = record.year or ""
        parts = [f"{index}. "]
        if author_text:
            parts.append(f"{author_text}. ")
        parts.append(f"{title}. ")
        if journal:
            parts.append(f"{journal}. ")
        if year:
            parts.append(f"{year}. ")
        if record.doi:
            parts.append(f"doi:{record.doi}. ")
        parts.append(f"PMID:{record.identifier}.")
        refs.append("".join(parts).strip())
        index += 1

    for record in package.sources.get("fda", [])[:max_items_per_source]:
        refs.append(
            f"{index}. U.S. Food and Drug Administration. {record.title or package.molecule} label. "
            f"Available from: {record.url or 'https://www.accessdata.fda.gov/scripts/cder/daf/'}."
        )
        index += 1

    for record in package.sources.get("ema", [])[:max_items_per_source]:
        refs.append(
            f"{index}. European Medicines Agency. {record.title or package.molecule}. "
            f"Available from: {record.url or 'https://www.ema.europa.eu/' }."
        )
        index += 1

    for record in package.sources.get("clinicaltrials", [])[:max_items_per_source]:
        nct = record.identifier or "NCT"
        refs.append(
            f"{index}. ClinicalTrials.gov. {record.title or package.molecule}. {nct}. "
            f"Available from: {record.url or 'https://clinicaltrials.gov/' }."
        )
        index += 1

    if not refs:
        refs.append("1. No live references were retrieved. Add verified PubMed, FDA, EMA, or ClinicalTrials.gov citations before release.")
    return "\n".join(refs)


def _format_authors(authors: list[str]) -> str:
    clean = [author.strip() for author in authors if author and author.strip()]
    if not clean:
        return ""
    if len(clean) > 6:
        clean = clean[:6]
        return ", ".join(clean) + ", et al"
    return ", ".join(clean)


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
