# Vera Bot — magicpin AI Challenge

A context-aware AI business assistant that helps merchants improve bookings through intelligent, trigger-driven WhatsApp conversations.

---

## 🧠 Overview

Vera combines a **deterministic rule engine (decision layer)** with **LLM-assisted language generation (optional polish)** to ensure:

- High specificity
- Strong personalization
- Category-appropriate tone
- Clear trigger relevance
- High engagement

---

## ⚙️ Architecture

```
Context (Category + Merchant + Trigger + Customer)
        ↓
Rule Engine (deterministic decisions)
        ↓
Structured Message Draft
        ↓
LLM Polish (optional)
        ↓
Final Output
```

### Rule Engine (Core Logic)

- Trigger classification (`perf_dip`, `research_digest`, `recall_due`, etc.)
- Anchor fact extraction (metrics, trends, payload data)
- CTA selection (`yes_stop`, open-ended)
- Category voice selection (clinical, warm, operator, etc.)
- Engagement strategy (loss aversion, curiosity, action)

### LLM Layer (Optional)

- Uses Anthropic Claude (`claude-sonnet-4-20250514`)
- Temperature = 0 (deterministic)
- Only rewrites messages for **clarity and tone**
- Does NOT decide logic or add new data

---

## 📦 Context Handling (4-Layer Model)

| Context         | Purpose                              |
| --------------- | ------------------------------------ |
| CategoryContext | Voice, peer stats, domain knowledge  |
| MerchantContext | Performance data, identity, history  |
| TriggerContext  | Why messaging now                    |
| CustomerContext | (Optional) for customer-facing flows |

---

## 🔁 Conversation Handling

### Supported behaviors:

- ✅ YES / acceptance detection → immediate action
- ❌ STOP / opt-out → graceful exit
- 🤔 Intent detection:
  - cost queries
  - business impact
  - "how it works"
- 👋 Greeting handling (non-aggressive responses)
- 🔁 Context-aware replies using last trigger

---

## 🛠️ Running the Project

### 1️⃣ Install dependencies

```bash
pip install anthropic
```

### 2️⃣ Set API key (optional)

```bash
export ANTHROPIC_API_KEY=your_key
```

### 3️⃣ Generate submission

```bash
python bot.py generate --dataset ./dataset
```

### 4️⃣ Test single case

```bash
python bot.py test --merchant m_001_drmeera_dentist_delhi --trigger trg_001_research_digest_dentists
```

### 5️⃣ Run server

```bash
python bot.py server --port 8080
```

---

## 🌐 API Endpoints

| Endpoint       | Purpose                    |
| -------------- | -------------------------- |
| `/v1/healthz`  | Health check               |
| `/v1/metadata` | Bot identity               |
| `/v1/context`  | Receive dataset context    |
| `/v1/tick`     | Generate outbound messages |
| `/v1/reply`    | Handle user responses      |

---

## 📁 Project Structure

```
vera-bot/
├── bot.py                   ← Main logic + server
├── README.md                ← This file
├── challenge-brief.md       ← Challenge documentation
├── judge_simulator.py       ← Testing simulator
├── dataset/
│   ├── categories/          ← Category contexts
│   ├── merchants_seed.json
│   ├── customers_seed.json
│   ├── triggers_seed.json
│   └── generate_dataset.py
├── examples/
│   ├── api-call-examples.md
│   └── case-studies.md
└── submission.jsonl        ← Generated outputs
```

---

## 🎯 Scoring Strategy

| Dimension         | Strategy                                      |
| ----------------- | --------------------------------------------- |
| Specificity       | Uses numbers, payload data, concrete examples |
| Category Fit      | Enforced tone + vocabulary rules              |
| Merchant Fit      | Uses name, performance data                   |
| Trigger Relevance | Explicit "WHY NOW" messaging                  |
| Engagement        | Strong CTAs + action framing                  |

---

## 🚀 Key Features

- ✅ Rule-based decision system (no blind AI reliance)
- ✅ Payload-aware messaging (e.g., "fluoride care")
- ✅ CTA variation (avoids repetition)
- ✅ Suppression logic (prevents spam)
- ✅ Context-aware replies (multi-turn)
- ✅ Human-like conversational tone

---

## 🌑 Supported Categories

- **Dentists** — Clinical/peer voice, technical terms OK
- **Salons** — Warm, service-oriented
- **Restaurants** — Food-focused, local appeal
- **Gyms** — Fitness-oriented, transformation-focused
- **Pharmacies** — Health-conscious, compliance-aware

---

## 📋 Supported Triggers

| Trigger Type | Description |
|--------------|-------------|
| `perf_dip` | Performance dropped below peer average |
| `perf_spike` | Performance exceeded expectations |
| `research_digest` | New category research available |
| `recall_due` | Customer follow-up due |
| `winback` | Re-engage lapsed customers |
| `seasonal` | Seasonal trends and opportunities |
| `milestone_reached` | Achievement notification |
| `renewal_due` | Subscription renewal needed |
| `regulation_change` | Compliance updates |
| `competitor_opened` | New competitor in area |

---

## 🔧 Tradeoffs

| Decision                       | Tradeoff                                       |
| ------------------------------ | ---------------------------------------------- |
| Rule engine first              | Less flexible than full LLM, but more reliable |
| Optional LLM polish            | Adds quality, slight dependency                |
| Keyword-based intent detection | Fast, but not perfect for edge cases         |
| No vector search              | Simpler system, less dynamic ranking          |

---

## 📖 Example Usage

### Generate a message for a merchant:

```python
from bot import compose, store

# Load data
category = store["categories"]["dentists"]
merchant = store["merchants"]["m_001_drmeera_dentist_delhi"]
trigger = store["triggers"]["trg_001_research_digest_dentists"]

# Compose message
result = compose(category, merchant, trigger)
print(result["body"])
```

### Run server and test:

```bash
# Start server
python bot.py server --port 8080

# In another terminal, test the API
curl -X POST http://localhost:8080/v1/context \
  -H "Content-Type: application/json" \
  -d '{"scope": "categories", "context_id": "dentists", "payload": {...}}'
```

---

## 🏁 Future Improvements

- Vector-based retrieval for better content ranking
- Advanced intent classification (LLM-based)
- Multi-turn memory with session tracking
- Time-based messaging optimization
- Merchant-specific personalization models

---

*Built for the magicpin AI Challenge*
