# Jobify — AI-Powered Interview Coach

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Made with ❤️ by Jobify](https://img.shields.io/badge/made%20by-Jobify-fb7299?logo=github)](#team)

Proudly created by **Jobify**.

---

## Getting Started

Below is the minimal set of third‑party tools, libraries, SDKs and cloud services that Jobify depends on directly.  
## 🖥️ Front-End Dependencies

| Library/Tool | Purpose | Link |
|--------------|---------|------|
| React.js | UI framework for building interactive interfaces | [reactjs.org](https://reactjs.org/) |
| Quill | Rich text editor for user input | [quilljs.com](https://quilljs.com/) |
| Video.js | HTML5 video player | [videojs.com](https://videojs.com/) |
| AWS S3 JS SDK | Upload and retrieve videos from AWS S3 | [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/S3.html) |
| Countdown.js | Countdown timer for interviews | [GitHub - hilios/jQuery.countdown](https://github.com/hilios/jQuery.countdown) |
| Bootstrap | UI component library for layouts and styling | [getbootstrap.com](https://getbootstrap.com/) |
| Tailwind CSS | Utility-first CSS framework for custom styling | [tailwindcss.com](https://tailwindcss.com/) |

---

## 🧠 Back-End Dependencies

| Library/Tool | Purpose | Link |
|--------------|---------|------|
| LlamaParse | Process PDF files | [llamaindex.ai/llamaparse](https://www.llamaindex.ai/llamaparse?gad_source=1&gad_campaignid=21116317807&gbraid=0AAAAA9du_J0CkmThGan_q1frhfR59JbAE&gclid=Cj0KCQjwyIPDBhDBARIsAHJyyVjUe6Zg1Wtgn6OlPtRq2REI2zOr368RSxqPsimjxi_sFbUiBKNWaWwaAr_AEALw_wcB) |
| OpenAI API | Extract keywords and form questions | [platform.openai.com](https://platform.openai.com/docs/) |
| spaCy | NLP toolkit in Python | [spacy.io](https://spacy.io/) |
| LanguageTool | Grammar and style checking | [languagetool.org](https://languagetool.org/) |
| Neo4j | Graph database for knowledge representation | [neo4j.com](https://neo4j.com/) |
| Express.js | Minimal backend framework for Node.js | [expressjs.com](https://expressjs.com/) |
| AWS Boto3 SDK | Python SDK for accessing AWS services (e.g., S3) | [boto3.amazonaws.com](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) |
| FFmpeg | Video/audio processing for recordings | [ffmpeg.org](https://ffmpeg.org/) |

---

## 🧰 Infrastructure & Data Storage

| Library/Tool | Purpose | Link |
|--------------|---------|------|
| PostgreSQL | Relational database | [postgresql.org](https://www.postgresql.org/) |
| MongoDB | NoSQL document database | [mongodb.com](https://www.mongodb.com/) |

---

## Model and Engine

> **Story‑map**  
> ![](docs/storymap.png) 
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

