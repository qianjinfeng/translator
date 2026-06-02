# Research: DOCX Parsing and Generation Libraries for Node.js/Electron

- **Query**: Compare DOCX parsing/generation libraries for format-preserving document translation in Electron app
- **Scope**: Mixed (npm packages, GitHub repos, Python ecosystem, commercial tools)
- **Date**: 2026-06-01

## Findings

### 1. Library Comparison

#### 1.1 python-docx (via child_process) — RECOMMENDED PRIMARY APPROACH

| Attribute | Details |
|---|---|
| **Version** | 1.2.0 (latest) |
| **GitHub Stars** | ~5,600 |
| **License** | MIT |
| **Last Updated** | June 2025 |
| **Type** | Read + Write + Modify |

**Strengths:**
- Mature library (10+ years), large community, well-documented
- Can READ existing DOCX with full formatting extraction: fonts, sizes, bold/italic/underline, colors, paragraph styles, alignment, spacing, indentation
- Can WRITE modifications back while preserving all original formatting
- Tables, headers/footers, sections, images all accessible via API
- XML-level access via `doc.element` for edge cases (text boxes, complex formatting)
- Excellent CJK support (handles `w:eastAsia` font attribute for Chinese/Japanese/Korean)

**Key capabilities verified through testing:**
- Run-level formatting extraction: `run.font.name`, `.size`, `.bold`, `.italic`, `.underline`, `.color.rgb`
- Paragraph formatting: `paragraph.alignment`, `.paragraph_format.space_before/after`, `.line_spacing`, `.indent`
- Table operations: `doc.tables[]`, `table.rows[]`, `table.cells[]`, cell text replacement
- Headers/footers: `section.header.paragraphs`, `section.footer.paragraphs`
- XML deepcopy for bilingual mode (see Section 3.1)

**Limitations:**
- Requires Python 3 runtime on the system
- Text boxes not directly exposed via API (need XML traversal to find `w:txbxContent`)
- `run.font.name` only reads the ASCII font; CJK fonts stored in `w:eastAsia` attribute require XML access
- `cell.text = "..."` replaces all cell content and loses formatting (must modify runs individually)
- IPC overhead between Node.js and Python child_process
- Deployment complexity: bundling Python or requiring it as system dependency

**CJK handling details:**
- Tested successfully with SimSun (宋体) and mixed CJK/Latin text
- CJK fonts read/written correctly via `w:rFonts` -> `w:eastAsia` attribute
- Deepcopy approach preserves all font attributes including CJK
- No known encoding issues with Unicode text

---

#### 1.2 docx npm package (v9.7.1)

| Attribute | Details |
|---|---|
| **Version** | 9.7.1 |
| **NPM Downloads** | High (widely used) |
| **License** | MIT |
| **Last Updated** | May 2026 |
| **Type** | Generate + Patch (placeholder-based) |

**Strengths:**
- Pure JavaScript, works in Node.js and browser
- Excellent API for generating DOCX from scratch
- Strong typing (TypeScript)
- Active development (monthly releases)
- Can generate complex documents with tables, images, headers/footers

**Limitations (for our use case):**
- `patchDocument` is PLACEHOLDER-BASED (replaces `{{placeholder}}` tokens), NOT a general document editor
- `from-docx.ts` reads the ZIP structure and manipulates XML, but does NOT parse into structured formatting objects
- Multiple open issues with `patchDocument`:
  - Headers being removed (#2690)
  - Numbering/bullets not working (#2966, #2088)
  - Footnotes not supported (#3113)
  - Heading styles not applied (#2735)
- Cannot read arbitrary DOCX and extract structured formatting data
- Does NOT provide run-level font/formatting access to existing documents

**Verdict:** Good for DOCX generation, but NOT suitable for reading/copying formatting from existing documents.

---

#### 1.3 docxtemplater (v3.68.7)

| Attribute | Details |
|---|---|
| **Version** | 3.68.7 |
| **NPM Downloads** | Wide usage |
| **License** | MIT (core) / Paid modules |
| **Last Updated** | May 2026 |
| **Type** | Template-based generation |

**Strengths:**
- Excellent template engine for replacing `{placeholders}` in pre-made templates
- Paid modules add image, HTML, chart, and advanced features
- Very robust with 8+ years of maintenance
- Good documentation and commercial support

**Limitations (for our use case):**
- REQUIRES pre-made templates with `{placeholder}` tags inserted
- Cannot parse arbitrary DOCX documents to extract formatting
- NOT a document reader/editor — it's a template engine
- Core features are free but advanced modules (images, HTML) are paid
- Not designed for translating existing documents without template preparation

**Verdict:** Suitable only if documents are prepared as templates beforehand. Not for arbitrary DOCX translation.

---

#### 1.4 mammoth.js (v1.12.0)

| Attribute | Details |
|---|---|
| **Version** | 1.12.0 |
| **GitHub Stars** | ~4,500 |
| **License** | BSD-2-Clause |
| **Last Updated** | March 2026 |
| **Type** | Read-only (DOCX -> HTML/Markdown) |

**Strengths:**
- Excellent at converting DOCX to clean HTML
- Extracts: headings, lists, tables (structure), images, bold/italic/underline, links, footnotes
- Custom style mapping
- Cross-platform (also has Python, Java, .NET ports)

**Limitations (for our use case):**
- READ-ONLY — cannot generate DOCX output
- Does NOT preserve exact font names, sizes, colors
- Does NOT preserve exact paragraph spacing/indentation
- Table formatting (borders, cell shading) is intentionally ignored
- No round-trip capability (DOCX -> HTML -> DOCX loses fidelity)

**Verdict:** Good for extracting text content with basic structure, but NOT for format-preserving translation output.

---

#### 1.5 officegen (v0.6.5)

| Attribute | Details |
|---|---|
| **Version** | 0.6.5 |
| **License** | MIT |
| **Last Updated** | June 2022 (NOT ACTIVELY MAINTAINED) |
| **Type** | Generation only |

**Strengths:**
- Can generate DOCX, PPTX, XLSX
- Stream-based

**Limitations:**
- NOT updated since 2022 — abandonware risk
- Cannot read/parse existing documents
- Limited formatting API
- No TypeScript support

**Verdict:** Not recommended for new projects.

---

#### 1.6 Aspose.Words (Commercial)

| Attribute | Details |
|---|---|
| **Latest Version** | Varies by platform |
| **License** | Commercial ($1,000+ per developer) |
| **Type** | Full read/write/modify |

**Strengths:**
- Best-in-class format preservation
- Full API: fonts, styles, tables, images, text boxes, headers/footers, everything
- Node.js support via Java bridge (`aspose.words` via Java/.NET)
- Enterprise-grade reliability

**Limitations:**
- VERY EXPENSIVE ($1,000+ per developer license, plus runtime licenses)
- Heavy dependency: requires Java or .NET runtime
- Overkill for text translation use case
- No npm package available (requires separate download)

**Verdict:** The gold standard but cost-prohibitive for a single-user desktop tool.

---

#### 1.7 docx4js (v3.3.0)

| Attribute | Details |
|---|---|
| **Version** | 3.3.0 |
| **GitHub Stars** | ~400 |
| **License** | MIT |
| **Last Updated** | Sep 2024 (publish), Mar 2026 (last commit) |
| **Type** | Parser + Modifier |

**Strengths:**
- Pure JavaScript (works in Node.js and browser)
- Can parse DOCX and traverse document model (paragraphs, runs, tables, images)
- Can modify content and save back
- No external dependencies
- Identifies: sections, headers/footers, paragraphs, runs, tables, images, hyperlinks, fields

**Limitations:**
- Low-level API — requires custom event handlers
- Formatting attributes must be handled manually
- Smaller community, less battle-tested
- Not specifically designed for text replacement workflows
- Documentation is sparse

**Verdict:** A possible pure-JS alternative but requires significantly more custom code than python-docx.

---

### 2. What Do Similar Translation Tools Use?

| Tool | Approach |
|---|---|
| **hebrew_doc_translator** (GitHub) | mammoth.js for text extraction (loses formatting), then docx npm package for generating new document. Note: does NOT preserve original formatting in output. |
| **Professional CAT tools** (Trados, memoQ, OmegaT) | Native DOCX XML manipulation via Open XML SDK or similar. These tools work directly with the DOCX ZIP structure, replacing text at the XML level while preserving everything else. |
| **Typical Node.js translation apps** | Two common patterns: (A) extract text -> translate -> reconstruct from template (loses formatting), or (B) use python-docx via child_process for format preservation. |

**Key insight:** Most open-source Node.js translation tools sacrifice format preservation. Professional tools either use the Open XML SDK directly or use python-docx.

---

### 3. Format Preservation Trade-offs

#### 3.1 Bilingual Output Mode (Original + Translation)

**Approach with python-docx:**
1. Read document via `Document(filepath)`
2. For each paragraph, deep-copy the XML element via `copy.deepcopy(p._element)`
3. Modify text in the copy's runs to contain the translation
4. Insert the copy after the original via `orig_elem.addnext(new_elem)`
5. Save

**Verified working:** The deepcopy preserves ALL formatting including fonts, sizes, colors, bold/italic/underline, paragraph styles, alignment, etc.

**What's hardest to duplicate:**
- **Numbering (bullets/lists)**: List numbering is managed through `w:numPr` references. Deepcopy preserves the reference, so numbered lists continue correctly. Inserting translations may break numbering sequence.
- **Images**: Images are inline in paragraphs. Deepcopy duplicates the image reference. The image file in the ZIP is shared, so there's no duplication of binary data.
- **Nested tables**: Deepcopy works but table structure deepcopy is complex.

#### 3.2 Standalone Output Mode (Translation Only)

**Approach with python-docx:**
1. Read document via `Document(filepath)`
2. For each paragraph, iterate runs and replace `run.text`
3. Save

**Format preservation:** All formatting is preserved because we only change the text content of each run, leaving font properties, styles, and layout unchanged.

#### 3.3 Elements Hardest to Preserve

| Element | Difficulty | Notes |
|---|---|---|
| **Text boxes** | Hard | Text in `w:txbxContent` is NOT exposed via python-docx paragraph API. Must traverse XML manually. |
| **WordArt / SmartArt** | Very Hard | Complex XML structures, not exposed via any library API |
| **Equations** | Very Hard | OMML format, not directly manipulable |
| **Fields (TOC, cross-refs)** | Hard | Field codes may need updating after text changes |
| **ActiveX / Form controls** | Very Hard | Binary data embedded in document |
| **Charts** | Hard | Chart XML is in separate part, linked to data |
| **Comments / Track changes** | Moderate | python-docx has no direct API; must use XML |
| **Content controls (structured document tags)** | Moderate | XML-level manipulation needed |
| **Bookmarks** | Moderate | Can be preserved but relocating text may affect them |
| **Hyperlinks** | Easy | Preserved via XML deepcopy; URLs remain intact |
| **Images** | Easy | Preserved; shared via ZIP references |
| **Tables** | Moderate | Structure preserved; cell text replacement needs run-level access |
| **Headers/Footers** | Moderate | Accessible via `section.header/footer`; page numbers and fields need care |
| **Page layout (margins, orientation, columns)** | Easy | Stored in section properties, accessible and preservable |

#### 3.4 Formatting Attributes That python-docx Handles

| Attribute | Read | Write | Preserved in deepcopy |
|---|---|---|---|
| Font name (ASCII) | Yes | Yes | Yes |
| Font name (East-Asian/CJK) | Via XML | Via XML | Yes |
| Font size | Yes | Yes | Yes |
| Bold | Yes | Yes | Yes |
| Italic | Yes | Yes | Yes |
| Underline | Yes | Yes | Yes |
| Strikethrough | Yes | Yes | Yes |
| Font color | Yes | Yes | Yes |
| Highlight | Yes | Yes | Yes |
| Superscript/subscript | Yes | Yes | Yes |
| Character spacing | Via XML | Via XML | Yes |
| Paragraph alignment | Yes | Yes | Yes |
| Line spacing | Yes | Yes | Yes |
| Space before/after | Yes | Yes | Yes |
| Indentation | Yes | Yes | Yes |
| Paragraph borders | Via XML | Via XML | Yes |
| Shading (background) | Via XML | Via XML | Yes |
| List numbering | Partial | No (read reference) | Yes (reference preserved) |
| Tab stops | Via XML | Via XML | Yes |
| Table cell shading | Via XML | Via XML | Yes |
| Table cell borders | Via XML | Via XML | Yes |
| Section page size/orientation | Yes | Yes | N/A |

---

### 4. CJK (Chinese/Japanese/Korean) Text Issues

#### 4.1 python-docx
- **No encoding issues**: python-docx handles Unicode natively
- **Font handling**: CJK fonts are stored in `w:rFonts` -> `w:eastAsia` attribute
  - `run.font.name` only returns the ASCII/Latin font name
  - To read CJK font: access `run._element.find(qn('w:rPr')).find(qn('w:rFonts')).get(qn('w:eastAsia'))`
  - When deep-copying paragraphs, CJK fonts are preserved automatically
- **Font size**: Works correctly for CJK text (same EMU units)
- **Bold/italic/underline**: Works identically for CJK and Latin text
- **Mixed CJK/Latin in same paragraph**: Each run preserves its own font settings

#### 4.2 docx npm package
- CJK text can be set via `font` property: `new TextRun({ text: "中文", font: { eastAsia: "SimSun" } })`
- No known CJK-specific issues
- Works in Node.js with full Unicode support

#### 4.3 docxtemplater
- CJK text in templates works fine
- Font replacement: may need attention to ensure CJK fonts are specified

#### 4.4 mammoth.js
- Extracts CJK text correctly
- But loses font names (converts to HTML/CSS with generic font mapping)

#### 4.5 General CJK considerations
- **Line breaking**: CJK text has different line break rules; libraries typically handle this
- **Font fallback**: Systems without CJK fonts installed may display incorrectly; this is a system/rendering issue, not a library issue
- **Character width**: Both full-width and half-width characters are preserved
- **Vertical text**: Rare in DOCX, but python-docx has limited support for vertical writing (`w:textDirection`)

---

### 5. Recommended Architecture for the Translation App

```
                    +------------------+
                    |   Electron App   |
                    |  (main process)  |
                    +--------+---------+
                             |
             +---------------+---------------+
             |                               |
    +--------v--------+           +----------v---------+
    |   File I/O      |           | Python child_proc  |
    |  (JSZip/fs)     |           |  (python-docx)     |
    +-----------------+           +----------+---------+
                                             |
                             +---------------+---------------+
                             |               |               |
                     +-------v----+  +------v------+  +-----v------+
                     | Read DOCX   |  | Translate   |  | Write DOCX |
                     | (extract    |  | text (AI)   |  | (format    |
                     |  paragraphs)|  |             |  |  preserved)|
                     +------------+  +-------------+  +-----------+
```

**Suggested workflow:**
1. Electron main process spawns Python script via `child_process.spawn`
2. Python script reads DOCX, extracts paragraphs with formatting metadata to JSON
3. Electron sends paragraph text to AI for translation
4. Python script receives translated text, applies it to document (bilingual or standalone)
5. Python script writes the output DOCX

**Alternative (all-JS) approach using JSZip + XML:**
1. Use JSZip to unzip the DOCX
2. Parse `word/document.xml` to find `w:p` and `w:r` elements
3. Replace text in `w:t` elements while preserving all XML attributes
4. Repackage into DOCX

This XML approach avoids the Python dependency but requires careful handling of all DOCX XML namespaces and edge cases.

### 6. Decision Matrix

| Criteria | python-docx | docx (npm) | docxtemplater | mammoth.js | docx4js |
|---|---|---|---|---|---|
| Read existing DOCX | YES | Limited (patch only) | NO | YES (HTML only) | YES |
| Extract formatting | Full | No | N/A | Partial | Partial |
| Generate DOCX output | YES | YES | YES | NO | YES |
| Format preservation | Excellent | Limited | Template-defined | Poor (read-only) | Manual |
| CJK support | Excellent | Good | Good | Basic | Unknown |
| No external runtime | NO (needs Python) | YES | YES | YES | YES |
| Maturity | High (10yr) | Medium (5yr) | High (8yr) | High (10yr) | Low |
| Community | Large | Large | Medium | Large | Small |
| TypeScript friendly | No (Python) | Yes | Yes | Yes | No |
| Deployment complexity | High | Low | Low | Low | Low |
| License cost | Free (MIT) | Free (MIT) | Free + Paid modules | Free (BSD) | Free (MIT) |

**Recommendation: Use python-docx as primary approach** for its superior format preservation, CJK handling, and full read/write capability. Supplement with direct JSZip+XML manipulation for edge cases (text boxes) if needed.

## Caveats / Not Found

- **Aspose.Words pricing**: Exact pricing not publicly listed for Node.js version. Requires contacting sales. Estimates suggest $1,000+ per developer license.
- **Text boxes in python-docx**: No library provides direct text box API. Must manipulate XML at `w:txbxContent` level using lxml.
- **Real-world DOCX with complex medical formatting**: The tests were done on programmatically created documents. Real medical device documents may have more complex formatting (nested tables, form fields, complex fields) that need additional testing.
- **OCR for scanned PDFs**: Out of scope for this DOCX research. PDF handling is a separate topic.
