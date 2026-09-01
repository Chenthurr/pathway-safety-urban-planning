# 🌆 Pathway Safety Urban Planning

[![Pathway](https://img.shields.io/badge/Powered%20by-Pathway%20AI-blue.svg)](https://pathway.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)

> Real-time anomaly detection and urban planning system using **Pathway's LLM App** with dynamic RAG capabilities.

![Dashboard Preview](https://via.placeholder.com/800x400/1e3a8a/ffffff?text=City+Operations+Center)

## 🚀 Features

### Public Safety & Anomaly Detection
- **Real-time ingestion** of safety alerts, social media feeds, and IoT sensors
- **Dynamic anomaly detection** with configurable YAML-based rules
- **LLM-powered semantic analysis** for contextual threat assessment
- **Live threat monitoring** via REST API and WebSocket

### Urban Planning Assistant
- **Integration** with transit, traffic, and environmental data streams
- **Real-time city status** visualization with windowed aggregations
- **Predictive resource allocation** insights via LLM summarization
- **Holistic city health dashboard**

### Pathway LLM App Integration
- **VectorStoreServer** for live document indexing (auto-updates as data changes)
- **BaseRAGQuestionAnswerer** for RAG Q&A over city data
- **Native REST API** via `pw.io.http.rest_connector` — no FastAPI/Flask needed
- **Hybrid search** (usearch + Tantivy) for fast vector + text retrieval

---

## 📁 Project Structure

```
pathway-safety-urban-planning/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── config/
│   ├── app.yaml                # Unified mode config
│   ├── public_safety.yaml      # Safety mode config
│   └── urban_planning.yaml     # Planning mode config
├── data/
│   ├── safety_feeds/
│   │   ├── alerts.csv          # Safety alerts stream
│   │   └── iot_sensors.csv     # IoT sensor readings
│   └── city_data/
│       ├── traffic.csv         # Traffic data
│       ├── transit.csv         # Transit data
│       └── environment.csv     # Environmental data
├── frontend/
│   └── dashboard.html          # Real-time ops dashboard
├── scripts/
│   ├── start.py                # Cross-platform launcher
│   ├── start.sh                # Unix launcher
│   └── start.bat               # Windows launcher
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── schemas.py              # Pathway schemas
│   ├── connectors.py           # Data ingestion
│   ├── safety_pipeline.py      # Anomaly detection + RAG
│   ├── planning_pipeline.py    # Urban insights
│   ├── rag_engine.py           # Unified RAG engine
│   └── api_server.py           # REST API server
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── nginx.conf
├── Procfile
├── README.md
├── render.yaml
├── requirements.txt
└── vercel.json
```

---

## 🛠️ Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### 1. Clone & Install

```bash
git clone https://github.com/your-username/pathway-safety-urban-planning.git
cd pathway-safety-urban-planning
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"
```

### 3. Launch Everything

```bash
# Using the cross-platform launcher
python scripts/start.py unified

# Or using shell script (Unix)
./scripts/start.sh unified 8080 3000

# Or start services separately
python -m http.server 3000 --directory frontend &
python src/main.py --mode unified
```

**Open your browser:**
- **Dashboard:** http://localhost:3000/dashboard.html
- **API:** http://localhost:8080
- **API Docs:** http://localhost:8080/_schema

---

## 🐳 Docker Deployment

### Docker Compose (Recommended)

```bash
# Start both backend and frontend
docker-compose up --build

# Dashboard: http://localhost:3000
# API:       http://localhost:8080
```

### Single Container

```bash
docker build -t city-ops .
docker run -p 8080:8080 -e OPENAI_API_KEY=$OPENAI_API_KEY city-ops
```

---

## ☁️ Cloud Deployment

### Render.com

1. Fork this repo to GitHub
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repo
4. Add `OPENAI_API_KEY` as an environment variable
5. Deploy!

The `render.yaml` blueprint is included for easy deployment.

### Vercel (Frontend Only)

```bash
npm i -g vercel
vercel --prod
```

The `vercel.json` config is included for static site deployment.

### Heroku

```bash
heroku create your-city-ops
heroku config:set OPENAI_API_KEY=sk-your-key
heroku config:set APP_VARIANT=unified
git push heroku main
```

---

## 🔌 API Endpoints

### Safety Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/safety/anomalies` | Get current anomalies with severity filter |

### Planning Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/planning/insights` | Get city insights by category |
| `GET`  | `/planning/status` | City health dashboard |

### RAG Endpoints (Pathway LLM App)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v2/answer` | RAG Q&A over live city data |
| `POST` | `/v1/retrieve` | Vector similarity search |
| `GET`  | `/v1/statistics` | Index health statistics |
| `GET`  | `/_schema` | Auto-generated OpenAPI docs |

### Example API Calls

```bash
# Query safety anomalies
curl -X POST http://localhost:8080/safety/anomalies   -H "Content-Type: application/json"   -d '{"severity": "high", "limit": 5}'

# RAG query over live city data
curl -X POST http://localhost:8080/v2/answer   -H "Content-Type: application/json"   -d '{"prompt": "What areas need immediate attention?"}'

# Vector similarity search
curl -X POST http://localhost:8080/v1/retrieve   -H "Content-Type: application/json"   -d '{"query": "fire emergency", "k": 3}'

# Get city status
curl http://localhost:8080/planning/status

# Get OpenAPI schema
curl http://localhost:8080/_schema
```

---

## 🖥️ Dashboard

The included `frontend/dashboard.html` provides a real-time operations center:

- **Live Safety Alerts** — Color-coded by severity (Critical/High/Medium/Low)
- **Anomaly Detection Metrics** — Active count, critical alerts, last detection
- **Traffic Status** — Avg speed, congestion level, active intersections
- **Transit Operations** — Delayed routes, avg delay, fleet status
- **Environment Monitor** — Temperature, humidity, AQI, UV index
- **AI Planning Assistant** — Interactive RAG query interface
- **Auto-refresh** — Polls every 10 seconds

![Dashboard](https://via.placeholder.com/600x300/1e293b/60a5fa?text=Dark+Theme+Dashboard)

---

## ⚙️ Configuration

### Anomaly Detection Rules
Edit `config/public_safety.yaml`:

```yaml
anomaly_rules:
  - name: high_temperature
    field: temperature_c
    condition: "> 80"
    severity: critical
  - name: crowd_density
    field: crowd_count
    condition: "> 500"
    severity: warning
```

### Data Sources
Configure streaming sources in YAML:

```yaml
sources:
  safety_alerts:
    type: csv_stream
    path: "./data/safety_feeds/alerts.csv"
    schema: SafetyAlertSchema
    mode: streaming
    refresh_interval: 2
```

### LLM Settings
```yaml
$llm: !pw.xpacks.llm.llms.OpenAIChat
  model: "gpt-4o-mini"
  temperature: 0.2
  max_tokens: 512

$embedder: !pw.xpacks.llm.embedders.OpenAIEmbedder
  model: "text-embedding-3-small"
```

---

## 🧠 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Safety Alerts  │     │  IoT Sensors    │     │  Traffic Data   │
│   (CSV Stream)  │     │  (CSV Stream)   │     │  (CSV Stream)   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────┐
                    │   Pathway Engine      │
                    │  (Incremental Compute)│
                    └──────────┬────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Rule-Based      │  │ VectorStoreServer│  │ Windowed        │
│ Anomaly Filter  │  │ (Live RAG Index) │  │ Aggregations    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                 ┌─────────────────────┐
                 │ BaseRAGQuestionAnswerer│
                 │    (/v2/answer)       │
                 └──────────┬────────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        ┌─────────────┐      ┌─────────────┐
        │ REST API    │      │ Dashboard   │
        │ (Port 8080) │      │ (Port 3000) │
        └─────────────┘      └─────────────┘
```

### Key Pathway Features

| Feature | Implementation |
|---------|---------------|
| **Streaming RAG** | `VectorStoreServer` auto-updates as alerts arrive |
| **Native REST API** | `pw.io.http.rest_connector` + `PathwayWebserver` |
| **LLM xpack** | `OpenAIChat`, `OpenAIEmbedder`, `BaseRAGQuestionAnswerer` |
| **Incremental Compute** | Only changed data is reprocessed |
| **Hybrid Search** | `usearch` vector + `Tantivy` text index |

---

## 🗺️ Roadmap

- [ ] Kafka connector for production streaming
- [ ] Geospatial joins for location-based correlation
- [ ] Slack/Teams bot integration for alerts
- [ ] Kubernetes deployment manifests
- [ ] Custom ML models for anomaly detection
- [ ] Multi-modal data (images from cameras)
- [ ] Historical trend analysis with Pathway windows

---

## 🤝 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 📧 Contact

Project Link: [https://github.com/your-username/pathway-safety-urban-planning](https://github.com/your-username/pathway-safety-urban-planning)

Built with ❤️ using [Pathway AI](https://pathway.com)
