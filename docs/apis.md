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

#### Error occurred - `500 Internal Server Error` or custom `502 Bad Gateway`

```json
{
  "finished": false,
  "keywords": [],
  "error": "Server timed out."
}
```

---

## 🎯 Select Target Job

### Description

Saves the user’s **target job preferences** (title, location, expected salary, skills).

### Endpoint

```text
POST /api/v1/target-job/
```

### Request

#### Content-Type

```text
application/json
```

#### Body Parameters

| Field          | Type             | Required | Description                                |
| -------------- | ---------------- | -------- | ------------------------------------------ |
| `title`        | string           | ✅       | Desired job title.                         |
| `location`     | string           | ✅       | Preferred job location.                    |
| `salary_range` | string           | ✅       | Expected salary range.                     |
| `tags`         | array of strings | ✅       | Keywords/tags related to the desired role. |

### Example cURL

```bash
curl -X POST \
  http://localhost:8000/api/v1/target-job/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "location": "Remote",
    "salary_range": "80k-100k",
    "tags": ["python", "django", "rest"]
  }'
```

### Response

#### Success - `201 Created`

```json
{
  "message": "Target job saved successfully"
}
```

#### Validation error - `400 Bad Request`

```json
{
  "error": "Missing required fields."
}
```

## 📝 Get Interview Questions

### Description

Retrieves **auto-generated interview questions** based on the uploaded resume identified by `doc_id`.  
The request can include `doc_id` and may accept more fields in the future.

### Endpoint

```text
POST /api/v1/get-questions/
```

### Request

#### Content-Type

```text
application/json
```

#### Body Parameters

| Field    | Type          | Required | Description                                                                     |
| -------- | ------------- | -------- | ------------------------------------------------------------------------------- |
| `doc_id` | string (UUID) | ✅       | The `doc_id` returned by `/upload-resume/`. Used to fetch associated questions. |

> ⚠️ Note: Additional fields may be supported in future versions for customization (e.g., question difficulty, category).

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
  "finished": true,
  "questions": [
    "Tell me about a project where you used Python.",
    "How do you manage deadlines when working remotely?",
    "One more question."
  ],
  "error": null
}
```

#### Still processing - `200 OK`

```json
{
  "finished": false,
  "questions": [],
  "error": null
}
```

#### Error occurred - `500 Internal Server Error`

```json
{
  "finished": false,
  "questions": [],
  "error": "Server timed out."
}
```
