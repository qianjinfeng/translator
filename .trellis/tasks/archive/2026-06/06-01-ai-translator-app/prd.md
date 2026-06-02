# AI-Powered Medical Document Translation App (Prototype)

## Goal

Build a Docker-based web application for translating internal medical device industry documents.
Local open-source AI models (Qwen3 14B) as the primary translation engine, with cloud API fallback.
Input: DOCX and PDF → Three-step wizard → Output: formatted bilingual or standalone DOCX.
Language pairs: EN→ZH, EN+DE→EN+ZH.

## Requirements

**MVP (must have):**
1. Import DOCX and PDF documents (up to ~50MB, intranet upload)
2. Three-step wizard: Upload → Configure → Translate → Preview → Download
3. Translate using local Qwen3 14B (Ollama); optional cloud API switch (Anthropic/DeepL)
4. Preserve document formatting: tables, line breaks, inline styles (bold/italic/etc.)
5. Output: bilingual (original + translation) OR standalone translated DOCX
6. Glossary: optional; CSV/Excel import + UI 管理 + 下拉选择。无 glossary 也可正常翻译
7. Progressive translation with progress bar + timeout retry for long documents
8. RAG/Translation Memory: toggleable (on/off), uses sqlite-vec + multilingual-e5-small for similar segment retrieval
9. Image translation within documents: toggleable (on/off), extracts and translates text in images
10. Docker Compose dev environment (`docker compose up` starts everything)
11. CI/CD deferred to post-prototype phase

**Quality requirements:**
- Table cells identified and translated individually without breaking table structure
- Line breaks / paragraph boundaries preserved accurately (soft vs hard breaks)
- Inline formatting (bold, italic, superscript/subscript) preserved where possible

**Optional (post-MVP):**
- Batch document processing
- TMX import/export for CAT tool interoperability
- CI/CD pipeline (GitHub Actions or GitLab CI)

## Acceptance Criteria

- [ ] User can import a DOCX file, translate it, and download a formatted bilingual/standalone DOCX
- [ ] User can import a PDF file (via docling), translate it, and download a translated DOCX
- [ ] User can select language pair: EN→ZH or EN+DE→EN+ZH
- [ ] User can choose output mode: bilingual or standalone
- [ ] User can upload CSV/Excel glossary, view/edit entries, select per task — but translation works without one
- [ ] Translation works with local Ollama (Qwen3 14B)
- [ ] Translation works with at least one cloud AI API (provider switchable in UI)
- [ ] User can toggle RAG on/off in translation config; when on, prior translation pairs improve consistency
- [ ] User can toggle image translation on/off; when on, text within document images is extracted and translated
- [ ] Long documents show progress bar; failed segments retry with timeout
- [ ] `docker compose up` starts all services (frontend + backend + ollama)

## Definition of Done

- Unit + integration tests for backend (FastAPI + doc parsing + translation pipeline)
- Lint / typecheck (Python: ruff/mypy, Frontend: ESLint/TypeScript)
- Docker Compose dev setup documented in README
- Docs updated if behavior changes

## Technical Approach

**Stack:**
```
Frontend:  React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query
Backend:   FastAPI + Pydantic + SQLAlchemy + Alembic
Database:  SQLite (volume-mounted, no separate service)
AI:        Ollama (Qwen3 14B Q5_K_M) + provider abstraction for cloud APIs
Doc:       python-docx (DOCX read/write) + docling (PDF → markdown)
Infra:     Docker Compose (3 services: frontend, backend, ollama)
```

**Data flow:**
```
Upload DOCX/PDF → python-docx/docling extract → markdown segments
  → AI translate (segments + glossary + language pair) → translated segments
  → python-docx rebuild → formatted DOCX → download
```

## Decisions (ADR-lite)

### ADR-01: Architecture — Docker Web App
**Decision**: Docker-based web app (React + FastAPI), not Electron
**Consequences**: Browser upload, Docker Compose services, simpler CI/CD. No native desktop features. Electron-specific specs partially inapplicable.

### ADR-02: Document Parsing — python-docx + docling
**Decision**: python-docx for DOCX (round-trip formatting), docling for PDF (→ markdown → DOCX output)
**Consequences**: Docker includes PyTorch (~1.5GB). Table cells + line breaks preserved as atomic units.

### ADR-03: Backend — FastAPI
**Decision**: FastAPI + Pydantic + uvicorn. Async file handling, auto OpenAPI docs.

### ADR-04: UX — Three-step Wizard
**Decision**: Upload → Configure (language, glossary, mode) → Translate (progress) → Preview (side-by-side) → Download

### ADR-05: Database — SQLite + SQLAlchemy + Alembic
**Decision**: SQLite with SQLAlchemy ORM. Zero extra Docker service. Sufficient for prototype.

### ADR-06: Docker Compose — 3 services
**Decision**: frontend (Vite) + backend (FastAPI) + ollama. No reverse proxy in dev.

### ADR-07: AI Strategy — Local-first, cloud-optional
**Decision**: Qwen3 14B via Ollama as default. Provider abstraction layer. Cloud APIs (Anthropic/DeepL) optional via env vars.

### ADR-08: Glossary — CSV/Excel import + UI CRUD
**Decision**: Import primary path; Web UI for view/edit/delete. Department-tagged. Future: TBX support.

### ADR-09: CI/CD — Deferred
**Decision**: Manual `docker compose up` during prototype. Pipeline added post-validation.

## Out of Scope

- Multi-user auth / team features
- CI/CD pipeline (post-prototype)
- Nginx/reverse proxy (dev only)
- PDF output generation (output always DOCX)
- Batch document processing
- TMX import/export (post-MVP)

### ADR-10: Testing — Mock AI provider (no real model on dev machine)

**Context**: Dev machine has limited disk space; cannot pull Qwen3 14B (~9.2GB)
**Decision**: Use mock/fake AI provider in tests and dev; real Ollama only in full Docker deployment
**Consequences**:
- Backend provider layer supports a `MockProvider` returning predictable translations
- Integration tests can run without Ollama
- `docker compose up` includes ollama service definition but devs can skip starting it

## Technical Notes

- Research: [docx-parsing.md](research/docx-parsing.md)
- Research: [pdf-parsing.md](research/pdf-parsing.md)
- Research: [ai-translation-apis.md](research/ai-translation-apis.md)
- Research: [rag-translation-memory.md](research/rag-translation-memory.md)
- Research: [docling-evaluation.md](research/docling-evaluation.md)
- Research: [local-models-medical-translation.md](research/local-models-medical-translation.md)
- `.trellis/spec/` Electron guidelines partially inapplicable; frontend TS/React + shared guidelines still valid
