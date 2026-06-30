# Suraksha Chakra AI

AI-powered predictive labour intelligence and climate vulnerability platform for protecting migrant workers and vulnerable communities.

---

## The Problem

Every major disaster creates a critical window during which displaced and vulnerable populations face elevated risk of:

- Wage theft
- Forced labour
- Human trafficking
- Fraudulent contractors
- Unsafe migration
- Information asymmetry

Existing systems respond only after exploitation has already occurred. Suraksha Chakra AI is built to predict vulnerability before exploitation begins.

---

## Vision

Suraksha Chakra AI is a nationwide early warning network that combines labour intelligence, climate signals, migration trends, public datasets, and worker-submitted reports to identify vulnerable communities in advance.

Rather than functioning as an isolated complaint system, it operates as an intelligence layer connecting workers, NGOs, labour departments, and disaster response agencies.

---

## Stakeholders

### Workers
- AI-driven wage verification
- Anonymous complaint registration
- Contractor risk verification
- Voice and WhatsApp interface
- Automated legal notice generation
- **End-to-End Multilingual Support** (Text & Voice in regional languages)

### NGOs
- District-level vulnerability forecasting
- Disaster monitoring
- High-risk district identification
- Field deployment planning
- Trafficking prevention intelligence

### Labour Departments
- Complaint investigation
- Contractor monitoring
- Legal notice management
- Enforcement analytics
- Inspection planning

---

## Current Implementation for Prototype

**Worker Platform**
- Wage verification against official BOCW wage schedules
- Voice and text interaction
- **Multilingual Support**: Fully localized UI, contextual LLM replies, and native text-to-speech (TTS) for **English, Hindi, Tamil, Bengali, and Marathi**.
- Contractor verification
- Anonymous complaint reporting
- Legal notice generation

**NGO Dashboard**
- District vulnerability forecasting
- Migration analytics
- Contractor risk intelligence
- Labour complaint summaries

**Labour Officer Dashboard**
- Complaint management
- Investigation workflow
- Contractor monitoring
- Legal notice downloads

---

## System Architecture

```
Public Datasets
  - Wage notifications
  - Weather data
  - Crime statistics
        |
Statistical Data Engineering
        |
Data Cleaning and Feature Engineering
        |
Machine Learning Inference
        |
Composite Vulnerability Intelligence
        |
   -----------------------------------
   |              |                  |
Worker AI    NGO Portal      Officer Portal
```

---

## AI Pipeline

1. Worker input (voice or text)
2. Speech recognition (Sarvam AI for regional languages, Groq Whisper fallback)
3. Intent extraction & Translation (Groq, Llama 3 - dynamically locked to user's selected language)
4. Labour intelligence engine (RAG over wage schedules)
5. Risk assessment (contractor scoring)
6. Complaint database (SQLite)
7. Predictive vulnerability model (scikit-learn)
8. **Text-to-Speech (Edge TTS)** dynamically generating voice responses in native regional voices.
9. NGO and officer dashboards

---

## Statistical Data Engineering

The predictive model combines structured features from multiple data sources.

Current features:
- Historical crime ratios
- Migration intensity
- Flood severity
- Active wage reports
- District-level indicators

Pipeline:

```
Raw Data → Cleaning → Normalization → Feature Engineering
→ ML Inference → Composite Vulnerability Score
```

The model is a logistic regression classifier trained on a synthetic dataset of 1,000 samples across 50 district archetypes in Uttar Pradesh and Bihar, achieving an ROC-AUC of 0.861 on held-out test data. Logistic regression was chosen for interpretability — each coefficient maps directly to a risk factor that can be explained to policymakers and field officers.

---

## Public Data Sources

- Ministry of Labour and Employment (BOCW wage notifications)
- National Crime Records Bureau (NCRB)
- Census of India
- Periodic Labour Force Survey (PLFS)
- India Meteorological Department / OpenWeather
- National Disaster Management Authority (NDMA)
- Worker-generated reports (primary data, collected in-app)

---

## Technology Stack

**Frontend**
React, CSS Modules

**Backend**
FastAPI, SQLite, SQLAlchemy

**AI**
Groq (Llama 3), Sarvam AI (speech-to-text), Edge TTS (text-to-speech)

**Machine Learning**
scikit-learn, pandas, NumPy

**Search and Retrieval**
FAISS, LangChain, sentence-transformers

**Communication**
Twilio (WhatsApp), SendGrid

---

## Future Roadmap

**Predictive Intelligence**
- News NLP for emerging disaster signals
- Social media sentiment analysis
- Satellite flood detection
- River basin monitoring
- Climate anomaly forecasting

**Data Expansion**
- Panchayat and village-level intelligence
- Block-level vulnerability mapping
- Government open-data integrations
- NGO field validation pipeline

**Machine Learning**
- Online model retraining using verified reports
- Graph neural networks for migration route modelling
- Time-series forecasting of exploitation windows
- Explainable AI (SHAP) for vulnerability score breakdowns

**Worker Empowerment**
- Offline-first mobile application
- IVR support for feature phones
- OCR document verification
- Aadhaar/CSC-assisted identity verification
- Digital evidence collection

**Government Integration**
- Labour department workflow integration
- Disaster Management Authority dashboard
- Police referral workflows
- Real-time inspection scheduling
- Automated district-level alerts

---

## Impact

Suraksha Chakra AI is built to shift labour protection from a reactive complaint system to a predictive intelligence platform capable of identifying vulnerable communities before exploitation occurs.
