import hashlib
from functools import lru_cache
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

PERSIST_DIR =str(Path(__file__).resolve().parent / "chroma.db")
MAX_CHUNKS = 1500        # latency ki limit, apne hisaab se badlo
MIN_CHUNK_CHARS = 80     # chhote junk chunks hata deta hai


@lru_cache(maxsize=1)
def get_embeddings():
    # Model sirf pehli baar load hota hai, phir yaad rehta hai
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def collection_name(project_id):
    # Har project ka apna collection, taaki data mix na ho
    return "p_" + hashlib.md5(project_id.encode()).hexdigest()[:16]


def get_store(project_id):
    return Chroma(
        collection_name=collection_name(project_id),
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIR,
    )


def is_indexed(project_id):
    return len(get_store(project_id).get(limit=1)["ids"]) > 0


def build_index(documents, project_id):
    """Returns (chunks_ka_count, cached_hai_ya_nahi)."""
    if is_indexed(project_id):
        return 0, True

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    chunks = [c for c in chunks if len(c.page_content.strip()) >= MIN_CHUNK_CHARS]
    chunks = chunks[:MAX_CHUNKS]

    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=collection_name(project_id),
        persist_directory=PERSIST_DIR,
    )
    return len(chunks), False