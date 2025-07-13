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
  -F "file=@resume.pdf"
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

## ⚠️ Planned Endpoints (Not Yet Implemented)

The following endpoints are planned for future development but are **not currently available**:

### Target Job Selection

- **Endpoint**: `POST /api/v1/target-job/`
- **Purpose**: Save user's target job preferences
- **Status**: Planned

### Interview Questions

- **Endpoint**: `POST /api/v1/get-questions/`
- **Purpose**: Generate interview questions based on resume
- **Status**: Planned

> **Important**: These endpoints will return `404 Not Found` if called.

---

## API Summary

### Currently Available:

- `POST /api/v1/upload-resume/` - Upload PDF resume
- `POST /api/v1/get-keywords/` - Get extracted keywords
- `GET /api/v1/debug/` - Debug info (dev only)
- `POST /api/v1/signup/` - User registration
- `POST /api/v1/login/` - User authentication
- `POST /api/v1/logout/` - User logout

### Coming Soon:

- `POST /api/v1/target-job/` - Target job preferences
- `POST /api/v1/get-questions/` - Interview questions
