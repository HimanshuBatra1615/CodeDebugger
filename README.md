# CodeDebugger

AI-powered code error analysis tool. Upload your source files and a runtime log —
the pipeline parses stack traces, correlates them to exact source lines,
and generates precise fix suggestions via the **Google Gemini API** (free tier).

---

## Architecture

```
Code files + Log file
        │
        ▼
 ┌─────────────────────────────────────────┐
 │           Parse & Ingest                │  Regex-based log parser
 │  Errors, stack traces, line numbers     │  Java / Python / Node.js / Go
 └──────────────────────┬──────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────┐
 │         Correlation Engine              │  Fuzzy filename matching
 │  Errors mapped to source code lines     │  Context window extraction
 └──────────────────────┬──────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────┐
 │          AI Analysis Engine             │  Structured prompt
 │      Structured prompt + Gemini API     │  JSON response parsing
 └──────────────────────┬──────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────┐
 │       Structured Suggestions Report     │  Severity / fix / confidence
 └─────────────────────────────────────────┘
```

**Stack:** Python FastAPI · React 18 + Vite + Tailwind CSS · Google Gemini API

---

## Quick Start (Local Development)

### 1. Get a free Gemini API key

Go to **https://aistudio.google.com/app/apikey** → Create API key.  
No billing required. Free tier gives you 15 RPM and 1 M tokens/day.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env with your key
echo "GEMINI_API_KEY=your_key_here" > .env

uvicorn main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`  
Vite proxies `/api` calls to `localhost:8000` automatically.

---

## Running Without an API Key (Mock Mode)

If `GEMINI_API_KEY` is empty or not set, the AI engine returns realistic
mock suggestions. The entire frontend pipeline — upload → progress stream →
suggestions — works without spending any API quota.

---

## Docker (Production)

```bash
# Set your Gemini key
echo "GEMINI_API_KEY=your_key_here" > backend/.env

# Build and start both services
docker compose up --build
```

| Service  | URL                    |
|----------|------------------------|
| Frontend | http://localhost:3000  |
| Backend  | http://localhost:8000  |

---

## API Reference

### `POST /api/analyze`
Upload files and start an analysis.

**Form fields:**
- `code_files` — one or more source files, or a single `.zip` archive
- `log_file` — application log file (`.log` or `.txt`)

**Response:**
```json
{ "analysis_id": "a3f9c1", "status": "pending" }
```

---

### `GET /api/analyze/{id}/progress`
Server-Sent Events stream of real-time pipeline progress.

```json
{ "type": "progress", "step": "parsing",  "message": "Found 7 errors", "count": 7 }
{ "type": "complete", "result": { ... } }
{ "type": "error",    "message": "..." }
```

---

### `GET /api/analyze/{id}`
Full analysis result after completion.

```json
{
  "analysis_id": "a3f9c1",
  "scanned_at": "2026-06-03T10:30:00Z",
  "status": "complete",
  "language": "Java",
  "files_analyzed": ["UserService.java", "UserController.java"],
  "total_log_errors": 7,
  "correlated": 5,
  "suggestions": [
    {
      "id": "sug_001",
      "severity": "CRITICAL",
      "error_type": "NullPointerException",
      "source_file": "UserService.java",
      "line": 42,
      "method": "processUser",
      "root_cause": "user.getName() returns null when user has no profile",
      "suggestion": "Add a null guard before calling .length()",
      "fixed_code": "String name = Optional.ofNullable(user.getName()).orElse(\"\");",
      "confidence": 0.94,
      "original_context": "   41      public String processUser(User user) {\n   42 →      return user.getName().length();\n   43      }"
    }
  ]
}
```

---

## Supported Runtimes

| Runtime     | Log format                    | Stack trace pattern                        |
|-------------|-------------------------------|--------------------------------------------|
| Java        | Log4j / Logback / Spring Boot | `at com.example.Class.method(File.java:n)` |
| Kotlin      | Same as Java                  | Same as Java                               |
| Python      | `logging` + tracebacks        | `File "path.py", line n, in func`          |
| Node.js/TS  | Any format                    | `at FunctionName (file.js:n:c)`            |
| Go          | Any format                    | `file.go:n +0x...`                         |

---

## Environment Variables

| Variable          | Default             | Description                             |
|-------------------|---------------------|-----------------------------------------|
| `GEMINI_API_KEY`  | *(empty = mock)*    | Your Google Gemini API key              |
| `MODEL`           | `gemini-1.5-flash`  | Gemini model (`gemini-1.5-pro` for best quality) |
| `MAX_SUGGESTIONS` | `10`                | Max suggestions per analysis            |

---

## Project Structure

```
debugger/
├── backend/
│   ├── main.py                     FastAPI app, endpoints, SSE streaming
│   ├── config.py                   Settings loaded from .env
│   ├── parsers/
│   │   ├── log_parser.py           Block splitter + error extractor
│   │   ├── stack_trace_parser.py   Per-runtime regex frame extraction
│   │   └── code_reader.py          File indexer + language detection
│   ├── engines/
│   │   ├── correlation_engine.py   Fuzzy file match + context window
│   │   └── ai_engine.py            Gemini API + structured prompts
│   ├── models/schemas.py           Pydantic data models
│   └── utils/file_utils.py         Zip extraction
│
├── frontend/
│   └── src/
│       ├── App.jsx                 State machine: upload → analyzing → results
│       ├── api/client.js           Fetch wrappers
│       ├── hooks/useProgressStream.js  SSE React hook
│       └── components/
│           ├── UploadZone.jsx      Drag-and-drop file upload
│           ├── AnalysisProgress.jsx Terminal-style progress tracker
│           ├── ReportPanel.jsx     Results with filter + JSON export
│           ├── SuggestionCard.jsx  Code diff + copy button
│           ├── SeverityBadge.jsx   Colour-coded severity pill
│           └── Header.jsx
│
├── docker-compose.yml
└── .env.example
```
