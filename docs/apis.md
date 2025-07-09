# Jobify Backend APIs

## Quick Reference

| Endpoint                | Method | Description               |
| ----------------------- | ------ | ------------------------- |
| `/api/v1/signup/`       | POST   | Create new user account   |
| `/api/v1/login/`        | POST   | Authenticate user         |
| `/api/v1/parse-resume/` | POST   | Parse uploaded resume     |
| `/api/v1/debug/`        | GET    | Debug endpoint (dev only) |

## Base URL

- **Local Development**: `http://localhost:8000/api/v1`
- **Production**: `http://115.29.170.231:8000/api/v1`

All API endpoints are prefixed with `/api/v1` for versioning.

## Authentication

Currently, the API does not implement token-based authentication. Authentication is handled through basic login verification.

---

## 🔐 Authentication Endpoints

### 1. User Signup

**POST** `/api/v1/signup/`

Creates a new user account.

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "is_employer": false
}
```

#### Curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe",
    "is_employer": false
  }'
```

#### Response

```json
// Success (201 Created)
{
  "message": "User created"
}

// Error (400 Bad Request)
{
  "email": ["This field is required."],
  "password": ["This field is required."]
}
```

#### Request Fields

| Field         | Type    | Required | Description                                       |
| ------------- | ------- | -------- | ------------------------------------------------- |
| `email`       | string  | ✅       | User's email address (must be unique)             |
| `password`    | string  | ✅       | User's raw password (will be hashed)              |
| `full_name`   | string  | ❌       | User's full name                                  |
| `is_employer` | boolean | ❌       | Indicates if user is an employer (default: false) |

---

### 2. User Login

**POST** `/api/v1/login/`

Authenticates a user with email and password.

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

#### Request Fields

| Field      | Type   | Required | Description                             |
| ---------- | ------ | -------- | --------------------------------------- |
| `email`    | string | ✅       | User's email address for authentication |
| `password` | string | ✅       | User's password for authentication      |

#### Response

```json
// Success (200 OK)
{
  "message": "Login successful"
}

// Error (400 Bad Request)
{
  "error": "Invalid credentials"
}

// Error (404 Not Found)
// Returns 404 if user with provided email doesn't exist
```

---

## 📄 Resume Processing Endpoints

### 3. Parse Resume

**POST** `/api/v1/parse-resume/`

Parses uploaded resume files using LlamaIndex API.

#### Request

- **Content-Type**: `multipart/form-data`
- **Body**: File upload

#### Curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/parse-resume/ \
  -F "file=@resume.pdf"
```

#### Response

```json
// Success (200 OK)
{
  "parsed": {
    // LlamaIndex API response data
    "text": "extracted text content",
    "metadata": { ... }
  }
}

// Error (400 Bad Request)
{
  "error": "No file uploaded"
}

// Error (502 Bad Gateway)
{
  "error": "Request failed with status 500"
}
```

#### Response Fields

| Field             | Type   | Description                                           |
| ----------------- | ------ | ----------------------------------------------------- |
| `parsed`          | object | LlamaIndex API response containing parsed resume data |
| `parsed.text`     | string | Extracted text content from the resume                |
| `parsed.metadata` | object | Additional metadata from the parsing process          |
| `error`           | string | Error message when request fails                      |

#### Supported File Types

- PDF files
- Other formats supported by LlamaIndex API

---

### 4. Debug Endpoint

**GET** `/api/v1/debug/`

Development endpoint for testing OpenAI and LanguageTool integrations.

⚠️ **Note**: This endpoint is only available when `DEBUG=True` in Django settings.

#### Curl Example

```bash
curl -X GET \
  http://localhost:8000/api/v1/debug/
```

#### Response

```json
// Success (200 OK)
{
  "sample_text": "My name is Alice and I have 3 years experience in machine learning.",
  "keywords": ["machine learning", "experience", "Alice"],
  "grammar": {
    // LanguageTool grammar check results
  },
  "KEYS": {
    "LLAMA_PARSE_API_KEY": "sk-...",
    "OPENAI_API_KEY": "sk-...",
    "LANGUAGETOOL_API_KEY": "...",
    "EXAMPLE_KEY": "..."
  },
  "DJANGO_SECRET_KEY": "..."
}

// Error (403 Forbidden)
{
  "error": "Debug endpoint disabled in production"
}
```

#### Response Fields

| Field               | Type   | Description                               |
| ------------------- | ------ | ----------------------------------------- |
| `sample_text`       | string | The input text being analyzed             |
| `keywords`          | array  | Array of extracted keywords from the text |
| `grammar`           | object | LanguageTool grammar check results        |
| `KEYS`              | object | API keys configuration (for debugging)    |
| `DJANGO_SECRET_KEY` | string | Django secret key (for debugging)         |

---

## 📊 Data Models

### User Model

```json
{
  "id": 1,
  "email": "user@example.com",
  "password": "hashed_password",
  "is_employer": false,
  "full_name": "John Doe",
  "created_at": "2025-07-10T10:30:00Z"
}
```

---

## 🔧 Development Setup

### Required Environment Variables

Create a `.api-keys` file in the project root:

```env
LLAMA_PARSE_API_KEY=your_llama_api_key
OPENAI_API_KEY=your_openai_api_key
LANGUAGETOOL_API_KEY=your_languagetool_api_key
DJANGO_SECRET_KEY=your_django_secret_key
```

### Running the Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

---

## 📝 Error Handling

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: External API error

### Error Response Format

```json
{
  "error": "Error message description"
}
```

For validation errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

---

## 🚀 Future Enhancements

### Planned Features

- [ ] JWT token-based authentication
- [ ] User profile management endpoints
- [ ] Job posting endpoints
- [ ] Resume analysis and scoring
- [ ] File upload validation and security
- [ ] Rate limiting
- [x] API versioning (v1 implemented)

---

## 📞 Support

For API support and questions, contact the development team or refer to the project documentation.
