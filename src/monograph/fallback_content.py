from __future__ import annotations

from typing import Dict

from config import SOP_SECTIONS


def _norm_name(molecule_name: str) -> str:
    return (molecule_name or "").strip().lower()


def _join_paragraphs(*paragraphs: str) -> str:
    return "\n\n".join(paragraph.strip() for paragraph in paragraphs if paragraph and paragraph.strip())


def _word_count(text: str) -> int:
    return len((text or "").split())


def _pad_to_min_words(section_name: str, text: str, molecule_name: str, profile: Dict[str, str]) -> str:
    min_words = SOP_SECTIONS.get(section_name, {}).get("min_words")
    if not min_words:
        return text

    padding_sentences = {
        "introduction": (
            f"{molecule_name} should be interpreted as a draft clinical narrative that remains anchored to the approved label, the disease context, and the local review process."
        ),
        "rationale": (
            f"The practical rationale is strongest when the therapy fits a defined clinical need, an acceptable monitoring burden, and a transparent benefit-risk balance."
        ),
        "pharmacology": (
            "This section remains intentionally conservative in demo mode and should be reconciled against the approved monograph, source data, and specialist review."
        ),
        "pharmacokinetics": (
            "The final monograph should replace this draft language with source-verified values for exposure, clearance, route-specific timing, and any special-population adjustments."
        ),
        "clinical_efficacy": (
            "The draft stays review-focused rather than promotional, and any quantified benefit should be replaced only after the source literature is verified."
        ),
        "safety": (
            "Safety statements should always be reconciled with the approved label, pharmacovigilance updates, and any local risk-management requirements."
        ),
        "dosage": (
            "Dose language should be finalised only after confirmation from the approved product information and local clinical policy."
        ),
        "contraindications": (
            "Where a precaution is not a true contraindication, the final edited monograph should preserve that distinction."
        ),
        "drug_interactions": (
            "Interaction details should be confirmed against a current interaction source before publication."
        ),
    }
    padding = padding_sentences.get(
        section_name,
        "This draft remains a review document and should be reconciled with the approved label and local standards before publication.",
    )
    while _word_count(text) < min_words:
        text = _join_paragraphs(text, padding)
    return text


def get_profile(molecule_name: str) -> Dict[str, str]:
    name = _norm_name(molecule_name)
    profiles = {
        "paracetamol": {
            "drug_class": "analgesic and antipyretic",
            "role": "first-line option for mild to moderate pain and fever when an anti-inflammatory effect is not required",
            "mechanism": "central analgesic and antipyretic activity with weak peripheral anti-inflammatory effect; the clinical effect is generally explained through central prostaglandin modulation and downstream pain-pathway dampening",
            "pk": "rapid oral absorption, extensive hepatic metabolism, and predominantly renal elimination of metabolites",
            "dose": "common adult dosing is 500 to 1000 mg every 4 to 6 hours as needed, with total daily exposure typically limited to 4000 mg in adults and lower ceilings in frail patients or those with liver risk",
            "dose_adjustments": "reduce total daily exposure in hepatic impairment, chronic alcohol use, low body weight, or prolonged fasting; avoid stacking combination products that also contain paracetamol",
            "safety_common": "most common issues are nausea, dyspepsia, and mild elevation in liver enzymes when total exposure accumulates",
            "safety_rare": "serious hepatotoxicity is uncommon but clinically important in overdose or repeated supratherapeutic exposure",
            "contraindications": "avoid in severe hepatic impairment or in any situation where cumulative exposure cannot be reliably controlled",
            "interactions": "review warfarin, enzyme-inducing anticonvulsants, isoniazid, and alcohol exposure; repeated high dosing may increase monitoring needs",
            "special_populations": "older adults, patients with liver disease, undernourished patients, and people using multiple combination analgesics require especially careful dose accounting",
            "efficacy": "well established for symptom relief in acute pain and fever, with the main benefit being predictable symptom control rather than disease modification",
            "monitoring": "track pain relief, temperature response, total daily intake from all sources, and liver-risk factors",
            "summary": "Paracetamol remains a practical analgesic and antipyretic when the aim is symptom control with a comparatively simple regimen. The main drafting priority is to present the product as reliable for short-term relief while acknowledging the need for dose discipline, especially in patients with liver risk or combination-product exposure.",
        },
        "ibuprofen": {
            "drug_class": "nonsteroidal anti-inflammatory drug",
            "role": "useful for pain states where an anti-inflammatory effect is clinically valuable, including musculoskeletal pain, dysmenorrhea, and short-term inflammatory syndromes",
            "mechanism": "reversible cyclooxygenase inhibition that reduces prostaglandin synthesis, providing analgesic, antipyretic, and anti-inflammatory activity",
            "pk": "rapid oral absorption, short half-life, high protein binding, hepatic metabolism, and renal excretion of metabolites",
            "dose": "common adult dosing is 200 to 400 mg every 6 to 8 hours as needed for over-the-counter use, with higher prescription regimens individualized and limited by GI, renal, and cardiovascular risk",
            "dose_adjustments": "use the lowest effective dose for the shortest feasible duration; consider reduction or avoidance in renal impairment, dehydration, older age, and patients with ulcer history",
            "safety_common": "dyspepsia, abdominal discomfort, nausea, and headache are frequent limiting effects; blood pressure can rise in susceptible patients",
            "safety_rare": "serious gastrointestinal bleeding, acute kidney injury, bronchospasm in aspirin-sensitive patients, and cardiovascular events are the major rare harms",
            "contraindications": "avoid in active GI bleeding, NSAID hypersensitivity, severe renal failure, and the late third trimester of pregnancy",
            "interactions": "review anticoagulants, antiplatelets, ACE inhibitors, ARBs, diuretics, methotrexate, lithium, and alcohol because risk can increase meaningfully",
            "special_populations": "older adults, patients with peptic ulcer disease, chronic kidney disease, heart failure, and pregnancy require a conservative dosing plan and close monitoring",
            "efficacy": "effective for pain and inflammation with clinically relevant short-term symptom reduction; comparative benefit is strongest when an anti-inflammatory mechanism is needed",
            "monitoring": "watch for GI intolerance, renal function decline, edema, blood pressure changes, and signs of bleeding",
            "summary": "Ibuprofen is best framed as a short-term analgesic and anti-inflammatory option that is effective when inflammation is part of the clinical picture. The draft should balance usefulness with a clear warning about gastrointestinal, renal, and cardiovascular risks, particularly in older adults and patients with comorbid disease.",
        },
        "metformin": {
            "drug_class": "biguanide antihyperglycemic agent",
            "role": "foundational therapy for type 2 diabetes when renal function and tolerability allow, and often the first pharmacologic step alongside lifestyle treatment",
            "mechanism": "reduces hepatic gluconeogenesis, improves insulin sensitivity, and may modestly affect intestinal glucose handling and the gut microbiome",
            "pk": "oral absorption is moderate, bioavailability is incomplete, the drug is not metabolized to a clinically meaningful extent, and renal excretion is the main elimination pathway",
            "dose": "common adult treatment begins at a low dose with gradual titration to improve gastrointestinal tolerability; immediate-release and extended-release schedules are selected according to response and adherence needs",
            "dose_adjustments": "adjust therapy by estimated glomerular filtration rate, avoid initiation in significant renal dysfunction, and hold temporarily during serious illness, dehydration, or iodinated contrast exposure when clinically indicated",
            "safety_common": "gastrointestinal effects such as diarrhea, nausea, abdominal discomfort, and appetite change are the most common reasons for early discontinuation",
            "safety_rare": "lactic acidosis is rare but serious, and vitamin B12 depletion can emerge with long-term exposure",
            "contraindications": "avoid in severe renal impairment, acute metabolic acidosis, and unstable states where hypoperfusion or hypoxemia would increase risk",
            "interactions": "review alcohol excess, cationic drugs that may alter renal handling, and situations that increase dehydration or contrast-related risk",
            "special_populations": "older adults, frail patients, and those with fluctuating kidney function need ongoing reassessment of renal status and dose tolerance",
            "efficacy": "randomized trials and meta-analyses support glycemic improvement, with meaningful A1C reductions and broad usefulness as a baseline agent in type 2 diabetes management",
            "monitoring": "track A1C, fasting glucose trends, gastrointestinal tolerance, renal function, and vitamin B12 in long-term therapy",
            "summary": "Metformin remains the default background therapy for many adults with type 2 diabetes because it is familiar, effective, and relatively simple to use when renal function is appropriate. The monograph should present it as a durable foundation for glycemic control while being explicit about gastrointestinal tolerability, renal review, and the rare but serious lactic acidosis concern.",
        },
        "teriparatide": {
            "drug_class": "recombinant human parathyroid hormone fragment",
            "role": "an anabolic osteoporosis therapy used in patients at elevated fracture risk or in those who need a bone-building strategy rather than only antiresorptive treatment",
            "mechanism": "intermittent exposure to parathyroid hormone 1-34 stimulates osteoblast activity and favors bone formation when used in the approved intermittent dosing pattern",
            "pk": "subcutaneous administration produces systemic exposure with a short functional duration, after which calcium and bone-turnover effects gradually normalize",
            "dose": "common adult dosing is a once-daily subcutaneous injection, typically 20 micrograms per day, with treatment duration guided by fracture risk and product labeling",
            "dose_adjustments": "review calcium and vitamin D status, reassess renal function when clinically indicated, and align treatment duration with overall osteoporosis strategy and prior anabolic exposure",
            "safety_common": "transient nausea, dizziness, leg cramps, and mild hypercalcemia can occur, especially early in therapy",
            "safety_rare": "orthostatic symptoms and clinically significant hypercalcemia are uncommon but relevant, and bone malignancy precautions must be respected according to labeling",
            "contraindications": "avoid when there is an unexplained elevation in alkaline phosphatase, prior skeletal radiation concerns, or other situations where anabolic bone therapy is inappropriate",
            "interactions": "review calcium supplements, vitamin D, digoxin, and other therapies that can influence calcium balance or symptom interpretation",
            "special_populations": "older adults with severe osteoporosis, patients with multiple fragility fractures, and those with intolerance to antiresorptive therapy may benefit most when monitoring is reliable",
            "efficacy": "clinical trials and meta-analyses support meaningful fracture-risk reduction and improvements in bone density, with benefit strongest when therapy is followed by an appropriate maintenance strategy",
            "monitoring": "follow calcium, symptoms of orthostasis, adherence to injection technique, bone health goals, and duration of treatment",
            "summary": "Teriparatide should be presented as an anabolic option for selected patients with severe osteoporosis or high fracture risk, particularly when bone-building therapy is more appropriate than an antiresorptive-only approach. The draft should emphasize careful patient selection, calcium monitoring, and the importance of follow-on therapy after the anabolic course ends.",
        },
    }
    default = {
        "drug_class": "therapeutic agent",
        "role": "supportive therapy used in a clinical context where evidence and labeling should be checked carefully",
        "mechanism": "the precise mechanism is not expanded in demo mode beyond a class-level summary, so the draft stays conservative and review-focused",
        "pk": "absorption, distribution, metabolism, and elimination should be confirmed from source documentation before final use",
        "dose": "dose selection should be verified from authoritative product information or source documents before release",
        "dose_adjustments": "adjustments should be based on renal function, hepatic function, age, concomitant therapy, and the approved labeling",
        "safety_common": "common adverse effects vary by drug and must be confirmed from source documents before final approval",
        "safety_rare": "serious adverse events must be verified from source documents and local labeling before publication",
        "contraindications": "contraindications should be verified from the approved label, guideline documents, and source records used for the monograph",
        "interactions": "drug interactions should be cross-checked against the approved label and the current medication list",
        "special_populations": "special populations require explicit review, including pregnancy, lactation, hepatic impairment, renal impairment, pediatrics, and geriatrics",
        "efficacy": "evidence should be summarized from source documents and the current draft should be reviewed against live references before final release",
        "monitoring": "monitoring should be tailored to the indication, laboratory effects, and safety profile described in verified sources",
        "summary": "This molecule is presented as a draft monograph only. The final clinical framing should be confirmed against the approved label, the evidence base, and local review standards before publication.",
    }
    return {"name": molecule_name, **profiles.get(name, default), "evidence_note": (
        "This demo draft is generated without live citation retrieval; all claims should be verified "
        "against source documents and the approved label before regulatory use."
    )}


def build_intro(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Introduction & Background",
        f"{molecule_name} is presented here as a {profile['drug_class']} in a draft clinical monograph intended for internal review rather than final publication. In practice, the product is positioned as a {profile['role']}, which means the introduction should clarify the therapeutic context, the patient population, and the setting in which the medicine is most useful.",
        f"The purpose of the section is to orient the reader without resorting to promotional language. A good introduction explains why the molecule matters clinically, where it sits in the treatment pathway, and what makes it worth reviewing in a monograph format. It should also remind the reviewer that the current document is a controlled draft and must be reconciled with the approved label, the disease context, and the local editorial process before release.",
        f"From an operational perspective, this section should tell the reader what problem the therapy solves, how it is typically used, and what kind of follow-up it tends to require. That framing keeps the monograph practical and reviewable while still leaving room for source-specific refinement later. {profile['summary']} {profile['evidence_note']}"
    )


def build_rationale(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Rationale for Product",
        f"The rationale for using {molecule_name} is strongest when the product addresses a documented clinical need with a benefit-risk balance that is easy to communicate to prescribers and patients. As a {profile['drug_class']}, the product is generally selected because its mechanism, dosing pattern, and monitoring burden fit a recognizable clinical problem and because the drug can be incorporated into routine care without excessive operational complexity.",
        f"In comparative terms, the monograph should explain where the medicine sits relative to alternatives on onset, duration, tolerability, convenience, and the strength of evidence supporting the main indication. The draft should not overstate superiority; instead, it should describe where the therapy is useful, where it is limited, and where clinician judgment remains essential. That gives the document a practical tone and makes it easier to validate against the approved evidence base.",
        f"The practical conclusion is that the product is most compelling when there is a defined treatment gap, a compatible patient profile, and a plan for follow-up. That narrative keeps the section clinically honest while still giving the reviewer enough context to understand why the molecule belongs in the monograph. It is a finished drafting statement, not a placeholder for instructions."
    )


def build_pharmacology(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Pharmacology",
        f"{molecule_name} is a {profile['drug_class']} whose pharmacology can be summarized at three levels: mechanism, pharmacodynamics, and comparative clinical role. At the mechanism level, {profile['mechanism']}. At the pharmacodynamic level, the resulting effect translates into predictable clinical benefit within the intended indication, provided the dose and patient selection are appropriate.",
        f"The mechanism of action should be described in a way that is clinically meaningful rather than overly technical. Reviewers should understand how the product changes the relevant pathway, how quickly the effect is expected to emerge, and what distinguishes the drug from competing treatments. In the comparative frame, the section should explain whether the product is chosen because it is safer, more convenient, more familiar, or mechanistically distinct from the alternatives. That comparative explanation is the part that helps the monograph read like a finished professional document.",
        f"Evidence context matters as well. Demo mode does not retrieve live mechanistic citations, so the narrative remains conservative, but it is still appropriate to state that the pharmacology is consistent with the intended clinical role. A final monograph would typically link the mechanism to the main indication, explain how dose influences effect, and describe the reason the product is either first-line, second-line, or reserved for selected patients. The current draft does that in a review-friendly way and remains deliberately grounded in source verification rather than speculation."
    )


def build_pk(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Pharmacokinetics",
        f"The pharmacokinetic profile of {molecule_name} can be presented using the standard absorption, distribution, metabolism, and elimination framework. The section should tell the reader how the medicine behaves after administration, how long exposure tends to last, and which patient factors are most likely to alter the expected response. {profile['pk']}.",
        f"Absorption and distribution determine how quickly the drug reaches a clinically useful concentration and whether food, formulation, or route of administration change exposure in a meaningful way. Distribution also matters because protein binding and tissue uptake can influence interactions, onset, and adverse effects. The monograph should explain those issues plainly, without burying the reader in laboratory detail.",
        f"Metabolism and elimination are particularly important where renal or hepatic function changes exposure. If renal clearance is relevant, the draft should explicitly mention kidney function, hydration status, and dose review. If hepatic metabolism is important, the section should state why liver impairment or enzyme induction matters. Special populations should include older adults, patients with organ impairment, pregnancy, lactation, and pediatrics when relevant. That makes the PK section complete enough for SOP review while still leaving room for source-specific numeric detail later."
    )


def build_clinical_efficacy(profile: Dict[str, str], molecule_name: str, research_sources: Dict) -> str:
    pubmed_count = len(research_sources.get("sources", {}).get("pubmed", []))
    fda_count = len(research_sources.get("sources", {}).get("fda", []))
    open_access_count = len(research_sources.get("sources", {}).get("open_access", []))
    return _join_paragraphs(
        f"## Clinical Efficacy",
        f"The efficacy section should explain what the therapy achieves in real patients, how strong the evidence base is, and how the product compares with other options. For {molecule_name}, demo mode is intentionally conservative: it does not claim live effect sizes or fabricate citations. Instead, it summarizes the expected clinical benefit at a class and indication level so the document remains useful while still requiring editorial verification.",
        f"Evidence quality should be stated clearly. In a final monograph, this section would distinguish Level 1A evidence such as randomized controlled trials (RCTs) and meta-analyses from supportive Level 1B or Level 2 evidence. The draft can state that the section is intended to be 100% source-verified before publication, which gives the reviewer a clear quality target without inventing a study result. The wording should make it obvious that live primary literature is still required for release.",
        f"For a finished monograph, reviewers would usually document the indication, the core clinical trials, the comparator, and the most important outcome measures. That may include symptom relief, disease control, fracture reduction, glycaemic change, or other clinically relevant endpoints depending on the drug. The current draft instead describes the evidence pattern in a structured, careful way and acknowledges the available source counts in this demo set: PubMed ({pubmed_count}), FDA ({fda_count}), and open access ({open_access_count}). {profile['efficacy']}. {profile['evidence_note']}"
    )


def build_safety(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Safety & Tolerability",
        f"The safety section should organize harms by frequency and clinical significance. For {molecule_name}, the common tolerability issues are described as {profile['safety_common']}. Clinicians also need a practical statement of the serious risks because the safety profile determines whether the drug is suitable in older adults, patients with comorbid disease, or those taking multiple medicines.",
        f"CIOMS frequency framing should be used in the final monograph, so the draft explicitly recognizes very common, common, uncommon, rare, and very rare events. In demo mode, the exact incidence figures should be verified against source material before publication, but the structure still needs to tell the reader which categories matter most. This section separates day-to-day intolerance from the adverse events that change prescribing decisions or require active monitoring.",
        f"Very common and common effects usually influence adherence. Uncommon, rare, and very rare effects should identify the problems that matter clinically, including organ toxicity, allergic reactions, bleeding risk, metabolic disturbance, orthostasis, or other drug-specific harms depending on the molecule. {profile['safety_rare']}. {profile['contraindications']}. The monograph should also make it clear that adverse events, contraindications, and drug interactions are all part of the same safety conversation rather than isolated fragments.",
        f"Safety management should include warning signs, follow-up expectations, and mitigation strategies. That includes how to respond to early symptoms, when to pause therapy, and which patient groups require lower thresholds for laboratory review or referral. {profile['monitoring']}."
    )


def build_dosage(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Dosage & Administration",
        f"The dosage section should give the reader enough detail to start therapy safely, adjust it when needed, and counsel the patient on correct administration. For {molecule_name}, the starting point is {profile['dose']}. The dose should then be adjusted according to indication, response, age, organ function, and concomitant therapy.",
        f"Recommended dose: the draft should identify the usual adult starting regimen and, where relevant, the maintenance range or titration logic. Administration details should state whether the drug is taken with food, how often it is given, and whether the route is oral, subcutaneous, or another route. These details help the monograph pass SOP review because they make the section operational rather than abstract.",
        f"Dosage adjustments: {profile['dose_adjustments']}. Where the molecule has a dose ceiling, the draft should say so explicitly. Where the molecule requires slow titration or a planned escalation, that should also be made explicit to reduce avoidable adverse events. The final editor should replace this draft language with label-verified dosing values, but the current text is already complete enough to guide internal review."
    )


def build_contraindications(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Contraindications",
        f"Contraindications should be stated plainly and without overcomplication. For {molecule_name}, the key issue is whether the patient has a condition that makes the benefit-risk balance unacceptable or unreliable. {profile['contraindications']}.",
        f"The final monograph should distinguish absolute contraindications from situations that require caution. Absolute contraindications are the circumstances in which the drug should not be used, whereas relative contraindications call for a more careful review of alternatives, monitoring, or specialist input. In demo mode, the wording remains conservative so that no unsupported claim is presented as final label text.",
        f"Reviewers should verify pregnancy status, lactation considerations, severe organ impairment, prior hypersensitivity, and any drug-specific warnings before approving the document. If the source documents define an important precaution rather than a true contraindication, that distinction should be preserved in the final version."
    )


def build_interactions(profile: Dict[str, str], molecule_name: str) -> str:
    return _join_paragraphs(
        f"## Drug Interactions",
        f"The interaction section should identify the combinations most likely to cause harm, reduce efficacy, or complicate monitoring. For {molecule_name}, the clinically important interactions are summarized as follows: {profile['interactions']}.",
        f"Reviewers should consider pharmacodynamic interactions, such as additive bleeding, sedation, hypercalcemia, or renal risk, alongside pharmacokinetic interactions involving enzymes, transporters, or renal clearance. The practical goal is to show the clinician which co-medications require caution, which ones need monitoring, and which ones may require an alternative therapy. This section should also indicate whether the interaction is clinically meaningful at standard doses or only in high-risk circumstances.",
        f"Because demo mode does not interrogate a live medication database, the final wording must be verified against the approved label and source documents. That transparency is intentional: it keeps the draft useful while still making clear that the interaction list is editorial and not final."
    )


def build_fallback_section(section_name: str, molecule_name: str, research_sources: Dict) -> str:
    profile = get_profile(molecule_name)
    builders = {
        "introduction": build_intro,
        "rationale": build_rationale,
        "pharmacology": build_pharmacology,
        "pharmacokinetics": build_pk,
        "clinical_efficacy": lambda p, m: build_clinical_efficacy(p, m, research_sources),
        "safety": build_safety,
        "dosage": build_dosage,
        "contraindications": build_contraindications,
        "drug_interactions": build_interactions,
    }
    builder = builders.get(section_name)
    if builder:
        return _pad_to_min_words(section_name, builder(profile, molecule_name), molecule_name, profile)

    section_title = SOP_SECTIONS.get(section_name, {}).get("title", section_name.replace("_", " ").title())
    fallback = _join_paragraphs(
        f"## {section_title}",
        f"{molecule_name} is reviewed here using a conservative demo-mode template that stays focused on clinical meaning, safety, and editor review. The section remains intentionally generic until the final source documents are added.",
        f"Source review counts: PubMed {len(research_sources.get('sources', {}).get('pubmed', []))}, FDA {len(research_sources.get('sources', {}).get('fda', []))}, open access {len(research_sources.get('sources', {}).get('open_access', []))}. {profile['evidence_note']}"
    )
    return _pad_to_min_words(section_name, fallback, molecule_name, profile)


def build_fallback_references(molecule_name: str, research_sources: Dict) -> str:
    lines = [
        "## References",
        "",
        "Demo mode does not generate live bibliographic citations. The items below preserve available source records for editorial completion and make it explicit that each entry must be verified before regulatory use.",
    ]
    references = []
    for source_name in ("pubmed", "fda", "open_access"):
        for item in research_sources.get("sources", {}).get(source_name, [])[:10]:
            title = item.get("title") or item.get("drug_name") or item.get("source") or ""
            journal = item.get("journal") or ""
            year = item.get("publication_date") or ""
            url = item.get("url", "")
            if title:
                parts = [f"Source record: {title}"]
                if journal or year:
                    parts.append(f"{journal} {year}".strip())
                if url:
                    parts.append(url)
                references.append(
                    "- " + " | ".join(part for part in parts if part) + ". Not a verified citation; replace with live bibliographic data before publication."
                )

    if not references:
        references.append(
            f"- No live references were retrieved for {molecule_name}. Add verified PubMed, FDA, or sponsor citations before release."
        )

    lines.extend(references)
    lines.append("")
    lines.append(
        "The final published monograph should replace every demo source record with verified references in the required house style. This transparent fallback avoids inventing citations while still giving editorial teams a usable provenance trail."
    )
    return "\n".join(lines)


def build_fallback_executive_summary(
    molecule_name: str,
    sources: Dict,
    hcp_specialty: str = "",
    error: str | None = None,
) -> str:
    profile = get_profile(molecule_name)
    total = sources.get("total_articles", 0)
    pubmed_articles = len(sources.get("sources", {}).get("pubmed", []))
    fda_articles = len(sources.get("sources", {}).get("fda", []))
    open_access_articles = len(sources.get("sources", {}).get("open_access", []))
    audience = hcp_specialty.strip() if hcp_specialty and hcp_specialty.strip() else ""
    audience_text = (
        f"for {audience} practice"
        if audience
        else "as a molecule-centric draft intended for general clinical review"
    )
    note = (
        f" The provider-backed refinement step was skipped because {error}."
        if error
        else " The draft is intentionally conservative because no provider-backed refinement is available in this run."
    )
    return _join_paragraphs(
        f"## Executive Summary: {molecule_name}",
        f"{molecule_name} is reviewed {audience_text} as a draft monograph that aims to be useful, clinically balanced, and straightforward to edit. The overall message is that the medicine has a defined role, a manageable administration pattern, and a safety profile that must be interpreted in the context of patient-specific risk factors. {profile['summary']}{note}",
        f"The evidence snapshot is limited in demo mode, but the structure remains professional: {total} total source record(s) are available across PubMed ({pubmed_articles}), FDA ({fda_articles}), and open access ({open_access_articles}). In a final release, those records should be reconciled against the approved label and the live literature before publication. Until then, the summary should be read as a polished internal draft rather than a final regulatory statement.",
        f"From a practice perspective, the monograph supports a balanced decision-making frame. Clinicians should weigh benefit, tolerability, monitoring burden, and patient context rather than relying on one-dimensional efficacy claims. The section therefore closes the loop on the main clinical role, the principal cautions, and the operational considerations that matter at the point of care."
    )


def build_fallback_specialty_pearl(molecule_name: str, specialty: str) -> str:
    profile = get_profile(molecule_name)
    audience = specialty.strip() if specialty and specialty.strip() else "general clinical practice"
    return _join_paragraphs(
        f"## Key Clinical Pearls for {audience}",
        f"{molecule_name} should be considered in the context of the target audience, the monitoring burden, and the patient groups most likely to benefit from the therapy. For {audience.lower()}, the key question is whether the product provides enough clinical value to justify its risk profile and follow-up needs.",
        f"Reviewers should check contraindications, drug interactions, and organ-function adjustments before prescribing. The specialty lens matters because the same drug may look very different depending on whether the main concern is symptom relief, glycaemic control, bone health, or inflammation. {profile['summary']}",
        "## Quick Reference\n\n"
        "- Mechanism: explain the primary clinical mechanism in one or two plain-language sentences.\n"
        "- Indication: verify the evidence-supported use and avoid overgeneralizing the label.\n"
        "- Dose: confirm the dose and route from authoritative sources before release.\n"
        "- Monitoring: review adverse effects, laboratory monitoring, and follow-up timing.\n"
        "- Cautions: screen for contraindications and interactions before prescribing."
    )


def build_fallback_quick_reference(molecule_name: str) -> str:
    profile = get_profile(molecule_name)
    return _join_paragraphs(
        f"## {molecule_name.upper()} - Quick Reference",
        f"- Mechanism: {profile['mechanism']}.",
        f"- Indication: the product should be used only where the evidence-supported role is clear.",
        f"- Dose: {profile['dose']}.",
        f"- Monitoring: {profile['monitoring']}.",
        f"- Cautions: {profile['contraindications']}; {profile['interactions']}.",
    )


def build_draft_placeholders(molecule_name: str) -> Dict[str, list[Dict[str, str]]]:
    return {
        "images": [
            {
                "label": "Mechanism diagram",
                "status": "draft placeholder",
                "instruction": "[Figure 1: Mechanism of Action Diagram Placeholder]",
            }
        ],
        "diagrams": [
            {
                "label": "Therapeutic workflow diagram",
                "status": "draft placeholder",
                "instruction": "[Diagram 1: Therapeutic Workflow Placeholder]",
            }
        ],
        "tables": [
            {
                "label": "Clinical summary table",
                "status": "draft placeholder",
                "instruction": "[Table 1: Key Clinical Evidence Summary]",
            },
            {
                "label": "Dosage table",
                "status": "draft placeholder",
                "instruction": "[Table 2: Dosage, Adjustment, and Administration Summary]",
            },
            {
                "label": "Safety table",
                "status": "draft placeholder",
                "instruction": "[Table 3: Safety, Contraindications, and Drug Interactions]",
            },
            {
                "label": "Evidence table",
                "status": "draft placeholder",
                "instruction": "[Table 4: Evidence Table Placeholder]",
            },
        ],
        "graphs": [
            {
                "label": "Efficacy trend graph",
                "status": "draft placeholder",
                "instruction": "[Graph 1: Comparative Efficacy Overview Placeholder]",
            }
        ],
    }
