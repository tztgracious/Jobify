# 🚀 Jobify Backend APIs

## 📂 Upload Resume

### Description

Allows the user to upload a **resume PDF file** (less than 5MB).  
The server generates a `doc_id` and validates the file type and size.

### Endpoint

```text
POST /api/v1/upload-resume/
```

### Request

#### Content-Type

```text
multipart/form-data
```

#### Body Parameters

| Field  | Type | Required | Description                                       |
| ------ | ---- | -------- | ------------------------------------------------- |
| `file` | file | ✅       | The resume PDF file to upload. Must be under 5MB. |

### Example cURL

```bash
curl -X POST \
  http://localhost:8000/api/v1/upload-resume/ \
  -F "file=@./backend/test/fixtures/resume_1.pdf"
curl -k -X POST \
  https://115.29.170.231/api/v1/upload-resume/ \
  -F "file=@./backend/test/fixtures/resume_1.pdf"
```

### Response

#### Success - `201 Created`

```json
{
  "doc_id": "12f4f5a8-9d20-43a6-8104-0b03cfd56ab3",
  "valid_file": true,
  "error_msg": null
}
```

#### Validation failure - `400 Bad Request`

```json
{
  "doc_id": null,
  "valid_file": false,
  "error_msg": "File too big."
}
```

or

```json
{
  "doc_id": null,
  "valid_file": false,
  "error_msg": "Not a PDF file."
}
```

---

## 🔍 Get Resume Keywords

### Description

Fetches extracted **keywords** from the uploaded resume file identified by `doc_id`.

### Endpoint

```text
POST /api/v1/get-keywords/
```

### Request

#### Content-Type

```text
multipart/form-data
```

#### Body Parameters

| Field    | Type          | Required | Description                                              |
| -------- | ------------- | -------- | -------------------------------------------------------- |
| `doc_id` | string (UUID) | ✅       | The `doc_id` returned by the `/upload-resume/` endpoint. |

### Example cURL

```bash
curl -X POST \
  http://localhost:8000/api/v1/get-keywords/ \
  -F "doc_id=12f4f5a8-9d20-43a6-8104-0b03cfd56ab3"
```

### Response

#### Success - `200 OK`

```json
{
  "finished": true,
  "keywords": ["c++", "java"],
  "error": ""
}
```

#### Processing not finished - `200 OK`

```json
{
  "finished": false,
  "keywords": [],
  "error": ""
}
```

#### Error occurred - `500 Internal Server Error`

```json
{
  "finished": false,
  "keywords": [],
  "error": "Resume processing failed. Trying again."
}
```

#### Resume not found - `404 Not Found`

```json
{
  "finished": false,
  "keywords": [],
  "error": "Resume not found"
}
```

#### Missing doc_id - `400 Bad Request`

```json
{
  "finished": false,
  "keywords": [],
  "error": "doc_id is required"
}
```

---

## 🐛 Debug Endpoint (Development Only)

### Description

Returns debug information about the server configuration. **Only available when DEBUG=True**.

### Endpoint

```text
GET /api/v1/debug/
```

### Request

No parameters required.

### Example cURL

```bash
curl -X GET http://localhost:8000/api/v1/debug/
```

### Response

#### Success - `200 OK` (when DEBUG=True)

```json
{
  "DEBUG": true,
  "DATABASES": "sqlite3",
  "KEYS": {
    "OPENAI_API_KEY": "sk-..."
  }
}
```

#### Forbidden - `403 Forbidden` (when DEBUG=False)

```json
{
  "error": "Debug endpoint disabled in production"
}
```

---

## 👤 Authentication APIs(NOT in use)

### User Signup

#### Endpoint

```text
POST /api/v1/signup/
```

#### Request Body

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword123",
  "full_name": "Test User",
  "is_employer": false
}
```

#### Response

```json
{
  "message": "User created"
}
```

### User Login

#### Endpoint

```text
POST /api/v1/login/
```

#### Request Body

```json
{
  "email": "test@example.com",
  "password": "securepassword123"
}
```

#### Response

```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "full_name": "Test User",
    "is_employer": false
  }
}
```

### User Logout

#### Endpoint

```text
POST /api/v1/logout/
```

#### Response

```json
{
  "message": "Logged out successfully"
}
```

---

## 🎯 Target Job Selection

### Description

Allows users to save their target job preferences for a specific resume. This information can be used to tailor interview questions and recommendations.

### Endpoint

```text
POST /api/v1/target-job/
```

### Request

#### Content-Type

```text
application/json
```

or

```text
multipart/form-data
```

#### Body Parameters

| Field    | Type          | Required | Description                                              |
| -------- | ------------- | -------- | -------------------------------------------------------- |
| `doc_id` | string (UUID) | ✅       | The `doc_id` returned by the `/upload-resume/` endpoint. |
| `title`  | string        | ✅       | The target job title (e.g., "Software Engineer").        |

### Example cURL

```bash
curl -X POST \
  http://localhost:8000/api/v1/target-job/ \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "12f4f5a8-9d20-43a6-8104-0b03cfd56ab3",
    "title": "Software Engineer"
  }'
```

### Response

#### Success - `200 OK`

```json
{
  "doc_id": "12f4f5a8-9d20-43a6-8104-0b03cfd56ab3",
  "message": "Target job saved successfully"
}
```

#### Missing required fields - `400 Bad Request`

```json
{
  "error": "Missing required fields"
}
```

#### Resume not found - `404 Not Found`

```json
{
  "error": "Resume not found"
}
```

---

## 🔄 Get Interview Questions (In Development)

### Description

Generates interview questions based on the uploaded resume and target job preferences. This endpoint analyzes the resume keywords and target job to create relevant interview questions.

**⚠️ Note**: This endpoint is currently in development with a skeletal implementation. It returns placeholder questions and should not be used in production.

### Endpoint

```text
POST /api/v1/get-questions/
```

### Request

#### Content-Type

```text
application/json
```

or

```text
multipart/form-data
```

#### Body Parameters

| Field    | Type          | Required | Description                                              |
| -------- | ------------- | -------- | -------------------------------------------------------- |
| `doc_id` | string (UUID) | ✅       | The `doc_id` returned by the `/upload-resume/` endpoint. |

### Example cURL

```bash
curl -X POST \
  http://localhost:8000/api/v1/get-questions/ \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "12f4f5a8-9d20-43a6-8104-0b03cfd56ab3"
  }'
```

### Response

#### Success - `200 OK`

```json
{
  "doc_id": "12f4f5a8-9d20-43a6-8104-0b03cfd56ab3",
  "interview_questions": [
    "What are your strengths?",
    "Why do you want to work here?",
    "Describe a challenging situation you've faced."
  ]
}
```

#### Missing doc_id - `400 Bad Request`

```json
{
  "error": "doc_id is required"
}
```

#### Resume not found - `404 Not Found`

```json
{
  "error": "Resume not found"
}
```

### Development Status

- ✅ Basic endpoint structure implemented
- ✅ Request validation (doc_id required)
- ✅ Resume existence check
- ⚠️ Returns placeholder questions (not AI-generated)
- ❌ Multi-agent AI question generation (planned)
- ❌ Personalization based on keywords and target job (planned)

---

## ⚠️ Endpoints in Development

The following endpoints are currently being developed but are **not yet fully functional**:

### Interview Questions

- **Endpoint**: `POST /api/v1/get-questions/`
- **Purpose**: Generate interview questions based on resume and target job
- **Status**: In Development (Skeletal Implementation)
- **Note**: Basic endpoint structure exists but functionality is not yet complete

> **Important**: This endpoint currently returns placeholder responses and should not be used in production.

---

## 📋 TODO APIs (Planned)

The following endpoints are planned for future development:

### Submit Answer

- **Endpoint**: `POST /api/v1/submit-answer/`
- **Purpose**: Submit user's answer (text or video) to a specific interview question
- **Description**: Stores the user's response and evaluates it using OpenAI API. Returns evaluation results and correct answers with explanations.
- **Status**: TODO
- **Features**:
  - Accept text or video responses
  - OpenAI-powered evaluation
  - Detailed feedback and explanations
  - Correct answer suggestions

### Update Knowledge Graph

- **Endpoint**: `POST /api/v1/update-knowledge-graph/`
- **Purpose**: Add new nodes (concepts, questions, answers) to the Neo4j knowledge graph
- **Description**: Manages the knowledge graph by adding new concepts, questions, and answers to improve the system's understanding and question generation.
- **Status**: TODO
- **Features**:
  - Add concept nodes
  - Link questions to concepts
  - Store answer patterns
  - Return update confirmation

> **Note**: These endpoints are in the planning phase and will be implemented in future iterations.

---

## API Summary

### Currently Available:

- `POST /api/v1/upload-resume/` - Upload PDF resume
- `POST /api/v1/get-keywords/` - Get extracted keywords
- `POST /api/v1/target-job/` - Save target job preferences
- `GET /api/v1/debug/` - Debug info (dev only)
- `POST /api/v1/signup/` - User registration
- `POST /api/v1/login/` - User authentication
- `POST /api/v1/logout/` - User logout

### In Development:

- `POST /api/v1/get-questions/` - Interview questions (skeletal implementation)

### Planned (TODO):

- `POST /api/v1/submit-answer/` - Submit and evaluate user answers
- `POST /api/v1/update-knowledge-graph/` - Update Neo4j knowledge graph
