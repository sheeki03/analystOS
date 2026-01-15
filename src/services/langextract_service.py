"""
LangExtract Service - Structured entity extraction with source grounding.
"""

import asyncio
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

# Module-level import check
LANGEXTRACT_IMPORT_SUCCESS = False
_IMPORT_ERROR: Optional[str] = None

try:
    import langextract as lx
    LANGEXTRACT_IMPORT_SUCCESS = True
except ImportError as e:
    _IMPORT_ERROR = str(e)


# ============== ENTITY SCHEMA ==============
# NOTE: This schema is documentation only - NOT enforced at runtime.
# The actual extraction is driven by the prompt in _get_extraction_prompt() and few-shot examples.
# If you add/remove entity types, update BOTH this schema AND the prompt/examples.
# WARNING: Schema drift risk - keep this synchronized with _get_extraction_prompt() and FEW_SHOT_EXAMPLES.
# partnership: captures business partnerships, strategic alliances, and collaborations

ENTITY_SCHEMA = {
    "person": {"attributes": ["title", "organization", "role"]},
    "organization": {"attributes": ["role", "relationship", "type"]},
    "funding_round": {"attributes": ["stage", "date"]},
    "funding_amount": {"attributes": ["currency", "amount", "context"]},
    "metric": {"attributes": ["type", "value", "period"]},
    "date": {"attributes": ["type", "year", "quarter"]},
    "technology": {"attributes": ["category", "context"]},
    "risk_factor": {"attributes": ["severity", "category"]},
    "partnership": {"attributes": ["partner", "type"]},  # Business partnerships and alliances
}


# ============== FEW-SHOT EXAMPLES ==============

FEW_SHOT_EXAMPLES = [
    {
        "text": "Acme Corp announced a $50M Series B round led by Sequoia Capital. CEO John Smith said the funds will accelerate product development.",
        "extractions": [
            {"class": "organization", "text": "Acme Corp", "attrs": {"role": "company"}},
            {"class": "funding_amount", "text": "$50M", "attrs": {"currency": "USD", "amount": 50000000}},
            {"class": "funding_round", "text": "Series B", "attrs": {"stage": "growth"}},
            {"class": "organization", "text": "Sequoia Capital", "attrs": {"role": "investor"}},
            {"class": "person", "text": "John Smith", "attrs": {"title": "CEO", "organization": "Acme Corp"}},
        ]
    },
    {
        "text": "The platform reached 2.5M MAU with 15% MoM growth since Q1 2024 launch.",
        "extractions": [
            {"class": "metric", "text": "2.5M MAU", "attrs": {"type": "MAU", "value": 2500000}},
            {"class": "metric", "text": "15% MoM growth", "attrs": {"type": "growth_rate", "value": 0.15}},
            {"class": "date", "text": "Q1 2024", "attrs": {"type": "launch_date", "year": 2024, "quarter": 1}},
        ]
    },
]


# ============== DATACLASSES ==============

@dataclass
class ExtractedEntity:
    entity_class: str
    entity_text: str
    attributes: Dict[str, Any]
    source_start: int
    source_end: int
    source_name: str
    source_type: str  # "document", "web", "docsend"
    confidence: Optional[float] = None


@dataclass
class NormalizedExtractionResult:
    """Lightweight result for caching - no raw text stored."""
    entities: List[ExtractedEntity]
    source_name: str
    source_type: str
    entity_count: int
    success: bool
    error: Optional[str] = None


# ============== SERVICE CLASS ==============

class LangExtractService:
    def __init__(self):
        self._available: Optional[bool] = None
        self._last_error: Optional[str] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    def _configure_openai_env(self) -> None:
        """Set OpenAI env vars for langextract only if not already set."""
        if os.getenv("OPENROUTER_API_KEY"):
            if not os.getenv("OPENAI_API_KEY"):
                os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
            if not os.getenv("OPENAI_BASE_URL"):
                os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
            if not os.getenv("OPENAI_API_BASE"):
                os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

    async def is_available(self) -> Tuple[bool, Optional[str]]:
        """Check if langextract is available and configured."""
        if self._available is not None:
            return self._available, self._last_error

        if not LANGEXTRACT_IMPORT_SUCCESS:
            self._available = False
            self._last_error = f"langextract not installed: {_IMPORT_ERROR}"
            return False, self._last_error

        if not (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")):
            self._available = False
            self._last_error = "No API key (OPENROUTER_API_KEY or OPENAI_API_KEY)"
            return False, self._last_error

        self._configure_openai_env()
        self._available = True
        return True, None

    def _chunk_document(self, text: str, chunk_size: int, overlap: int = 200) -> List[Tuple[int, int, str]]:
        """Slice text into chunks with overlap, returning (start, end, content) tuples.

        NOTE: Entities spanning chunk boundaries may still be missed despite overlap.
        This is an acceptable tradeoff for performance; overlap reduces but doesn't eliminate this.

        Args:
            text: Source text to chunk
            chunk_size: Target chunk size
            overlap: Characters of overlap between chunks to catch boundary-spanning entities
        """
        if len(text) <= chunk_size:
            return [(0, len(text), text)]

        # Clamp overlap to prevent chunk explosion if overlap >= chunk_size
        overlap = min(overlap, max(0, chunk_size - 1))
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))

            if end < len(text):
                # Try to break at paragraph boundary
                search_start = start + int(chunk_size * 0.9)
                break_point = text.rfind('\n\n', search_start, end)
                if break_point > search_start:
                    end = break_point + 2

            chunks.append((start, end, text[start:end]))

            # Advance with overlap (backtrack by overlap chars, but don't go negative)
            start = max(start + 1, end - overlap) if end < len(text) else end

        return chunks

    def _normalize_result(
        self,
        raw_result: Any,
        source_name: str,
        source_type: str,
        offset: int
    ) -> List[ExtractedEntity]:
        """Convert langextract output to ExtractedEntity list."""
        entities = []

        # Handle various result formats
        extractions = []
        if raw_result is None:
            extractions = []
        elif hasattr(raw_result, 'extractions'):
            # Object with extractions attribute
            extractions = raw_result.extractions or []
        elif isinstance(raw_result, dict):
            # Dict result - check for extractions/entities keys
            extractions = raw_result.get('extractions', raw_result.get('entities', []))
            if not isinstance(extractions, list):
                extractions = [extractions] if extractions else []
        elif isinstance(raw_result, list):
            # Direct list of extractions
            extractions = raw_result
        else:
            extractions = [raw_result] if raw_result else []

        for ext in extractions:
            # Handle both object and dict formats
            if hasattr(ext, 'extraction_class'):
                # Object format - try extraction_text, then text fallback
                entity_text = getattr(ext, 'extraction_text', None) or getattr(ext, 'text', '')
                entity = ExtractedEntity(
                    entity_class=ext.extraction_class,
                    entity_text=entity_text,
                    attributes=getattr(ext, 'attributes', {}) or {},
                    source_start=getattr(ext, 'start', 0) + offset,
                    source_end=getattr(ext, 'end', len(entity_text)) + offset,
                    source_name=source_name,
                    source_type=source_type,
                    confidence=getattr(ext, 'confidence', None)
                )
            elif isinstance(ext, dict):
                entity_text = ext.get('text') or ext.get('extraction_text') or ''
                start = ext.get('start', 0)
                # Default end to start + len(text) if not provided
                end = ext.get('end', start + len(entity_text)) if entity_text else start
                entity = ExtractedEntity(
                    entity_class=ext.get('class', ext.get('extraction_class', 'unknown')),
                    entity_text=entity_text,
                    attributes=ext.get('attrs', ext.get('attributes', {})),
                    source_start=start + offset,
                    source_end=end + offset,
                    source_name=source_name,
                    source_type=source_type,
                    confidence=ext.get('confidence')
                )
            else:
                continue

            entities.append(entity)

        return entities

    def _dedupe_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities."""
        seen = set()
        unique = []
        for e in entities:
            key = (e.entity_class, e.entity_text, e.source_start, e.source_end, e.source_name)
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def _validate_model_for_openrouter(self, model: str) -> None:
        """Log warning if model might not be OpenRouter-compatible."""
        # Warn if using OpenRouter and model doesn't look like provider/model format
        using_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        if using_openrouter and "/" not in model:
            logger.warning(
                f"Model '{model}' may not be OpenRouter-compatible. "
                "OpenRouter models typically use 'provider/model' format (e.g., 'openai/gpt-4o')."
            )

    async def extract_entities(
        self,
        text: str,
        source_name: str,
        source_type: str = "document"
    ) -> NormalizedExtractionResult:
        """Extract entities from text with chunking and deduplication."""
        import inspect
        from src.config import (
            LANGEXTRACT_MAX_CHUNK_SIZE,
            LANGEXTRACT_MAX_CONCURRENT,
            LANGEXTRACT_MODEL,
            LANGEXTRACT_EXTRACTION_PASSES
        )

        available, error = await self.is_available()
        if not available:
            return NormalizedExtractionResult(
                entities=[], source_name=source_name, source_type=source_type,
                entity_count=0, success=False, error=error
            )

        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(LANGEXTRACT_MAX_CONCURRENT)

        async with self._semaphore:
            try:
                import langextract as lx

                chunks = self._chunk_document(text, LANGEXTRACT_MAX_CHUNK_SIZE)
                all_entities = []

                # Determine if fence_output needed (non-Gemini models)
                model = LANGEXTRACT_MODEL or "gpt-4o"
                self._validate_model_for_openrouter(model)
                use_fence = "gemini" not in model.lower()

                # Cache examples once per extraction call (not per chunk)
                cached_examples = self._build_lx_examples()

                for chunk_start, chunk_end, chunk_text in chunks:
                    # Check if lx.extract is async or sync
                    if inspect.iscoroutinefunction(lx.extract):
                        # Async: call directly
                        raw_result = await self._call_lx_extract_async(
                            chunk_text, model, LANGEXTRACT_EXTRACTION_PASSES, use_fence, cached_examples
                        )
                    else:
                        # Sync: wrap in to_thread
                        raw_result = await asyncio.to_thread(
                            self._call_lx_extract,
                            chunk_text,
                            model,
                            LANGEXTRACT_EXTRACTION_PASSES,
                            use_fence,
                            cached_examples
                        )
                        # Handle edge case where sync call somehow returns awaitable
                        if inspect.isawaitable(raw_result):
                            raw_result = await raw_result

                    chunk_entities = self._normalize_result(
                        raw_result, source_name, source_type, chunk_start
                    )
                    all_entities.extend(chunk_entities)

                all_entities = self._dedupe_entities(all_entities)

                return NormalizedExtractionResult(
                    entities=all_entities,
                    source_name=source_name,
                    source_type=source_type,
                    entity_count=len(all_entities),
                    success=True
                )

            except Exception as e:
                logger.error(f"Extraction failed for {source_name}: {e}")
                return NormalizedExtractionResult(
                    entities=[], source_name=source_name, source_type=source_type,
                    entity_count=0, success=False, error=str(e)
                )

    def _get_extraction_prompt(self) -> str:
        return """Extract investment research entities: person, organization, funding_round, funding_amount, metric, date, technology, risk_factor, partnership. Use exact text, include context attributes."""

    def _build_lx_examples(self) -> List[Any]:
        """Build few-shot examples, with fallback if lx.data types unavailable."""
        try:
            import langextract as lx
            if hasattr(lx, 'data') and hasattr(lx.data, 'Extraction'):
                examples = []
                for ex in FEW_SHOT_EXAMPLES:
                    extractions = [
                        lx.data.Extraction(
                            extraction_class=e["class"],
                            extraction_text=e["text"],
                            attributes=e.get("attrs", {})
                        ) for e in ex["extractions"]
                    ]
                    examples.append(lx.data.ExampleData(text=ex["text"], extractions=extractions))
                return examples
        except Exception:
            pass
        # Fallback: return raw dicts (may work with some versions)
        return FEW_SHOT_EXAMPLES

    def _call_lx_extract(self, text: str, model: str, passes: int, use_fence: bool, cached_examples: List[Any]) -> Any:
        """Call lx.extract with compatibility handling for different API versions (sync)."""
        import langextract as lx

        # Common args
        kwargs = {
            "fence_output": use_fence,
        }
        prompt = self._get_extraction_prompt()

        # Input parameter variations: text_or_documents, text, documents (as list)
        input_params = [
            {"text_or_documents": text},
            {"text": text},
            {"documents": [text]},  # documents expects a list
        ]

        # Model parameter variations: model_name, model, none
        model_params = [
            {"model_name": model},
            {"model": model},
            {},  # fallback: no model param
        ]

        # Passes parameter variations: extraction_passes, passes, num_passes
        passes_params = [
            {"extraction_passes": passes},
            {"passes": passes},
            {"num_passes": passes},
        ]

        # Prompt parameter variations: prompt_description, instructions
        prompt_params = [
            {"prompt_description": prompt},
            {"instructions": prompt},
        ]

        for input_param in input_params:
            for model_param in model_params:
                for passes_param in passes_params:
                    for prompt_param in prompt_params:
                        try:
                            return lx.extract(
                                **input_param,
                                **prompt_param,
                                examples=cached_examples,
                                **passes_param,
                                **model_param,
                                **kwargs
                            )
                        except TypeError as e:
                            # Only continue if it's a signature mismatch error
                            msg = str(e)
                            if ("unexpected keyword argument" in msg or
                                "multiple values for argument" in msg or
                                "missing required positional argument" in msg):
                                continue
                            raise

        # If all combinations fail, raise
        raise RuntimeError("Could not find compatible lx.extract API signature")

    async def _call_lx_extract_async(self, text: str, model: str, passes: int, use_fence: bool, cached_examples: List[Any]) -> Any:
        """Call lx.extract with compatibility handling (async version)."""
        import langextract as lx

        kwargs = {"fence_output": use_fence}
        prompt = self._get_extraction_prompt()

        input_params = [
            {"text_or_documents": text},
            {"text": text},
            {"documents": [text]},
        ]

        model_params = [
            {"model_name": model},
            {"model": model},
            {},
        ]

        passes_params = [
            {"extraction_passes": passes},
            {"passes": passes},
            {"num_passes": passes},
        ]

        prompt_params = [
            {"prompt_description": prompt},
            {"instructions": prompt},
        ]

        for input_param in input_params:
            for model_param in model_params:
                for passes_param in passes_params:
                    for prompt_param in prompt_params:
                        try:
                            return await lx.extract(
                                **input_param,
                                **prompt_param,
                                examples=cached_examples,
                                **passes_param,
                                **model_param,
                                **kwargs
                            )
                        except TypeError as e:
                            # Only continue if it's a signature mismatch error
                            msg = str(e)
                            if ("unexpected keyword argument" in msg or
                                "multiple values for argument" in msg or
                                "missing required positional argument" in msg):
                                continue
                            raise

        raise RuntimeError("Could not find compatible lx.extract API signature")

    def create_entity_summary(
        self,
        entities: List[ExtractedEntity],
        include_heading: bool = True,
        max_sources: int = 10,
        min_confidence: Optional[float] = None
    ) -> str:
        """Create bounded summary for prompt injection.

        Args:
            entities: List of extracted entities
            include_heading: Include "## Extracted Entities" heading
            max_sources: Limit to top N sources by entity count to prevent bloat
            min_confidence: Filter out entities below this confidence (for noisy OCR)
        """
        MAX_SUMMARY_CHARS = 2000
        MAX_PER_CLASS = 5

        # Filter by confidence if specified (helps with noisy DocSend OCR)
        if min_confidence is not None:
            entities = [e for e in entities if e.confidence is None or e.confidence >= min_confidence]

        # Group by source and take top N sources by entity count
        by_source = defaultdict(list)
        for e in entities:
            by_source[e.source_name].append(e)
        top_sources = sorted(by_source.keys(), key=lambda s: len(by_source[s]), reverse=True)[:max_sources]
        entities = [e for e in entities if e.source_name in top_sources]

        grouped = defaultdict(list)
        for e in entities:
            if len(grouped[e.entity_class]) < MAX_PER_CLASS:
                grouped[e.entity_class].append(e)

        lines = []
        if include_heading:
            lines.append("## Extracted Entities")
        for cls, ents in sorted(grouped.items()):
            texts = ", ".join(e.entity_text for e in ents)
            lines.append(f"**{cls}**: {texts}")

        summary = "\n".join(lines)
        if len(summary) > MAX_SUMMARY_CHARS:
            summary = summary[:MAX_SUMMARY_CHARS] + "\n[truncated]"
        return summary

    def create_source_entity_summary(self, entities: List[ExtractedEntity], min_confidence: Optional[float] = None) -> str:
        """Create per-source summary without global heading (for display).

        Args:
            min_confidence: Filter out entities below this confidence.
                           Use 0.5 for DocSend OCR sources to reduce noise.
        """
        return self.create_entity_summary(entities, include_heading=False, min_confidence=min_confidence)


# Global instance
_service: Optional[LangExtractService] = None
_init_lock = asyncio.Lock()

async def get_langextract_service() -> LangExtractService:
    """Get or create the global LangExtractService instance (thread-safe)."""
    global _service
    if _service is not None:
        return _service
    async with _init_lock:
        if _service is None:
            _service = LangExtractService()
    return _service
