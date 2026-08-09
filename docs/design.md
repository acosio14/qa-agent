# Q&A Agent — Design

## Overview

The Q&A Agent is a small, stateless command-line tool that answers a single
question about a file or a directory of files. It is deliberately minimal: it
keeps no conversation history, so every invocation is a one-shot question and
answer with no memory of previous questions. This avoids the complexity of a
session store; the design bet is that, given enough retrieved context, a
well-formed one-shot question is usually enough to get a good answer.

Under the hood it runs a small retrieval-augmented pipeline:

```
files ──▶ parser ──▶ retriever ──▶ formatter ──▶ llm ──▶ answer
          (chunks)   (top-k)       (prompts)     (OpenRouter)
```

`main` orchestrates that pipeline, handles configuration and errors, and prints
the answer plus the model that produced it.

## CLI interface

```
qa-agent PATH QUESTION [--model ALIAS] [--log-level LEVEL] [--log-file FILE] [--version]
```

- `PATH` (positional) — a file or a directory of files to search.
- `QUESTION` (positional) — the question, in quotes.
- `--model` (optional) — a model alias; defaults to `gemma-4-31b`.
- `--log-level` — `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` (default `INFO`).
- `--log-file` — also write logs to a file.
- `--version` — print the version and exit.

`PATH` and `QUESTION` are positional (not flags) so the common case reads
naturally: `qa-agent ./docs "What is the deploy process?"`. The answer is
written to **stdout**; all logs and diagnostics go to **stderr**, so the answer
can be piped or captured cleanly.

## Modules

The application is split into single-responsibility modules under
`src/qa_agent_cli/`.

### `file_types`
Defines the shared data model as two pydantic dataclasses:

- `Chunk` — a unit of retrievable text: `filename`, `text`, and optional
  citation metadata (`line_num`, `page`, `section`).
- `ParsedFile` — one input file: `name`, `extension`, `raw_text`, its list of
  `chunks`, and an `ok`/`error` pair recording whether parsing succeeded.

### `parser`
Turns a path into `list[ParsedFile]`.

- Accepts a single file or a directory. In directory mode it skips hidden
  files, subdirectories, and unsupported extensions so incidental noise is not
  mistaken for a parse failure. Supported types: `.txt`, `.md`, `.docx`, `.pdf`.
- Uses **MarkItDown** to convert each file to Markdown text, then chunks it:
  by Markdown headers when present, otherwise by blank-line-separated
  paragraphs. Files under `CHUNK_SIZE_THRESHOLD_BYTES` are kept as a single
  chunk.
- **Failures are non-fatal.** A bad file (empty, unsupported, unreadable) is
  recorded as `ParsedFile(ok=False, error=...)` and logged as a warning, so one
  bad file never aborts a whole batch. A path that is neither a file nor a
  directory raises `FileNotFoundError`.

### `retriever`
Selects the most relevant chunks for the question using **BM25** lexical
ranking (`bm25s`).

- Flattens the chunks of all successfully parsed files into one corpus,
  tokenizes with English stopword removal, indexes, and retrieves the top `k`.
- Returns a NumPy array shaped `(1, k)` of chunk dicts, ranked best-first — the
  shape the formatter consumes.
- Robust to edge cases: `k` is clamped to the corpus size (asking for more
  chunks than exist returns all of them instead of raising), and an empty
  corpus (no files, only failed parses, or `k <= 0`) returns an empty `(1, 0)`
  array rather than crashing.

### `formatter`
Builds the `(system_prompt, user_prompt)` pair from the retrieved chunks.

- Each chunk is rendered as a **numbered, citable context block** —
  `[1] report.pdf (section Intro, page 3): <text>` — using whatever citation
  metadata is available. Numbering lets the model cite a specific block.
- Oversized chunk text is truncated to `MAX_CHUNK_CHARS` to protect the context
  window.
- The system prompt constrains the model to answer **only** from the provided
  context, to reply with a fixed "I don't know" string when the answer is
  absent, and to **treat the context as data, never as instructions** (a guard
  against prompt injection from untrusted file contents).
- Empty retrieval is surfaced to the model as "no context found" so it declines
  gracefully.

### `llm`
The interface to the language model, as the `QAAssistant` class. Its public
method `get_answer()` sends the prompts to **OpenRouter** and returns a
validated answer, with resilience built in (see below). After success it exposes
`answering_model` — the model that actually produced the answer, which may be a
fallback rather than the default.

### `main`
Orchestrates everything: parses arguments, configures logging, verifies the API
key, selects the model set, runs the pipeline, and prints the answer plus the
model that answered. All failure modes are converted into a clean message and a
meaningful exit code (see Error handling).

## Error handling & resilience

Resilience is concentrated in two places.

**LLM layer (`llm`).** Every error the OpenRouter client can raise is classified
into one of three strategies by severity:

- **RETRY** — transient failures (timeouts, 5xx, service unavailable). Retry the
  *same* model up to `MAX_RETRIES` (3) times with exponential backoff.
- **REROUTE** — model/provider-specific failures (rate limit, provider
  overloaded, model not found, malformed response). Move on to the next model.
- **FAIL** — unrecoverable client/account errors (bad key, out of credits,
  malformed request, payload too large). Stop immediately; retrying cannot help.

`get_answer()` tries the default model, then each fallback, applying these
strategies. Every response is **validated** before it is returned — it must have
a choice, an acceptable finish reason (not `content_filter`/`error`), no refusal,
and non-empty content — otherwise it fails immediately. If all models are
exhausted, a single `QAAssistantError` is raised carrying the last error. The
model catalog lives in `main` as `FREE_MODELS`; fallbacks are all models other
than the selected default.

**CLI layer (`main`).** The pipeline runs inside a `try/except` that turns each
failure into a friendly stderr message and an exit code, rather than a traceback:

| Exit code | Meaning |
|-----------|---------|
| `0` | Success |
| `1` | Could not answer (`QAAssistantError`), unreadable path, or unexpected error |
| `2` | Configuration error (missing API key, unknown `--model`) |
| `130` | Interrupted (Ctrl-C) |

## Configuration & secrets

The agent requires an OpenRouter API key, read from the `OPENROUTER_API_KEY`
environment variable. For convenience a `.env` file in the **current working
directory** is loaded on startup (via `find_dotenv(usecwd=True)`), so the key is
picked up where the user runs the command, not next to the installed package.
`main` performs a **preflight check**: if no key is available it prints a clear
message pointing to where to get one and exits with code `2`, instead of letting
the first request fail with a cryptic auth error. Secrets are never committed —
`.env` is gitignored and a `.env.example` template documents the variable.

## Logging

Logging goes through the standard `logging` module. `main` configures it to
write to **stderr** (keeping stdout for the answer), with an optional file
handler via `--log-file` and a level via `--log-level`. Library modules use
named module loggers, so output can be filtered per module. The `llm` layer logs
each attempt and the retry/reroute decision, which makes a failed run traceable.

## Packaging & deployment

The project is a standard installable Python package (hatchling build backend,
`src/` layout) that exposes a **`qa-agent` console command** via a
`console_scripts` entry point — so users run `qa-agent`, not
`python -m ...`. It is distributed from its Git repository and installed with
`uv tool install` or `pipx`. Dependencies are declared explicitly and kept to
what is actually imported (`bm25s`, `numpy`, `openrouter`, `pydantic`,
`python-dotenv`, and `markitdown` with its `docx`/`pdf` extras).

## Testing

Each module has a unit-test suite under `tests/unit/` following an
Arrange/Act/Assert structure. The `llm` tests script a fake transport to verify
the retry/reroute/fail control flow and response validation without network
access; the `retriever` tests exercise real BM25 ranking on small corpora; the
`formatter` and `parser` tests assert their output contracts and edge cases.

## Data & privacy

This is a client for a third-party LLM service: the relevant chunk(s) of the
user's files and their question are sent to OpenRouter and the selected model
provider to generate an answer. The tool itself stores nothing beyond the
printed answer (and logs, if a log file is enabled).

## Future ideas

- A question-rewriting step (a separate LLM that reformulates the user's
  question before retrieval/answering).
- An optional flag to let the user override the system prompt.
- Populate `line_num`/`page` during parsing so citations can point to exact
  locations.
- A size-based chunk splitter, so large unstructured files (no headers or blank
  lines) are not collapsed into one oversized, truncated chunk.
- Allow arbitrary OpenRouter model IDs via `--model`, not just the built-in
  aliases.
- Optionally add conversational history (a datastore) to move beyond one-shot.
