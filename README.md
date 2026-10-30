# Carbon Coach 🌿

> **A conversational sustainability coach for students, families, and campuses built with Google ADK (Agent Development Kit) for Python.**

---

## 🏛️ Architecture in 5 Lines
1. **Google ADK Framework**: Built using Google ADK (`google-adk`) with a Gemini model configured via the `GEMINI_MODEL` environment variable (default: `gemini-2.5-flash`).
2. **Zero-Hallucination Tool Core**: All emissions figures and savings are calculated by deterministic Python functions in `factors.py` & `tools.py`—the LLM never estimates or performs math.
3. **Session Memory**: Stateful session tracking (`ToolContext.state["activities"]`) stores logged footprints across conversation turns, enabling dynamic running totals and historical trends.
4. **Actionable Suggestions**: Rule-based reduction engine (`suggest_reductions`) inspects user habits and recommends high-impact alternatives ranked by computed kg CO2e savings.
5. **Multi-Agent Coordination (Bonus)**: Clean modular design with an optional coordinator delegating to a specialized `tracker_agent` and `coach_agent`.

---

## 📁 Project Structure

```text
gdg_hackathon/
├── carbon_coach/
│   ├── __init__.py               # Package export (imports agent module)
│   ├── agent.py                  # Primary root_agent with prompt and tools
│   ├── agent_multi.py            # Bonus multi-agent coordinator (tracker + coach)
│   ├── factors.py                # Plain dicts of emission factors with cited sources
│   ├── tools.py                  # Calculation, logging, summary & tip tools
│   ├── evals/
│   │   ├── carbon_coach.evalset.json   # 8 golden test cases in official ADK schema
│   │   └── test_config.json            # ADK evaluation criteria configuration
│   └── tests/
│       ├── test_tools.py         # Pytest unit tests for all tools (20 tests)
│       └── test_simulation.py   # Multi-turn demo sequence simulation test
├── .env.example                  # Environment configuration template
├── requirements.txt              # Project dependencies
└── README.md                     # Setup, testing, deployment & demo script
```

---

## ⚡ Quickstart & Setup

### 1. Clone & Set Up Virtual Environment
```bash
# Clone the repository
git clone https://github.com/Rishitha73/HackFest.git
cd HackFest

# Create and activate virtual environment
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
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Add your Gemini API key from [Google AI Studio](https://aistudio.google.com/):
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

---

## 🖥️ Running the Application

### Option A: Custom Premium Web Dashboard (Recommended for Demo)
We built an emerald-dark glassmorphism dashboard with a live circular carbon gauge, real-time category cards, an activity feed, quick prompt chips, and conversational chat with transparent tool execution badges:

```bash
# 1. In Terminal 1: Ensure the Google ADK server is running
python -m google.adk.cli web .

# 2. In Terminal 2: Start the Custom Web Dashboard
python frontend_server.py
```
- Open **`http://localhost:3000`** in your browser!
- Watch your carbon gauge animate in real-time as you log activities or click quick-prompt chips.

### Option B: ADK Developer Web UI
Launch ADK's built-in developer inspection interface:
```bash
adk web .
# Or via python module:
python -m google.adk.cli web .
```
- Open **`http://127.0.0.1:8000`** in your browser to inspect raw ADK events, schemas, and live session traces.

---

## 🧪 Testing & Evaluation

### 1. Run Unit & Simulation Tests (No API Key Required)
Run the automated pytest suite:
```bash
python -m pytest carbon_coach/tests/ -v
```
All 21 unit and simulation tests validate:
- Distance, appliance, food, and waste calculations
- Negative numbers and invalid input rejections
- Session memory persistence and date overrides
- Today, week, and all-time summaries with benchmark comparisons
- Rule-based suggestion generation ranked by impact

### 2. Run Official ADK Evaluations
Run regression evaluations against the 8 golden eval cases:
```bash
adk eval carbon_coach carbon_coach/evals/carbon_coach.evalset.json --config_file_path carbon_coach/evals/test_config.json
```
*(Or `python -m google.adk.cli eval carbon_coach carbon_coach/evals/carbon_coach.evalset.json --config_file_path carbon_coach/evals/test_config.json`)*

**Golden Eval Cases Covered**:
1. `travel_bus_12km`: Asserts `calculate_travel_emissions(mode="bus", km=12)` & `log_activity`.
2. `electricity_ac_4hours`: Asserts `calculate_electricity_emissions(appliance="ac", hours=4)` & `log_activity`.
3. `food_chicken_biryani`: Asserts `calculate_food_emissions(meal_type="chicken", meals=1)` & `log_activity`.
4. `multi_activity_three_tools`: Multi-tool chaining across travel, electricity, and food in one message.
5. `ambiguous_input_clarification`: "I travelled today" -> Agent asks clarifying question; zero tool calls.
6. `unknown_travel_mode`: "I flew by helicopter" -> Handles error gracefully without hallucinating.
7. `weekly_summary_request`: "How did I do this week?" -> Calls `get_summary(period="week")`.
8. `improvement_tips_request`: "How can I improve?" -> Calls `suggest_reductions()`.

---

## 🚀 Deployment to Google Cloud Run

Deploy Carbon Coach as a serverless service on Cloud Run with ADK:

```bash
adk deploy cloud_run ./carbon_coach \
  --project YOUR_GCP_PROJECT_ID \
  --region us-central1 \
  --service_name carbon-coach \
  --with_ui \
  --env GOOGLE_API_KEY=YOUR_GEMINI_API_KEY \
  --env GEMINI_MODEL=gemini-2.5-flash
```

### Production Deployment Notes:
- **API Key Security**: For production environments, mount your Gemini API key from **Google Secret Manager** or set it via Cloud Run Environment Secrets rather than passing it as plaintext.
- **Session State Persistence**: The default session service uses an in-memory session store (`--session_service_uri memory://`). In-memory sessions will reset when Cloud Run scales to zero or restarts. For persistent sessions across restarts, connect a database service URI (such as `--session_service_uri sqlite:///data/sessions.db` or Cloud SQL / Firestore).

---

## 📊 Emission Factor Sources & Pre-Demo Checklist

All conversion factors are centralized in [`carbon_coach/factors.py`](carbon_coach/factors.py):

| Category | Item | Factor Value | Cited Source | Pre-Demo Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Travel** | Bus | 0.089 kg CO2e / pass-km | UK DEFRA GHG Factors | [ ] Verify urban bus transit assumptions |
| **Travel** | Petrol Car | 0.170 kg CO2e / pass-km | UK DEFRA / ARAI India | [ ] Verify single passenger occupancy |
| **Travel** | Metro | 0.030 kg CO2e / pass-km | Indian Urban Metro Transit | [ ] Verify electric grid mix alignment |
| **Travel** | Two-Wheeler | 0.070 kg CO2e / pass-km | ARAI India commuter scooter | [ ] Verify standard 100-150cc engine |
| **Electricity**| India Grid | 0.710 kg CO2e / kWh | CEA CO2 Baseline (Ver 19) | [ ] Confirm CEA baseline year / report |
| **Appliance** | 1.5-Ton AC | 1.500 kW | BEE Star Rating standard | [ ] Verify average compressor draw |
| **Appliance** | Ceiling Fan | 0.075 kW | BEE Standard 75W Fan | [ ] Verify BLDC vs standard fan rating |
| **Food** | Chicken Meal | 1.600 kg CO2e / meal | Poore & Nemecek (Science) | [ ] Verify standard portion size (300g) |
| **Food** | Veg Meal | 0.700 kg CO2e / meal | Poore & Nemecek / OWID | [ ] Verify Indian vegetarian mix |
| **Food** | Mutton Meal | 5.000 kg CO2e / meal | Poore & Nemecek (Science) | [ ] Verify ruminant meat footprint |
| **Waste** | Landfill Waste| 0.450 kg CO2e / kg | IPCC Waste Sector Guidelines | [ ] Verify municipal unmanaged landfill |
| **Benchmark** | Daily Indian | 5.000 kg CO2e / person/day | World Bank / OWID (1.9 t/yr) | [ ] Confirm illustrative benchmark |

---

## ⏱️ 3-Minute Live Demo Script

| Time | Step | User Input | What the Agent Does & What to Point Out in the UI |
| :---: | :--- | :--- | :--- |
| **0:00 - 0:30** | **1. Messy Multi-Activity Input** | *"Hey! Today I travelled 12 km by bus to campus and used the AC in my hostel room for 4 hours."* | • **Point out Tool Execution Trace**: Agent calls `calculate_travel_emissions(mode="bus", km=12)` -> returns `1.068 kg CO2e`.<br>• Agent calls `calculate_electricity_emissions(appliance="ac", hours=4)` -> returns `4.26 kg CO2e` (kW: 1.5, kWh: 6.0).<br>• Agent calls `log_activity` twice.<br>• **Point out Response**: "12 km by bus: 1.068 kg CO2e. 4 hours AC: 4.26 kg CO2e (assumed 1.5 kW rating). Today's running total: **5.328 kg CO2e**." |
| **0:30 - 1:15** | **2. Second Turn & Memory Accumulation** | *"I just had a chicken biryani for lunch."* | • Agent calls `calculate_food_emissions(meal_type="chicken", meals=1)` -> returns `1.6 kg CO2e`.<br>• Agent calls `log_activity` with food activity.<br>• Today's cumulative total automatically updates in memory to **6.928 kg CO2e**.<br>• Highlight that the agent never guessed numbers; every figure comes straight from `tools.py`. |
| **1:15 - 2:00** | **3. Ambiguity & Error Guardrails** | *"I travelled today."* | • **Point out Zero-Hallucination Guardrail**: The agent **does not call any tool** and does not make up numbers.<br>• Agent politely asks a single clarifying question: *"Which travel mode did you use (e.g. bus, metro, car) and how many kilometers did you travel?"* |
| **2:00 - 2:40** | **4. Weekly Summary & Benchmark** | *"How did I do this week?"* | • Agent invokes `get_summary(period="week")`.<br>• Displays total emissions (**6.928 kg CO2e**), category breakdown (*electricity: 4.26 kg, food: 1.6 kg, travel: 1.068 kg*), and top emitting category (*electricity*).<br>• Compares against the 7-day benchmark (**35.0 kg CO2e**) showing the user is **28.072 kg below benchmark** (19.8%). |
| **2:40 - 3:00** | **5. Actionable Tips & Wrap-up** | *"How can I reduce my footprint?"* | • Agent invokes `suggest_reductions()`.<br>• Displays personalized, ranked tips:<br>&nbsp;&nbsp;1. *"Use a ceiling fan instead of AC for 4 hours (saves ~4.047 kg CO2e)."*<br>&nbsp;&nbsp;2. *"Swap one chicken meal for a vegetarian meal (saves ~0.9 kg CO2e)."*<br>&nbsp;&nbsp;3. *"Switch your 12 km bus trip to metro (saves ~0.708 kg CO2e)."*<br>• Wrap up: Carbon Coach turns climate awareness into measurable, personalized action! |

---

## 👥 Hackathon Team & License
Built with ❤️ for the GDG Hackathon using Google ADK & Gemini. Released under the Apache 2.0 License.
#   C a r b o n - C o a c h  
 