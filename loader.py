import hashlib
import os
import re
import shutil
import stat
import tempfile

from langchain_core.documents import Document

ALLOWED_EXT = {".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx",
               ".json", ".yaml", ".yml", ".toml", ".java", ".cpp", ".c"}
SKIP_DIRS = {".git", "node_modules", "venv", "env", ".venv", "__pycache__",
             "dist", "build", ".next", "chroma.db"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "poetry.lock"}
MAX_FILES = 60
MAX_FILE_BYTES = 100_000


def load_readme_file(uploaded):
    """st.file_uploader ka object lo."""
    text = uploaded.getvalue().decode("utf-8", errors="ignore")
    pid = "upload:" + hashlib.md5(text.encode()).hexdigest()[:12]
    return [Document(page_content=text, metadata={"source": uploaded.name})], pid


def load_pasted_text(text):
    pid = "paste:" + hashlib.md5(text.encode()).hexdigest()[:12]
    return [Document(page_content=text, metadata={"source": "pasted_text"})], pid


def parse_github_url(url):
    m = re.match(r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", url.strip())
    if not m:
        raise ValueError("Sahi GitHub repo link daalo, jaise https://github.com/user/repo")
    return m.group(1), m.group(2)


def _priority(path):
    name = path.lower().split("/")[-1]
    if name.startswith("readme"):
        return 0
    if name.endswith(".md"):
        return 1
    if name in ("requirements.txt", "package.json", "pyproject.toml"):
        return 2
    return 3


def collect_files(folder):
    found = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext not in ALLOWED_EXT or name in SKIP_FILES:
                continue
            full = os.path.join(root, name)
            try:
                if os.path.getsize(full) > MAX_FILE_BYTES:
                    continue
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            if not text.strip():
                continue
            rel = os.path.relpath(full, folder).replace("\\", "/")
            found.append(Document(page_content=text, metadata={"source": rel}))
    found.sort(key=lambda d: _priority(d.metadata["source"]))  # README pehle
    return found[:MAX_FILES]


def _force_remove(func, path, exc):
    # Windows par .git ki files read-only hoti hain, isliye ye zaroori hai
    os.chmod(path, stat.S_IWRITE)
    func(path)


def load_github_repo(url):
    from git import Repo  # pip install gitpython (git bhi installed hona chahiye)

    owner, repo = parse_github_url(url)
    tmp = tempfile.mkdtemp()
    try:
        Repo.clone_from(
            f"https://github.com/{owner}/{repo}.git", tmp,
            depth=1, env={"GIT_TERMINAL_PROMPT": "0"},
        )
        docs = collect_files(tmp)
    finally:
        shutil.rmtree(tmp, onexc=_force_remove)
    if not docs:
        raise ValueError("Is repo mein padhne layak files nahi mili.")
    return docs, f"github:{owner}/{repo}"