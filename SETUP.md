# 🚀 Quick Setup Guide

Get the Pharmaceutical Product Monograph Generator running in 5 minutes.

---

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Active Anthropic API key (get one at https://console.anthropic.com)

---

## Installation (5 minutes)

### Step 1: Clone & Navigate
```bash
cd ~/monograph-generator
```

### Step 2: Create Virtual Environment (Optional but recommended)
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys
```bash
# Copy template
cp .env.example .env

# Edit .env and add your Anthropic API key
# On macOS/Linux
nano .env

# On Windows
notepad .env
```

Set `ANTHROPIC_API_KEY=sk-ant-...your-key...`

### Step 5: Create Data Directories
```bash
mkdir -p data/monographs data/skill_files data/feedback
```

---

## Launch (1 command)

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## First Generation (Try This!)

1. **Open the web interface** at http://localhost:8501
2. **Paste your API key** in the sidebar
3. **Type "Metformin"** in the molecule name field
4. **Click "Generate Monograph"** and wait ~45 minutes
5. **Download the PDF** from the "View" tab

---

## Troubleshooting

### "Command not found: streamlit"
→ Verify pip installation: `pip list | grep streamlit`
→ Try: `python -m streamlit run app.py`

### "Invalid API key"
→ Check your .env file
→ Verify API key is active at https://console.anthropic.com/account/billing/overview

### "PubMed rate limit exceeded"
→ Wait 60 seconds and try again
→ The system automatically retries

### "Low memory"
→ Reduce `max_results` slider to 20-30 articles
→ Close other applications

---

## Configuration

### .env Parameters

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
MAX_TOKENS=2000                    # Max tokens per section
TEMPERATURE=0.3                    # Lower = more deterministic
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Latest recommended
PUBMED_TIMEOUT=10                  # Seconds before timeout
GENERATION_TIMEOUT=60              # Seconds per section
```

### App Settings (Sidebar)

- **Include diagrams & charts**: Add visual elements to PDF
- **Auto-validate**: Run compliance checks before delivery
- **Generate PDF**: Create PDF output (vs JSON only)

---

## What Gets Generated

After each monograph generation, you'll find:

```
data/monographs/
├── Metformin_monograph_20240608_143022.pdf  ← Download this!
├── validation_report_20240608_143022.json   ← Detailed metrics
└── ...
```

---

## Next Steps

1. **Generate first monograph** (Metformin recommended)
2. **Review validation report** on the "Validate" tab
3. **Check SOP compliance** score (target: ≥90%)
4. **Download PDF** for medical expert review
5. **Provide feedback** via the "Learn" tab to improve future generations

---

## Performance Expectations

| Task | Time |
|------|------|
| Data retrieval | 5-10 min |
| Section generation | 20-30 min |
| Validation | <2 min |
| PDF creation | 1-2 min |
| **TOTAL** | **<45 min** ✓ |

---

## Cost Calculator

| Usage | Cost |
|-------|------|
| 1 monograph | ~$0.15 |
| 10 monographs | ~$1.50 |
| 100 monographs/year | ~$15 |

---

## Getting Help

**Issue?** Check these resources:

1. **README.md** - Full documentation
2. **Validation report** - Specific compliance issues
3. **Example molecules** - Test with Aspirin, Lisinopril, Omeprazole
4. **Logs** - Check terminal output for API errors

---

## Advanced: Self-Hosted Deployment

### Docker
```bash
# Build image
docker build -t monograph-generator .

# Run container
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key monograph-generator
```

### Streamlit Cloud (Free)
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Create new app → select your repo
4. Set `ANTHROPIC_API_KEY` in settings
5. Deploy! ✓

---

## Tips for Success

✅ **DO:**
- Start with well-studied molecules (Metformin, Aspirin)
- Set max_results to 50 for balance of speed/quality
- Review validation reports carefully
- Have an expert review before using monographs

❌ **DON'T:**
- Use API key in version control (use .env)
- Distribute PDFs without medical review
- Trust compliance score alone (always verify)
- Forget to add disclaimer to final documents

---

## API Rate Limits

The system respects:
- **PubMed**: 3 requests/second max
- **FDA**: 240 requests/minute max
- **Anthropic**: Token budgets and concurrent requests

Built-in retry logic with exponential backoff handles rate limits automatically.

---

**Ready?** Run `streamlit run app.py` and generate your first monograph! 🎉
