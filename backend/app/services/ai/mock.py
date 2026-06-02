"""Mock translation provider for testing and development."""

from __future__ import annotations

import asyncio
from copy import deepcopy

from app.services.ai.base import TranslationProvider
from app.services.segment import DocumentSegment


class MockProvider(TranslationProvider):
    """Mock translation provider that simulates translation without a real AI model.

    Features:
    - Returns translated segments with language prefix markers ([ZH], [EN]).
    - Uses pinyin-like output for EN→ZH translation.
    - Handles mixed source-language input.
    - Deliberately slow (50 ms per segment) to simulate real translation latency.
    - Accepts and injects glossary terms into mock output.
    """

    # Mock pinyin equivalents for common English words (EN → ZH)
    _EN_TO_ZH: dict[str, str] = {
        "the": "",
        "a": "",
        "an": "",
        "is": "shi",
        "are": "shi",
        "was": "shi",
        "were": "shi",
        "has": "you",
        "have": "you",
        "had": "you",
        "with": "he",
        "and": "yu",
        "or": "huo",
        "of": "de",
        "in": "zai",
        "to": "dao",
        "for": "wei",
        "on": "zai",
        "at": "zai",
        "by": "tongguo",
        "from": "cong",
        "patient": "bingren",
        "fever": "fashao",
        "blood": "xueye",
        "pain": "tengtong",
        "heart": "xinzang",
        "lung": "fei",
        "liver": "gan",
        "kidney": "shen",
        "test": "jiancha",
        "result": "jieguo",
        "normal": "zhengchang",
        "abnormal": "yichang",
        "treatment": "zhiliao",
        "diagnosis": "zhenduan",
        "surgery": "shoushu",
        "medicine": "yaowu",
        "hospital": "yiyuan",
        "doctor": "yisheng",
        "symptom": "zhengzhuang",
        "infection": "ganran",
        "inflammation": "fayan",
        "chronic": "manxing",
        "acute": "jixing",
        "cancer": "aizheng",
        "tumor": "zhongliu",
        "pressure": "yali",
        "rate": "lv",
        "cell": "xibao",
        "tissue": "zuzhi",
        "dose": "jiliang",
        "therapy": "liaofa",
        "examination": "jianyan",
        "screening": "shaicha",
        "surgical": "waike",
        "clinical": "linchuang",
    }

    # Mock English equivalents for ZH → EN
    _ZH_TO_EN: dict[str, str] = {
        "病人": "patient",
        "发烧": "fever",
        "血液": "blood",
        "疼痛": "pain",
        "心脏": "heart",
        "肺": "lung",
        "肝脏": "liver",
        "肾脏": "kidney",
        "测试": "test",
        "结果": "result",
        "正常": "normal",
        "异常": "abnormal",
        "治疗": "treatment",
        "诊断": "diagnosis",
        "手术": "surgery",
        "药物": "medicine",
        "医院": "hospital",
        "医生": "doctor",
        "症状": "symptom",
        "感染": "infection",
        "炎症": "inflammation",
        "慢性": "chronic",
        "急性": "acute",
        "癌症": "cancer",
        "肿瘤": "tumor",
        "压力": "pressure",
        "率": "rate",
        "细胞": "cell",
        "组织": "tissue",
        "剂量": "dose",
        "疗法": "therapy",
        "检查": "examination",
        "筛查": "screening",
        "外科": "surgical",
        "临床": "clinical",
    }

    # Delay per segment in seconds (simulates real translation latency)
    _DELAY_PER_SEGMENT: float = 0.05

    async def translate(
        self,
        segments: list[DocumentSegment],
        source_lang: str,
        target_lang: str,
        glossary: dict[str, str] | None = None,
        rag_examples: list[tuple[str, str]] | None = None,
    ) -> list[DocumentSegment]:
        result: list[DocumentSegment] = []

        for seg in segments:
            await asyncio.sleep(self._DELAY_PER_SEGMENT)

            text = seg.source_text
            metadata = deepcopy(seg.metadata)

            # If RAG examples are provided, prepend them as context
            # for the mock translation so the caller can verify they
            # were received.
            if rag_examples:
                rag_prefix_parts: list[str] = []
                for src, tgt in rag_examples:
                    rag_prefix_parts.append(f"[RAG] {src} -> {tgt}")
                text = "\n".join(rag_prefix_parts) + "\n" + text

            # Mock-translate based on target language
            target_lang_upper = target_lang.upper()
            if target_lang_upper == "ZH":
                translated = self._mock_to_zh(text, glossary)
                target_text = f"[ZH] {translated}"
            elif target_lang_upper == "EN":
                translated = self._mock_to_en(text, glossary)
                target_text = f"[EN] {translated}"
            else:
                target_text = f"[{target_lang_upper}] {text}"

            result.append(
                DocumentSegment(
                    index=seg.index,
                    source_text=target_text,
                    segment_type=seg.segment_type,
                    metadata=metadata,
                )
            )

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_glossary(
        glossary: dict[str, str],
    ) -> dict[str, str]:
        """Return glossary with case-folded keys for matching."""
        return {k.lower(): v for k, v in glossary.items()}

    def _mock_to_zh(
        self,
        text: str,
        glossary: dict[str, str] | None = None,
    ) -> str:
        """Convert text to mock Chinese (pinyin-like).

        Glossary term keys take priority over the built-in mapping.
        """
        norm_glossary = self._normalise_glossary(glossary) if glossary else {}

        words = text.split()
        translated: list[str] = []
        for word in words:
            clean = word.strip(".,;:!?()[]{}«»\"''")
            punct = word[len(clean) :] if len(clean) < len(word) else ""
            lower = clean.lower()

            # Glossary override (exact word, case-insensitive)
            if norm_glossary and lower in norm_glossary:
                mapped = norm_glossary[lower]
            elif lower in self._EN_TO_ZH:
                mapped = self._EN_TO_ZH[lower]
            else:
                mapped = self._to_pinyin_like(clean)

            if mapped:
                translated.append(mapped + punct)

        result = " ".join(t for t in translated if t).strip()
        return result if result else text

    def _mock_to_en(
        self,
        text: str,
        glossary: dict[str, str] | None = None,
    ) -> str:
        """Convert text to mock English using built-in and glossary mappings."""
        # Apply glossary directly (source-lang terms likely Chinese for ZH→EN)
        if glossary:
            for src, tgt in glossary.items():
                text = text.replace(src, tgt)
        # Then apply built-in ZH → EN
        for zh, en in self._ZH_TO_EN.items():
            text = text.replace(zh, en)
        return text

    @staticmethod
    def _to_pinyin_like(word: str) -> str:
        """Generate a plausible pinyin-like approximation for any word."""
        pinyin_initials = "bpmfdtnlgkhjqxzcsryw"
        result: list[str] = []
        for ch in word.lower():
            if ch in "aeiou":
                result.append(ch)
            else:
                idx = (ord(ch) - ord("a")) % len(pinyin_initials)
                result.append(pinyin_initials[idx])
        return "".join(result)
