# Suraksha Chakra AI
**AI-Powered Predictive Safety & Labour Intelligence Platform for Climate-Vulnerable Communities**


Suraksha Chakra AI is an AI-powered early warning platform that combines labour rights intelligence, crowdsourced wage reports, contractor risk scoring, and climate vulnerability forecasting into a unified decision-support system for workers, NGOs, labour departments, and disaster management authorities.

Rather than responding after exploitation occurs, the platform continuously learns from worker reports and public datasets to identify unsafe contractors, detect exploitation patterns, and forecast vulnerable districts before disasters increase the risk of women trafficking,forced marriage, wage theft, and forced labour. 

It does not rely on manually assigned district scores. I made district-level features from multiple public datasets like migration intensity, historical crime trends, disaster frequency, socioeconomic vulnerability, and live crowdsourced wage reports. These standardized features are combined into a composite vulnerability index. As more real worker reports are collected, the model transitions from rule-based scoring to a data-driven predictive model.


---



## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook/whatsapp` | Twilio WhatsApp webhook |
| POST | `/api/wages/query` | Query fair wage (PWA) |
| GET  | `/api/wages/occupations` | Occupation list |
| POST | `/api/reports/submit` | Submit wage report |
| POST | `/api/reports/contractor-check` | Check contractor risk |
| GET  | `/api/reports/contractors/high-risk` | High-risk contractor list |
| GET  | `/api/dashboard/overview` | Dashboard summary stats |
| GET  | `/api/dashboard/district-heatmap` | Per-district report data |
| GET  | `/api/dashboard/vulnerability-scores` | Predictive scores |
| GET  | `/api/dashboard/recent-alerts` | Alert activity feed |

## Architecture




## Data Sources (all free, all public)

- **BOCW wage schedules**: labour.gov.in (state-wise)
- **NCRB crime data**: ncrb.gov.in 
- **IMD weather**: api.imd.gov.in
- **NDMA displacement**: ndma.gov.in
- **Migration flows**: Census 2011 + PLFS (mospi.gov.in)


