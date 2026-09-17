"""
OmniLab AI - Curriculum Service Layer
Text chunking, embedding generation, and RAG retrieval.
"""
import logging
import math
from typing import List, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

# Chunk settings
CHUNK_SIZE_TOKENS = 400       # target tokens per chunk
CHUNK_OVERLAP_TOKENS = 50     # overlap for context continuity
CHARS_PER_TOKEN_APPROX = 4    # rough approximation


class CurriculumService:
    """Handles lesson ingestion, chunking, embedding, and vector search."""

    # ── Text Chunking ─────────────────────────────────────────────────────────

    @staticmethod
    def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_TOKENS, overlap: int = CHUNK_OVERLAP_TOKENS) -> List[str]:
        """
        Splits text into overlapping chunks of approximately `chunk_size` tokens.
        Uses paragraph boundaries for clean splits when possible.
        """
        max_chars = chunk_size * CHARS_PER_TOKEN_APPROX
        overlap_chars = overlap * CHARS_PER_TOKEN_APPROX

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Para itself might be too long → split by sentences
                if len(para) > max_chars:
                    sentences = para.replace(". ", ".|").split("|")
                    temp = ""
                    for sent in sentences:
                        if len(temp) + len(sent) <= max_chars:
                            temp += (" " if temp else "") + sent
                        else:
                            if temp:
                                chunks.append(temp.strip())
                            temp = sent
                    current_chunk = temp
                else:
                    # Start new chunk, carry overlap from previous
                    overlap_text = current_chunk[-overlap_chars:] if chunks else ""
                    current_chunk = (overlap_text + "\n\n" + para).strip()

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    # ── Embedding Generation ──────────────────────────────────────────────────

    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """
        Calls OpenAI Embeddings API and returns a float vector.
        Falls back to zero vector if API key not set (development mode).
        """
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            dimension = settings.EMBEDDING_DIMENSION
            logger.warning("OPENAI_API_KEY not set. Returning zero embedding (dev mode).")
            return [0.0] * dimension

        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
                encoding_format="float",
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.exception("Embedding API call failed: %s", exc)
            return [0.0] * settings.EMBEDDING_DIMENSION

    # ── Lesson Ingestion ──────────────────────────────────────────────────────

    @classmethod
    def chunk_and_embed_lesson(cls, lesson, re_embed: bool = False) -> int:
        """
        Chunks lesson content and stores DocumentChunks with embeddings.
        If re_embed=True, deletes existing chunks first.
        Returns number of chunks created.
        """
        from .models import DocumentChunk

        if re_embed:
            deleted, _ = DocumentChunk.objects.filter(lesson=lesson).delete()
            logger.info("Deleted %d old chunks for lesson %s", deleted, lesson.id)

        text = lesson.content
        if not text.strip():
            logger.warning("Lesson %s has empty content. Skipping chunking.", lesson.id)
            return 0

        raw_chunks = cls.chunk_text(text)
        created = 0

        for idx, chunk_text in enumerate(raw_chunks):
            token_count = max(1, len(chunk_text) // CHARS_PER_TOKEN_APPROX)
            embedding = cls.generate_embedding(chunk_text)

            DocumentChunk.objects.create(
                lesson=lesson,
                chunk_index=idx,
                text=chunk_text,
                token_count=token_count,
                embedding=embedding,
            )
            created += 1

        logger.info("Created %d chunks for lesson '%s'", created, lesson.title)
        return created

    # ── RAG Retrieval ─────────────────────────────────────────────────────────

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a ** 2 for a in vec_a))
        mag_b = math.sqrt(sum(b ** 2 for b in vec_b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    @classmethod
    def retrieve_relevant_chunks(
        cls,
        query: str,
        lesson_ids: List,
        top_k: int = None,
        threshold: float = None,
    ) -> List[Tuple[str, float]]:
        """
        Semantic search over DocumentChunks for given lesson_ids.
        Returns list of (chunk_text, similarity_score) sorted by relevance.

        Production note: Replace in-Python cosine sim with pgvector SQL:
            ORDER BY embedding <=> query_vector LIMIT top_k
        """
        from .models import DocumentChunk

        top_k = top_k or settings.RAG_TOP_K
        threshold = threshold or settings.RAG_SIMILARITY_THRESHOLD

        query_embedding = cls.generate_embedding(query)

        chunks = DocumentChunk.objects.filter(
            lesson_id__in=lesson_ids,
            embedding__isnull=False,
        ).values("text", "embedding")

        scored = []
        for chunk in chunks:
            if chunk["embedding"]:
                sim = cls.cosine_similarity(query_embedding, chunk["embedding"])
                if sim >= threshold:
                    scored.append((chunk["text"], sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
