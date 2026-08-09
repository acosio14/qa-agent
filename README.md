# Q&A Agent CLI

A stateless Q&A agent that answers questions about a given set of files, docs, and/or
notes. It is a simple one-shot agent: it doesn't store conversations and answers one
question at a time with no memory of previous questions.

Under the hood it parses your file(s) into chunks, retrieves the most relevant chunk
with BM25, and asks an LLM (via [OpenRouter](https://openrouter.ai)) to answer using
only that context — with automatic retry/fallback across models.

## About this project

- **Why I built it:** The idea behind this project was to learn and get experience building a tool that works with an LLM. I wanted to see how to set up a proper API call to an LLM and give it the right context so it returns adequate responses. It exposed me to the full flow of parsing a file, chunking it, formatting it, and sending it to an LLM.
- **What I wanted to practice:** I mainly wanted to practice building AI API calls and everything that comes with setting up a proper prompt so the model answers correctly. I also wanted to add proper guardrails and error handling to deal with the non-deterministic issues that LLMs have, and to build a complete, near-production application to get the full experience of putting a real tool together.
- **How I built it:** I started by splitting the tool into parsing, retrieving, formatting, and llm — each part with one specific job. Together they form a pipeline that takes a user's input and returns a proper response. I worked from scratch in the initial phase and used Claude (the chatbot) to help me understand the conceptual details of how a CLI AI agent should work. Once the structure was in place, I used Claude Code (Opus 4.8) to help clean up the codebase, fix bugs, and turn it into a deployable tool.
- **Known limitations:** The application is intentionally simple and not production-grade. It uses basic parsing and retrieval on purpose, to keep things straightforward and get a basic understanding of an end-to-end system. To improve it, I'd implement a true RAG system that uses embeddings and semantic search to retrieve the relevant content.

For the technical rationale behind the design (module layout, error-handling
strategy, trade-offs), see [docs/design.md](docs/design.md).

## Requirements

- Python >= 3.12
- An [OpenRouter API key](https://openrouter.ai/keys)

## Install

The project is distributed via this Git repository (not yet published to PyPI).

Install straight from GitHub with [uv](https://docs.astral.sh/uv/) (recommended) —
this exposes a global `qa-agent` command:

```bash
uv tool install "git+https://github.com/<owner>/qa-agent"
```

Or with pipx:

```bash
pipx install "git+https://github.com/<owner>/qa-agent"
```

From a local clone:

```bash
git clone https://github.com/<owner>/qa-agent
cd qa-agent
uv tool install .        # install the command
# or: uv sync            # dev setup (project + dev deps in a venv)
```

## Configure

The agent needs an OpenRouter API key. Either export it:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

...or copy the template and fill it in (the CLI loads `.env` from the working directory):

```bash
cp .env.example .env
# then edit .env
```

## Usage

```bash
qa-agent <path> "<question>" [--model ALIAS] [--log-level LEVEL] [--log-file FILE]
```

- `path` — a file or a directory of files to search (`.txt`, `.md`, `.docx`, `.pdf`).
- `question` — the question to answer, in quotes.
- `--model` — optional model alias (see below). Defaults to `gemma-4-31b`.
- `--log-level` — `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` (default `INFO`); logs go to stderr.
- `--log-file` — also write logs to this file.

Example:

```bash
qa-agent ./docs "What is the deployment process?"
```

The answer is printed to stdout; diagnostics go to stderr, so you can safely pipe or
capture just the answer.

### Model aliases

`gemma-4-31b` (default), `gemma-4-26b`, `gpt-oss-120`, `gpt-oss-20b`,
`nemotron-3-ultra`, `nemotron-3-nano-omni`.

If the chosen model is rate-limited or unavailable, the agent automatically falls back
to the others and reports which model actually answered.

## Data & privacy

This tool is a client for a third-party LLM service. When you ask a question, the
**relevant chunk(s) of your file(s) and your question are sent to OpenRouter and the
selected model provider** to generate the answer. Do not point it at files you are not
comfortable sending to those services. Nothing is stored by this tool itself — it keeps
no history and writes nothing beyond the answer (and logs, if you enable a log file).

## Costs & rate limits

The default models are OpenRouter **free** tiers, which have per-day rate limits; when
one is exhausted the agent falls back to the others. Selecting a non-free model with
`--model` may incur charges on your OpenRouter account. See
[OpenRouter pricing](https://openrouter.ai/models) for details.

## Development

Run the test suite:

```bash
uv run pytest
```
