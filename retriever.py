from store import get_store


def get_chunks(question, project_id, k=3):
    return get_store(project_id).similarity_search(question, k=k)


def getcontext(question, project_id, k=3):
    chunks = get_chunks(question, project_id, k)
    return "\n\n".join(
        f"[{c.metadata.get('source', '?')}]\n{c.page_content}" for c in chunks
    )