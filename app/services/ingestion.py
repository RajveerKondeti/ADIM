"""
ingestion.py — text processing pipeline.

The flow for every document:
  raw text → clean → chunk → embed → store in Qdrant

Three ingestion sources supported:
  1. Raw text (paste anything)
  2. File upload (.pdf or .txt)
  3. URL (fetches and strips HTML)
"""
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


# ── Text chunking ─────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 75,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Why overlap? If a sentence is split across two chunks, the overlap
    ensures neither chunk loses critical context at its boundary.

    chunk_size=500 chars ≈ 80-100 words — a good balance between
    providing enough context and keeping chunks focused.
    """
    # Normalize whitespace first
    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 30:          # Skip chunks that are too short to be useful
            chunks.append(chunk)
        start += chunk_size - overlap

    logger.debug(f"Chunked text into {len(chunks)} chunks.")
    return chunks


# ── Embedding model ───────────────────────────────────────────────────────────
# @lru_cache means the model loads ONCE and stays in memory.
# First call: ~30 seconds (downloads ~90MB model).
# Every call after: instant.

@lru_cache(maxsize=1)
def _get_embed_model():
    from sentence_transformers import SentenceTransformer
    logger.info("⏳ Loading embedding model 'all-MiniLM-L6-v2' (one-time, ~30s)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("✅ Embedding model ready.")
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert a list of text strings into a list of 384-dim vectors."""
    model = _get_embed_model()
    return model.encode(texts, show_progress_bar=False).tolist()


def embed_query(text: str) -> list[float]:
    """Convert a single query string into a 384-dim vector."""
    model = _get_embed_model()
    return model.encode(text).tolist()


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_pdf_text(content: bytes) -> str:
    """Extract all text from a PDF byte stream."""
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return " ".join(pages)
    except Exception as e:
        raise ValueError(f"Could not parse PDF: {e}")


# ── URL fetching ──────────────────────────────────────────────────────────────

async def fetch_url_text(url: str) -> str:
    """
    Fetch a URL and extract clean readable text.

    Strips: <script>, <style>, <nav>, <footer>, <header> — anything
    that isn't actual content. Joins remaining text with spaces.
    """
    try:
        import httpx
        from bs4 import BeautifulSoup

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "div"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text

    except Exception as e:
        raise ValueError(f"Could not fetch URL '{url}': {e}")