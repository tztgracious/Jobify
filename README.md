# GenView — AI-Powered Digital Human Interview Coach
> **Practice smarter. Interview better.**  — Real-time AI feedback for every candidate.

[![Build](https://img.shields.io/github/actions/workflow/status/your-org/genview/ci.yml?branch=main)](../../actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Made with ❤️ by Jobify](https://img.shields.io/badge/made%20by-Jobify-fb7299?logo=github)](#team)

Proudly created by **Team Jobify**.


---

## Getting Started

Below is the **minimal set of third‑party tools, libraries, SDKs and cloud services that GenView depends on _directly_**.  
(Transitive dependencies installed automatically by the packages below need not be listed.)

| Layer        | Technology / Service | Purpose | Link |
|--------------|----------------------|---------|------|
| **Front‑End** | React 18 + Vite      | SPA shell, routing, hot‑reload | <https://react.dev> |
|              | Tailwind CSS         | Utility‑first styling          | <https://tailwindcss.com> |
|              | React Query          | Declarative data‑fetching cache | <https://tanstack.com/query/latest> |
|              | framer‑motion        | Micro‑interactions / animations | <https://www.framer.com/motion/> |
| **Back‑End** | FastAPI 0.111        | Typed REST/WS APIs, OpenAPI docs | <https://fastapi.tiangolo.com> |
|              | Uvicorn              | ASGI web‑server                | <https://www.uvicorn.org> |
|              | PyTorch 2.3 + Transformers | Fine‑tuned LLM & embedding models | <https://pytorch.org> |
|              | Sentence‑Transformers | Real‑time similarity search    | <https://www.sbert.net> |
|              | LangChain           | RAG orchestration / prompt‑flows | <https://www.langchain.com> |
|              | Weights & Biases     | Experiment tracking & dashboards | <https://wandb.ai> |
| **Infra / Ops** | PostgreSQL 16       | Persist interview records & analytics | <https://www.postgresql.org> |
|              | Redis 7             | Low‑latency cache / pub‑sub     | <https://redis.io> |
|              | Docker 24           | Dev/prod parity containerisation | <https://docs.docker.com> |
|              | GitHub Actions      | CI / CD pipeline                | <https://github.com/features/actions> |

> **Build & Run (local dev)**  
> ```bash
> # 1. Clone
> git clone https://github.com/<ORG>/genview.git && cd genview
> 
> # 2. Back‑end
> cd server
> python -m venv .venv && source .venv/bin/activate
> pip install -r requirements.txt
> uvicorn app.main:app --reload
> 
> # 3. Front‑end (new shell)
> cd web
> npm ci
> npm run dev
> ```
> Visit <http://localhost:5173> in your browser.

---

## Model and Engine

> **Story‑map**  
> ![](docs/storymap.png) <!-- TODO: replace with the exported PNG or embed PDF -->

GenView’s core is a two‑tier **Conversation & Feedback Engine**:



| Block                     | Responsibility                                                        | Implementation notes                                                                                                 |
| ------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **ASR**                   | Convert candidate speech to text in ≈ real‑time.                      | OpenAI Whisper‑v3 (English, 16 kHz), streaming via websockets.                                                       |
| **NLU**                   | Extract intents, slot‑fill, sentiment.                                | `all‑minilm‑l6‑v2` for embeddings + lightweight classifiers.                                                         |
| **Dialogue Controller**   | State machine that chooses the next system action.                    | Pydantic state models; persistence in Redis for recovery.                                                            |
| **LLM Interview Agent**   | Generates interviewer questions, follow‑ups and “probing” hints.      | Fine‑tuned Llama‑3‑8B‑Instruct served with vLLM; prompt templates parameterised by role, difficulty, STAR framework. |
| **Speech/Video Features** | Measure WPM, pauses, pitch variance, gaze and facial affect.          | Mediapipe + torchaudio; runs on separate GPU worker.                                                                 |
| **Scoring & Rubrics**     | Map raw features to rubric levels (e.g. clarity, confidence).         | XGBoost models calibrated on \~2k labelled mock‑interviews.                                                          |
| **Report Builder**        | Fuse rubric scores, LLM critique, transcripts into a PDF/HTML report. | Jinja2 templates → WeasyPrint rendering; saved in S3.                                                                |

---

## APIs and Controller

The **REST + WebSocket surface** defines how the React front‑end communicates with the engine.

### 1. `POST /v1/session`

| Key              | In   | Type   | Description                      |
| ---------------- | ---- | ------ | -------------------------------- |
| `candidate_name` | JSON | string | Display name to show in coach UI |

**Returns**

```json
{
  "session_id": "bf52…",
  "ws_url": "wss://api.genview.ai/v1/stream/bf52…"
}
```

### 2. `WS /v1/stream/{session_id}`

Bidirectional messages in the following frames:

| Event          | Direction       | Payload                                  | Notes                         |
| -------------- | --------------- | ---------------------------------------- | ----------------------------- |
| `user_audio`   | ↑ client→server | Binary Ogg chunks                        | 64 kbit/s Opus, 500 ms frames |
| `agent_text`   | ↓ server→client | `{ "text": "...", "utterance_id": 42 }`  | Interviewer speaks via TTS    |
| `score_update` | ↓               | `{ "fluency":0.84,"confidence":0.72,… }` | Real‑time gauges              |

*All messages are acknowledged with `{ "ack": <event_id> }`.*

### 3. `GET /v1/report/{session_id}`

Returns the final PDF plus a machine‑readable JSON companion.

| Code            | Description       |
| --------------- | ----------------- |
| `200 OK`        | `application/pdf` |
| `404 Not Found` | Unknown session   |

> **Controller layer** uses FastAPI dependency‑injection to route calls to `engine/*` modules, each of which is a façade over the subsystems shown in the block‑diagram.

*If you later decide to off‑load part of the engine (e.g., ASR) to an external SaaS, replace the corresponding internal block by an SDK/wrapper and keep the API contract unchanged.*

---

## View UI/UX

<!-- TODO: Fill in wire‑frames, component library decisions, user journeys in HW‑3. -->

---

## Team Roster

| Member           |  Contribution<sup>†</sup> |
| ---------------- | ------------------------ |
| **Zhitong Tang** |                           |
| **Minjia Tang** |                         |
| **Yile Sun** |                       |
| **Zhenjie Sun** |                         |
| **Houcheng Yu** |                         |

<sup>†</sup> Detailed contribution statements will be completed at project close‑out.


*© 2025 GenView Team. Licensed under the MIT License.*

