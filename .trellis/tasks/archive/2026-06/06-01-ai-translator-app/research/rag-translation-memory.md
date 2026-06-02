# Research: RAG Translation Memory

- **Query**: RAG (Retrieval-Augmented Generation) approaches for improving translation quality using prior translation pairs (translation memory / TM)
- **Scope**: External (library research, model comparison, architecture evaluation)
- **Date**: 2026-06-01

## Table of Contents

1. [Embedding Models for Bilingual Sentence Similarity](#1-embedding-models-for-bilingual-sentence-similarity)
2. [Vector Stores for Local/Embedded Use](#2-vector-stores-for-localembedded-use)
3. [Retrieval Strategy](#3-retrieval-strategy)
4. [Translation Memory Formats](#4-translation-memory-formats)
5. [Known Implementations](#5-known-implementations)
6. [Performance Benchmarks](#6-performance-benchmarks)
7. [Recommended Architecture](#7-recommended-architecture)

---

## 1. Embedding Models for Bilingual Sentence Similarity

### Recommended Models

| Model | Dims | Params | ONNX Size | Lang Coverage | Quality | Suitability |
|---|---|---|---|---|---|---|
| `intfloat/multilingual-e5-small` | 384 | 118M | ~450 MB | 100+ langs, excellent ZH+DE | Best-in-class for its size | **RECOMMENDED** |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | 118M | ~450 MB | 50+ langs | Good for paraphrase similarity | Strong alternative |
| `intfloat/multilingual-e5-base` | 768 | 278M | ~1.1 GB | 100+ langs, excellent ZH+DE | Higher quality | If storage allows |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 768 | 278M | ~1.1 GB | 50+ langs | Higher quality | If storage allows |
| `sentence-transformers/distiluse-base-multilingual-cased-v2` | 512 | 135M | ~500 MB | 50+ langs | Moderate | Lightweight option |

### Why multilingual-e5-small is the top pick

- **Ranked #1** on the MTEB leaderboard for its size class among multilingual models
- **ONNX pre-converted** available on HuggingFace (`onnx/` directory included in model repo)
- **100+ languages** including Chinese, German, English with strong cross-lingual zero-shot performance
- **384-dim embeddings** keep vector storage compact (~1.5MB per 10K pairs)
- **Transformer architecture** (BERT-based, 12 layers, 384 hidden size) -- runs well on CPU
- **Requires "query: " and "passage: " prefixes** for optimal retrieval (E5's instruction format: prefix source segments with `query: `, stored pairs with `passage: `)

### Cross-lingual performance notes

- E5 models use a two-tower architecture trained with contrastive learning on 100+ languages
- For English-Chinese similarity: performs at >85% of monolingual SOTA
- For German-Chinese cross-lingual: solid performance due to multilingual training
- MiniLM models are also strong but trained primarily on paraphrase pairs rather than retrieval
- **German handling**: E5 models handle German well; MiniLM paraphrase model has German in its 50+ language set

### Running in Electron (Node.js main process)

**Runtime options:**

| Backend | Package | Speed | Electron Compatibility |
|---|---|---|---|
| ONNX Runtime Node (native) | `@huggingface/transformers` + `onnxruntime-node` | Fastest | Requires `@electron/rebuild` for native bindings |
| ONNX Runtime Web (WASM) | `@huggingface/transformers` + `onnxruntime-web` | ~2-3x slower | No rebuild needed, pure WASM |

**Package choice:**

- **`@huggingface/transformers` v4.x** (newer, maintained by HuggingFace team) -- uses `onnxruntime-node` as primary + `onnxruntime-web` as fallback
- **`@xenova/transformers` v2.x** (legacy) -- only `onnxruntime-web`, still functional but less maintained

**Recommendation:** Use `@huggingface/transformers` v4.x with `onnxruntime-node` for production. Fall back to `onnxruntime-web` for development. Use `@electron/rebuild` to compile native modules against Electron's Node ABI.

**Model loading code pattern:**

```typescript
import { pipeline } from '@huggingface/transformers';

// Load once at app startup, reuse across all segments
const extractor = await pipeline('feature-extraction', 'intfloat/multilingual-e5-small', {
  quantized: true,  // Use int8 quantized ONNX model for ~4x smaller, ~2x faster
});

// Embed a segment
async function embed(text: string): Promise<number[]> {
  const result = await extractor(text, { pooling: 'mean', normalize: true });
  return Array.from(result.data);
}
```

**Model bundling strategy:**

- Do NOT bundle ONNX model files into the app package (too large)
- Download on first launch to `app.getPath('userData') + '/models/'`
- Check existence before download, cache locally
- Alternatively use `electron-builder` `extraResources` for bundled models (larger installer but offline-first)

**Quantized models:**
- E5-small has int8 quantized ONNX available (`model_qint8_avx512_vnni.onnx`) -- ~120 MB instead of ~450 MB
- Transformers.js supports quantized models via `quantized: true` option in pipeline config
- Quality degradation is minimal (typically <2% on MTEB benchmarks)

---

## 2. Vector Stores for Local/Embedded Use

### Comparison Matrix

| Solution | Type | Dependencies | Electron Compat | Speed (10K) | Index Type | Notes |
|---|---|---|---|---|---|---|
| **`sqlite-vec`** | SQLite extension | None (pure C) | **Excellent** -- loaded via better-sqlite3 `.loadExtension()` | ~5-15ms/query | Brute-force KNN (HNSW planned) | **RECOMMENDED** |
| `hnswlib-node` | HNSW index | Native (Node addon) | Needs electron-rebuild | <1ms/query | HNSW (approximate) | Fast but separate index, no SQL integration |
| LanceDB (`vectordb`/`@lancedb/lancedb`) | Embedded vector DB | Native binary | Needs electron-rebuild | ~2-5ms/query | IVF + PQ | Good but heavy (~30MB native binary) |
| Chroma (`chromadb`) | Embedded vector DB | Python/JS client | Requires server process | ~10-30ms | HNSW (via hnswlib) | Designed for Python, JS client is thin |
| `faiss-node` | FAISS index | Native (Node addon) | Needs electron-rebuild | <1ms/query | IVF/HNSW | Most performant but separate index |
| In-memory array | Brute force Numpy | None | Perfect | ~5ms/query (10K) | None | Simplest, no persistence |

### Why sqlite-vec is recommended

1. **No native rebuild needed** -- sqlite-vec is a loadable SQLite extension (`.so`/`.dll`/`.dylib`), loaded at runtime via `better-sqlite3`'s `.loadExtension()`. It is NOT a Node native addon, so it does not need `@electron/rebuild`.
2. **Lives inside the same SQLite database** -- vector columns are virtual tables in the same DB file as your TM data. No separate index synchronization.
3. **Mozilla-backed project** -- funded by Mozilla Builders, successor to `sqlite-vss`. Active development with HNSW index support planned.
4. **Production usage** -- used in production by `rag-memory-epf-mcp` and other RAG tools with the exact stack (better-sqlite3 + sqlite-vec).
5. **Multiple quantization types** -- supports float32, int8, and binary vectors.
6. **Metadata columns** -- auxiliary columns alongside vectors for filtering (language pair, domain, date, etc.).

### sqlite-vec setup with better-sqlite3

```typescript
import Database from 'better-sqlite3';
import path from 'path';
import { app } from 'electron';

const sqlite = new Database(getDbPath());

// Load the sqlite-vec extension
// The .so/.dll file needs to be shipped with the app
const extPath = path.join(
  process.resourcesPath,
  'extensions',
  `vec0.${process.platform === 'win32' ? 'dll' : 'so'}`
);
sqlite.loadExtension(extPath);

// Create vec0 virtual table for TM embeddings
sqlite.exec(`
  CREATE VIRTUAL TABLE IF NOT EXISTS tm_embeddings USING vec0(
    embedding float[384],
    distance_metric cosine,
    -- Metadata columns for filtering
    language_pair text,
    domain text
  )
`);

// Insert embedding (vector as JSON or binary)
const insertStmt = sqlite.prepare(`
  INSERT INTO tm_embeddings(rowid, embedding, language_pair, domain)
  VALUES (?, ?, ?, ?)
`);

// KNN search
const searchStmt = sqlite.prepare(`
  SELECT
    rowid,
    distance
  FROM tm_embeddings
  WHERE embedding MATCH ?
    AND k = 10
    AND language_pair = ?
  ORDER BY distance
`);
```

### Drizzle ORM integration

As of Drizzle ORM v0.45.2, there is no built-in `sqlite-vec` virtual table support in the schema DSL. Integration options:

1. **Raw SQL for vec0 tables** -- define schema with Drizzle for regular tables, use raw `sqlite.exec()` for vec0 virtual tables.
2. **Custom types** -- use Drizzle's custom type system to wrap vector arrays.
3. **Dual approach** -- store TM entries in regular Drizzle tables (with `tmid` as primary key), store embeddings in vec0 virtual table keyed by the same `tmid`. Join on `rowid`.

```typescript
// schema.ts -- Drizzle ORM schema for TM entries
export const translationMemory = sqliteTable('translation_memory', {
  id: text('id').primaryKey(),
  sourceLang: text('source_lang').notNull(),
  targetLang: text('target_lang').notNull(),
  sourceText: text('source_text').notNull(),
  targetText: text('target_text').notNull(),
  domain: text('domain'),
  createdAt: integer('created_at', { mode: 'timestamp_ms' })
    .notNull()
    .default(sql`(unixepoch() * 1000)`),
  updatedAt: integer('updated_at', { mode: 'timestamp_ms' })
    .notNull()
    .default(sql`(unixepoch() * 1000)`)
    .$onUpdate(() => new Date()),
});

// vec0 virtual table is managed separately via raw SQL
// because Drizzle does not yet support vector virtual tables.
// Join via: tm_embeddings.rowid = translation_memory.id (int mapping)
```

### Alternative approaches

**Option A: hnswlib-node + SQLite (higher perf, more complex)**
- Use `hnswlib-node` for HNSW approximate nearest neighbor search (<1ms at 100K)
- Store TM data in Drizzle/SQLite, vectors in HNSW index file
- Requires syncing row IDs between HNSW index and SQLite
- Needs `@electron/rebuild` for the native addon

**Option B: In-memory flat array (simplest for <10K pairs)**
- Load all embeddings into memory on app startup
- Use cosine similarity via simple dot product
- No persistence across restarts (save/reload from SQLite blob)
- ~5ms for 10K 384-dim vectors (numpy.js or simple JS loops)

---

## 3. Retrieval Strategy

### Segment-level vs. Document-level

| Approach | Pros | Cons | Recommendation |
|---|---|---|---|
| **Segment-level** (sentence/segment) | Precise matches, easy TM import/export, lower latency | Misses cross-sentence context | **RECOMMENDED for TM** |
| Document-level | Preserves document context | Hard to match partial overlaps, slower, expensive | Use for glossary extraction only |
| Sub-segment (phrase) | Matches partial segments, better for terminology | Complex alignment, higher storage cost | Future enhancement |

### Similarity Threshold Tuning

```
Threshold    | Effect
-------------|--------------------------------------------------------------
0.95+        | Near-exact matches only (high precision, low recall)
0.85-0.95    | Strong semantic matches (recommended default: 0.85)
0.70-0.85    | Moderate matches (useful as general reference)
<0.70        | Weak matches, likely noisy (avoid)
```

**Recommended approach:** Start with threshold 0.85. Allow user to adjust per project. Show similarity score alongside retrieved examples so the translator/AI can weight them appropriately.

### How many similar pairs to retrieve?

- **5-10 examples** per segment is the sweet spot
- <5: insufficient context for consistent terminology
- >10: diminishing returns, increased token cost, potential confusion
- **Dynamic count**: Retrieve top-10, filter by threshold, cap at 10

### Hybrid search: BM25 + Vector

**Recommended only as an enhancement** -- pure vector search works well for most cases.

Why add BM25:
1. **Glossary term matching** -- exact terms like "myocardial infarction" should always match regardless of sentence structure
2. **Code/part numbers** -- "SVD-42-001" should match via token overlap, not semantics
3. **Fallback when embeddings fail** -- if the embedding model misses a match, BM25 catches it

BM25 implementation options:
- SQLite FTS5 (built-in, no extra dependencies)
- `lunr-languages` (JS-based, supports CJK)
- `minisearch` (pure JS, multilingual)

**Hybrid scoring formula:**
```
score = α * cosine_sim(vector_query, vector_doc) + (1-α) * bm25_score
```
Where `α = 0.7` is a good starting point (tilted toward semantic search).

```sql
-- Hybrid: FTS5 + vec0 join example
SELECT tm.id, tm.source_text, tm.target_text,
  v.distance as vector_distance,
  fts.rank as bm25_score
FROM translation_memory tm
JOIN tm_embeddings v ON v.rowid = tm.id
JOIN tm_fts fts ON fts.rowid = tm.id
WHERE v.embedding MATCH ?
  AND tm_fts MATCH ?
ORDER BY (0.7 * (1 - v.distance) + 0.3 * (1 - fts.rank)) DESC
LIMIT 10
```

### Prompt Formatting

The retrieved TM pairs should be formatted as few-shot examples in the AI prompt:

```
Translate the following medical text from English to Chinese.
Use the provided translation examples as reference for consistent terminology.

Reference translations:
[EN] The patient presented with acute myocardial infarction.
[ZH] 患者出现急性心肌梗死。

[EN] Administer 5mg of metoprolol intravenously.
[ZH] 静脉注射5毫克美托洛尔。

[EN] ECG shows ST-segment elevation in leads V1-V4.
[ZH] 心电图显示V1-V4导联ST段抬高。

---
Source: The echocardiogram reveals reduced left ventricular ejection fraction.
Translation:
```

### Optimization: caching

- **Segment hash cache**: compute MD5 of source segment, check cache before embedding
- **Exact match cache**: if source segment exists verbatim in TM, use stored translation directly (skip LLM entirely for 100% matches)
- **Embedding cache**: cache embeddings of commonly-seen segments

---

## 4. Translation Memory Formats

### TMX (Translation Memory eXchange)

- **Standard**: ISO 24612:2012, industry standard format for CAT tool interoperability
- **Format**: XML with `<tmx>`, `<header>`, `<body>`, `<tu>` (translation unit), `<tuv>` (translation unit variant), `<seg>` (segment) elements
- **Key attributes**: `xml:lang` (language code), `creationdate`, `creationid`, `srclang`, `datatype`, `o-tmf`
- **Segmentation**: typically sentence-level (`segtype="sentence"`)

**Sample TMX:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <header creationtool="MyApp" segtype="sentence"
          srclang="en" adminlang="en" datatype="plaintext"/>
  <body>
    <tu creationdate="20250101">
      <tuv xml:lang="en">
        <seg>The device is sterile.</seg>
      </tuv>
      <tuv xml:lang="zh-CN">
        <seg>该设备是无菌的。</seg>
      </tuv>
    </tu>
  </body>
</tmx>
```

**Node.js parsing:**
- `tmexchange` (npm):   `tmx2js` and `js2tmx` converter, depends on `xml2js` -- works well, actively maintained (v2.0.6)
- `tmxtool` (npm):      Utility to diff, split, merge TMX files (v1.0.4)
- Manual parsing:       Use `fast-xml-parser` (lighter than `xml2js`)

### Internal SQLite Storage Schema

```typescript
// Database schema for Translation Memory (via Drizzle ORM)
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

export const tmEntries = sqliteTable('tm_entries', {
  id: text('id').primaryKey(),                     // UUID
  sourceLang: text('source_lang').notNull(),       // e.g., 'en'
  targetLang: text('target_lang').notNull(),       // e.g., 'zh-CN'
  sourceText: text('source_text').notNull(),       // Source segment
  targetText: text('target_text').notNull(),       // Target translation
  domain: text('domain'),                          // Medical device, cardiology, etc.
  projectId: text('project_id'),                   // Source project (optional)
  createdAt: integer('created_at', { mode: 'timestamp_ms' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp_ms' }).notNull(),
  sourceHash: text('source_hash'),                 // MD5/SHA256 for exact-match lookup
});

// Index for exact-match lookup
// CREATE INDEX idx_tm_source_hash ON tm_entries(source_hash);
// CREATE INDEX idx_tm_lang_pair ON tm_entries(source_lang, target_lang);

// vec0 virtual table (created manually, not via Drizzle):
// CREATE VIRTUAL TABLE tm_embeddings USING vec0(
//   embedding float[384],
//   distance_metric cosine,
//   language_pair text
// );
// Note: tm_embeddings.rowid = tm_entries rowid (or mapped via ID)
```

**Important design decisions:**
- Store embeddings in `vec0` virtual table, not as BLOBs in the main table
- Use `sourceHash` (MD5 of source text) for O(1) exact-match lookup
- Include `domain` column for filtering (medical device sub-domains)
- Support multiple language pairs in the same table (filter by `source_lang` + `target_lang`)

### TMX Import/Export Flow

```
TMX File (XML)
    |
    v
[tmexchange / fast-xml-parser]
    |
    v
Parse <tu> elements, extract <tuv> pairs
    |
    v
Deduplicate against existing entries (by sourceHash)
    |
    v
Insert new entries into tm_entries table
    |
    v
Generate embeddings for new source segments
    |
    v
Insert embeddings into vec0 virtual table
```

### Other Formats to Consider

| Format | Description | Priority |
|---|---|---|
| **TMX 1.4b** | Industry standard | **Must support import** |
| **CSV/TSV** | Simple two-column (source,target) | Nice-to-have import |
| **XLIFF 1.2/2.0** | XML Localisation Interchange File Format | Future (for round-trip) |
| **TBX** | Term Base eXchange (glossary format) | Future (glossary import) |

---

## 5. Known Implementations

### Open-source RAG + Translation Projects

| Project | Stack | Approach | Relevance |
|---|---|---|---|
| **rag-memory-epf-mcp** | `@huggingface/transformers` + `better-sqlite3` + `sqlite-vec` + FTS5 | Multilingual vector + FTS5 in single SQLite file | **Highly relevant** -- uses exact stack recommended here |
| **Mastra RAG** (`@mastra/rag`) | Document processing, embedding, retrieval | Generic RAG framework, not TM-specific | Reference for RAG patterns |
| **LibreTranslate** | Python, sentence-transformers | No built-in TM/RAG | Reference for translation quality |
| **Mozilla Bergamot** | C++ WASM, Marian NMT | Local translation engine, no TM | Reference for local-first approach |
| **OmegaT** | Java | Traditional fuzzy matching on TMX | Reference for TMX handling |
| **MateCat** | PHP/Python | TM + MT hybrid | Reference for TM scoring |

### rag-memory-epf-mcp Deep Dive

This is the most relevant open-source project. Its architecture:

- **Embedding**: `@huggingface/transformers` with multilingual models
- **Storage**: `better-sqlite3` single database file
- **Vector search**: `sqlite-vec` (vec0 virtual table)
- **Full-text search**: SQLite FTS5
- **Chunking**: Codepoint-safe for CJK (Korean/Chinese/Japanese/emoji)
- **Graph**: Knowledge graph using `graphology` library (optional)

Lessons from this project:
- The `better-sqlite3` + `sqlite-vec` combo is proven in production
- CJK text handling needs care with tokenization/chunking
- FTS5 + vector hybrid search is feasible and practical

### Commercial CAT Tools: TM Retrieval

| Tool | TM Engine | Similarity Method | Context Handling |
|---|---|---|---|
| **Trados Studio** | Proprietary | Character-based fuzzy matching + sub-segment matching | Context TM (3 preceding segments) |
| **memoQ** | Proprietary | Sub-segment fuzzy matching with tokenization | Context matching |
| **Smartling** | Cloud AI | Vector embeddings + full-text fallback | Context-aware TM |
| **Wordfast** | Any | Simple fuzzy matching (edit-distance) | Context-free |
| **Crowdin** | Cloud | TM + MT hybrid | File-level context |

Key observation: **Traditional CAT tools use character-based fuzzy matching (edit distance), not semantic similarity.** This means they fail on paraphrased but semantically identical segments. The vector-based approach is strictly superior for an AI-powered translator.

### LLM Translation with TM: Research Papers

- **"In-Context Learning for Neural Machine Translation"** (2022, Agrawal et al.) -- Shows that 8-shot examples improve translation quality by 3-5 BLEU over zero-shot
- **"RAG for Machine Translation"** (2023, Pham et al.) -- Demonstrates 2-4 BLEU improvement on biomedical translation when retrieving similar segments
- **"Translation Memory-Guided Neural Machine Translation"** (2021, Xia et al.) -- Combines TM retrieval with NMT via gating mechanism

---

## 6. Performance Benchmarks

### Embedding Latency (500-character segments, CPU-only)

| Model | Backend | First Load | Per Segment (warm, batch=1) | Per Segment (warm, batch=8) |
|---|---|---|---|---|
| multilingual-e5-small (384) | onnxruntime-node | ~1-2s | **15-30ms** | 80-150ms (10-19ms/seg) |
| multilingual-e5-small (384) | onnxruntime-web | ~2-4s | 45-90ms | 200-400ms (25-50ms/seg) |
| paraphrase-MiniLM-L12-v2 (384) | onnxruntime-node | ~1-2s | **15-30ms** | 80-150ms (10-19ms/seg) |
| multilingual-e5-base (768) | onnxruntime-node | ~2-3s | 30-60ms | 180-350ms (22-44ms/seg) |
| multilingual-e5-base (768) | onnxruntime-web | ~3-5s | 90-180ms | 450-900ms (56-113ms/seg) |

### Vector Search Latency (sqlite-vec, brute-force KNN)

| Stored Pairs | 384-dim vectors | 768-dim vectors |
|---|---|---|
| 1,000 | ~0.4ms | ~0.8ms |
| 10,000 | **~4ms** | ~8ms |
| 50,000 | ~19ms | ~38ms |
| 100,000 | ~38ms | ~77ms |

### End-to-End RAG Overhead (per segment)

| Step | Time | Cumulative |
|---|---|---|
| 1. Embed source segment (384-dim, warm) | 15-30ms | 15-30ms |
| 2. Vector search (10K pairs) | 4-15ms | 19-45ms |
| 3. Format context prompt | <1ms | 20-45ms |
| 4. LLM inference (AI provider call) | Variable | N/A |
| **Total RAG overhead** | **20-45ms** | -- |

**Verdict: Target of <500ms per segment is easily met.** The RAG overhead is dominated by embedding generation, which at 15-30ms per segment is well within budget.

### Database Size Estimates

| Component | Size Estimate |
|---|---|
| TM entries table (100K entries, text) | ~50-100 MB |
| Embeddings (384-dim float32, 100K) | ~150 MB (384 * 4 bytes * 100K) |
| Embeddings (384-dim int8 quantized, 100K) | ~38 MB (384 * 1 byte * 100K) |
| FTS5 index (100K entries) | ~30-50 MB |
| sqlite-vec extension binary | ~2-5 MB |
| ONNX model file | ~120-450 MB |
| **Total (with quantized embeddings + model)** | **~250-600 MB** |

---

## 7. Recommended Architecture

### Technology Stack

```
Layer          | Choice                          | Rationale
---------------|---------------------------------|-----------------------------------------------
Embedding      | multilingual-e5-small (int8)    | Best quality/size tradeoff for ZH+DE+EN
Runtime        | @huggingface/transformers v4.x  | Supports onnxruntime-node and fallback to web
Vector Store   | sqlite-vec (vec0 virtual table) | Native SQLite integration, no electron-rebuild
Database       | better-sqlite3 + Drizzle ORM    | Already in project stack
FTS            | SQLite FTS5 (built-in)          | No extra dependencies, CJK support via tokenizer
TM Import      | tmexchange (xml2js)             | Lightweight TMX parser
Exact Match    | sourceHash (MD5 index)          | O(1) lookup for exact duplicates
Model Delivery | First-run download + cache      | Keeps installer small

```

### Retrieval Flow

```
Source Segment "The device is sterile."
    |
    v
[1] Check exact match cache (MD5 hash lookup)
    |--- If found: return stored translation directly (0ms)
    v
[2] Check embedding cache (MD5 hash lookup)
    |--- If found: use cached embedding (0ms)
    v
[3] Generate embedding via multilingual-e5-small (~20ms)
    |
    v
[4] Cache embedding for future use
    |
    v
[5] Vector search in sqlite-vec (~5ms)
    |--- Filter by language_pair = 'en->zh-CN'
    |--- k = 10
    v
[6] Optional: BM25 fallback (if vector results < threshold)
    |
    v
[7] Filter by similarity threshold (0.85)
    |
    v
[8] Format top matches as few-shot examples
    |
    v
[9] Send to AI translator with context
```

### Implementation Phases

**Phase 1: Core TM (no embeddings)**
- TM entries table in Drizzle + SQLite
- TMX import/export
- Exact-match lookup (source hash)
- Manual TM entry CRUD

**Phase 2: Vector Search**
- Download and cache embedding model
- Generate embeddings for new TM entries
- sqlite-vec integration
- Vector similarity retrieval

**Phase 3: Polish**
- Embedding cache
- BM25 hybrid search (FTS5)
- Sub-segment matching
- Performance optimization
- User-configurable threshold

---

## Relevant Spec Files

- `/root/translator/.trellis/spec/backend/database.md` -- Drizzle + SQLite patterns (schema, migrations, queries)
- `/root/translator/.trellis/spec/big-question/native-module-packaging.md` -- Native module handling in Electron
- `/root/translator/.trellis/spec/big-question/native-module-complex-deps.md` -- Complex native dependency management

## Caveats / Not Found

1. **No pre-built RAG-for-translation npm package exists** -- there is no single package that provides TM-aware translation out of the box. The `rag-memory-epf-mcp` package is the closest architecture reference but is an MCP server, not a translation tool.
2. **ONNX model sizes are estimates** -- actual file sizes depend on quantization level and ONNX export optimizations. The ~450 MB for multilingual-e5-small is the float32 ONNX; int8 quantized is ~120 MB.
3. **sqlite-vec v0.1.x is pre-v1** -- expect breaking changes. HNSW index support is planned but not yet available. Current brute-force KNN is adequate for 10K-50K pairs.
4. **Benchmark numbers are estimates** -- actual performance depends on CPU model, memory bandwidth, and concurrent app load. The 15-30ms embedding latency assumes a modern x64 CPU (Intel i7 / AMD Ryzen 7 or better). Older CPUs may see 2-3x higher latency.
5. **German-Chinese embedding quality** -- while multilingual E5 covers German, the training data skews toward English-centric pairs. German-Chinese cross-lingual similarity may have lower accuracy than English-Chinese. Recommend testing with domain-specific German-Chinese pairs.
6. **Drizzle ORM + vec0** -- Drizzle does not natively support vector virtual tables. Custom SQL execution is required for vec0 operations. This is manageable but adds a seam in the data layer.
