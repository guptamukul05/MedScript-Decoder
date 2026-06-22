<div align="center">

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white"/>
<img src="https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black"/>
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>

# 🏥 MedScript Decoder

**AI-Powered Medical Prescription & Lab Report Intelligence Platform**

*Transforming unstructured medical documents into clear, actionable patient insights*

</div>

---

## 🎯 What is MedScript Decoder?

MedScript Decoder is an end-to-end AI healthcare platform that reads medical prescriptions and lab reports, extracting structured insights that patients can actually understand. From medicine schedules and drug interactions to lab value trends and disease advisory — all powered by fine-tuned biomedical NLP models, medical APIs, and generative AI.

The platform is **privacy-preserving and locally deployable** — patient data never leaves the device except for anonymized AI reasoning queries.

---

## 🧠 Research Contribution

Three biomedical NLP models were fine-tuned and benchmarked on the **[BC5CDR dataset](https://huggingface.co/datasets/tner/bc5cdr)** (BioCreative V CDR Task Corpus) for Named Entity Recognition of chemical and disease entities:

| Model | Precision | Recall | F1 Score |
|:---|:---:|:---:|:---:|
| BioBERT | 0.9187 | 0.9240 | 0.9213 |
| ClinicalBERT | 0.8506 | 0.8586 | 0.8546 |
| **PubMedBERT** ✅ | **0.9137** | **0.9361** | **0.9248** |

**PubMedBERT** selected as production model — highest F1 and superior recall, critical in medical NER where missing a drug entity is more costly than a false positive.

> **Dataset:** [BC5CDR on HuggingFace](https://huggingface.co/datasets/tner/bc5cdr) — Chemical and Disease NER corpus from BioCreative V Challenge

---

## ⚙️ System Architecture

```
Medical Document (PDF / Image)
        │
        ▼
┌───────────────────────┐
│    OCR Layer          │
│  PyMuPDF (digital)    │
│  EasyOCR (scanned)    │
└──────────┬────────────┘
           │
        ▼
┌───────────────────────┐
│  NLP Extraction       │
│  PubMedBERT NER       │  ← Fine-tuned on BC5CDR
│  Regex Pipeline       │
│  Patient/Doctor Info  │
└──────────┬────────────┘
           │
        ▼
┌───────────────────────┐
│  Information Layer    │
│  OpenFDA API          │
│  RxNorm API           │
│  Indian Med Database  │
└──────────┬────────────┘
           │
        ▼
┌───────────────────────┐
│  AI Reasoning         │
│  Groq LLaMA-3.3-70B   │  ← Symptom analysis, interactions,
│                       │    disease advisory, translation
└──────────┬────────────┘
           │
        ▼
┌───────────────────────┐
│  Streamlit Interface  │
│  4 Dashboards         │
│  Patient Portal       │
└───────────────────────┘
```

---

## ✨ Features

### 📋 Prescription Analysis
- Supports digital PDFs, scanned images, and typed text
- Auto-detects prescription type — digital vs scanned
- Extracts patient info, doctor details, registration number
- PubMedBERT NER identifies drug and disease entities
- Structured medicine cards — dosage, frequency, duration, timing
- Drug purpose and warnings from OpenFDA + RxNorm APIs
- Tests ordered and clinical complaints displayed separately

### 🧪 Lab Report Analysis
- Multi-page lab report PDFs from any diagnostic lab
- Dynamic reference range extraction — reads ranges from the report itself, no hardcoded values
- Abnormal values in color-coded table 🔴 HIGH / 🟡 LOW / 🟢 NORMAL
- Groq LLaMA-3 suggests possible symptoms from abnormal values
- Interactive symptom confirmation flow
- Disease advisory combining lab values and reported symptoms
- Urgency classification — Consult Today / This Week / Routine / Normal

### 🔄 Combined Analysis
- Upload prescription and lab reports together
- Cross-reference tests ordered vs reports uploaded
- Unified summary — medicines, abnormal values, urgency in one view

### 📈 Report Trend Tracking
- SQLite stores patient report history locally
- Trend table across multiple report dates
- Test name normalization — handles synonym variants across labs
- Overall trend direction with context — Improving / Worsening / Stable
- Interactive Plotly charts with normal range shading

### 💊 Medicine Interaction Checker
- User enters existing regular medicines
- All combinations checked against prescription medicines
- Groq LLaMA-3 analyzes with clinical pharmacology knowledge
- Three severity levels — 🔴 Serious / 🟡 Moderate / 🟠 Mild

### 📅 Calendar Reminders
- Generates .ics calendar file — works with Google Calendar, Apple, Outlook
- One reminder per medicine per dose per day
- Handles different durations per medicine independently
- Last dose reminder — "Do not take further" notification

### 🌐 Multilingual Output
- 10 Indian languages — Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, English
- Medicine names preserved in English, instructions translated
- Language selector applies across all dashboards

### 🔊 Voice Output
- Text-to-speech of patient report in selected language
- Powered by gTTS — runs locally, no API needed
- Audio playback directly in browser

### 👤 Patient Portal
- Register and login with secure password hashing
- Upload and store prescriptions, lab reports, test results
- Each record tagged with date, doctor, clinic, and visit reason
- Search and filter through complete medical history
- Local SQLite database — all data stays on device

---

## 🛠️ Tech Stack

| Layer | Technology |
|:---|:---|
| Language | Python 3.10+ |
| NER Models | BioBERT · PubMedBERT · ClinicalBERT |
| Model Training | HuggingFace Transformers · PyTorch · Seqeval |
| NER Dataset | [BC5CDR](https://huggingface.co/datasets/tner/bc5cdr) |
| OCR | EasyOCR · PyMuPDF |
| Drug APIs | OpenFDA API · RxNorm API |
| AI Reasoning | Groq API — LLaMA-3.3-70B |
| Database | SQLite |
| UI Framework | Streamlit |
| Visualization | Plotly · Pandas |
| Voice | gTTS |
| Calendar | iCalendar (.ics) |

---

## 📁 Project Structure

```
MedScript-Decoder/
├── src/
│   ├── ocr_pipeline.py         # PDF and image text extraction
│   ├── ner_pipeline.py         # PubMedBERT NER + medicine extraction
│   ├── openfda_api.py          # OpenFDA, RxNorm, interaction checker
│   ├── rxnorm_api.py           # RxNorm drug profile
│   ├── report_generator.py     # Lab report parser + Groq AI analysis
│   └── trend_tracker.py        # SQLite trend tracking
├── notebooks/
│   └── model_comparison.ipynb  # BioBERT vs PubMedBERT vs ClinicalBERT
├── results/
│   ├── metrics/                # F1 scores, evaluation JSON
│   └── plots/                  # Model comparison plots
├── data/
│   └── medscript.db            # Local SQLite database
├── outputs/                    # Generated reports and calendar files
├── app.py                      # Main Streamlit application
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

**1. Clone the repository**
```bash
git clone https://github.com/guptamukul05/MedScript-Decoder.git
cd MedScript-Decoder
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

**4. Configure environment**
```bash
cp .env.example .env
# Add your Groq API key to .env
```

**5. Run the application**
```bash
streamlit run app.py
```

---

## 🔐 Environment Variables

```env
GROQ_API_KEY=your_groq_api_key_here
OPENFDA_BASE_URL=https://api.fda.gov/drug
OCR_LANGUAGE=en
APP_NAME=MedScript Decoder
APP_VERSION=1.0.0
```

---

## 🌐 APIs

| API | Purpose |
|:---|:---|
| [OpenFDA](https://open.fda.gov/apis/) | Drug labels, warnings, side effects |
| [RxNorm](https://lhncbc.nlm.nih.gov/RxNav/) | Generic names, drug classification |
| [Groq](https://console.groq.com) | LLaMA-3.3-70B for AI reasoning |

---

## 📊 Dataset

**[BC5CDR — BioCreative V CDR Task Corpus](https://huggingface.co/datasets/tner/bc5cdr)**
- Chemical and Disease Named Entity Recognition
- Used for fine-tuning BioBERT, PubMedBERT, and ClinicalBERT
- Evaluation metric: Seqeval F1 Score

---

<div align="center">

**⭐ Star this repository if you find it useful**

[GitHub](https://github.com/guptamukul05/MedScript-Decoder) · [Report Bug](https://github.com/guptamukul05/MedScript-Decoder/issues) · [Request Feature](https://github.com/guptamukul05/MedScript-Decoder/issues)

</div>