from functools import lru_cache
from typing import Tuple, List
import numpy as np
import spacy
from sentence_transformers import SentenceTransformer

from .config import get_settings


@lru_cache()
def get_nlp():
    # lightweight English model
    return spacy.load("en_core_web_sm")


@lru_cache()
def get_embedder() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embed_model_name)


def encode_norm(embedder: SentenceTransformer, texts: List[str]) -> np.ndarray:
    return embedder.encode(texts, normalize_embeddings=True)
