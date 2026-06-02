# Research: PDF Parsing & Handling for Translation Application

- **Query**: Research PDF text extraction and handling libraries for Node.js/Electron, with focus on translation use cases
- **Scope**: Mixed (external library research + architecture analysis)
- **Date**: 2026-06-01

## 1. Library Comparison: PDF Text Extraction in Node.js/Electron

### 1.1 pdfjs-dist (Mozilla's PDF.js)

| Attribute | Value |
|---|---|
| **npm** | `pdfjs-dist` |
| **Version** | 6.0.227 |
| **License** | Apache-2.0 |
| **Dependencies** | None (zero-dependency) |
| **TypeScript** | Types included (`types/src/pdf.d.ts`) |
| **Maintainers** | Mozilla (Yury Delendik, Brendan Dahl, Calixte Denizet, et al.) |

**Capabilities:**
- Full PDF parser and renderer (the gold standard in browser JS PDF processing)
- Text extraction via `page.getTextContent()` which returns an ordered array of text items with position data (x, y, width, height, transform matrix)
- Page rendering to canvas/image (useful for OCR pipeline on scanned PDFs)
- Works in both browser and Node.js with appropriate polyfills
- Respects reading order reasonably well for single-column layouts

**Translation-specific considerations:**
- `getTextContent()` returns items grouped by text runs, not paragraphs. Paragraph boundaries must be inferred from position gaps and font size changes.
- Multi-column layouts require heuristics to reorder text correctly (PDF.js returns items in PDF content stream order, which may be column-by-column or interleaved).
- Tables are not recognized structurally -- cells are just positioned text items.
- Headers/footers are not automatically identified and filtered; must be detected via position heuristics (e.g., items near page edges, repeating content across pages).
- No built-in support for scanned PDFs / OCR.

**Example usage for text extraction:**
```typescript
import * as pdfjsLib from 'pdfjs-dist';

const doc = await pdfjsLib.getDocument(data).promise;
const page = await doc.getPage(1);
const content = await page.getTextContent();
// content.items: Array of { str, dir, width, height, transform, ... }
// Can reconstruct text by sorting by transform[5] (y) then transform[4] (x)
```

---

### 1.2 pdf-parse (v2.x)

| Attribute | Value |
|---|---|
| **npm** | `pdf-parse` |
| **Version** | 2.4.5 |
| **License** | Apache-2.0 |
| **Dependencies** | `pdfjs-dist@5.4.296`, `@napi-rs/canvas@0.1.80` |
| **TypeScript** | Written in TypeScript |

**Capabilities:**
- Wrapper around pdfjs-dist with improved text structure extraction
- Claims to extract text, images, and tabular data
- Pure TypeScript, marketed as cross-platform (browser + Node.js)

**Translation-specific considerations:**
- **CRITICAL**: Depends on pdfjs-dist v5.4.296, which is behind latest (v6.0.227). May miss recent PDF rendering fixes.
- **CRITICAL**: Depends on `@napi-rs/canvas` -- this is a native Node.js addon (Skia canvas). In Electron, native addons must be rebuilt for the Electron Node.js ABI using `electron-rebuild` or `@electron/rebuild`. This adds significant packaging complexity, especially for cross-platform builds.
- The `@napi-rs/canvas` dependency was introduced in v2.x (v1.x did not have it). If canvas rendering is not needed, v1.x might be lighter.
- The table extraction claim is worth evaluating -- likely relies on spatial analysis of text positions rather than PDF structure tags (Tagged PDF).

**Verdict: High risk for Electron due to native canvas dependency.** Prefer pdfjs-dist directly (zero native deps) with custom text structure extraction logic.

---

### 1.3 pdf2json

| Attribute | Value |
|---|---|
| **npm** | `pdf2json` |
| **Version** | 4.0.3 |
| **License** | Apache-2.0 |
| **Dependencies** | Zero (claims zero-dependency) |
| **Repository** | https://github.com/modesty/pdf2json |

**Capabilities:**
- PDF parser that outputs JSON with text items, position data, and styling
- Based on a fork of older PDF.js
- Designed for server-side processing and CLI use
- Output includes: text content with font, size, color, and transform data
- Can output plain text as well as JSON

**Translation-specific considerations:**
- Zero dependencies is attractive for Electron packaging
- Output format: `{ Texts: [{ x, y, w, h, fontName, fontSize, R, G, B, A, str }], Width, Height, ... }`
- But the underlying PDF.js fork is old -- may not handle modern PDF features well
- Position data is flat (per-page array of text items), no paragraph grouping
- Same structural limitations as pdfjs-dist for multi-column, table, header/footer detection
- Less actively maintained than pdfjs-dist (Mozilla's PDF.js has frequent releases)

**Verdict:** Useful as a lightweight option if JSON structure is needed, but the older PDF.js engine is a risk for edge-case PDFs.

---

### 1.4 pdf.js-extract

| Attribute | Value |
|---|---|
| **npm** | `pdf.js-extract` |
| **Version** | 1.0.1 |
| **License** | MIT |
| **Dependencies** | `dommatrix@0.1.1` |
| **Repository** | https://github.com/ffalt/pdf.js-extract |

**Capabilities:**
- Lightweight async wrapper around pdf.js
- Extracts text with x,y page positions
- Simple API: returns `{ page: number, content: [{ x, y, w, h, str, dir }] }`

**Translation-specific considerations:**
- Very basic -- no paragraph detection, no structure preservation
- Effectively a thin wrapper over pdf.js's `getTextContent()`
- Low maintenance (only 1 release, published 2026-04-19)
- Position output is raw from pdf.js

**Verdict:** Too minimal for translation use cases. Better to use pdfjs-dist directly.

---

### 1.5 pdf-lib

| Attribute | Value |
|---|---|
| **npm** | `pdf-lib` |
| **Version** | 1.17.1 |
| **License** | MIT |
| **Dependencies** | `@pdf-lib/standard-fonts`, `@pdf-lib/upng`, `pako`, `tslib` |
| **Homepage** | https://pdf-lib.js.org/ |

**Capabilities:**
- Create and modify PDF documents
- Add text, images, fonts, annotations
- Fill PDF forms
- Split/merge PDFs
- **NOT a text extraction library** -- it has no `getTextContent()` equivalent

**Translation-specific considerations:**
- Useful only for the OUTPUT side: generating a translated PDF from scratch
- Can embed custom fonts (important for CJK, Arabic, etc.)
- Has limited layout capabilities (no auto-flow, no multi-column layout, no table layout)
- Better suited for simple translated PDF output (overlaying translated text on original page images) than full document reconstruction

**Verdict:** Not for extraction. Good candidate for simple translated PDF generation, but lacks advanced layout features for complex restoration.

---

### 1.6 MuPDF.js (Artifex)

| Attribute | Value |
|---|---|
| **npm** | `mupdf` |
| **Version** | 1.27.0 |
| **License** | **AGPL-3.0** (strong copyleft -- critical for commercial apps) |
| **Dependencies** | Zero |
| **Homepage** | https://mupdf.readthedocs.io/en/latest/ |
| **Source** | https://cgit.ghostscript.com/mupdf.git/ |

**Capabilities:**
- MuPDF is a high-performance, high-fidelity PDF rendering engine written in C
- The `mupdf` npm package provides WASM-based JavaScript bindings
- Fast text extraction with excellent structural fidelity
- Page rendering to image (bitmap)
- Supports PDF, XPS, EPUB, CBZ, and other document formats
- Handles complex layouts, transparency, and modern PDF features well
- Can output text with position information via `StructuredText` API

**Translation-specific considerations:**
- **LICENSE CRITICAL**: AGPL-3.0 requires the entire application to be open-sourced under AGPL, or a commercial license must be purchased from Artifex Software. For a closed-source or proprietary translation app, this is a blocker without purchasing a commercial license.
- Text extraction quality is generally excellent -- preserves reading order, paragraph structure, and column layout better than pdf.js in many cases
- Very fast (C-based, even with WASM overhead)
- Provides access to PDF structure tree (Tagged PDF) when available, giving access to logical document structure (headings, paragraphs, figures, tables)
- Can render pages to images scaled precisely, useful for OCR failover

**Verdict:** Best-in-class extraction quality, but the AGPL license makes it risky for commercial applications. If the app is open-source or a commercial MuPDF license is budgeted, this is the best option.

---

### 1.7 Tesseract.js

| Attribute | Value |
|---|---|
| **npm** | `tesseract.js` |
| **Version** | 7.0.0 |
| **License** | Apache-2.0 |
| **Dependencies** | `tesseract.js-core`, `wasm-feature-detect`, `node-fetch` |
| **Homepage** | https://github.com/naptha/tesseract.js |

**Capabilities:**
- Pure JavaScript OCR engine (Tesseract compiled to WebAssembly)
- Supports 100+ languages
- Can be trained with custom data
- Runs entirely client-side (no external API calls)
- Returns text with confidence scores, bounding boxes, and word-level data

**Translation-specific considerations:**
- **IMPORTANT: Tesseract.js does NOT support PDF files directly.** It only accepts images. For scanned PDF OCR, you must first render each PDF page to an image (using pdfjs-dist or MuPDF), then pass the image to Tesseract.js.
- OCR accuracy is good but not excellent -- typically 90-95% for clean documents, lower for poor quality scans, unusual fonts, or complex layouts.
- Output structure: returns text with word-level bounding boxes (`words`), line-level grouping (`lines`), paragraph-level grouping (`paragraphs`), and block-level grouping (`blocks`).
- Block-level output preserves reading order reasonably well for single-column documents.
- Slow -- processing a single page can take 1-10 seconds depending on content complexity and CPU.
- Memory intensive -- each language adds ~5-15MB of WASM data.
- For multi-column layouts, Tesseract's layout analysis (LSTM-based) is decent but not perfect.
- See Section 4 below for detailed comparison with cloud OCR APIs.

**Verdict:** Viable for client-side OCR of scanned PDFs (when combined with PDF page rendering), but the quality and speed limitations make cloud APIs preferable for production use, especially in a translation workflow where OCR errors compound with translation errors.

---

### 1.8 scribe.js-ocr (Alternative)

| Attribute | Value |
|---|---|
| **npm** | `scribe.js-ocr` |
| **Version** | 0.12.3 |
| **License** | **AGPL-3.0** |
| **Dependencies** | `@scribe.js/canvas`, `commander` |
| **Homepage** | https://github.com/scribeocr/scribe.js |

**Capabilities:**
- OCR + text extraction for images and PDFs (directly supports PDF input)
- Improved recognition model over base Tesseract
- Built on Tesseract but with enhancements

**Verdict:** AGPL license is a blocker for commercial use. Pdf.js + Tesseract.js combination achieves the same result with Apache-2.0 licensing.

---

### 1.9 Summary Comparison Table

| Library | Extraction | OCR | License | Dependencies | Electron Risk | Structure Quality |
|---|---|---|---|---|---|---|
| **pdfjs-dist** | Yes | No (render to img only) | Apache-2.0 | Zero | Low | Good (needs custom grouping) |
| **pdf-parse v2** | Yes | No | Apache-2.0 | pdfjs-dist + @napi-rs/canvas | HIGH (native) | Good (built-in grouping) |
| **pdf2json** | Yes | No | Apache-2.0 | Zero | Low | Fair (old pdf.js fork) |
| **pdf.js-extract** | Yes | No | MIT | dommatrix | Low | Minimal (raw positions) |
| **pdf-lib** | No (generate only) | No | MIT | 4 small libs | Low | N/A |
| **MuPDF.js** | Yes | No | AGPL-3.0 | Zero | Low | **Excellent** |
| **Tesseract.js** | No (images only) | Yes | Apache-2.0 | 3 libs | Low-Medium | Good (word/line/block) |
| **scribe.js-ocr** | Yes | Yes | AGPL-3.0 | @scribe.js/canvas | Medium | Good |

---

## 2. How Commercial Translation Tools Handle PDF Input

### 2.1 memoQ
- Converts PDF to its internal bilingual format via built-in PDF filter
- Uses a combination of text extraction and OCR (ABBYY FineReader engine for scanned PDFs)
- Extracted text is segmented into sentences/paragraphs for translation
- Preserves formatting tags inline (bold, italic, font changes, positioning hints)
- On re-import, attempts to restore original formatting -- generally works for simple layouts, degrades gracefully for complex ones
- **Key insight**: Commercial tools treat PDF as a "source-only" format; they rarely output translated PDF with identical formatting. Output is typically DOCX, XLIFF, or a bilingual format.

### 2.2 Trados Studio (RWS)
- Uses built-in PDF parser based on Adobe's PDF technology
- Scanned PDFs: requires OCR add-on (previously ABBYY, now internal)
- Text extraction preserves inline formatting via Trados-style tags
- Segments text into translatable units based on sentence boundaries
- Output: typically DOCX or Trados's native SDLXLIFF format
- **Key insight**: Trados relies on intermediate formats -- it does not attempt to generate a re-layouted PDF from translated content.

### 2.3 DeepL Pro API (Document Translation)
- Accepts PDF input directly
- Internally extracts text and metadata, translates, returns translated document preserving original layout
- Supports output formats: DOCX, PDF (with layout preserved), PPTX, XLSX, XLIFF, HTML, TXT, SRT
- **Key insight**: DeepL preserves PDF layout quite well, but uses proprietary technology. The API charges a minimum of 50,000 characters per document regardless of actual content length.
- Technical approach: likely renders original PDF page to background image, overlays translated text in approximately the same positions, adjusts text size/wrapping to fit.

### 2.4 General Pattern Across All CAT Tools

The industry standard workflow for PDF translation is:

```
PDF -> Extract Text + Formatting + Position -> Segment into Translation Units -> 
Translate (with context) -> Reassemble (usually output to DOCX or HTML, rarely back to PDF)
```

- **PDF is a source-only input format.** All professional tools prefer outputting to DOCX or HTML rather than trying to recreate the original PDF layout exactly.
- **Tagged PDFs** (Tagged PDF / PDF/UA) provide structural metadata that greatly improves extraction quality, but most PDFs in the wild are untagged.
- **The intermediate format** used internally is typically:
  - XLIFF (OASIS standard) -- the industry standard for translation data interchange
  - Inline tag format (similar to HTML with position markers)
  - Sentence/segment-aligned bilingual pairs

---

## 3. Intermediate Representation Before Translation

### 3.1 Candidate Formats

#### Option A: Structured JSON with Position Data
```json
{
  "pages": [{
    "pageNumber": 1,
    "width": 612,
    "height": 792,
    "blocks": [{
      "type": "paragraph",
      "bbox": { "x": 72, "y": 72, "w": 468, "h": 36 },
      "textRuns": [
        { "text": "Hello ", "font": "Helvetica", "size": 12, "bold": false },
        { "text": "World", "font": "Helvetica", "size": 12, "bold": true }
      ]
    }]
  }]
}
```
**Pros:**
- Preserves all position data for potential re-layout
- Can represent inline formatting (bold, italic, font changes)
- Segments can be extracted for translation while preserving context
- Machine-readable and format-agnostic

**Cons:**
- Large file size
- Complex to generate and consume
- Overkill if output is not PDF

#### Option B: Markdown with Positional Hints
```markdown
<!-- p1 bbox: 0,0,612,792 -->
# Section Title

This is a paragraph of text. It contains **bold** and *italic* text.

- List item one
- List item two

> A blockquote that might have been indented in the original
```
**Pros:**
- Human-readable and editable
- LLMs handle markdown natively (natural for LLM-based translation)
- Supports structure (headings, lists, blockquotes, tables)
- Easy to review and post-process
- Can be converted to many output formats easily

**Cons:**
- No precise position data (if exact PDF re-layout is needed)
- Table representation is lossy for complex table layouts
- Header/footer distinction is lost

#### Option C: Plain Text Segments with Segment IDs
```
[1] This is the first sentence of the document.
[2] This is the second sentence.
[3] This paragraph continues here.
```
**Pros:**
- Simplest possible format
- Easy to translate (works with any translation service)
- Smallest overhead

**Cons:**
- All structure lost
- No formatting, no positions, no context
- Impossible to reconstruct document layout from output

#### Option D: XLIFF (Standard Translation Format)
```xml
<xliff version="2.0">
  <file original="doc.pdf">
    <unit id="1">
      <segment>
        <source>Hello World</source>
        <target>Hola Mundo</target>
      </segment>
    </unit>
  </file>
</xliff>
```
**Pros:**
- Industry standard for translation tools
- Supported by CAT tools, TM systems, and translation APIs
- Preserves segmentation, context, and metadata
- The `xliff` npm package v6.3.0 can read/write XLIFF

**Cons:**
- Verbose XML
- Does not natively preserve visual layout/positioning
- Overengineered if not interoperating with other CAT tools

#### Option E: HTML (with data attributes for position)
```html
<p data-page="1" data-bbox="72,72,468,36">
  This is a <strong>paragraph</strong> of text.
</p>
```
**Pros:**
- Universal rendering support
- CSS can approximate original layout
- Easy to translate (extract text nodes, leave tags)
- Many conversion tools exist (HTML -> DOCX via mammoth, HTML -> PDF via puppeteer/electron)
- Natural fit for Electron renderer process

**Cons:**
- HTML rendering differs across engines
- Exact pixel-perfect re-layout is not achievable
- Tables from PDF are difficult to represent correctly

### 3.2 Recommended Approach

**Use Markdown as the primary intermediate format for AI/LLM-based translation, with a JSON metadata sidecar for positional data.**

Rationale:
- LLMs (the likely translation engine in this app) understand markdown natively and preserve structure well during translation.
- Position metadata can be captured separately for optional PDF re-generation.
- Markdown is easily converted to HTML (via markdown-it or similar), then to DOCX via mammoth or html-to-docx.
- Markdown tables, lists, headings, and code blocks map well to PDF text structure.
- When position precision is needed (e.g., for PDF re-layout), the JSON sidecar provides the raw coordinates.

```
Extracted PDF Text + Structure
        |
        v
Markdown (primary) + Position JSON (sidecar)
        |
        v
LLM Translation (preserves markdown structure)
        |
        v
Translated Markdown  +  Translated Position JSON (adjusted for expansion/shrinkage)
        |
        +---> DOCX output (via mammoth / html-to-docx)
        +---> HTML output
        +---> PDF (via pdf-lib or Electron print-to-PDF)
```

---

## 4. OCR Quality: Tesseract.js vs Cloud OCR APIs

### 4.1 Tesseract.js (Local, Client-Side)

| Aspect | Assessment |
|---|---|
| **Accuracy (clean scan)** | 90-95% for high-quality scans, good fonts, clean backgrounds |
| **Accuracy (poor quality)** | 60-80% for low DPI, skewed, noisy, or unusual font documents |
| **Accuracy (handwriting)** | Poor (20-40%) |
| **Speed** | 1-10 seconds per page (CPU-bound, varies by content) |
| **Languages** | 100+ languages supported, trained data files are ~5-15MB each |
| **Multi-column layout** | LSTM layout analysis is decent but imperfect; columns may merge |
| **Table detection** | Basic -- can detect table blocks but cell boundaries are unreliable |
| **Output detail** | Word-level bounding boxes, confidence scores, paragraph/block grouping |
| **Memory usage** | ~100-300MB per worker (WASM + trained data) |
| **License** | Apache-2.0 |
| **Dependencies** | Self-contained (WASM-based) |

**Strengths:**
- Fully offline, no external API calls
- No per-page costs
- Privacy-preserving (no document data leaves the machine)
- Apache-2.0 license

**Weaknesses:**
- Significantly lower accuracy than cloud APIs for challenging documents
- Slower than cloud APIs (WASM-bound, no GPU acceleration)
- High memory consumption per worker
- Requires PDF page rendering to images as a preprocessing step
- Layout analysis is inferior to cloud solutions
- Cannot handle handwriting or decorative fonts

### 4.2 Google Cloud Document AI (OCR)

| Aspect | Assessment |
|---|---|
| **Accuracy (clean scan)** | 98-99% |
| **Accuracy (poor quality)** | 90-95% |
| **Accuracy (handwriting)** | 80-85% |
| **Speed** | 1-3 seconds per page (server-side, GPU-accelerated) |
| **Pricing** | $1.50 per 1,000 pages (OCR processor) |
| **Languages** | 200+ languages |
| **Multi-column** | Excellent -- uses deep learning layout analysis |
| **Table detection** | Very good -- detects tables, rows, cells, headers |
| **Output** | Structured JSON with layout, paragraphs, tables, form fields |
| **Free tier** | First 1,000 pages/month free |

**Strengths:**
- Best-in-class OCR accuracy
- Excellent structure preservation (reading order, tables, forms, headers, footers)
- Handles complex layouts, multi-column, and mixed content
- Extracts key-value pairs and form fields
- GPU accelerated

**Weaknesses:**
- Requires internet connection
- Per-page costs at scale
- Data leaves the machine (privacy/compliance concern)
- Vendor lock-in
- Requires Google Cloud setup and API key

### 4.3 AWS Textract

| Aspect | Assessment |
|---|---|
| **Accuracy** | Comparable to Google (98-99%) |
| **Pricing** | $1.50 per 1,000 pages |
| **Table/form detection** | Excellent |
| **Languages** | Limited (~20 languages for full features, more for text detection) |
| **Free tier** | 1,000 pages/month for 3 months |

### 4.4 Azure AI Document Intelligence

| Aspect | Assessment |
|---|---|
| **Accuracy** | Comparable to Google/AWS |
| **Pricing** | $1.50-$10 per 1,000 pages (varies by feature) |
| **Languages** | Extensive (100+) |
| **Table/form detection** | Excellent |
| **Free tier** | 500 pages/month free |

### 4.5 Verdict

For a **translation application**, OCR errors are particularly harmful because they compound with translation errors:
- OCR "hello" -> translation "hola" (correct)
- OCR "he11o" (misread 'l' as '1') -> translation may be garbled

**Recommendation by use case:**

| Use Case | Recommended OCR |
|---|---|
| Occasional personal use, offline | Tesseract.js (free, private, adequate for clean scans) |
| Commercial product, high quality, online | Google Cloud Document AI (best accuracy + structure) |
| Privacy-critical documents | Tesseract.js with a fallback note that quality is lower |
| Mixed approach | Try pdfjs-dist text extraction first; fall back to Tesseract.js for pages with low confidence, offer cloud API as premium option |

**Key insight**: Many "scanned PDFs" actually contain hidden text layers (from a previous OCR pass). Always try text extraction with pdfjs-dist first; only fall back to OCR if the extracted text is empty or has very low density (less than 1% of the page area has text).

---

## 5. PDF Output Generation

### 5.1 Options for Output

#### Option A: Render Translated Text Over Original PDF Page Images (Best Fidelity)

**Process:**
1. Render each page of the original PDF to a high-resolution background image (pdfjs-dist can do this)
2. Add a transparent text layer on top with translated text in approximately the same positions
3. Output as a new PDF with image background + selectable text layer

**Tools:**
- pdfjs-dist for page rendering (canvas to image)
- pdf-lib to create the new PDF, embed images, and add text overlay
- Or: use Electron's `BrowserWindow.webContents.printToPDF()` for HTML-based rendering

**Pros:**
- Exact visual preservation of original formatting
- Text is selectable/searchable (if text layer is added)
- Works for any original PDF regardless of complexity

**Cons:**
- Background is a raster image (larger file size, doesn't scale to very high zoom)
- Text overlays may not fit if translation is much longer/shorter than original
- Font substitution may cause visual mismatches
- Complex for mixed RTL/LTR text

#### Option B: Generate New PDF with pdf-lib (Limited Layout)

**Process:**
1. Extract text and formatting info from original
2. Translate text
3. Create new PDF page by page using pdf-lib, placing text with embedded fonts

**Pros:**
- Small file size (vector text)
- Fully searchable and selectable text
- Full control over fonts and layout

**Cons:**
- pdf-lib has no auto-flow, no multi-column layout, no table support, no line-wrapping
- Would need to implement a complete layout engine from scratch
- Impractical for anything but the simplest single-column documents
- **Verdict: Not recommended for restoring complex layouts.**

#### Option C: Output as DOCX (Recommended)

**Process:**
1. Extract text as structured markdown or HTML (preserving formatting hints)
2. Translate
3. Convert to DOCX using `docx` npm package (v9.7.1, MIT) or `html-to-docx` (v1.8.0)

**Tools:**
- `docx` npm package: declarative API for creating .docx with styles, tables, images
- `html-to-docx`: converts HTML to DOCX
- `mammoth` (v1.12.0): can also output DOCX from HTML, though primarily for DOCX->HTML

**Pros:**
- DOCX is widely editable and accepted
- Good formatting preservation (headings, styles, tables)
- Can be further refined by the user in Word/Google Docs/LibreOffice
- Industry standard for translated document delivery

**Cons:**
- Not pixel-identical to the original PDF
- Table structure may need manual adjustment
- Font substitution may occur

#### Option D: Output as HTML (Simplest)

**Process:**
1. Extract to structured markdown
2. Translate
3. Convert to HTML (markdown-it or similar)
4. Apply basic CSS styling to approximate original layout

**Tools:**
- markdown-it for markdown -> HTML
- Electron's `BrowserWindow.webContents.printToPDF()` to convert HTML to print-quality PDF if needed

**Pros:**
- Universal rendering
- Very easy to produce from markdown output of LLM translation
- Can be styled with CSS
- Electron's `printToPDF()` can convert to vector PDF with good quality

**Cons:**
- Not a standard delivery format for translated documents
- Printing to PDF via Electron may have pagination issues with long documents

### 5.2 Recommended Output Strategy

**Primary: Output translated Markdown + provide option to export as DOCX.**
**Secondary: Offer "Overlay PDF" mode using original page images + translated text overlay for visual fidelity.**

```
                    +---> DOCX (recommended primary output)
                   /         via html-to-docx or docx npm
                  /
[Translated Markdown] ----> HTML (preview in Electron)
                  \
                   \
                    +---> Original-page-image PDF with text overlay
                          via pdfjs-dist render + pdf-lib
                          (preserves original formatting exactly)
```

The DOCX output path is the most practical and standard for professional use. The image-overlay PDF path is worth implementing as a premium "preserve layout" feature but is technically more complex.

---

## 6. Architectural Recommendations

### 6.1 Recommended Extraction Pipeline

```
 PDF File
    |
    v
[pdfjs-dist getDocument()]
    |
    +---> Can render pages? (No encrypted/corrupt errors)
    |         |
    |     (yes)     (no)
    |       |         |
    |       v         v
    |   Try text    Mark as
    |   extraction  unsupported / error
    |       |
    |       v
    |   [page.getTextContent()]
    |       |
    |       +---> Text density > threshold?
    |       |         |
    |       |     (yes)     (no -- likely scanned)
    |       |       |         |
    |       |       v         v
    |       |   Use native   Render page to image
    |       |   text           |
    |       |                 v
    |       |             [Tesseract.js OCR]
    |       |                 |
    |       |                 v
    |       |            OCR text + blocks
    |       |
    |       v
    |   [Structure Analyzer]
    |   - Group text items into paragraphs (y-position proximity)
    |   - Detect columns (x-position clustering)
    |   - Filter headers/footers (page-edge detection, content repetition)
    |   - Detect tables (tabular alignment of text)
    |   - Identify headings (font size changes, bold)
    |       |
    |       v
    |   [Markdown + Position JSON]
    |       |
    |       v
    |   [Sentence Segmenter]
    |   - Split paragraphs into sentence-level segments for translation
    |   - Preserve position info per segment (for potential re-layout)
    |
    v
 Ready for Translation
```

### 6.2 Key Packages for Implementation

| Purpose | Package | Version | License | Risk Level |
|---|---|---|---|---|
| PDF text extraction | `pdfjs-dist` | 6.0.227 | Apache-2.0 | Low |
| PDF page rendering (to image for OCR) | `pdfjs-dist` (canvas) | same | Apache-2.0 | Low |
| OCR (scanned PDF fallback) | `tesseract.js` | 7.0.0 | Apache-2.0 | Low |
| Markdown parsing | `marked` or `markdown-it` | latest | MIT | Low |
| DOCX generation | `docx` | 9.7.1 | MIT | Low |
| HTML -> DOCX | `html-to-docx` | 1.8.0 | MIT | Low |
| PDF generation (for simple output) | `pdf-lib` | 1.17.1 | MIT | Low |
| XLIFF (if CAT tool interop needed) | `xliff` | 6.3.0 | MIT | Low |

### 6.3 What to Avoid

- **pdf-parse v2.x** -- native dependency `@napi-rs/canvas` adds Electron packaging complexity
- **MuPDF.js** -- AGPL license is incompatible with commercial closed-source distribution without purchasing a license
- **pdf-lib for text extraction** -- it's a write-only library
- **Rebuilding the full PDF layout** -- impractical; output to DOCX/HTML instead

### 6.4 Electron-Specific Considerations

1. **pdfjs-dist in Electron**: Works well in both main and renderer processes. In the renderer (Chromium), pdfjs-dist can use the built-in Canvas API. In the main process (Node.js), use the `canvas` package or simply use the renderer for PDF processing.

2. **Tesseract.js in Electron**: Works in both processes. WASM loading in the renderer may require specific `Content-Security-Policy` headers. Main process usage is straightforward. Memory consumption (~200MB per worker) is a concern -- consider loading workers only when needed.

3. **Native addons**: Avoid packages with native dependencies (`@napi-rs/canvas`, `sharp`, `node-canvas`) as they require `electron-rebuild` and complicate CI/CD pipelines. All recommended packages above are pure JS/WASM.

4. **Worker threads**: For both pdfjs-dist and Tesseract.js, consider running extraction in a Node.js worker thread to avoid blocking the UI. Electron supports `Worker` in the renderer and `worker_threads` in the main process.

5. **File system access**: Electron main process can use Node.js `fs` to read PDF files. The renderer should use IPC to request file content from the main process.

---

## 7. Key Caveats

- **PDF is fundamentally a visual format, not a content format.** Perfect text extraction with structure preservation is not always possible, especially for untagged PDFs with complex layouts. Always communicate this limitation to users.
- **No open-source library handles 100% of PDFs correctly.** pdfjs-dist is the most widely tested and maintained option, but it still has edge cases.
- **OCR accuracy directly impacts translation quality.** A two-pass approach (extract native text first, fall back to OCR only when needed) minimizes this risk.
- **Multi-column detection** requires custom logic regardless of the library chosen. Expect to invest effort in grouping/sorting algorithms.
- **RTL text handling** (Arabic, Hebrew) is complex in pdfjs-dist and pdf-lib. Plan for dedicated RTL testing and potentially per-language layout adjustments.
- **File size limits:** Very large PDFs (500+ pages) may need streaming/on-demand page processing rather than loading the entire document at once.
