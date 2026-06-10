"""
Indian Market Context Generator
Provides India-specific pharmaceutical, regulatory, and market information
"""
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

class IndianMarketContextGenerator:
    """Generates India-specific context for pharmaceutical monographs"""

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL

    def generate_indian_context(self, molecule_name: str) -> Dict:
        """Generate comprehensive Indian market context"""

        context = {
            "regulatory_status": self._get_cdsco_status(molecule_name),
            "indian_brands": self._get_indian_brands(molecule_name),
            "pricing_category": self._get_pricing_info(molecule_name),
            "manufacturers": self._get_manufacturers(molecule_name),
            "schedule_classification": self._get_schedule(molecule_name),
            "nlem_status": self._get_nlem_status(molecule_name),
            "comparator_drugs": self._get_comparator_drugs(molecule_name),
            "insurance_coverage": self._get_insurance_info(molecule_name)
        }

        return context

    def _get_cdsco_status(self, molecule_name: str) -> str:
        """CDSCO (Central Drugs Standard Control Organization) approval status"""

        prompt = f"""For {molecule_name}, provide:
1. CDSCO approval status in India (Approved/Restricted/Proposed/Not Approved)
2. Approval date (if known)
3. Approved indications in India
4. Any restricted/conditional use in India

Be specific about Indian regulatory status. If specific data unavailable, indicate sources to check."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch CDSCO status: {str(e)}"

    def _get_indian_brands(self, molecule_name: str) -> str:
        """Get Indian brand names and manufacturers"""

        prompt = f"""List major Indian brands/formulations of {molecule_name}:

Format:
- Brand Name | Manufacturer | Strength(s) | Type (Generic/Branded)

Examples:
- Metrogyl | Cipla | 400mg | Branded
- Flagyl | Pfizer | 400mg | Branded
- Metronidazole | Various | Multiple | Generic

Include at least 10 major Indian brands if available.
If specific data unavailable, note that information should be verified from CDSCO database."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch Indian brands: {str(e)}"

    def _get_pricing_info(self, molecule_name: str) -> str:
        """Get Indian pricing and affordability information"""

        prompt = f"""For {molecule_name} in India, provide:

1. **Price Range** - Typical price per unit in INR (rupees)
   - Branded versions: ₹X-₹Y
   - Generic versions: ₹X-₹Y

2. **Price Regulation** - Is it under DPCO price control?
   - Ceiling price (if applicable)
   - Percentage markup allowed

3. **Affordability** - Typical course cost (30-day supply):
   - Branded: ~₹X
   - Generic: ~₹X

4. **Comparison** - Price vs comparable drugs in India

Note: Provide realistic estimates based on current Indian pharmaceutical market.
Disclaimer: Prices vary and should be verified with current suppliers."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch pricing info: {str(e)}"

    def _get_manufacturers(self, molecule_name: str) -> str:
        """Get CDSCO-approved Indian manufacturers"""

        prompt = f"""List major CDSCO-approved Indian manufacturers of {molecule_name}:

Format:
- Manufacturer Name | Manufacturing Facility Location | Product Types

Include:
- Large pharma companies (Cipla, Ranbaxy, Lupin, etc.)
- Mid-size manufacturers
- Generic manufacturers

Also note:
- WHO-GMP certified manufacturers
- Any recent manufacturing concerns

If specific data unavailable, note that CDSCO approved manufacturers list should be checked."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch manufacturer info: {str(e)}"

    def _get_schedule(self, molecule_name: str) -> str:
        """Get Indian Drugs & Cosmetics Act Schedule classification"""

        prompt = f"""For {molecule_name}, what is the Drugs & Cosmetics Act Schedule classification in India?

Possible categories:
- Schedule X - Narcotic/Psychotropic (Restricted - Prescription only, record keeping)
- Schedule H - Potential hazard (Prescription only, pharmacist supervision)
- Schedule H1 - Higher risk Schedule H drugs
- Schedule G - Habit forming (Unrestricted but marked)
- Schedule F - Formulations with certain restrictions
- Unlisted - Generally safe OTC drugs

Provide:
1. Exact schedule classification
2. What this means for:
   - Prescription requirements
   - Dispensing records
   - Patient counseling
   - Usage restrictions"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch schedule classification: {str(e)}"

    def _get_nlem_status(self, molecule_name: str) -> str:
        """Check National List of Essential Medicines (NLEM) status"""

        prompt = f"""Is {molecule_name} on India's National List of Essential Medicines (NLEM)?

NLEM is WHO-based list of essential medicines maintained by India.
If included:
- Which version/category?
- What indication(s)?
- What strength(s)?
- Impact on procurement in government hospitals?

Also check:
- State formularies (differ by state)
- CGHS coverage
- PMJAY (Ayushman Bharat) coverage"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch NLEM status: {str(e)}"

    def _get_comparator_drugs(self, molecule_name: str) -> str:
        """Get Indian comparator/alternative drugs"""

        prompt = f"""For {molecule_name} in India, what are the main comparator/alternative drugs?

Provide:
1. **Direct Comparators** - Same drug class, similar indication
   - Drug name
   - Indian brands available
   - Price comparison
   - Efficacy comparison

2. **Therapeutic Alternatives** - Different class, same indication
   - Drug alternatives
   - When preferred over {molecule_name}?

3. **Clinical Practice in India** - How is {molecule_name} positioned?
   - First-line or second-line?
   - Preferred in specific patient populations?
   - Common combinations?"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch comparator info: {str(e)}"

    def _get_insurance_info(self, molecule_name: str) -> str:
        """Get Indian insurance/government scheme coverage"""

        prompt = f"""For {molecule_name}, what is the coverage under Indian health schemes?

Cover these:
1. **PMJAY (Ayushman Bharat)** - Is it covered? Hospital list? Amount?
2. **CGHS** - Central Government Health Scheme coverage?
3. **ESIC** - Employees' State Insurance Corporation coverage?
4. **State Health Insurance** - Covered in major states?
5. **Private Insurance** - Common coverage?

Also mention:
- Any copay requirements
- Prior authorization needed?
- Restrictions on which manufacturers covered?
- Recent updates (2024-2025)?"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Unable to fetch insurance info: {str(e)}"

    def generate_indian_context_section(self, molecule_name: str) -> str:
        """Generate complete Indian context section for monograph"""

        context = self.generate_indian_context(molecule_name)

        section = f"""
## INDIA-SPECIFIC CONTEXT

### Regulatory Status (CDSCO)
{context['regulatory_status']}

### Indian Brand Names & Manufacturers
{context['indian_brands']}

### Pricing in India
{context['pricing_category']}

### CDSCO-Approved Manufacturers
{context['manufacturers']}

### Drugs & Cosmetics Act Schedule
{context['schedule_classification']}

### Essential Medicine Status (NLEM)
{context['nlem_status']}

### Comparable Drugs in Indian Market
{context['comparator_drugs']}

### Insurance & Government Scheme Coverage
{context['insurance_coverage']}

---
*Note: This information should be verified with current CDSCO website, current price lists,
and latest government scheme guidelines as regulations and prices change frequently.*
"""

        return section


# Initialize globally
from typing import Dict
indian_context_generator = IndianMarketContextGenerator()
