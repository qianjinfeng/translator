# Research: Docling Evaluation for Medical Document Translation Pipeline

- **Query**: Evaluate IBM's docling library as the document parsing backbone in a medical document translation pipeline, with comparison to pymupdf4llm and other alternatives.
- **Scope**: mixed (internal dependency analysis + external research)
- **Date**: 2026-06-01

## Findings

## 1. Overview: IBM Docling

Docling is an open-source document understanding library developed by IBM Research Zurich. It parses diverse document formats (PDF, DOCX, PPTX, XLSX, HTML, images, and more) into a unified `DoclingDocument` representation that can be exported to Markdown, JSON, HTML, and other formats.

**Key Links:**
- GitHub: https://github.com/docling-project/docling
- Docs: https://docling-project.github.io/docling/
- Paper: https://arxiv.org/abs/2408.09869
- PyPI: https://pypi.org/project/docling/

**License:** MIT (codebase; individual model licenses apply per package)

---

## 2. Maturity & Community

| Metric | Value |
|---|---|
| GitHub Stars | ~60,700 |
| Forks | ~4,200 |
| Open Issues | ~862 |
| Open PRs | ~53 |
| PyPI Version | 2.96.0 |
| First Release | ~v0.1.0 (mid 2024) |
| Release Cadence | Very frequent (2-7 days between recent releases) |
| Monthly PyPI Downloads | ~38 million (cumulative) |
| Python Support | 3.10+ (3.9 dropped in v2.70.0) |
| OS Support | Linux, macOS, Windows (x86_64 and arm64) |
| Author Contact | Christoph Auer, Michele Dolfi, Maxim Lysak, Nikos Livathinos, Ahmed Nassar, Panos Vagenas, Peter Staar (all IBM Research Zurich) |

The project is hosted under **LF AI & Data Foundation** and has a Discord community. The rapid release cadence (170+ releases in ~2 years) indicates active development but also means the API surface changes frequently.

---

## 3. Unified API: DOCX + PDF (Key Question 1)

**YES -- docling provides a truly unified API for both DOCX and PDF (and many other formats).**

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()

# Both work with identical API:
pdf_result = converter.convert("document.pdf")
docx_result = converter.convert("document.docx")

# Unified output format:
print(pdf_result.document.export_to_markdown())
print(docx_result.document.export_to_markdown())
```

The unified representation is the `DoclingDocument` (a Pydantic v2 model) which stores:
- Text items (paragraphs, headings, lists, equations)
- Tables with cell-level structure
- Pictures with captions
- Document hierarchy (sections, groups)
- Furniture (headers, footers, page numbers)
- Layout information (bounding boxes)
- Provenance metadata

**Backends by format** (auto-selected by the converter):

| Format | Backend | Notes |
|---|---|---|
| PDF | `DoclingParseDocumentBackend` (custom C/C++ parser) + `pypdfium2` (rendering) | Full ML pipeline: layout analysis, table detection, OCR |
| DOCX | `MsWordDocumentBackend` (via python-docx) | Structure extracted from OOXML, no ML needed |
| PPTX | `MsPowerpointDocumentBackend` (via python-pptx) | |
| XLSX | `MsExcelDocumentBackend` (via openpyxl) | |
| HTML | `HTMLDocumentBackend` | |
| Images | `ImageDocumentBackend` | Scanned documents go through OCR |
| LaTeX | `LatexBackend` | |

**Key insight for translation pipeline:** DOCX parsing is lightweight (python-docx reads OOXML natively) while PDF parsing is heavyweight (requires PyTorch + ML models). The unified API hides this complexity, but the performance characteristics differ drastically.

---

## 4. Output Format Suitability for LLM Translation (Key Question 2)

### Markdown Export

```python
markdown_output = result.document.export_to_markdown()
```

Features:
- Headings preserved as `#` hierarchy (correct levels)
- Paragraphs separated by blank lines (clear boundaries)
- Tables rendered as GitHub Flavored Markdown pipe tables
- Bold/italic/code inline formatting preserved
- Lists (ordered and unordered) preserved
- Image references as `![caption](...)`
- Equations rendered with LaTeX delimiters
- Headers/footers excluded by default (furniture)
- Reading order preserved (including multi-column layouts)

### JSON Export (DoclingDocument serialization)

```python
json_output = result.document.export_to_dict()  # or model_dump()
```

Contains full structural information including:
- Per-item bounding boxes
- Provenance (which page, which backend)
- Type labels (text, table, picture, heading, etc.)
- Table cell grid coordinates
- Picture references with page/area coordinates

### DocTags Format

Docling also supports a compact text-based format called DocTags (https://arxiv.org/abs/2503.11576) designed for LLM fine-tuning, which wraps document structure with XML-like tags.

### Suitability for LLM Translation

**Strengths:**
- Paragraph boundaries are explicit (blank lines in markdown or separate items in JSON)
- Table structure is preserved as pipe tables -- LLMs generally handle this well
- Headings maintain document hierarchy -- important for medical documents with section structure
- Reading order is reconstructed (headings, body text sequence preserved)

**Weaknesses for round-trip:**
- Markdown output does NOT contain page break information
- Inline formatting is preserved but not all DOCX features (footnotes, cross-references, tracked changes, comment annotations) survive
- The markdown is a simplification -- fine for LLM consumption, lossy for exact DOCX reconstruction

---

## 5. Round-Trip: Markdown back to Formatted DOCX (Key Question 3)

**Partial answer: Yes, but with caveats.**

Docling can go from DOCX -> DoclingDocument -> JSON/markdown. However, the reverse path (markdown -> DOCX with formatting) is **not** a docling feature. You would need a separate library (e.g., python-docx with manual markdown parsing) to reconstruct a DOCX from the markdown output.

The **DoclingDocument JSON** format is richer and more lossless than markdown -- it preserves layout metadata, table cell geometry, and per-item types. If you serialize to JSON and use that as the translation intermediary, you could reconstruct a DOCX with better fidelity:

- Text items retain their type (heading vs paragraph vs list)
- Table cells have grid coordinates and content
- Pictures have location references
- Formatting (bold/italic) is marked per-text-run

**However**, docling does NOT provide a built-in "export to DOCX" function. The `DoclingDocument` can export to markdown, HTML, JSON, and DocTags, but not back to Office OpenXML. Reconstructing a DOCX would require writing a custom converter from the JSON format.

**Verdict on round-trip:** The JSON intermediate format is structured enough to rebuild a DOCX with custom code, but there is no off-the-shelf solution. The markdown output alone is insufficient for high-fidelity round-trip.

---

## 6. Handling of Specific Document Features

### Tables
- **PDF tables:** Detected via ML model (docling-ibm-models), converted to structured table objects with cell grid. Exported as GFM pipe tables.
- **DOCX tables:** Extracted from OOXML directly (python-docx). Same grid structure.
- **Complex tables:** Cell merging, rowspan/colspan, and nested tables are supported. For medical documents with complex regulatory tables, the table structure fidelity is good but very dense tables with merged cells in unusual patterns may have reduced accuracy from the PDF path.

### Headers and Footers
- Correctly identified as "furniture" and separated from body content.
- By default, headers/footers are excluded from markdown export.
- Configurable via `furniture_options` in the pipeline options.

### Images
- Detected, classified (via ML model for PDF), and either extracted or referenced.
- In markdown, images are represented as `![type](...ref...)`.
- For PDF, image classification categorizes figures, logos, diagrams, etc.
- For DOCX, images are extracted from the OOXML package.

### Multi-Column Layouts
- Docling's PDF pipeline (with the Heron layout model) handles multi-column layouts.
- Reading order is reconstructed: left-to-right across columns, top-to-bottom.
- This is a ML-driven capability, not purely rules-based.

### CJK Text (Chinese, Japanese, Korean)
- Docling uses OCR engines (RapidOCR by default, Tesseract optional, SuryaOCR as alternative) for scanned text in any script.
- For digital PDFs and DOCX files, CJK text is extracted via the text layer or OOXML parsing.
- The markdown output handles Unicode natively -- CJK text passes through correctly.
- **Potential issue:** CJK text has no spaces between words, so the LLM may need to handle word segmentation. Docling does not add spaces or tokenize CJK.
- For scanned CJK documents, RapidOCR supports CJK languages, but OCR accuracy on medical CJK text (technical terms, drug names) is an open question and should be tested.

---

## 7. Installation & Dependencies

### Basic Install (pip)

```bash
pip install docling
```

This installs `docling-slim[standard]` which pulls in the "standard" extras.

### Full Dependency Tree (critical for system requirements)

| Package | Size (approx) | Notes |
|---|---|---|
| `torch>=2.2.2` | 532 MB | PyTorch (CPU + CUDA) |
| `torchvision` | 7.6 MB | Vision models |
| `transformers>=4.42.0` | 10.8 MB | HuggingFace transformers |
| `accelerate>=1.0.0` | 383 KB | GPU acceleration |
| `huggingface-hub` | 671 KB | Model download |
| `docling-ibm-models` | 94 KB | IBM model weights (slim, downloads more on-demand) |
| `docling-parse` | 10.2 MB | Native C/C++ binary for PDF parsing |
| `pypdfium2` | 3.7 MB | PDF rendering |
| `rapidocr` | 15.1 MB | OCR engine (includes ONNX runtime) |
| `python-docx` | (already installed) | DOCX reading |
| `python-pptx` | 472 KB | PPTX reading |
| `openpyxl` | 250 KB | XLSX reading |
| `pillow` | 7.1 MB | Image processing |
| `numpy` | 16.6 MB | |
| `scipy` | ~30 MB | |
| `pandas` | ~15 MB | |
| `lxml` | (pre-installed) | XML parsing |
| `pydantic` + `pydantic-core` | ~5 MB | Data modeling |
| Various NVIDIA CUDA packages | ~200+ MB | GPU support for torch |
| **Total estimated install size** | **~1-1.5 GB** | |

**Critically, the `[standard]` install requires PyTorch** (532 MB + CUDA packages). There is a `docling-slim` base without ML (for DOCX/PPTX/XLSX only), but PDF understanding requires the standard extras.

### CPU vs GPU

By default, torch with CUDA support is installed. For CPU-only environments, the Docker approach uses `--extra-index-url https://download.pytorch.org/whl/cpu` to reduce size.

### Model Weights

Docling downloads ML model weights on first use (via `huggingface-hub`). The total model cache is approximately 500 MB - 1 GB depending on pipeline configuration.

### Docker

Docling provides a Dockerfile based on `python:3.11-slim-bookworm`:
- Installs `libgl1`, `libglib2.0-0` (OpenCV/rendering dependencies)
- Installs docling with CPU-only torch
- Sets `OMP_NUM_THREADS=4` for container environments
- Provides `docling-tools models download` to pre-download model weights
- Sets `HF_HOME=/tmp/` and `TORCH_HOME=/tmp/` for model caching

---

## 8. Performance on Large Documents (up to 50MB)

Docling has configurable `DocumentLimits`:
- Default page limit: 100 pages (configurable)
- Default file size limit: adjustable via settings
- Documents up to 50MB are within capability but will be memory-intensive due to PyTorch model loading

**Estimates:**
- **PDF (50MB, ~200-500 pages):** Parsing may take 5-30 minutes depending on page complexity, OCR needs, and CPU/GPU. Memory usage could reach 2-4 GB with PyTorch + model cache.
- **DOCX (50MB, formatted text + images):** Parsing is nearly instant (python-docx reads OOXML directly). No ML pipeline needed. Memory usage is minimal.
- **Mixed pipeline:** Processing a batch of documents is best done sequentially or with the built-in `ThreadPoolExecutor`.

**Verdict:** Performance is acceptable for batch processing but not real-time. The PDF pipeline is the bottleneck.

---

## 9. Comparison with Alternatives

### pymupdf4llm

| Aspect | docling | pymupdf4llm |
|---|---|---|
| **Developed by** | IBM Research Zurich | Artifex Software (MuPDF creators) |
| **License** | MIT (code) + varies (models) | AGPL v3 or commercial |
| **GitHub Stars** | ~60,700 | ~1,800 (pymupdf/RAG) |
| **PyPI Version** | v2.96.0 | v1.27.2.3 |
| **Python** | 3.10+ | 3.10+ |
| **Install Size** | ~1-1.5 GB (with torch/CUDA) | ~56 MB (pymupdf + layout + onnxruntime) |
| **GPU Required** | No (but heavy without it) | No |
| **PyTorch Needed** | YES | NO |
| **PDF Support** | Full ML pipeline (layout, table, OCR) | Layout-aware, table detection, OCR |
| **DOCX Support** | YES (via python-docx), native | Requires PyMuPDF Pro (PAID) |
| **PPTX Support** | YES | Requires PyMuPDF Pro (PAID) |
| **XLSX Support** | YES | Requires PyMuPDF Pro (PAID) |
| **Unified API** | YES -- single converter for all formats | **NO** -- PDF only (Office via paid addon) |
| **Markdown Output** | Excellent | Excellent |
| **JSON Output** | Yes (full DoclingDocument serialization) | Yes (layout + bbox metadata) |
| **Reading Order** | ML-driven | Algorithmic + layout model |
| **Table Detection** | ML model (docling-ibm-models) | Layout analysis (ONNX model) |
| **OCR** | RapidOCR, Tesseract, SuryaOCR | Hybrid selective OCR (Tesseract-based) |
| **CJK Support** | Via OCR engines; no special handling | Via OCR; no special handling |
| **Document Hierarchy** | Rich (headings, sections, furniture) | Heading detection via font analysis |
| **LLM Integrations** | LangChain, LlamaIndex, Haystack, Crew AI | LangChain, LlamaIndex |
| **CLI Tool** | `docling` command | Not bundled |
| **MCP Server** | YES | NO |
| **Maturity** | Very active, frequent breaking changes | Stable, smaller community |

**pymupdf4llm is NOT a viable DOCX parser** without the commercial PyMuPDF Pro addon. It is a PDF-only solution in its free form. This is the single most important differentiator.

### Other Alternatives

| Tool | Stars | DOCX? | PDF? | Install Size | License | Notes |
|---|---|---|---|---|---|---|
| **unstructured.io** | ~14,800 | YES | YES | ~500 MB+ | Apache 2.0 | Heavy, many system deps. Enterprise-focused. |
| **marker (VikParuchuri)** | ~35,600 | NO | YES | ~1 GB+ | GPL v3 | PDF-only. Fast. PyTorch + Surya models. No DOCX. |
| **llmsherpa** | (small) | NO | YES | Variable | MIT | API-based (NLPCloud). No local option. |
| **pymupdf4llm** | ~1,800 | NO (paid) | YES | ~56 MB | AGPL v3 | Lightest option. PDF-only free. |

---

## 10. Medical Document Specific Concerns

### Complex Tables
- Docling's ML-based table detection works well on typical academic/business tables. Medical regulatory tables (e.g., adverse event reporting, clinical trial data) often have:
  - Merged cells spanning multiple rows/columns
  - Multi-line cells with paragraph-level text inside
  - Cell-level formatting (bold terms, italicized medical terms)
  - Numeric alignment with decimal precision
- **Risk:** Table extraction from PDF for such documents may have errors, especially with cell merging. Testing on actual medical documents is essential.

### Regulatory Formatting
- CTD (Common Technical Document) modules, FDA forms, and other regulatory PDFs often have:
  - Strict margins and header/footer requirements
  - Multi-level numbering (1.1, 1.1.1)
  - Table of contents with page references
- Docling handles multi-level headings well but does NOT extract TOC structure natively.

### OCR for Scanned Medical Documents
- Many older medical documents are scanned PDFs (not born-digital).
- Docling supports multiple OCR engines (RapidOCR default, Tesseract optional).
- Medical terminology OCR accuracy is a concern -- drug names, lab values, and proper nouns may have OCR errors.
- RapidOCR supports the scripts needed for most languages but has not been specifically benchmarked on medical text.

### Sensitive Data
- Docling runs fully locally, which is important for HIPAA/GDPR compliance -- no data leaves the environment.
- All ML inference happens on local hardware.
- No cloud dependency for document processing.

---

## 11. Caveats and Known Issues

### API Stability
- Docling v2 has had breaking changes across minor versions. The API differs from v1 significantly. Pinning the version is essential.
- The `DoclingDocument` Pydantic schema changes between releases. JSON serialized with one version may not deserialize with another.

### Heavy Installation
- The `[standard]` install is ~1-1.5 GB. If only DOCX parsing is needed, docling is overkill.
- PyTorch brings in CUDA packages even on systems without GPU. Use CPU-only pip index to reduce size.

### Docker Image
- The Dockerfile uses CPU-only torch. Without GPU, PDF parsing is slow (potentially 5-30 seconds per page).
- Model weights download on first run (~500 MB-1 GB additional).

### DOCX Limitations
- While docling reads DOCX well, it only goes one direction: DOCX -> DoclingDocument. Round-trip (DoclingDocument -> translated DOCX) is not supported.
- Track changes, comments, footnotes, and some advanced OOXML features may not be captured.

### Not Found
- Native support for DICOM medical image formats (not expected, but note for context)
- Built-in DOCX export (would need custom implementation)
- Built-in document comparison/diff for pre/post translation verification

---

## 12. Recommendations for Translation Pipeline

### Scenario A: Unified DOCX + PDF pipeline (the main reason to choose docling)
- **Choose docling.** It is the only serious option that handles both DOCX and PDF with a single API and produces a unified intermediate representation.
- **Architecture:** DOCX -> DoclingDocument -> JSON -> LLM Translate -> JSON -> Custom DOCX Builder
- **Downsides:** Heavy install, no built-in DOCX reconstruction, ML model weight management.

### Scenario B: PDF-only pipeline
- **Consider pymupdf4llm** for lightweight, no-PyTorch PDF parsing. It handles multi-column, tables, images, and OCR well.
- Combine with `python-docx` natively for DOCX handling (separate code path).
- **Advantage:** ~56 MB vs ~1.5 GB install. No GPU needed. Faster processing.
- **Downside:** Two code paths for PDF vs DOCX, less rich intermediate representation.

### Scenario C: DOCX-only pipeline
- Docling is overkill. Use `python-docx` directly with custom markdown extraction.
- Much simpler, no ML dependencies.

### Recommended approach for this project:
Use **docling** if unified DOCX+PDF handling is essential and the team can accept the heavy install footprint. Use **pymupdf4llm + python-docx** as a lighter alternative if separate code paths for each format are acceptable.

### Related Specs

- None yet. Consider creating a `docling-integration.md` spec if proceeding with docling, covering:
  - Pinned version (e.g., `docling==2.96.0`)
  - Pipeline options (disable table model, set page limits, configure OCR)
  - JSON schema versioning strategy
  - Custom DOCX reconstruction from DoclingDocument JSON

## Detailed Alternative: pymupdf4llm

### Overview

pymupdf4llm is a lightweight extension for PyMuPDF (the Python binding for the MuPDF C library) that converts documents into structured Markdown, JSON, and plain text. Developed by Artifex Software (the company behind MuPDF).

**GitHub:** https://github.com/pymupdf/RAG  
**Docs:** https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/  
**License:** AGPL v3 (free open source) or commercial license from Artifex

### Maturity

| Metric | Value |
|---|---|
| GitHub Stars | ~1,800 (in pymupdf/RAG repo) |
| Open Issues | ~25 |
| PyPI Version | 1.27.2.3 (tracks PyMuPDF versioning) |
| First Release | ~0.0.1 (late 2023) |
| Python Support | 3.10+ |
| License | AGPL v3 (copyleft -- implications for proprietary use) |

### Installation

```bash
pip install pymupdf4llm
```

Total installed size: ~56 MB (PyMuPDF 24MB + pymupdf-layout 15MB + onnxruntime 17MB + minor packages)

**No PyTorch, no CUDA, no GPU required.**

### Supported Formats

| Format | Free Version | With PyMuPDF Pro (paid) |
|---|---|---|
| PDF | Full support | Full support |
| XPS/OXPS | Full support | Full support |
| EPUB/MOBI/FB2 | Full support | Full support |
| Images (PNG, JPG, TIFF) | Full support | Full support |
| DOCX | NO | YES |
| XLSX | NO | YES |
| PPTX | NO | YES |
| HWP/HWPX | NO | YES |

**Critical limitation:** DOCX, XLSX, and PPTX parsing requires PyMuPDF Pro, which is a commercial/paid addon from Artifex. This makes pymupdf4llm effectively a PDF-only solution in its free form.

### API

```python
import pymupdf4llm

# Markdown output (PDF only free)
md = pymupdf4llm.to_markdown("document.pdf")

# JSON output with layout metadata
data = pymupdf4llm.to_json("document.pdf")

# Plain text
text = pymupdf4llm.to_text("document.pdf")

# Page chunks (metadata per page)
chunks = pymupdf4llm.to_markdown("document.pdf", page_chunks=True)
```

### Output Quality

- **Markdown:** GitHub-compatible, with GFM pipe tables, heading hierarchy via font size analysis, inline formatting (bold, italic, code), list detection, image references
- **Layout analysis:** Reconstructs reading order for multi-column layouts using ONNX-based layout model
- **Table detection:** Finds and converts tables to markdown; handles multi-line cells
- **OCR:** Hybrid selective OCR (only regions that need it); uses Tesseract backend; configurable language
- **Images:** Can extract images to disk with configurable DPI

### CJK Support

- No special CJK handling in the text extraction layer
- OCR supports Tesseract language packs (`ocr_language="eng+chi_sim+jpn"`)
- Unicode text passes through correctly in markdown output

### Performance

- 10-250x cheaper than vision-based LLM extraction
- Selective OCR reduces OCR time by ~50% compared to full-page OCR
- Processing time is typically <1 second per page for digital PDFs

### Best For

- **PDF-only pipelines** (free version)
- **Lightweight RAG/LLM ingestion** where install size matters
- **GPU-free environments** (CPU only, no PyTorch)
- **High-volume batch processing** of PDF files

### Not Suitable For

- DOCX/PPTX/XLSX parsing without commercial license
- Rich document hierarchy beyond heading levels
- Applications needing AGPL compliance or wanting to avoid copyleft
- Round-trip reconstruction to Office formats

### Comparison Summary: docling vs pymupdf4llm

| Need | docling | pymupdf4llm |
|---|---|---|
| Unified DOCX + PDF API | **YES** | NO (PDF only free) |
| Lightweight install | NO (~1.5 GB) | **YES (~56 MB)** |
| No PyTorch/GPU | NO (requires torch) | **YES** |
| Rich document hierarchy | **YES** (sections, furniture, types) | Partial (heading levels, no section model) |
| Table extraction | **YES** (ML + OOXML) | **YES** (layout analysis + ONNX) |
| CJK text | OCR-based (RapidOCR) | OCR-based (Tesseract) |
| Medical document suitability | Good (local, private, table-aware) | Good for PDF; no DOCX free |
| Legal/license | **MIT** (permissive) | AGPL (copyleft) or commercial |
