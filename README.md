<div align="center">

# 🏥 MedScript Decoder

### AI-Powered Medical Prescription & Lab Report Intelligence Platform

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white"/>
<img src="https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black"/>
<img src="https://img.shields.io/badge/Groq-00A67E?style=for-the-badge&logo=groq&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>

*Transforming unstructured medical documents into clear, actionable patient insights*

[View Demo](https://github.com/guptamukul05/MedScript-Decoder) · [Report Bug](https://github.com/guptamukul05/MedScript-Decoder/issues) · [Request Feature](https://github.com/guptamukul05/MedScript-Decoder/issues)

</div>

---

## What is MedScript Decoder?

MedScript Decoder is an end-to-end AI healthcare platform that reads medical prescriptions and lab reports, extracting structured insights that patients can actually understand. From medicine schedules and drug interactions to lab value trends and disease advisory -all powered by fine-tuned biomedical NLP models, medical APIs, and generative AI.

The platform is **privacy-preserving and locally deployable** — all patient data stays on the device. Only anonymized AI reasoning queries reach external servers.

---

## Research Contribution

Three biomedical NLP models were fine-tuned and benchmarked on the **[BC5CDR dataset](https://huggingface.co/datasets/tner/bc5cdr)** (BioCreative V CDR Task Corpus) for Named Entity Recognition of chemical and disease entities from PubMed abstracts.

| Model | Precision | Recall | F1 Score |
|:---|:---:|:---:|:---:|
| ClinicalBERT | 0.8506 | 0.8586 | 0.8546 |
| BioBERT | 0.9187 | 0.9240 | 0.9213 |
| **PubMedBERT** ✅ | **0.9137** | **0.9361** | **0.9248** |

**PubMedBERT** selected as the production model — highest F1 and superior recall. In medical NER, recall matters more than precision because missing a drug entity is more dangerous than a false positive. PubMedBERT achieves this by being pre-trained from scratch exclusively on biomedical text, giving it cleaner vocabulary for drug and disease names compared to models initialized from general BERT weights.

---

## System Architecture

```
Medical Document (PDF / Image)
          │
          ▼
┌─────────────────────────┐
│       OCR Layer         │
│  PyMuPDF  →  Digital    │
│  EasyOCR  →  Scanned    │
└───────────┬─────────────┘
            │
          ▼
┌─────────────────────────┐
│    NLP Extraction        │
│  PubMedBERT NER         │  ← Fine-tuned on BC5CDR
│  Regex Pipeline         │  ← Dosage, timing, duration
│  Patient/Doctor Info    │  ← Name, reg number, date
└───────────┬─────────────┘
            │
          ▼
┌─────────────────────────┐
│  Information Layer      │
│  OpenFDA API            │  ← Drug labels, warnings
│  RxNorm API             │  ← Generic names, drug class
│  Indian Med Database    │  ← 80+ Indian brand medicines
└───────────┬─────────────┘
            │
          ▼
┌─────────────────────────┐
│    AI Reasoning         │
│  Groq LLaMA-3.3-70B    │  ← Symptoms, interactions,
│                         │    disease advisory, translation
└───────────┬─────────────┘
            │
          ▼
┌─────────────────────────┐
│  Streamlit Interface    │
│  4 Dashboards           │
│  Patient Portal         │
└─────────────────────────┘
```

---

## Features

### 📋 Prescription Analysis
- Supports digital PDFs, scanned images, and typed text input
- Auto-detects prescription type — digital vs scanned with separate handling
- Handwritten prescriptions — manual correction option before analysis
- Extracts patient info — name, age, gender, date of visit
- Extracts doctor info — name, qualification, registration number
- PubMedBERT NER identifies drug and disease entities from text
- Structured medicine cards with dosage, frequency, duration, and timing
- Drug purpose, warnings and side effects fetched from OpenFDA and RxNorm
- Tests ordered by doctor displayed separately
- Symptoms and clinical complaints detection from prescription text
- Prescription authenticity check — validates registration number, patient name, date, qualification, and medicines listed with an overall authenticity score

### 🧪 Lab Report Analysis
- Multi-page lab report PDFs from any diagnostic lab
- Dynamic reference range extraction — reads ranges directly from each report
- Works for any lab — Dr Lal PathLabs, SRL, Metropolis, Apollo — no lab-specific configuration
- Abnormal values displayed in color-coded table 🔴 HIGH 🟡 LOW 🟢 NORMAL
- Groq LLaMA-3 suggests possible symptoms based on abnormal values
- Interactive flow — user confirms symptoms, then AI suggests possible conditions
- Alternative path — user describes different symptoms, AI analyzes combination
- Routine checkup path — no symptoms, AI gives lifestyle advisory
- Urgency classification — Consult Today / This Week / Routine / Normal
- Medical disclaimer on all AI-generated content

### 🔄 Combined Analysis
- Upload prescription and lab reports together in one view
- Cross-reference between tests ordered in prescription and reports uploaded
- Unified summary with medicines, abnormal values, and urgency

### 📈 Report Trend Tracking
- SQLite stores patient report history locally on device
- Trend table across multiple report dates with color indicators per value
- Test name normalization handles synonym variants across different labs
- SGPT, ALT, and ALT (SGPT) all treated as the same parameter automatically
- Overall trend direction — first report vs latest report
- Shows Improving, Worsening, or Stable with percentage change
- Interactive Plotly charts with normal range shading
- Multi-parameter selection for comparative graphs
- Works with any number of reports over time

### 💊 Medicine Interaction Checker
- User optionally enters existing regular medicines
- All combinations checked between prescription and regular medicines
- Groq LLaMA-3 analyzes with clinical pharmacology knowledge
- Three severity levels — 🔴 Serious / 🟡 Moderate / 🟠 Mild
- Only problematic combinations displayed, clean and focused output

### 📅 Calendar Reminders
- Generates standard .ics calendar file compatible with all calendar apps
- One reminder per medicine per dose per day with correct timing
- Handles different durations per medicine independently
- Last dose gets special reminder — Do not take further notification
- Works with Google Calendar, Apple Calendar, Outlook, Android, iOS
- Step-by-step import instructions shown to user
- No login or email required

### 🌐 Multilingual Output
- 10 Indian languages — Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, English
- Language selector in sidebar applies across all dashboards
- Medicine names preserved in English, instructions translated
- Powered by Groq LLaMA-3 for natural, contextually accurate translations

### 🔊 Voice Output
- Text-to-speech of the complete patient report in selected language
- Language matches the multilingual selector automatically
- Powered by gTTS — runs locally, no additional API required
- Audio playback directly in browser with download option

### 👤 Patient Portal
- Register via email or mobile number with password
- Email format validation and Indian mobile number validation
- Date of birth calendar picker with automatic age calculation
- Secure login with PBKDF2 password hashing and 100,000 iterations
- Profile section — name, DOB, gender, blood group, phone, email
- Upload and store prescriptions, lab reports, and test results
- Each record tagged with date, doctor name, clinic, and reason for visit
- Search and filter records by name, doctor, clinic, or reason
- Sort records by newest or oldest
- One-click analyze — open any saved prescription or report directly in the analyzer
- Download any saved document
- All data stored locally in SQLite — nothing leaves the device

---

## Tech Stack

| Layer | Technology |
|:---|:---|
| Language | Python 3.10+ |
| NER Models | BioBERT · PubMedBERT · ClinicalBERT |
| Model Training | HuggingFace Transformers · PyTorch · Seqeval |
| NER Dataset | [BC5CDR — BioCreative V CDR Corpus](https://huggingface.co/datasets/tner/bc5cdr) |
| OCR | EasyOCR · PyMuPDF |
| Drug APIs | OpenFDA API · RxNorm API |
| AI Reasoning | Groq API — LLaMA-3.3-70B |
| Database | SQLite |
| UI Framework | Streamlit |
| Visualization | Plotly · Pandas |
| Voice | gTTS |
| Calendar | iCalendar (.ics) RFC 5545 |

---

## Project Structure

```
MedScript-Decoder/
├── src/
│   ├── ocr_pipeline.py         # PDF and image text extraction
│   ├── ner_pipeline.py         # PubMedBERT NER + medicine extraction
│   ├── openfda_api.py          # OpenFDA, RxNorm, interaction checker
│   ├── rxnorm_api.py           # RxNorm drug profile API
│   ├── report_generator.py     # Lab report parser + Groq AI analysis
│   ├── trend_tracker.py        # SQLite trend tracking
│   ├── patient_portal.py       # Authentication and medical records
│   └── main_pipeline.py        # End-to-end pipeline connector
├── notebooks/
│   └── model_comparison.ipynb  # BioBERT vs PubMedBERT vs ClinicalBERT
├── results/
│   ├── metrics/                # F1 scores, evaluation JSON, comparison CSV
│   └── plots/                  # Model comparison visualizations
├── data/                       # Local SQLite database (gitignored)
├── app.py                      # Main Streamlit application
├── requirements.txt
├── .env.example
└── README.md
```

---

## Getting Started

**Clone the repository**
```bash
git clone https://github.com/guptamukul05/MedScript-Decoder.git
cd MedScript-Decoder
```

**Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**Install dependencies**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

**Configure environment**
```bash
cp .env.example .env
# Add your Groq API key to .env
# Free key available at console.groq.com
```

**Run the application**
```bash
streamlit run app.py
```

---

## Environment Variables

```env
GROQ_API_KEY=your_groq_api_key_here
OPENFDA_BASE_URL=https://api.fda.gov/drug
OCR_LANGUAGE=en
APP_NAME=MedScript Decoder
APP_VERSION=1.0.0
```

---

## External APIs

| API | Purpose |
|:---|:---|
| [OpenFDA](https://open.fda.gov/apis/) | Drug labels, warnings, side effects — free, no key required |
| [RxNorm](https://lhncbc.nlm.nih.gov/RxNav/) | Generic name mapping, drug classification — free, no key required |
| [Groq](https://console.groq.com) | LLaMA-3.3-70B for AI reasoning — free tier, 1500 requests/day |

---

<div align="center">

**⭐ If you find this project useful, please consider starring the repository**

[GitHub](https://github.com/guptamukul05/MedScript-Decoder) · [Issues](https://github.com/guptamukul05/MedScript-Decoder/issues)

</div>