# Medical Document Translator (Prototype)

AI-powered document translation for medical device industry.
Translates DOCX and PDF files using local AI models (Ollama + Qwen3 14B) or cloud APIs.

Language pairs: EN→ZH, EN+DE→EN+ZH.
Output: Bilingual (original + translation) or standalone translated DOCX.

## Tech Stack

| Layer     | Technology                                       |
|-----------|--------------------------------------------------|
| Frontend  | React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query |
| Backend   | FastAPI + SQLAlchemy + SQLite + Alembic          |
| AI        | Ollama (Qwen3 14B), Anthropic Claude, DeepL      |
| Documents | python-docx (DOCX), docling (PDF)                |
| Infra     | Docker Compose (3 services)                      |

## Prerequisites

### Required

| Software          | Version      | Check              |
|-------------------|------------- |--------------------|
| Python            | 3.11 or 3.12 | `python3 --version`|
| Node.js           | 22+          | `node --version`   |
| npm               | 9+           | `npm --version`    |

### Recommended

| Software              | Purpose                        |
|-----------------------|--------------------------------|
| Docker + Docker Compose| One-command dev environment   |
| Ollama                | Local AI translation (Qwen3 14B) |

### Optional

| Service            | Purpose                    | Key Needed? |
|--------------------|----------------------------|:-----------:|
| Anthropic API      | Cloud AI (Claude)          | Yes         |
| DeepL API          | Cloud AI (DeepL)           | Yes         |

**GPU is not required.** CPU-only works for development and light translation.
For production document volumes, a GPU with 16GB+ VRAM is recommended.

## Disk Space

| Component              | Size       | Notes                              |
|------------------------|------------|------------------------------------|
| Project code           | ~2 MB      |                                    |
| Python dependencies    | ~3 GB      | docling pulls in PyTorch (~2 GB)   |
| Node.js dependencies   | ~200 MB    |                                    |
| docling model weights  | ~1 GB      | Downloaded automatically on first PDF parse |
| Ollama model (Qwen3)   | ~10 GB     | Optional; omit if using only cloud APIs |
| **Minimum total**      | **~4 GB**  | Without Ollama model               |
| **Full setup**         | **~14 GB** | With Ollama Qwen3 14B              |

## Quick Start

### 1. Clone & enter

```bash
cd translator
```

### 2. Choose your mode

---

#### Mode A: Docker (recommended — one command)

```bash
# Dev mode: frontend + backend only (no AI model)
docker compose up frontend backend

# Full mode: with Ollama service
docker compose --profile full up
```

Then open **http://localhost:5173**.

First PDF parse will download docling model weights (~1 GB) automatically inside the container.

---

#### Mode B: Without Docker

**Backend setup:**

```bash
cd backend

# Create virtual environment (Linux/macOS)
python3 -m venv .venv
source .venv/bin/activate

# Windows
# python -m venv .venv
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For PDF support: install docling separately (~2 GB with PyTorch)
pip install docling pandas

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend setup:**

```bash
cd frontend

npm install
npm run dev
```

Then open **http://localhost:5173**.

### 3. Verify it works

```bash
# Backend health check
curl http://localhost:8000/api/health
# → {"status":"ok","app":"Medical Document Translator"}

# Frontend
# Open http://localhost:5173 in browser — you should see the upload page
```

### 4. AI Provider (choose one)

**For development/testing — no setup needed:**
The app includes a **MockProvider** that returns pseudo-translations.
Select "Mock" as the AI provider in the UI to test the full workflow without any AI model.

**For real translations:**

- **Ollama (local):**
  ```bash
  # Install Ollama: https://ollama.com/download
  ollama pull qwen3:14b

  # Or a smaller model for limited RAM:
  ollama pull qwen3:8b
  ```
  RAM: 16GB minimum for 14B model, 8GB for 8B model.

- **Anthropic Claude (cloud):**
  ```bash
  export ANTHROPIC_API_KEY="sk-ant-..."
  ```

- **DeepL (cloud):**
  ```bash
  export DEEPL_API_KEY="your-key"
  ```

## Configuration

All settings via environment variables (or `.env` file in `backend/`):

| Variable                    | Default                        | Description                    |
|-----------------------------|--------------------------------|--------------------------------|
| `DATABASE_URL`              | `sqlite:///./data/translator.db` | SQLite database path         |
| `OLLAMA_BASE_URL`           | `http://ollama:11434`          | Ollama API endpoint (Docker)   |
| `OLLAMA_BASE_URL` (no Docker)| `http://localhost:11434`      | Ollama API endpoint (local)    |
| `ANTHROPIC_API_KEY`         | (empty)                        | Anthropic Claude API key       |
| `DEEPL_API_KEY`             | (empty)                        | DeepL API key                  |
| `MAX_UPLOAD_SIZE_MB`        | `50`                           | Max upload file size           |

For Docker: set these in `docker-compose.yml` under `backend.environment`.

For local: create `backend/.env` file.

## Translation Workflow

1. **Upload** — drag & drop DOCX or PDF (max 50 MB)
2. **Configure** — language pair, glossary, output mode, AI provider, RAG toggle, image toggle
3. **Translate** — watch progress bar
4. **Preview** — side-by-side original vs translation, edit if needed
5. **Download** — get formatted DOCX

## Glossary Management

Optional. Translation works fine without a glossary.

- Visit `/glossaries` in the app
- Import CSV (columns: `source_term,target_term,context_note`) or Excel (.xlsx)
- Manage entries via UI
- Select a glossary during translation for terminology consistency

## Testing

Tests use MockProvider — **no AI model required**.

```bash
# Backend (104 tests)
cd backend
source .venv/bin/activate  # if using venv
python -m pytest tests/ -v

# Frontend type-check + build
cd frontend
npx tsc --noEmit
npm run build
```

## Project Structure

```
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/              # DB migrations
│   │   └── env.py
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── config.py         # pydantic-settings
│   │   ├── database.py       # SQLAlchemy + SQLite engine
│   │   ├── models/           # TranslationTask, Segment, Glossary, TranslationMemory
│   │   ├── routers/          # translation.py (5 ep), glossary.py (9 ep)
│   │   └── services/         # parser, translator, ai/, rag, image_extractor
│   └── tests/                # 104 pytest tests
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx           # Routes
│       ├── main.tsx          # Entry
│       ├── api/client.ts     # API client (fetch wrapper)
│       ├── components/       # Layout
│       └── pages/            # Upload, Translate, Preview, Glossary
└── data/                     # Created at runtime: SQLite DB, uploads, outputs
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'docling'`

```bash
pip install docling pandas
```

This pulls in PyTorch (~2 GB). If disk space is limited, PDF parsing won't work — only DOCX translation is available via python-docx.

### Ollama connection refused

- Docker: make sure the `ollama` service is running (`docker compose --profile full up`)
- Local: check `OLLAMA_BASE_URL=http://localhost:11434` (not `ollama:11434`)
- If Ollama is unavailable, switch AI provider to "Mock" or a cloud API

### First PDF parse is slow

docling downloads model weights (~1 GB) on first run. This is a one-time cost.

### `Out of memory` with Ollama

Try a smaller model: `ollama pull qwen3:8b` and set `OLLAMA_MODEL=qwen3:8b` in config.

### No translations appearing / empty output

- Check you selected an AI provider in the configuration step
- For Mock provider: output will have `[ZH]` prefixes — this is expected
- Check backend logs for errors: `docker compose logs backend`
