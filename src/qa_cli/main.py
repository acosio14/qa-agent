import argparse
import logging
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import parser as file_parser
from . import formatter, llm, retriever

logger = logging.getLogger("qa_cli")

try:
    __version__ = version("qa-cli")
except PackageNotFoundError:  # running from source without an install
    __version__ = "0.1.0"

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# All logs go to a file (never the terminal), so stdout stays clean for the
# answer. Override the location with --log-file.
DEFAULT_LOG_FILE = Path.home() / ".qa-cli" / "qa-cli.log"

API_KEY_ENV = "OPENROUTER_API_KEY"

# Selectable models, keyed by the short alias accepted via --model.
FREE_MODELS = {
    "gemma-4-31b": "google/gemma-4-31b-it:free",
    "gemma-4-26b": "google/gemma-4-26b-a4b-it:free",
    "gpt-oss-120": "openai/gpt-oss-120b:free",
    "gpt-oss-20b": "openai/gpt-oss-20b:free",
    "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nemotron-3-nano-omni": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
}
DEFAULT_MODEL_ALIAS = "gemma-4-31b"

RETRIEVAL_K = 1  # number of chunks retrieved to build the context


def resolve_models(model_alias: str | None) -> tuple[str, list[str]]:
    """Return ``(default_model, fallback_models)`` for the given alias.

    ``model_alias`` is the value passed via ``--model`` (or ``None`` for the
    built-in default). Fallbacks are every other model, so the default is never
    listed as its own fallback. Raises ``ValueError`` for an unknown alias.
    """
    if model_alias is None:
        default_model = FREE_MODELS[DEFAULT_MODEL_ALIAS]
    elif model_alias in FREE_MODELS:
        default_model = FREE_MODELS[model_alias]
    else:
        raise ValueError(
            f"unknown model '{model_alias}'. Choose from: {', '.join(FREE_MODELS)}"
        )

    fallback_models = [m for m in FREE_MODELS.values() if m != default_model]
    return default_model, fallback_models


def run_pipeline(
    path: str, question: str, default_model: str, fallback_models: list[str]
) -> tuple[str, str | None]:
    """Run parse -> retrieve -> format -> answer, returning (answer, model).

    This is the CLI-free core: it takes plain inputs and returns the answer plus
    the model that actually produced it. It raises ``QAAssistantError`` or file
    errors on failure; the caller is responsible for turning those into exit
    codes and user-facing messages.
    """
    logger.info("Parsing input path: %s", path)
    parsed_files = file_parser.parse(path)

    logger.info("Retrieving top chunks for the question")
    top_k_chunks = retriever.retrieve_top_k_chunks(parsed_files, question, k=RETRIEVAL_K)

    system_prompt, user_prompt = formatter.format_prompts(top_k_chunks, question)

    logger.info(
        "Asking model (default=%s, %d fallbacks available)",
        default_model, len(fallback_models),
    )
    assistant = llm.QAAssistant(system_prompt, user_prompt, default_model, fallback_models)
    answer = assistant.get_answer()
    return answer, assistant.answering_model


def _configure_logging(level: str, log_file: str | None) -> None:
    """Route all logs to a file, keeping the terminal clean.

    Nothing is logged to the terminal: stdout carries only the answer, and the
    caller prints any user-facing error to stderr. Logs (ours and third-party
    libraries') go solely to ``log_file`` — defaulting to ``DEFAULT_LOG_FILE``.
    """
    path = Path(log_file) if log_file else DEFAULT_LOG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(path, delay=True)],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="qa-cli",
        description="Q&A CLI — answer a question about a file or directory of files.",
        epilog='Example:\n  qa-cli ./docs "What is the deployment process?"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path",
        metavar="PATH",
        help="File or directory of files to search (.txt, .md, .docx, .pdf).",
    )
    parser.add_argument(
        "question",
        metavar="QUESTION",
        help="The question to answer, in quotes.",
    )
    parser.add_argument(
        "--model",
        metavar="ALIAS",
        help=f"Model to use (default: {DEFAULT_MODEL_ALIAS}). "
        f"One of: {', '.join(FREE_MODELS)}.",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=LOG_LEVELS, help="Default: INFO."
    )
    parser.add_argument(
        "--log-file",
        metavar="FILE",
        help=f"Write logs to this file (default: {DEFAULT_LOG_FILE}).",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    _configure_logging(args.log_level, args.log_file)

    # Fail fast with a clear message if the API key is missing, rather than
    # letting the first request fail with a cryptic auth error.
    if not os.getenv(API_KEY_ENV):
        logger.error("%s is not set", API_KEY_ENV)
        print(
            f"Error: {API_KEY_ENV} is not set.\n"
            "Get a key at https://openrouter.ai/keys, then either export it:\n"
            f"  export {API_KEY_ENV}=sk-or-...\n"
            "or add it to a .env file in this directory (see .env.example).",
            file=sys.stderr,
        )
        return 2

    try:
        default_model, fallback_models = resolve_models(args.model)
    except ValueError as e:
        logger.error("%s", e)
        parser.error(str(e))  # prints usage + message, exits with code 2

    try:
        answer, answering_model = run_pipeline(
            args.path, args.question, default_model, fallback_models
        )
    except llm.QAAssistantError as e:
        logger.error("The model pipeline could not produce an answer: %s", e)
        print(f"Sorry, I couldn't answer that: {e}", file=sys.stderr)
        return 1
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        logger.error("Problem reading the input path '%s': %s", args.path, e)
        print(f"Error: could not read '{args.path}': {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        print("\nCancelled.", file=sys.stderr)
        return 130
    except Exception as e:  # last-resort safety net
        logger.exception("Unexpected error while answering the question")
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1

    print(answer)
    print(f"Model: {answering_model}")
    logger.info("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
