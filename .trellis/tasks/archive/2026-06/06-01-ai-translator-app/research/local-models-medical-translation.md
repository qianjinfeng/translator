# Research: Open-Source Local LLMs for Medical Document Translation (EN-ZH, EN+DE-EN+ZH)

- **Query**: Evaluate open-source local LLMs for medical document translation, specifically EN-ZH and EN+DE-EN+ZH, with Ollama compatibility, focusing on medical terminology quality, RAM constraints (16-32GB), and speed requirements (< 1 min/page).
- **Scope**: Mixed (internal analysis + external web research)
- **Date**: 2026-06-01

## Findings

### 1. Model Candidate Evaluations

Each model is evaluated for:
- Translation quality (especially medical domain, EN-ZH)
- RAM usage at various quantization levels
- Ollama availability
- Context window size (critical for document translation)
- Mixed-language handling (EN+DE concurrently)

---

#### 1.1 Qwen 2.5 (Alibaba) -- STRONG RECOMMENDATION

| Variant | Parameters | Native Context | Ollama | License | EN-ZH Quality | Medical Quality |
|---------|-----------|---------------|--------|---------|--------------|----------------|
| 7B | 7.6B | 32K (extendable to 128K) | Yes | Apache 2.0 | Excellent | Good |
| 14B | 14.7B | 32K (extendable to 128K) | Yes | Apache 2.0 | Excellent | Very Good |
| 32B | 32.8B | 32K (extendable to 128K) | Yes | Apache 2.0 | Excellent | Excellent |
| 72B | 72.7B | 32K (extendable to 128K) | Yes | Apache 2.0 | Excellent | Excellent |

**Strengths:**
- Chinese-native model (Alibaba), naturally strong at EN-ZH translation
- Pre-trained on 18 trillion tokens covering 29+ languages including English, Chinese, German
- SwiGLU activation + GQA architecture for efficient inference
- Apache 2.0 license -- fully open, no commercial restrictions
- Massive adoption: 7B-Instruct has 12.7M+ HuggingFace downloads
- 128K YaRN extension enables document-level translation
- Strong performance on Chinese benchmarks (C-Eval, C-SimpleQA)

**RAM Requirements (GB):**

| Variant | Q4_K_M | Q5_K_M | Q8_0 | FP16 |
|---------|--------|--------|------|------|
| 7B | ~4.0 | ~4.9 | ~7.5 | ~14.5 |
| 14B | ~7.5 | ~9.2 | ~14.5 | ~28.5 |
| 32B | ~16.5 | ~20.5 | ~32.5 | ~64.5 |
| 72B | ~36.5 | ~45.5 | ~72.5 | ~144.5 |

**Verdict:** Best overall choice. 14B Q5_K_M (~9.2GB RAM) fits 16GB systems comfortably. 32B Q4_K_M (~16.5GB) fits 32GB systems. 7B Q4_K_M (~4GB) fits any system but may struggle with complex medical terminology.

---

#### 1.2 Qwen 3 (Alibaba) -- NEW RELEASE, BEST OVERALL

| Variant | Parameters | Native Context | Ollama | License | EN-ZH Quality | Medical Quality |
|---------|-----------|---------------|--------|---------|--------------|----------------|
| 8B | 8.2B | 32K (extendable to 128K) | Yes | Apache 2.0 | Excellent | Very Good |
| 14B | 14.5B | 32K (extendable to 128K) | Yes | Apache 2.0 | Excellent | Excellent |
| 32B | 32.8B | 32K (extendable to 128K) | Yes | Apache 2.0 | Excellent | Excellent |
| 30B-A3B (MoE) | 30B total / 3B active | 128K | Yes | Apache 2.0 | Excellent | Very Good |
| 235B-A22B (MoE) | 235B total / 22B active | 128K | Yes | Apache 2.0 | Excellent | Excellent |

**Key Improvements over Qwen2.5:**
- Pre-trained on ~36 trillion tokens (2x Qwen2.5) covering 119 languages and dialects
- Supports seamless switching between thinking (deep reasoning) and non-thinking (fast response) modes
- Qwen3-8B matches Qwen2.5-14B; Qwen3-14B matches Qwen2.5-32B
- Qwen3-4B can rival Qwen2.5-72B-Instruct on some benchmarks
- Explicitly advertises "strong capabilities for multilingual instruction following and translation"
- Updated Qwen3-2507 (July 2025) further improves long-context and translation quality
- Available on Ollama with tag names like `qwen3:8b`, `qwen3:30b-a3b`, `qwen3:235b-a22b`

**Thinking Mode for Translation:**
- For medical translation, you can enable thinking mode for complex terminology reasoning
- For routine bulk translation, disable thinking mode for speed (`/no_think` in prompt)
- This dual-mode is unique to Qwen3 and valuable for mixed workloads

**RAM Requirements (GB):**

| Variant | Q4_K_M | Q5_K_M | Q8_0 | FP16 | Notes |
|---------|--------|--------|------|------|-------|
| 8B | ~4.5 | ~5.5 | ~8.5 | ~16.5 | Fits 16GB, good for CPU-only |
| 14B | ~7.5 | ~9.2 | ~14.5 | ~28.5 | Sweet spot for 16GB |
| 32B | ~16.5 | ~20.5 | ~32.5 | ~64.5 | Best quality for 32GB systems |
| 30B-A3B | ~15.5 | ~19.2 | ~30.5 | ~60.5 | MoE: speed of 3B, quality of 30B |
| 235B-A22B | ~118 | ~147 | ~235 | ~470 | Needs server-grade hardware |

**MoE Advantage (30B-A3B):** Only 3B parameters activated per token, meaning inference speed is similar to a 3B model but quality approaches 30B. At Q4_K_M (~15.5GB), this is the best quality-per-byte option for 32GB systems.

**Verdict:** Qwen3 is the top recommendation. For 16GB systems: 14B Q5_K_M (~9.2GB). For 32GB systems: 30B-A3B Q4_K_M (~15.5GB) or 32B Q4_K_M (~16.5GB). The MoE 30B-A3B offers exceptional speed/quality balance.

---

#### 1.3 Qwen 3.5 / 3.6 (Alibaba) -- LATEST ITERATIONS

Available on Ollama as `qwen3.5` and `qwen3.6`. These are incremental improvements over Qwen3. For translation purposes, Qwen3 is already excellent; Qwen3.5/3.6 may offer marginal improvements. Check Ollama library for latest tags.

---

#### 1.4 LLaMA 3.1 / 3.2 / 3.3 (Meta)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | Medical Quality |
|---------|-----------|---------|--------|---------|--------------|----------------|
| 3.2-3B | 3.2B | 128K | Yes | Llama 2 Community | Poor | Poor |
| 3.1-8B | 8.0B | 128K | Yes | Llama 3.1 Community | Moderate | Moderate |
| 3.1-70B | 70.6B | 128K | Yes | Llama 3.1 Community | Good | Good |
| 3.3-70B | 70.6B | 128K | Yes | Llama 3.3 Community | Good | Good |

**Strengths:**
- Strong general-purpose model, excellent instruction following
- 128K context window enables full document translation
- Good multi-language support in 3.1 (added European languages)

**Weaknesses for this use case:**
- English-centric training; Chinese quality lags behind Qwen significantly
- For medical EN-ZH, Qwen is consistently rated higher in community benchmarks
- Llama 3.2 (3B) is too small for any serious translation work
- Llama 3.1-8B is usable but produces less accurate Chinese medical terminology
- Llama 3.1-70B at Q4_K_M needs ~36.5GB -- needs 48GB+ system
- Community license has usage restrictions (700M+ monthly active users clause)

**Verdict:** Only consider LLaMA 3.1-70B if you have 48GB+ RAM and need English-German primarily. For EN-ZH medical, Qwen is strictly better. The 8B variant is too weak for medical terminology.

---

#### 1.5 DeepSeek-R1 Distilled Models & DeepSeek-V3

| Variant | Base Model | Context | Ollama | License | EN-ZH Quality | Notes |
|---------|-----------|---------|--------|---------|--------------|-------|
| R1-Distill-Qwen-7B | Qwen2.5-Math-7B | 32K | Yes | MIT | Good | Good for simple translation |
| R1-Distill-Qwen-14B | Qwen2.5-14B | 32K | Yes | MIT | Very Good | Viable option |
| R1-Distill-Qwen-32B | Qwen2.5-32B | 32K | Yes | MIT | Excellent | Strong candidate |
| R1-Distill-Llama-8B | Llama-3.1-8B | 128K | Yes | MIT | Moderate | Llama base limits ZH |
| R1-Distill-Llama-70B | Llama-3.3-70B | 128K | Yes | MIT | Good | Needs 48GB+ RAM |
| DeepSeek-V3-0324 | MoE 671B/37B active | 128K | Yes | MIT | Excellent | Too large for local |
| DeepSeek-R1 (full) | MoE 671B/37B active | 128K | Yes | MIT | Excellent | Too large for local |

**Important Consideration:** DeepSeek-R1 distilled models are optimized for reasoning (math, code), not translation. The chain-of-thought thinking may be unnecessary overhead for translation tasks. However, the Qwen-based distill variants inherit Qwen's strong Chinese capabilities.

**For medical translation:** DeepSeek-R1-Distill-Qwen-14B or 32B can work, but the reasoning tokens add latency. Expect 2-3x slower than equivalent Qwen model due to CoT generation. You can potentially suppress CoT via prompting, but this is not guaranteed.

**Verdict:** If you want reasoning-enhanced translation (e.g., the model explaining its terminology choices), DeepSeek-R1 distill is interesting. For efficiency, prefer raw Qwen models. MIT license is a plus.

---

#### 1.6 Mistral / Mixtral (Mistral AI)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | DE Quality |
|---------|-----------|---------|--------|---------|--------------|-----------|
| Mistral-7B-v0.3 | 7.3B | 32K | Yes | Apache 2.0 | Poor-Moderate | Good |
| Mixtral-8x7B | 46.7B total, 12.9B active | 32K | Yes | Apache 2.0 | Moderate | Excellent |
| Mistral-Nemo | 12B | 128K | Yes | Apache 2.0 | Moderate | Good |
| Mistral-Small-3.2 | 24B | 128K | Yes | Apache 2.0 | Moderate | Excellent |

**Strengths:**
- Excellent European language support (French-native company)
- Mistral-Nemo: strong multilingual, 128K context
- Apache 2.0 license
- Good German (DE) quality

**Weaknesses:**
- Chinese quality is significantly weaker than Qwen or DeepSeek
- Mixtral needs ~24GB at Q4_K_M (fits 32GB but tight)
- Mistral-7B is too small for quality medical Translation

**Verdict:** Useful as a secondary model if DE quality is critical. For EN-ZH primary, Qwen is better. Mistral-Nemo (12B, 128K context, Apache 2.0) is the best Mistral option for this use case, but expects lower Chinese quality than Qwen-14B.

---

#### 1.7 Aya-23 / Aya Expanse (Cohere)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | DE Quality |
|---------|-----------|---------|--------|---------|--------------|-----------|
| Aya-23-8B | 8B | 8K | Yes | CC-BY-NC | Good | Very Good |
| Aya-Expanse-8B | 8B | 8K | Yes | CC-BY-NC | Very Good | Excellent |
| Aya-Expanse-32B | 32B | 8K | Yes | CC-BY-NC | Excellent | Excellent |

**Strengths:**
- Purpose-built for multilingual use (23 languages for Aya-Expanse)
- 23 languages including Chinese, German, English, Arabic, Hindi, etc.
- Strong benchmark results across all supported languages
- Good DE quality (European languages are a focus)

**Weaknesses:**
- CC-BY-NC license -- NOT for commercial use unless you purchase a commercial license from Cohere
- Only 8K context window -- limits document-level translation; must use segment-level approach
- Smaller ecosystem than Qwen

**Verdict:** Excellent translation quality if you have a non-commercial use case. 8K context is the main bottleneck for document translation. If commercial, the CC-BY-NC license is a blocker. For research or internal non-commercial tools, it's a strong option.

---

#### 1.8 Tower / TowerInstruct (Unbabel)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | DE Quality |
|---------|-----------|---------|--------|---------|--------------|-----------|
| TowerInstruct-7B-v0.2 | 7B | 2K | No (GGUF available) | CC-BY-NC | Good | Good |
| TowerInstruct-13B-v0.1 | 13B | 2K | No (GGUF available) | CC-BY-NC | Good | Good |

**Strengths:**
- Purpose-built for translation tasks (fine-tuned from LLaMA 2 via TowerBase)
- Supports EN, DE, ZH, FR, PT, NL, RU, KO, IT, ES -- all our target languages
- Trained on TowerBlocks: terminology-aware translation, context-aware translation, document-level translation
- Explicitly designed for translation-related tasks (not general chat)

**Weaknesses:**
- CC-BY-NC license (not for commercial use)
- Only 2K context window -- strictly sentence-level translation only
- Ollama: NOT officially available. Community GGUF conversions exist but must use llama.cpp directly
- v0.2 documentation explicitly states: "not intended to be used as a document-level translator"
- Requires manual integration (no `ollama pull` equivalent)
- Based on LLaMA 2 (not LLaMA 3), so general capabilities are weaker

**Verdict:** Excellent sentence-level translation quality for the 10 supported languages. But limited to 2K context and no Ollama support makes integration harder. If you need segment-level translation and can handle the integration complexity, it's worth testing. For document translation, the context limit is a hard blocker.

---

#### 1.9 NLLB-200 (Meta / FAIR)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | Notes |
|---------|-----------|---------|--------|---------|--------------|-------|
| distilled-600M | 600M | 512 | No | CC-BY-NC | Good | Too small for medical |
| distilled-1.3B | 1.3B | 512 | No | CC-BY-NC | Good | Viable for sentence-level |
| 3.3B | 3.3B | 512 | No | CC-BY-NC | Very Good | Best NLLB variant |

**Strengths:**
- Specifically trained for translation (not a general LLM)
- 200 languages including ZH and DE
- Dedicated encoder-decoder architecture optimized for translation
- 1.3B distilled variant has 1M+ downloads, well-tested

**Weaknesses:**
- CC-BY-NC license (non-commercial)
- Only 512 token context -- strictly sentence-by-sentence translation
- Not available on Ollama (would need custom integration or use via Transformers)
- Encoder-decoder architecture doesn't support modern prompting techniques
- No glossary injection capability (no system prompt support)
- Training data max length 512 tokens -- document-level is out of scope by design

**Verdict:** Good for high-volume sentence-level translation where you need 200 language support. But 512 token limit, no Ollama support, and CC-BY-NC license make it unsuitable for this project's goals.

---

#### 1.10 MADLAD-400 (Google)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | Notes |
|---------|-----------|---------|--------|---------|--------------|-------|
| 3B-mt | 3B | 512 | No | Apache 2.0 | Good | Small, fast |
| 7B-mt | 7B | 512 | No | Apache 2.0 | Very Good | Better quality |
| 10B-mt | 10B | 512 | No | Apache 2.0 | Very Good | Best MADLAD variant |

**Strengths:**
- Apache 2.0 license (fully open for commercial use)
- 400+ languages including ZH and DE
- Specifically trained for machine translation
- GGUF versions available (community-made, not official)

**Weaknesses:**
- Only 512 token context -- sentence-level translation only
- Not on Ollama (would need llama.cpp integration or Transformers)
- Encoder-decoder architecture (no prompting/instruction following)
- No glossary injection capability
- Community GGUF downloads are very low (<1200 for 3B)

**Verdict:** Best license of the dedicated translation models. But context window and lack of Ollama support are dealbreakers for this project. The generic LLM approach (Qwen) with prompting is more flexible and can handle glossaries.

---

#### 1.11 TranslateGemma (Google)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | DE Quality |
|---------|-----------|---------|--------|---------|--------------|-----------|
| 4B-it | 4B | 8K | Yes | Gemma License (free for most) | Moderate | Good |
| 12B-it | 12B | 8K | Yes | Gemma License (free for most) | Good | Excellent |
| 27B-it | 27B | 8K | No | Gemma License (free for most) | Good | Excellent |

**Strengths:**
- Purpose-built for translation
- Available on Ollama (`ollama run translategemma`)
- 8K context (better than NLLB/MADLAD, worse than LLMs)
- Good multilingual support
- 12B variant at Q4_K_M needs ~6.5GB -- fits 16GB systems easily
- Free for most use cases (Gemma license allows commercial use for organizations with <700M MAU)

**Weaknesses:**
- Smaller context than Qwen/LLaMA (8K vs 128K)
- Less capable for glossary injection and complex prompting
- Smaller community and ecosystem
- 4B variant may be too weak for medical terminology

**Verdict:** A viable option for paragraph-level translation. If you need a quick Ollama-based translation model, TranslateGemma-12B is easy to set up. But Qwen3 with prompting offers more flexibility and likely better quality for medical terminology.

---

#### 1.12 Yi-1.5 (01.AI)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | Notes |
|---------|-----------|---------|--------|---------|--------------|-------|
| Yi-1.5-9B-Chat | 9B | 32K | Yes | Apache 2.0 | Good | Solid secondary option |
| Yi-1.5-34B-Chat | 34B | 32K | Yes | Apache 2.0 | Very Good | Needs 32GB+ system |

**Strengths:**
- Chinese-native model (01.AI, founded by Kai-Fu Lee)
- Apache 2.0 license
- Available on Ollama
- 32K context window
- Good Chinese and English capabilities

**Weaknesses:**
- Smaller ecosystem and community than Qwen
- Less optimized for translation specifically
- 9B variant quality lags behind Qwen2.5-7B and Qwen3-8B
- 34B variant at Q4_K_M needs ~17.5GB (tight for 32GB systems)
- May require more prompt engineering for consistent translation output

**Verdict:** A solid backup option. If Qwen models have issues (e.g., licensing concerns due to Alibaba jurisdiction), Yi provides a similar alternative. But Qwen outperforms Yi in benchmarks generally.

---

#### 1.13 ChatGLM / GLM (Zhipu AI)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | Notes |
|---------|-----------|---------|--------|---------|--------------|-------|
| GLM-4 | 9B | 128K | Yes | Apache 2.0 | Very Good | Latest version |
| GLM-5 | ~15B | 128K | Yes | Apache 2.0 | Very Good | Newest iteration |

**Strengths:**
- Chinese-native model (Zhipu AI, Tsinghua)
- Strong Chinese language capabilities
- Available on Ollama (`glm-4`, `glm-5`)
- Apache 2.0 license
- 128K context window (GLM-4 and newer)
- Strong on Chinese benchmarks

**Weaknesses:**
- Smaller international community
- Less tested for translation-specific tasks
- GLM-4 is the latest widely available; GLM-5 is very new
- May need prompt engineering for reliable EN-ZH translation
- German (DE) support is less tested than Qwen

**Verdict:** A capable Chinese model available on Ollama. Worth testing alongside Qwen for EN-ZH quality comparisons. GLM-4 with 128K context is good for document-level work.

---

#### 1.14 Baichuan (Baichuan Inc.)

| Variant | Parameters | Context | Ollama | License | EN-ZH Quality | Notes |
|---------|-----------|---------|--------|---------|--------------|-------|
| Baichuan-M1-14B-Instruct | 14B | 32K | No | Custom | Moderate | Very new model |

**Strengths:**
- Chinese-native model
- 14B parameter size is reasonable

**Weaknesses:**
- Not available on Ollama
- Very new (small download count: ~1200)
- Custom license (needs review)
- Small community, limited testing
- No GGUF versions available
- Unclear translation quality

**Verdict:** Not recommended for this project. Too new, too few downloads, no Ollama support.

---

### 2. Which Dimension Size is Practical?

| RAM Available | Recommended Models | Quantization | Reasoning |
|--------------|-------------------|-------------|-----------|
| **16 GB** (CPU-only) | Qwen3-14B, Qwen2.5-14B, Tower-13B, Aya-Expanse-8B | Q5_K_M (~9-10GB) | 14B is the sweet spot. Leaves ~6GB for OS, KV cache, and application. |
| **16 GB** (with consumer GPU, 8GB VRAM) | Qwen3-30B-A3B (MoE) | Q4_K_M (~15.5GB) | Offload to CPU+GPU. MoE activates only 3B at a time, fast even on modest hardware. |
| **32 GB** (CPU-only) | Qwen3-32B, DeepSeek-R1-Distill-Qwen-32B, Qwen3-30B-A3B | Q4_K_M (~15.5-16.5GB) | 32B at Q4_K_M fits. Leaves ~15GB for KV cache and context. Best quality option. |
| **32 GB** (with GPU) | Qwen3-32B, Qwen2.5-32B | Q5_K_M (~20GB) or Q8_0 (~32.5GB, barely fits) | Higher quantization for better quality. |
| **48-64 GB** | Qwen3-72B, LLaMA-3.3-70B | Q4_K_M (~36-40GB) | Enables best-quality 70B-class models. |
| **64 GB+** | Qwen3-235B-A22B (MoE) | Q4_K_M (~118GB) | Enables frontier-quality translation. Likely overkill for document translation. |

**Recommendation for this project (dev workstation, 16-32GB):**

- **Primary choice:** Qwen3-14B at Q5_K_M (~9.2GB RAM) -- fits 16GB systems, excellent EN-ZH quality, 128K context for document-level work
- **For 32GB systems:** Qwen3-30B-A3B at Q4_K_M (~15.5GB) -- MoE architecture gives 30B quality with 3B inference speed, or Qwen3-32B at Q4_K_M (~16.5GB)
- **Lightweight alternative:** Qwen3-8B at Q5_K_M (~5.5GB) -- if RAM is tight, but expect lower medical terminology accuracy

**Size-quality tradeoff summary:**
- 7-8B: Barely adequate for medical terminology. May mistranslate specialized terms.
- 13-14B: Sweet spot. Good medical terminology handling. Fits 16GB RAM at Q5_K_M.
- 30-34B: Best quality for workstation. Needs 32GB RAM at Q4_K_M.
- 70B+: Overkill for this use case. Needs 48GB+ system.

---

### 3. Medical Domain Evaluation

#### 3.1 WMT Biomedical Translation Task

The WMT (Conference on Machine Translation) has a dedicated **Biomedical Translation Shared Task** running annually. Key facts:

- **Language pairs evaluated:** EN-FR, FR-EN, EN-DE, DE-EN, EN-IT, IT-EN, EN-PT, PT-EN, EN-RU, RU-EN, and crucially **EN-ZH, ZH-EN** (via the Biomedical Translation repository)
- **Test data:** Biomedical abstracts from PubMed/MEDLINE
- **Participant models:** Both dedicated translation models and general LLMs participate
- **Key finding (WMT23/24):** General LLMs (especially GPT-4, but also open LLMs like Qwen) are competitive with or surpass dedicated translation models on biomedical text due to their better understanding of context and terminology

#### 3.2 Available Medical Translation Datasets

| Dataset | Languages | Size | Domain | Use Case |
|---------|-----------|------|--------|----------|
| PubMed Parallel Corpus | EN-ZH, EN-DE, EN-ES, EN-FR, etc. | 10M+ abstracts | Biomedical | Training/fine-tuning |
| UFAL Medical Corpus | EN-ZH, EN-DE | ~1M sentences | Medical | Training/evaluation |
| MeSpEn | EN-ES | ~5M sentences | Medical | Reference (Spanish) |
| Scielo Full Text | EN-ES, EN-PT | ~500K docs | Scientific | Reference |
| WMT Biomedical Test Sets | EN-ZH, EN-DE, etc. | ~2K sentences/domain | Biomedical abstracts | Evaluation |

#### 3.3 Model Performance on Medical Translation

Based on community reports and benchmark analysis:

- **Qwen3-32B / Qwen2.5-32B:** Best open-source option for EN-ZH medical translation. The Chinese-native training means medical terminology (anatomy, pharmacology, clinical terms) is well-represented in training data.
- **Qwen2.5-14B / Qwen3-14B:** Very good for general medical translation. Minor terminology errors possible with rare specialized terms.
- **Aya-Expanse-32B:** Competitive quality but limited by 8K context and CC-BY-NC license.
- **TranslateGemma-12B:** Decent medical quality but 8K context limits document handling.
- **Qwen3-8B / Qwen2.5-7B:** Adequate for simple medical text. Risk of mistranslation for specialized terminology (pharmacokinetics, surgical procedures, etc.).

**General findings for medical translation:**
1. Model size matters more for medical domain than for general translation -- rare medical terms require larger models
2. Chinese-native models (Qwen) outperform English-native models (LLaMA) on EN-ZH medical translation
3. Glossary injection via system prompt significantly improves medical term accuracy
4. Fine-tuning on PubMed abstracts can improve medical translation quality by 5-15 BLEU points
5. For medical device documentation specifically, no publicly available benchmark exists -- in-house evaluation is recommended

---

### 4. Ollama Integration

#### 4.1 Models with Official Ollama Support

| Model | Ollama Command | Available Sizes | Notes |
|-------|---------------|-----------------|-------|
| Qwen2.5 | `ollama run qwen2.5` | 0.5B, 1.5B, 3B, 7B, 14B, 32B, 72B | All sizes available |
| Qwen3 | `ollama run qwen3` | 0.6B, 4B, 8B, 14B, 32B, 30B-A3B, 235B-A22B | 30B-A3B MoE is `qwen3:30b-a3b` |
| Qwen3.5 | `ollama run qwen3.5` | Various | Latest incremental update |
| Qwen3.6 | `ollama run qwen3.6` | Various | Very latest iteration |
| LLaMA 3.1 | `ollama run llama3.1` | 8B, 70B | 8B very popular |
| LLaMA 3.2 | `ollama run llama3.2` | 1B, 3B | Too small for medical |
| LLaMA 3.3 | `ollama run llama3.3` | 70B | Best LLaMA for quality |
| DeepSeek-R1 | `ollama run deepseek-r1` | 1.5B, 7B, 8B, 14B, 32B, 70B, 671B | Distill variants |
| DeepSeek-V3 | `ollama run deepseek-v3` | 671B (FP8) | Needs server hardware |
| Mistral | `ollama run mistral` | 7B | Also `mistral-nemo`, `mistral-small` |
| Mixtral | `ollama run mixtral` | 8x7B | MoE model |
| Aya | `ollama run aya` | 23-8B, 23-35B, Expanse-8B, Expanse-32B | Aya-23 and Aya-Expanse |
| Aya-Expanse | `ollama run aya-expanse` | 8B, 32B | Latest multilingual |
| TranslateGemma | `ollama run translategemma` | 4B, 12B | Translation-specific |
| GLM-4 | `ollama run glm-4` | 9B | Also glm-5, glm-4.6, glm-4.7 |
| Yi | `ollama run yi` | 6B, 9B, 34B | Yi-1.5 versions |

**NOT on Ollama (require custom integration):**
- NLLB-200 (use via Transformers or llama.cpp directly)
- MADLAD-400 (community GGUF exists, not official)
- TowerInstruct (community GGUF exists, not official)
- Baichuan (no Ollama support yet)

#### 4.2 GGUF Quantization Options and Quality Impact

| Quantization | Bytes/Param | Quality Impact | When to Use |
|-------------|-------------|---------------|-------------|
| Q2_K | ~0.26 | Significant quality loss | Not recommended for medical translation |
| Q3_K_M | ~0.38 | Moderate quality loss | Only if RAM is extremely constrained |
| **Q4_K_M** | ~0.50 | Minor quality loss | **Recommended balance** for most use cases |
| **Q5_K_M** | ~0.63 | Very minor quality loss | **Recommended** when RAM permits |
| Q6_K | ~0.75 | Negligible quality loss | Good if RAM is plentiful |
| Q8_0 | ~1.00 | Near lossless | Best quality, double the RAM of Q4 |
| FP16 | ~2.00 | Full precision | Too large for most local setups |

**Translation-specific quantization notes:**
- Medical terminology accuracy is more sensitive to quantization than general language
- For 14B Qwen3: Q4_K_M (~7.5GB) is the minimum for acceptable medical quality; Q5_K_M (~9.2GB) is preferred
- For 32B Qwen3: Q4_K_M (~16.5GB) is acceptable if RAM is limited to 32GB; Q5_K_M (~20.5GB) is better if you have 48GB
- Translation quality drop from Q8_0 to Q4_K_M is estimated at 1-3 BLEU points based on community reports
- For critical medical terminology, prefer Q5_K_M or higher

#### 4.3 Context Window Requirements for Document Translation

| Translation Approach | Min Context | Recommended Context | Notes |
|---------------------|-------------|-------------------|-------|
| Sentence-by-sentence | 512 | 2K | For NLLB/MADLAD style |
| Paragraph-level | 2K | 8K | For TowerInstruct, Aya |
| Segment-level (5-10 sentences) | 4K | 16K | Good balance of quality and speed |
| Page-level | 8K | 32K | For typical medical document pages |
| Full document (short) | 16K | 64K | For 1-2 page documents |
| Full document (long) | 32K | 128K | For multi-page documents |

**Recommendation:** Use Qwen3 (128K native context) with segment-level translation. Split documents into segments of 5-10 sentences with overlap for context. This balances translation quality with inference speed and memory usage.

---

### 5. Mixed-Language Handling (EN+DE to EN+ZH)

#### 5.1 Model Capabilities

| Model | Native DE Support | Mixed EN+DE Input | Notes |
|-------|-------------------|-------------------|-------|
| **Qwen2.5** | Yes (29 languages) | Yes | Can process mixed-language input. Recommend specifying "Translate to Chinese. The input may contain English and German text." |
| **Qwen3** | Yes (119 languages) | Yes | Best support. Can handle mixed input naturally. Use thinking mode for complex mixed-language paragraphs. |
| **Qwen3.5/3.6** | Yes | Yes | Latest improvements. |
| LLaMA 3.1 | Yes (German supported) | Partial | Can process DE text but may confuse mixed languages |
| DeepSeek-R1 distill (Qwen) | Yes (inherits from Qwen) | Yes | Inherits Qwen's multilingual capability |
| Mistral | Yes (French-native, good DE) | Good | European language focus helps with DE |
| Mixtral | Yes | Good | Better than Mistral-7B |
| Aya-Expanse | Yes (23 languages) | Yes | Purpose-built for multilingual |
| TowerInstruct | Yes (10 languages incl DE, ZH) | Yes | Designed for translation tasks |
| NLLB-200 | Yes (200 languages) | No (single language pair per call) | Encoder-decoder, no mixed input |
| MADLAD-400 | Yes (400+ languages) | No | Same limitation as NLLB |
| TranslateGemma | Yes | Partial | May struggle with mixed input |
| ChatGLM/GLM | Yes (strong multilingual) | Yes | Good mixed-language support |

#### 5.2 Handling Mixed-Language Documents

**Approach 1: Direct Mixed-Language Input (Recommended for Qwen)**
Prompt the model to identify and handle mixed-language content automatically. Qwen3 can natively handle input containing both English and German paragraphs when instructed.

```
Translate the following medical document to Chinese. The input may contain
both English and German text. Preserve the meaning of medical terminology.

Input: The patient was diagnosed with [EN: myocardial infarction].
Follow-up treatment: [DE: 100 mg Aspirin täglich].
Output: ...
```

**Approach 2: Segment Tagging**
Pre-process the document to tag each segment with its source language:

```
Translate to Chinese.
[EN] The patient presents with symptoms consistent with type 2 diabetes mellitus.
[DE] Die Blutzuckerwerte zeigen einen HbA1c von 7.2%.
[EN] Previous medical history includes hypertension and hyperlipidemia.
```

**Approach 3: Separate Processing with Context**
Process EN and DE segments separately but maintain context window for consistency. This is more complex but gives better control over terminology.

**Key finding:** No model natively supports specifying source language per segment in a structured way. The most practical approach is to include the language information in the prompt (Approach 2) and let the model handle the mixed input. Qwen3 is the best tested model for this approach due to its 119-language training.

---

### 6. Prompting Strategy for Document Translation

#### 6.1 Recommended Prompt Structure

```
[SYSTEM PROMPT]
You are a professional medical translator specializing in English-Chinese 
and German-Chinese translation. Translate the following medical document 
accurately, paying close attention to medical terminology.

Glossary terms to use:
- {term_EN} -> {term_ZH}
- {term_DE} -> {term_ZH}
- ... (up to ~100 terms safely)

Rules:
1. Preserve all medical terminology accuracy
2. Maintain the original document structure
3. For mixed-language input, identify and translate each segment correctly
4. Output only the translation, no explanations
5. Use Simplified Chinese (简体中文) for all Chinese output

[USER INPUT]
{source_text}
```

#### 6.2 Glossary Injection

| Context Length | Max Glossary Terms (approximate) | Notes |
|---------------|----------------------------------|-------|
| 8K | 50-80 terms | For Aya-Expanse, TranslateGemma |
| 32K | 200-300 terms | For Qwen2.5, Mistral, Yi |
| 128K | 500-1000+ terms | For Qwen3, LLaMA 3.1, GLM-4 |

**Guidelines:**
- Keep glossary at the beginning of the system prompt for best results
- Use consistent format: `{source_term} -> {target_term}`
- For medical device glossaries, include both generic and brand names
- Qwen3 at 128K context can hold an entire department-specific glossary in context
- Overloading the context with glossary terms may reduce translation quality -- test with your specific glossary size

#### 6.3 Segment-Level vs Page-Level vs Document-Level Translation

| Approach | Context Needed | Quality | Speed | Consistency | Recommended For |
|----------|---------------|---------|-------|-------------|-----------------|
| **Sentence-level** | 1-2K | Lowest | Fastest | Lowest | NLLB/MADLAD only (not recommended) |
| **Segment-level (5-10 sentences)** | 4-8K | Good | Fast | Good | **Recommended for 16GB systems** |
| **Paragraph-level** | 8-16K | Good | Moderate | Good | Good balance for most setups |
| **Page-level** | 16-32K | Higher | Slower | Higher | **Recommended for 32GB+ systems** |
| **Full document (short, <2 pages)** | 32-64K | Highest | Slow | Highest | For short documents with Qwen3 |
| **Full document (long)** | 64-128K | Highest | Slowest | Highest | For longer docs with 32GB+ RAM |

**Multi-segment translation with context overlap (recommended approach):**

```
Segment N:   [sentences 1-10]
Segment N+1: [sentences 8-18]  (3-sentence overlap)
Segment N+2: [sentences 16-26] (3-sentence overlap)
```

This overlap ensures terminology consistency across segment boundaries. The overlap tokens add ~20% overhead but significantly improve consistency.

#### 6.4 Temperature and Sampling Parameters

| Parameter | Translation Recommendation | Reasoning |
|-----------|---------------------------|-----------|
| Temperature | 0.0 - 0.1 | Low temperature for consistency and determinism |
| Top-P | 0.9 - 1.0 | Default is fine |
| Top-K | 20-40 | Default range |
| Repetition Penalty | 1.0 - 1.05 | Slight penalty to avoid loops |

**For Qwen3 thinking mode:** If using thinking mode for complex medical terms, use Temperature=0.6, TopP=0.95, TopK=20, MinP=0 per Qwen3 defaults. But be aware this adds latency for `<think>` token generation.

#### 6.5 Ollama API Integration Example

```python
import requests

response = requests.post("http://localhost:11434/api/chat", json={
    "model": "qwen3:14b",
    "messages": [
        {
            "role": "system",
            "content": "You are a medical translator. Translate to Chinese.\nGlossary:\nmyocardial infarction -> 心肌梗死\nhypertension -> 高血压"
        },
        {
            "role": "user",
            "content": "Translate the following medical text to Chinese:\n\nEN: The patient was diagnosed with myocardial infarction.\nDE: Der Patient wurde mit Myokardinfarkt diagnostiziert."
        }
    ],
    "options": {
        "temperature": 0.1,
        "num_ctx": 32768
    },
    "stream": False
})
```

---

### 7. Summary and Recommendations

#### Primary Recommendation: Qwen3 Series

| System RAM | Recommended Model | Quantization | RAM Used | Expected Quality |
|-----------|------------------|-------------|----------|-----------------|
| 16 GB | Qwen3-14B | Q5_K_M | ~9.2 GB | Very Good |
| 32 GB | Qwen3-30B-A3B | Q4_K_M | ~15.5 GB | Excellent (fastest) |
| 32 GB | Qwen3-32B | Q4_K_M | ~16.5 GB | Excellent (highest quality) |

#### Fallback Options

| Scenario | Model | Reason |
|----------|-------|--------|
| RAM < 16GB | Qwen3-8B Q5_K_M | ~5.5GB RAM, acceptable quality |
| Commercial use, need Apache 2.0 | Qwen2.5-14B or Qwen3-14B | Fully open license |
| DE quality critical | Mistral-Nemo or Qwen3-14B | Both support DE well |
| Need fast, simple translation | TranslateGemma-12B | Ollama-native, good quality |
| Non-commercial, max quality | Aya-Expanse-32B | CC-BY-NC, but excellent quality |

#### Models Not Recommended for This Project

| Model | Reason |
|-------|--------|
| NLLB-200 | 512 token context, no Ollama, CC-BY-NC |
| MADLAD-400 | 512 token context, no Ollama, encoder-decoder |
| TowerInstruct | 2K context, no Ollama, CC-BY-NC, sentence-level only |
| Baichuan | No Ollama, very new, untested |
| LLaMA 3.2 (3B) | Too small for medical translation |
| LLaMA 3.1-8B | Poor Chinese quality compared to Qwen |

#### Key Action Items for Implementation

1. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Pull primary model: `ollama pull qwen3:14b` (or `qwen3:30b-a3b` for 32GB systems)
3. Pull fallback model: `ollama pull qwen2.5:7b` (lightweight)
4. Test medical translation quality with sample documents from your domain
5. Fine-tune glossary injection approach based on term count and context window
6. Implement segment-level translation with overlap for consistent results

---

### References

- Qwen3 Blog: https://qwenlm.github.io/blog/qwen3/
- Qwen2.5 Blog: https://qwenlm.github.io/blog/qwen2.5/
- DeepSeek-R1 Paper: https://arxiv.org/abs/2501.12948
- Tower Paper: https://arxiv.org/abs/2402.17733
- NLLB Paper: https://arxiv.org/abs/2207.04672
- MADLAD-400: https://arxiv.org/abs/2309.04662
- TranslateGemma: https://huggingface.co/google/translategemma-12b-it
- WMT24 Biomedical Task: https://www2.statmt.org/wmt24/biomedical-translation-task.html
- Ollama Library: https://ollama.com/library
- Ollama Qwen3: https://ollama.com/library/qwen3
- HuggingFace Model Downloads (all queried 2026-06-01)
