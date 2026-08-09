# Q&A Agent CLI

A stateless Q&A agent that answers questions about a given set of files, docs, and/or
notes. It is a simple one-shot agent: it doesn't store conversations and answers one
question at a time with no memory of previous questions.

Under the hood it parses your file(s) into chunks, retrieves the most relevant chunk
with BM25, and asks an LLM (via [OpenRouter](https://openrouter.ai)) to answer using
only that context — with automatic retry/fallback across models.

## Requirements

- Python >= 3.12
- An [OpenRouter API key](https://openrouter.ai/keys)

## Install

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
# Install as a global tool, exposing the `qa-agent` command
uv tool install .

# ...or run without installing
uvx --from . qa-agent --help
```

Using pip:

```bash
pip install .
```

For local development (installs the project plus dev dependencies into a venv):

```bash
uv sync
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

## Development

Run the test suite:

```bash
uv run pytest
```
