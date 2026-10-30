# Carbon Coach 🌿

> **A conversational sustainability coach for students, families, and campuses built with Google ADK (Agent Development Kit) for Python and Gemini.**

---

## 🏛️ Architecture Highlights
1. **Google ADK Framework**: Built using official Google ADK (`google-adk`) with Gemini (`gemini-3.5-flash-lite`).
2. **Zero-Hallucination Tool Core**: All emissions figures and savings are calculated by deterministic Python functions in `factors.py` & `tools.py` citing DEFRA, CEA India, BEE, and IPCC—the LLM never estimates or performs arithmetic.
3. **Telugu & Multilingual Voice (STT & TTS)**: Native Web Speech API integration with live microphone support (`te-IN`, `hi-IN`, `en-IN`), dynamic multilingual prompt chips, and synthesized voice audio readout.
4. **Dark & Light Mode Switcher**: Rich emerald-dark glassmorphism design system with an instant, persistent toggle to crisp eco-mint light mode.
5. **Session Memory**: Stateful tracking (`ToolContext.state["activities"]`) stores logged footprints across conversation turns, powering dynamic circular gauges and weekly summaries.
6. **Actionable Suggestions & Nature Impact**: Rule-based reduction engine (`suggest_reductions`) calculates exact kg CO₂e savings and explains positive nature impacts (cleaner air, PM2.5 reduction, coal saved).
7. **Cloud Run Ready**: Containerized with a production `Dockerfile` and `run_production.py` for automated serverless scaling on Google Cloud Run.

---

## 📁 Project Structure

```text
gdg_hackathon/
├── carbon_coach/
│   ├── __init__.py               # Package export (auto-loads .env & syncs API keys)
│   ├── agent.py                  # Primary root_agent with zero-hallucination prompt
│   ├── agent_multi.py            # Bonus multi-agent coordinator (tracker + coach)
│   ├── factors.py                # Plain dicts of emission factors with cited sources
│   ├── tools.py                  # 9 calculation, logging, summary, tip & board tools
│   ├── evals/
│   │   ├── carbon_coach.evalset.json   # 8 golden test cases in official ADK schema
│   │   └── test_config.json            # ADK evaluation criteria configuration
│   └── tests/
│       ├── test_tools.py         # Pytest unit tests for all tools (20 tests)
│       └── test_simulation.py   # Multi-turn demo sequence simulation test
├── frontend/
│   ├── index.html                # Modern dashboard layout with gauge & chat
│   ├── styles.css                # Emerald dark & light mode glassmorphism
│   └── app.js                    # Web Speech STT/TTS, ADK client, circular gauge math
├── frontend_server.py            # FastAPI reverse proxy gateway on port 3000
├── run_production.py             # Single entrypoint for Google Cloud Run
├── Dockerfile                    # Production container configuration
├── .dockerignore                 # Excludes local virtualenvs and secrets
├── .gitignore                    # Prevents leaking .env or cache files
├── requirements.txt              # Project dependencies
└── README.md                     # Setup, testing, deployment & demo script
```

---

## ⚡ Quickstart & Setup

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/Rishitha73/HackFest.git
cd HackFest

python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

---

## 🖥️ Running Locally

### Step 1: Start the Google ADK Agent Server
```bash
python -m google.adk.cli web .
```
*ADK runtime starts on `http://127.0.0.1:8000`.*

### Step 2: Start the Web Dashboard
In a second terminal:
```bash
python frontend_server.py
```
*Open **`http://localhost:3000`** in your browser!*

### Step 3: (Optional) Expose via Public HTTPS Tunnel for Mobile & Evaluators
```bash
npx -y localtunnel --port 3000
```
*Provides a public HTTPS URL enabling microphone access on mobile phones.*

---

## 🎙️ Multilingual & Voice Features

- **Microphone (Speech-to-Text)**: Tap the `🎙️` icon to speak your activities in **Telugu (`te-IN`)**, **English (`en-IN`)**, or **Hindi (`hi-IN`)**.
- **Dynamic Suggestions**: When you switch the `🌐` language dropdown, all quick suggestion chips and chat headers automatically translate to that language.
- **Voice Reply (Text-to-Speech)**: The coach speaks replies aloud using browser speech synthesis with native pronunciation.
- **Zero Hallucination across Languages**: Gemini translates regional phrases (e.g. *"నేను ఈరోజు 50 కిమీ బైక్ మీద ప్రయాణించాను"*) into deterministic tool calls (`calculate_travel_emissions(mode="two_wheeler", km=50)`) and responds back in natural Telugu.

---

## 🌓 Dark & Light (White) Mode

Click the **`☀️ Light Mode` / `🌙 Dark Mode`** toggle in the top navigation bar. The app features:
- **Dark Mode**: Deep forest emerald glassmorphism (`#070b09`) with luminous borders.
- **Light Mode**: Crisp eco-mint frosted glass (`#f2faf5`) with high-contrast slate text.
- Preferences automatically persist in `localStorage`.

---

## ☁️ Deployment to Google Cloud Run

Carbon Coach is fully configured for serverless production deployment on **Google Cloud Run**:

### Option A: Using Google Cloud Shell (Free & Instant in Browser)
1. Open [shell.cloud.google.com](https://shell.cloud.google.com).
2. Clone your repo and deploy:
   ```bash
   git clone https://github.com/Rishitha73/HackFest.git
   cd HackFest
   gcloud run deploy carbon-coach \
     --source . \
     --port 8080 \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_API_KEY="YOUR_GEMINI_KEY",GEMINI_MODEL="gemini-3.5-flash-lite"
   ```

### Option B: Using Google Cloud Console
1. Go to [Google Cloud Run Console](https://console.cloud.google.com/run).
2. Click **Create Service** -> **Continuously deploy from a repository** -> select `Rishitha73/HackFest`.
3. Select **Dockerfile** as the build configuration.
4. Add environment variables `GOOGLE_API_KEY` and `GEMINI_MODEL=gemini-3.5-flash-lite`.
5. Click **Create** to receive a public `https://carbon-coach-xxxx.a.run.app` endpoint.

---

## 🧪 Testing & Evaluation

### Run Unit Tests (21 automated pytest tests)
```bash
python -m pytest carbon_coach/tests/ -v
```
All 21 unit and simulation tests validate:
- Travel, electricity, food, and waste calculations
- Input validation, negative values, and bound constraints
- Session state persistence and cumulative memory
- Telugu & English tool parameter extraction
- Benchmark calculations and nature impact ratings

### Run Official Google ADK Evaluations
```bash
python -m google.adk.cli eval carbon_coach carbon_coach/evals/carbon_coach.evalset.json --config_file_path carbon_coach/evals/test_config.json
```

---

## 📊 Emission Factor Sources

All conversion factors are centralized in [`carbon_coach/factors.py`](carbon_coach/factors.py):

| Category | Item | Factor Value | Cited Source |
| :--- | :--- | :--- | :--- |
| **Travel** | Bus | 0.089 kg CO₂e / pass-km | UK DEFRA GHG Factors |
| **Travel** | Petrol Car | 0.170 kg CO₂e / pass-km | UK DEFRA / ARAI India |
| **Travel** | Metro | 0.030 kg CO₂e / pass-km | Indian Urban Metro Transit |
| **Travel** | Two-Wheeler | 0.070 kg CO₂e / pass-km | ARAI India commuter scooter |
| **Electricity**| India Grid | 0.710 kg CO₂e / kWh | CEA CO2 Baseline (Ver 19) |
| **Appliance** | 1.5-Ton AC | 1.500 kW | BEE Star Rating standard |
| **Appliance** | Ceiling Fan | 0.075 kW | BEE Standard 75W Fan |
| **Food** | Chicken Meal | 1.600 kg CO₂e / meal | Poore & Nemecek (Science) |
| **Food** | Veg Meal | 0.700 kg CO₂e / meal | Poore & Nemecek / OWID |
| **Food** | Mutton Meal | 5.000 kg CO₂e / meal | Poore & Nemecek (Science) |
| **Waste** | Landfill Waste| 0.450 kg CO₂e / kg | IPCC Waste Sector Guidelines |
| **Benchmark** | Daily Indian | 5.000 kg CO₂e / person/day | World Bank / OWID (1.9 t/yr) |

---

## 👥 Hackathon Team & License
Built with ❤️ for the GDG Hackathon using Google ADK & Gemini. Released under the Apache 2.0 License.