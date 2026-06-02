# Research: AI Translation APIs for Medical Device Document Translation

- **Query**: Compare AI translation APIs for medical device industry document translation quality, cost, and integration feasibility
- **Scope**: Mixed (external API research + internal architecture fit)
- **Date**: 2026-06-01

## Findings

### 1. Provider Comparison

#### 1.1 DeepL API

**Overview**: Dedicated translation API, widely considered the gold standard for European language pairs. Strong in DE-EN, EN-DE. Chinese support exists but quality compared to LLM-based approaches is debated for medical domain.

**Language Support**:
- EN -> ZH: Supported. Quality is good for general text, but medical terminology accuracy lags behind GPT-4o/Claude for specialized domains.
- DE -> EN: Excellent. DeepL's strongest language pair.
- DE -> ZH: Supported. Less common pair; quality not as strong as going DE->EN->ZH.

**Pricing (as of 2025-2026)**:
- Free API: 500,000 characters/month free
- Pro API (pay-as-you-go): Starts at ~8.99 EUR/month (individual), ~49.99 EUR/month (Advanced)
- API volume pricing (business): ~25 EUR per 1M characters at low volumes, decreasing to ~5 EUR per 1M at high volumes
- Billing: Character-based (including spaces). Context parameter not billed.

**Glossary Support**: **Native and robust.**
- Dedicated Glossary API endpoint (CRUD operations)
- Formats: CSV, TBX (TermBase eXchange)
- Source-target term pairs enforced by language direction
- Glossary entries can be single words or short phrases
- Applied at translation time via `glossary_id` parameter
- No limit on number of glossaries; per-glossary entry limits based on plan
- Maximum entry length: ~100 characters per term

**Additional Features**:
- `formality` parameter (formal/informal tone control)
- `model_type`: `quality_optimized` vs `latency_optimized`
- `translation_memory_id`: integrate with Translation Memory (TM)
- `custom_instructions`: style/domain instructions
- `tag_handling`: preserve XML/HTML tags during translation
- Document translation API (PDF, DOCX, PPTX, XLSX) -- format-preserving

**Data Privacy**:
- GDPR compliant
- DeepL Pro: no data storage, texts deleted immediately after translation
- SOC 2 Type II certified (business plans)
- No HIPAA-specific certification publicly listed
- TDM (Translation Memory) data retained per user configuration

**Rate Limits**:
- Free: ~50 requests/hour, max 50K chars/request
- Pro: higher limits, up to ~500K chars/request
- Ultimate: custom limits

**Node.js SDK**: Official `deepl-node` npm package available.

#### 1.2 Google Cloud Translation API (Advanced v3)

**Overview**: Mature translation API with NMT and LLM-backed models. Strong glossary infrastructure. Good for enterprise with GCP integration.

**Language Support**:
- EN -> ZH: Excellent. Google's NMT has been trained on massive parallel corpora including medical data.
- DE -> EN: Excellent.
- DE -> ZH: Supported via NMT. Quality adequate.

**Pricing**:
- NMT Model (default): $20 per million characters (input characters per target language)
- Translation LLM (specialized): $10 per million characters input + $10 per million characters output
- Custom Model Training: $80 per million characters of training data (max $300/training job)
- Custom Model Translation: $60 per million characters (NMT), $20 per million characters (LLM)
- Adaptive Translation API: $40 per million characters
- Document Translation: $0.08-0.25 per page (NMT/LLM-dependent)
- Free tier: $10 credit/month (applied to first usage), plus $300 initial credit

**Glossary Support**: **Native and well-designed.**
- Create glossary resource via API, referenced per translation request
- Formats: CSV (source,target pairs), TSV, TMX
- Each glossary limited to 10.4M UTF-8 bytes total
- Single glossary terms: < 5 words typically; < ~100 chars
- Stopwords are automatically filtered
- Requires Cloud Storage bucket for glossary file storage
- Glossary can be applied to both text and document translation

**Additional Features**:
- AutoML Translation: train custom models on domain-specific parallel data
- Language detection built-in
- Batch translation (async, for large documents)
- Adaptive Translation API: learns from user feedback/edits in real-time
- Glossary can also be used with AutoML models

**Data Privacy**:
- HIPAA-compliant (with BAA signed)
- SOC 1/2/3, ISO 27001 certified
- Data processed in specified region (e.g., EU, US)
- Customer-managed encryption keys (CMEK) available
- No data retention for translation (Google does not store translated content unless Cloud Logging enabled)
- Enterprise-grade IAM and access control

**Rate Limits**:
- Text Translation: 100,000+ characters/request (practical limit: ~500K chars)
- Document Translation: max 20MB/file, 100 pages
- Batch Translation: massive scale (millions of characters)
- Requests per minute: 1,000-10,000+ depending on quota

**Node.js SDK**: `@google-cloud/translate` official npm package with full v3 API support.

#### 1.3 Azure AI Translator (Foundry Tools)

**Overview**: Microsoft's translation service with Custom Translator for domain adaptation. Strong enterprise compliance.

**Language Support**:
- EN -> ZH: Supported (NMT). Quality good for general, Custom Translator can improve medical domain.
- DE -> EN: Supported. Good quality.
- DE -> ZH: Supported.

**Pricing**:
- Free Tier: 2 million characters/month (any mix of standard + custom translation)
- Standard Translation: ~$10 per million characters (text)
- Document Translation: varies
- Custom Training: charges based on training data characters
- Custom Model Hosting: per hosted model per month
- Volume tiers: 250M chars at ~$8.50/M, 1B chars at ~$7/M
- Commitment tiers available for volume discounts

**Glossary Support**: **Two approaches:**
1. **Dictionary/Custom Translator**: Upload parallel documents (bilingual sentence pairs) to train a custom NMT model
   - Gains 5-10 BLEU points reported with sufficient domain data
   - Supports TMX, XLIFF, CSV, TSV formats
   - No programming skills needed for training
   - Can be accessed via Translator Text API v3
2. **Dynamic Dictionary**: Inline glossary via API parameter (phrase overrides)
   - Specify source-target pairs per request
   - Simpler but per-request only

**Data Privacy**:
- HIPAA-compliant (BAA available)
- SOC 1/2/3, ISO 27001, FedRAMP
- Data residency controls (choose Azure region)
- No data retention for standard translation (data in transit, not stored)
- Customer-managed keys via Azure Key Vault

**Rate Limits**:
- Standard: ~1M chars/hour for S0 tier
- Up to 50 requests/second
- Document Translation: async batch with higher throughput

**Node.js SDK**: `@azure/cognitiveservices-translatortext` or REST API via `fetch`/`axios`.

#### 1.4 OpenAI GPT-4o / GPT-4.1

**Overview**: General-purpose LLM capable of high-quality translation. Excels at medical/technical translation when properly prompted. No dedicated translation mode -- relies entirely on prompt engineering.

**Language Support**:
- EN -> ZH: **Excellent when prompted well.** GPT-4o demonstrates strong understanding of Chinese medical terminology. Handles nuanced context better than dedicated NMT for specialized domains.
- DE -> EN: Excellent.
- DE -> ZH: Good. May benefit from chain-of-thought approach (DE->EN->ZH or direct with glossary injected).
- EN+DE -> EN+ZH: **Unique strength.** Can handle mixed-language documents in a single API call because it's a general LLM, not a translation-specific model.

**Pricing (as of 2026)**:
- **GPT-4.5**: $5/MTok input, $30/MTok output (most capable, potentially overkill)
- **GPT-4o**: $2.50/MTok input, $15/MTok output (sweet spot for translation quality/cost)
- **GPT-4o-mini**: $0.75/MTok input, $4.50/MTok output (budget option, noticeably lower quality)
- Context window: 128K tokens (GPT-4o family)
- Knowledge cutoff: Oct 2023 (GPT-4o), May 2025 (GPT-4.1)
- **Batch API**: 50% discount (GPT-4o: $1.25/MTok input, $7.50/MTok output) -- asynchronous with 24hr completion window
- **Cached input**: variable discount (usual ~50%)

**Glossary Support**: **Prompt engineering only.**
- Inject glossary as system prompt: "Use the following term mappings: device_name=设备名称, ..."
- No native glossary data structure
- Glossary must be included in every request context (can use system prompt prefix)
- Effectiveness depends on model following instructions -- GPT-4o is very reliable at following glossary instructions
- Larger glossaries consume tokens and increase cost
- Suggested approach: few-shot examples + term list in system prompt

**Data Privacy**:
- API: data not used for training (since March 2023 for API customers)
- HIPAA compliance: **Not available on standard API.** Available via Microsoft Azure OpenAI Service (HIPAA BAA possible)
- SOC 2 Type II
- GDPR compliant with DPA
- Data retention: 30 days for abuse monitoring (can be opted out for zero retention via API key isolation)

**Rate Limits**:
- Tier-dependent. Typical: ~500-10,000 RPM
- Tokens per minute (TPM): varies by tier (e.g., 10M TPM for GPT-4o at high tiers)
- 128K context window allows very large documents per request

**Node.js SDK**: Official `openai` npm package.

#### 1.5 Anthropic Claude API (claude-sonnet-4-6, claude-opus-4-8)

**Overview**: General-purpose LLM with strong multilingual capabilities. Excellent for technical/medical translation with proper prompting. **Key differentiator: prompt caching** makes glossary integration dramatically cheaper than OpenAI for repetitive translation tasks.

**Language Support**:
- EN -> ZH: **Excellent.** Claude demonstrates strong Chinese medical terminology capability, comparable to GPT-4o for medical domain.
- DE -> EN: Excellent.
- DE -> ZH: Very good.
- EN+DE -> EN+ZH: **Excellent.** Claude handles mixed-language input well, similar to GPT-4o. Can process documents with multiple source languages in one pass.
- Fully multilingual, all models support text/image input and text output.

**Pricing (as of 2026)**:
- **claude-opus-4-8**: $5/MTok input, $25/MTok output (most capable)
- **claude-sonnet-4-6**: $3/MTok input, $15/MTok output (best price/performance)
- **claude-haiku-4-5**: $1/MTok input, $5/MTok output (fastest, budget)
- Context window: 200K tokens (Opus 4.8, Sonnet 4.6), 200K (Haiku 4.5)
- Max output: 128K tokens (Opus), 64K tokens (Sonnet, Haiku)

**Prompt Caching (Key Advantage for Translation)**:
- Cache system prompt + glossary (the prefix) once; subsequent requests only charged for cache hits
- Pricing (Claude Opus 4.8): Base input $5/MTok, Cache write $6.25/MTok, **Cache hit $0.50/MTok** (10x cheaper)
- Pricing (Claude Sonnet 4.6): Base input $3/MTok, Cache write $3.75/MTok, **Cache hit $0.30/MTok** (10x cheaper)
- Cache lifetime: 5 minutes (default, free refreshes on each use), 1-hour (premium, higher cache write cost)
- For document translation: cache the system prompt (with glossary) once, then only pay ~10% of input cost for each subsequent chunk
- Massive savings when translating many documents with the same glossary

**Glossary Support**: **Prompt engineering + prompt caching.**
- No native glossary data structure
- System prompt with term mappings (same approach as OpenAI)
- **Prompt caching makes glossary approach cost-effective** -- glossary terms live in cached prefix, each request reuses cache at 90% discount
- Few-shot examples can also be cached for consistent translation style

**Data Privacy**:
- **HIPAA compliance: Available** (with Business Associate Agreement on Enterprise plan)
- SOC 2 Type II
- GDPR compliant
- API data not used for training (as indicated in Anthropic's API terms)
- Data retention configurable
- Enterprise tier: dedicated infrastructure, data never leaves chosen region

**Rate Limits**:
- Tier 1 (default): 1,000 RPM / 200K TPM for Sonnet
- Higher tiers up to 10K+ RPM / 10M+ TPM
- 200K context window handles long documents

**Node.js SDK**: Official `@anthropic-ai/sdk` npm package.

#### 1.6 Local Models (Ollama, llama.cpp)

**Overview**: Running translation models locally eliminates per-request costs and ensures complete data privacy. Viable for some use cases but quality/performance gap with cloud APIs remains significant for medical domain.

**Candidate Models**:

| Model | Size | Languages | Quality Assessment |
|---|---|---|---|
| TranslateGemma (Google, Gemma 3 based) | 12B | 55 languages | Promising but unproven for medical domain |
| Hunyuan-MT-1.5 (Tencent) | 1.8B / 7B | 33 languages (incl. ZH) | Decent for general translation, medical quality unknown |
| HY-MT2 (Hunyuan) | 1.8B / 7B / 30B-A3B | 33 languages | Improved version, supports instruction-following |
| NLLB-200 (Meta) | 600M-54.5B | 200 languages | Strong for low-resource pairs but medical quality mediocre |
| Qwen2.5 (Alibaba) | 7B-72B | Multilingual (strong ZH) | Strong Chinese, good instruction-following, can be prompted for translation |
| Llama 3.x (Meta) | 8B-405B | Multilingual | With careful prompting can translate, but ZH quality lags behind dedicated models |
| SeamlessM4T (Meta) | 2.3B | 100+ languages | Speech+text, not optimized for document translation |

**Assessment for Medical EN-ZH Translation**:
- **Not recommended as primary translation engine** for medical documents at this stage
- Quality gap vs GPT-4o/Claude-3.5+ is significant for specialized terminology
- Context window limitations (most open models: 8K-32K vs 128K-200K for cloud APIs)
- No native glossary support -- requires prompt engineering
- Requires GPU hardware (A100/H100) for 13B+ models at acceptable speed. CPU inference (llama.cpp) is 10-50x slower
- **Best used as supplement**: RAG embedding model, or for non-critical internal drafts
- Could become viable with future models (e.g., specialized medical translation LoRAs on Qwen2.5-72B)

**Cost**: Free (software), but hardware costs significant: ~$3K-15K for a capable GPU workstation, or ~$1-3/hr for cloud GPU rental.

**Privacy**: **Maximum.** Everything runs locally. No data leaves the machine.

---

### 2. What Do Medical Translation Professionals Use?

Professional medical/device translation workflows typically involve:

1. **Trados/MemoQ + Machine Translation plugins**: Industry-standard CAT tools with DeepL/Google/Azure MT integration
2. **DeepL** is most commonly cited among freelance medical translators for European languages
3. **Azure Custom Translator** is used by larger LSPs (Language Service Providers) for domain adaptation
4. **GPT-4/Claude** are increasingly used in "MT + Post-editing" workflows -- LLM provides base translation, human editor refines
5. **Post-editing is the norm**: No fully automated solution is trusted for regulated medical device documentation without human review (regulatory requirement under ISO 13485, MDR, FDA QSR)

**Key insight**: For medical device translation, **ISO 13485:2016** and **MDR (EU 2017/745)** require human review of translated documentation. The AI's role is to produce high-quality drafts that minimize post-editing effort.

---

### 3. Glossary Integration Comparison

| Provider | Native Glossary API | Format | Per-Request Size Limit | Notes |
|---|---|---|---|---|
| **DeepL** | Yes (dedicated endpoint) | CSV, TBX | 100 chars/term approx | Best native glossary support |
| **Google Cloud** | Yes (glossary resource) | CSV, TSV, TMX | 10.4M UTF-8 bytes total | Requires Cloud Storage; stopword filtering |
| **Azure** | Yes (Custom Translator + dynamic dict) | TMX, XLIFF, CSV, TSV | Model training: unlimited | Two-tier: training vs dynamic dictionary |
| **OpenAI GPT-4o** | No (prompt engineering) | System prompt text | Constrained by context window | Must include in every request |
| **Anthropic Claude** | No (prompt engineering) | System prompt text | Constrained by context window | **Prompt caching makes this practical** |
| **Local Models** | No (prompt engineering) | System prompt text | Constrained by context window | No caching benefit |

**Recommendation**: For glossary-heavy workflows, DeepL or Google Cloud win on native integration. However, Claude with prompt caching offers a **competitive middle ground** -- the cost of including a large glossary in every request is mitigated by 90% cache hit savings, and the translation quality is higher than dedicated NMT for medical terminology.

---

### 4. Cost Comparison

#### Volume A: ~10K words/month (approximately 15K-20K characters)

| Provider | Estimated Monthly Cost | Notes |
|---|---|---|
| DeepL API Pro | $10-25 | Free tier may cover this entirely |
| Google Cloud Translation (NMT) | $0.30-0.50 | Very cheap at low volume; $10 free credit covers it |
| Google Cloud Translation (LLM) | $0.30-0.60 | $10 free credit covers it |
| Azure Translator | $0.20-0.40 | Free 2M chars/month covers this |
| OpenAI GPT-4o | $2-5 (without caching) | Depends on input/output ratio; ~3-5K tokens for 10K words |
| Anthropic Claude Sonnet 4.6 | $1-3 (without caching) | Slightly cheaper than GPT-4o at comparable quality |
| Local Models | $0 (HW amortized) | GPU cost ~$0-3K upfront |

#### Volume B: ~100K words/month (approximately 150K-200K characters)

| Provider | Estimated Monthly Cost | Notes |
|---|---|---|
| DeepL API Pro | $25-100 | Depends on plan tier and overage |
| Google Cloud Translation (NMT) | $3-5 | Still very cheap; $10 credit may cover |
| Google Cloud Translation (LLM) | $3-6 | |
| Azure Translator | $2-4 | Free tier covers 2M chars |
| OpenAI GPT-4o | $20-50 | Prompt engineering + glossary tokens add to base |
| OpenAI GPT-4o (Batch API) | $10-25 | 50% discount, 24hr turnaround |
| Anthropic Claude Sonnet 4.6 | $12-30 | Without caching |
| **Anthropic Claude Sonnet 4.6 (with caching)** | **$5-12** | **Caching glossary/style reduces input cost ~90%** |
| Local Models | $0 | GPU upfront (see above) |

**Key Insight**: At 100K words/month, cloud API costs are negligible for most business use cases ($5-50/month). The decision should be driven by **quality** and **privacy** requirements, not cost. At higher volumes (1M+ words/month), DeepL or Google Cloud may become more cost-effective than LLM APIs due to character-based vs token-based billing.

---

### 5. Rate Limits and Latency

| Provider | Rate Limits | Latency per Request | Notes for Document Translation |
|---|---|---|---|
| DeepL | Free: ~50 req/hr. Pro: ~500 req/min | 1-3 seconds (text), 5-15s (document) | Document translation handles entire files |
| Google Cloud | 1K-10K req/min (configurable) | 0.5-2 seconds (text), 5-30s (document) | Batch translation for large volumes |
| Azure | ~50 req/sec (S0 tier) | 0.5-2 seconds | Good throughput |
| OpenAI GPT-4o | 500-10K RPM (tier-dependent) | 2-10 seconds per chunk | Must chunk documents; sequential processing |
| Anthropic Claude Sonnet 4.6 | 1K-10K RPM (tier-dependent) | 2-8 seconds per chunk | Must chunk documents; caching reduces latency |
| Local (7B model, GPU) | N/A | 10-30 seconds per chunk on consumer GPU | Much slower for high quality |

**Document Translation Strategy**: For document-length translation with LLM APIs (OpenAI/Claude), the document must be split into chunks (paragraphs/sections), translated individually, and reassembled. This introduces:
- Per-chunk latency overhead (2-10s each)
- Context consistency across chunks (may drift)
- Reassembly complexity (format preservation)

DeepL and Google Cloud support native document translation (single API call for entire DOCX/PDF), which is simpler to implement but offers no glossary or format customization control.

---

### 6. Data Privacy / HIPAA Compatibility

| Provider | HIPAA BAA | Data Retention | Data Used for Training | Region Control | Certifications |
|---|---|---|---|---|---|
| **DeepL Pro** | Not publicly listed | No retention (Pro plan) | No | EU only (limited) | SOC 2, GDPR, ISO 27001 |
| **Google Cloud** | **Yes** | Configurable | No | **Yes** (any GCP region) | SOC 1/2/3, ISO 27001, FedRAMP, HIPAA |
| **Azure** | **Yes** | Configurable | No | **Yes** (any Azure region) | SOC 1/2/3, ISO 27001, FedRAMP, HIPAA |
| **OpenAI (Direct)** | **No** | 30 days (can opt out) | No (API since March 2023) | US only (default) | SOC 2, GDPR |
| **OpenAI (Azure)** | **Yes** | Configurable | No | **Yes** (Azure regions) | Same as Azure |
| **Anthropic Claude** | **Yes** (Enterprise) | Configurable | No (API) | **Yes** (enterprise) | SOC 2, ISO 27001, HIPAA |
| **Local Models** | N/A (self-managed) | Full control | N/A | N/A | Self-managed |

**For medical device industry context**: HIPAA is primarily relevant if the documents contain PHI (patient health information). Many medical device documents (IFUs, technical manuals, quality procedures) do NOT contain PHI. However, internal company policies may still require HIPAA-level or equivalent data protection.

**Recommended approach**: If documents contain PHI, use **Google Cloud**, **Azure**, or **Anthropic Enterprise** with signed BAA. If no PHI, all major providers offer adequate data protection for most compliance requirements.

---

### 7. Mixed-Language Document Handling (EN+DE -> EN+ZH)

| Provider | Native Mixed-Language Support | Recommended Approach |
|---|---|---|
| DeepL | No (single source language per request) | Split document by language segments, translate separately, merge |
| Google Cloud | No (single source language per request) | Split by language, translate separately |
| Azure | No (single source language per request) | Split by language, translate separately |
| OpenAI GPT-4o | **Yes** (LLM handles mixed input) | Prompt: "Translate the following document. English text remains in English, German text is translated to English, and then produce Chinese translation." Single API call. |
| Anthropic Claude | **Yes** (LLM handles mixed input) | Same approach as OpenAI. Single API call. |

**LLMs have a significant advantage** for the EN+DE -> EN+ZH use case. Dedicated translation APIs require splitting and merging, which is complex for documents with interleaved languages (common in medical device documentation with German as original and English as secondary source).

---

### 8. Recommendations

#### Primary Recommendation: Anthropic Claude (claude-sonnet-4-6) with Prompt Caching

**Rationale**:
1. **Translation quality**: Claude Sonnet 4.6 is comparable to GPT-4o for medical/technical translation at lower cost
2. **Prompt caching**: Glossary terms in system prompt cached at 90% discount -- best cost structure for glossary-heavy translation workflows
3. **Mixed language support**: Handles EN+DE -> EN+ZH in a single call
4. **HIPAA available**: Enterprise plan offers BAA
5. **200K context window**: Can process large document chunks
6. **Cost at scale**: ~$5-12/month for 100K words. With caching, ~$5-8/month

#### Alternative: Google Cloud Translation (if native glossary is priority)

**Rationale**:
1. Best native glossary API with CSV/TMX support
2. HIPAA-compliant with BAA
3. Cheapest at low volume ($0-5/month for 100K words)
4. AutoML for custom domain adaptation
5. Native document translation (handles DOCX/PDF directly)
6. **Downside**: No mixed-language handling; requires splitting DE/EN content

#### Fallback: DeepL API (if dedicated translation tool preferred)

**Rationale**:
1. Best-in-class glossary management
2. Document translation preserves formatting
3. Good for DE-EN strength
4. **Downside**: Weaker EN-ZH medical quality vs LLMs; no mixed-language; no HIPAA BAA

#### Not Recommended: Local Models (at this stage)

Quality gap for medical terminology is still too large. Reassess in 12-18 months as open-source models improve.

---

### 9. Implementation Considerations for Electron App

**For Claude API (recommended path)**:
- Install `@anthropic-ai/sdk` in Electron main process (Node.js)
- Implement chunking: split document into paragraphs/sections (respecting ~50K token chunks)
- Cache system prompt with glossary (5-min cache TTL sufficient for batch processing)
- Sequential processing: send chunks one at a time, reassemble in order
- Retry logic for rate limits (exponential backoff)
- Store glossary in SQLite, convert to system prompt format on each translation session

**For Google Cloud Translation (alternative path)**:
- Install `@google-cloud/translate` in Electron main process
- Upload glossary to Cloud Storage, create glossary resource, reference by ID
- Send document content via Text Translation API (character-based billing)
- Simpler chunking (character-based limits, not token-based)

**API Key Management**:
- Store API keys securely in Electron's safe storage (electron-store with encryption, or OS keychain via keytar)
- Never expose keys to renderer process (IPC only)
- Allow user to configure their own API key (BYO model)

---

### 10. Sources

- Anthropic API pricing and model documentation (docs.anthropic.com, accessed 2026-06-01)
- Google Cloud Translation pricing page (cloud.google.com/translate/pricing, accessed 2026-06-01)
- Azure AI Translator pricing page (azure.microsoft.com/en-us/pricing/details/cognitive-services/translator/, accessed 2026-06-01)
- OpenAI Models documentation (platform.openai.com/docs/models, accessed 2026-06-01)
- DeepL API documentation (developers.deepl.com, accessed 2026-06-01)
- DeepL Pro API pricing information (deepl.com/en/pro-api, accessed 2026-06-01)
- Anthropic Prompt Caching documentation (docs.anthropic.com/en/docs/build-with-claude/prompt-caching, accessed 2026-06-01)
- Ollama model search results (ollama.com, accessed 2026-06-01)
- Azure Custom Translator overview (learn.microsoft.com/en-us/azure/ai-services/translator/custom-translator/overview, accessed 2026-06-01)

## Caveats

- Pricing information is as of 2026-06-01 and may change. All providers adjust pricing periodically.
- Translation quality assessments are based on available benchmarks and documentation. Actual quality should be validated with representative medical device documents before final provider selection.
- The recommendation assumes an Electron main process (Node.js) calling REST APIs. All major providers have official or community-maintained Node.js SDKs.
- HIPAA compliance requirements should be verified with the provider's legal documentation and your organization's compliance team before processing protected health information.
- Local model landscape is evolving rapidly. The quality gap may narrow significantly within 12 months.
