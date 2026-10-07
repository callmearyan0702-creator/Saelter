# Saelter: AI Interview Bot

A RAG-based mock interview chatbot for students. Give it your project (a README file, pasted text, or a GitHub repo link) and it interviews you about **your own code and design decisions**, then gives feedback on each answer.

Most mock interview tools ask generic questions. Saelter reads your project first, so every question is grounded in what you actually built.

<!-- Add a screenshot or GIF here: ![Saelter demo](docs/demo.png) -->

## How it works

```
Your project (README / pasted text / GitHub link)
        |
        v
  Load + filter files  ->  Chunk  ->  Embed  ->  Chroma vector store
                                                       |
   Topic (e.g. "database and storage")  -------------> Retrieve top chunks
                                                       |
                                                       v
                         LLM asks ONE question using only the retrieved text
                                                       |
                         You answer  ->  LLM compares your answer with the
                         project text, gives feedback + moves to next question
```

1. **Load**: reads an uploaded README, pasted text, or shallow-clones a public GitHub repo.
2. **Filter**: keeps useful files only (docs, config, source code), skips `.git`, `node_modules`, virtual envs, lock files and large files, and caps the number of files.
3. **Chunk + embed**: splits text into chunks and embeds them locally with `all-MiniLM-L6-v2`.
4. **Store**: saves chunks in Chroma, one collection per project so projects never mix. Re-loading the same project skips embedding (cached).
5. **Interview**: for each topic, retrieves relevant chunks and asks the LLM for one question, restricted to the retrieved text. If there isn't enough information, it says so instead of inventing something.
6. **Feedback**: your answer is compared with the same retrieved text, followed by the next question.

## Features

- Three input modes: README upload, pasted text, public GitHub repo link
- Continuous chat: answer, get feedback, next question, automatically
- Questions and feedback grounded in your project text (source file names are passed to the LLM)
- Per-project vector collections and caching to avoid re-embedding
- Progress and timing shown while a project is being indexed
- Free to run: local embeddings plus a free-tier LLM API key

## Tech stack

| Part | Tool |
|---|---|
| Orchestration | LangChain (core, text-splitters) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (runs locally) |
| Vector store | Chroma |
| LLM | Google Gemini via `langchain-google-genai` |
| UI | Streamlit |
| Repo fetching | GitPython |

## Project structure

```
app.py          # Streamlit UI and chat loop
loader.py       # README upload, pasted text, GitHub clone, file filtering
store.py        # chunking, embeddings, Chroma collections, caching
retriever.py    # retrieves chunks/context for a topic
interviewer.py  # prompts: ask a question, evaluate an answer
.env.example    # template for your API key
```

## Setup

You need Python 3.10+ and `git` installed (git is required for the GitHub link feature).

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv env
# Windows (cmd):   env\Scripts\activate
# Mac/Linux:       source env/bin/activate

pip install -r requirements.txt

cp .env.example .env      # Windows: copy .env.example .env
# open .env and add your GOOGLE_API_KEY (free key from Google AI Studio)

streamlit run app.py
```

The first run downloads the embedding model, so it will be slow once.

## Usage

1. In the sidebar, load your project: upload a README, paste text, or enter a public GitHub repo link.
2. Click **Start interview**.
3. Answer in the chat box. You get feedback, then the next question.
4. Click **New interview** to reset the chat.

## Configuration

Tweak these constants to trade speed against coverage:

| Setting | File | What it controls |
|---|---|---|
| `MAX_FILES`, `MAX_FILE_BYTES` | `loader.py` | How many files and how large each can be |
| `ALLOWED_EXT`, `SKIP_DIRS` | `loader.py` | Which files are read |
| `MAX_CHUNKS`, `MIN_CHUNK_CHARS` | `store.py` | Embedding workload and junk-chunk filtering |
| `chunk_size`, `chunk_overlap` | `store.py` | Chunk granularity |
| `TOPICS` | `app.py` | Topics the interviewer cycles through |
| `MODEL_NAME` | `interviewer.py` | Which Gemini model is used (names change often, check Google AI Studio) |

## Known limitations

- **Free-tier quota.** Each answer uses two LLM calls (feedback plus next question). Free API tiers have daily limits, so long sessions can hit a rate-limit error.
- **Fixed topic list.** Topics are generic and suit software projects. They are not yet generated from the project itself.
- **Retrieval quality depends on chunking.** README files with many headings and separators can produce tiny, low-value chunks. Header-aware splitting is on the to-do list.
- **Feedback quality depends on the LLM and prompt.** Treat it as practice, not as ground truth.
- **Public repos only.** Private repositories are not supported.
- **Large repos are truncated** by the file and chunk limits.

## Roadmap

- [ ] Voice input (speech-to-text) and optional spoken questions
- [ ] Header-aware Markdown chunking
- [ ] Topics generated from the project instead of a fixed list
- [ ] Combine feedback and next question into one LLM call to save quota
- [ ] Support for private repos and uploaded folders/zips
- [ ] Deployment (Streamlit Community Cloud or similar)

## What I learned

*(Rewrite these in your own words before publishing.)*

- Chunking decisions affect retrieval more than expected: tiny heading-only chunks ranked above the chunk that actually answered the question.
- Vector search always returns something, even when nothing relevant exists, so the prompt needs an explicit "not enough information" exit.
- Keep the retrieved context from the question step and reuse it when evaluating the answer, so both steps see the same evidence.
- Separate "build once" (ingestion) from "use many times" (retrieval) to keep the app fast, and give each project its own collection.
- LLM model names, response formats and free-tier limits change often, so keep them in one place and handle errors in the UI.

## Security notes

- Never commit `.env`. It is listed in `.gitignore`; use `.env.example` as a template.
- If an API key is ever pushed by mistake, revoke and regenerate it immediately.

## License

Add a license of your choice (for example MIT).
