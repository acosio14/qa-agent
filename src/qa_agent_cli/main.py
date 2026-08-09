import argparse
import logging
import os
import sys
from importlib.metadata import PackageNotFoundError, version

from . import parser as file_parser
from . import formatter, llm, retriever

logger = logging.getLogger("qa_agent")

try:
    __version__ = version("qa-agent")
except PackageNotFoundError:  # running from source without an install
    __version__ = "0.1.0"

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

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


def _configure_logging(level: str, log_file: str | None) -> None:
    """Send logs to stderr (and optionally a file), keeping stdout for the answer."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="qa-agent",
        description="Q&A Agent — answer a question about a file or directory of files.",
        epilog='Example:\n  qa-agent ./docs "What is the deployment process?"',
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
    parser.add_argument("--log-file", help="Also write logs to this file.")
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

    default_model = FREE_MODELS[DEFAULT_MODEL_ALIAS]
    fallback_models = [m for m in FREE_MODELS.values() if m != default_model]
    if args.model:
        if args.model not in FREE_MODELS:
            logger.error("Unknown model requested: %s", args.model)
            parser.error(
                f"unknown model '{args.model}'. Choose from: {', '.join(FREE_MODELS)}"
            )
        default_model = FREE_MODELS[args.model]
        fallback_models = [m for m in FREE_MODELS.values() if m != default_model]

    try:
        logger.info("Parsing input path: %s", args.path)
        parsed_files = file_parser.parse(args.path)

        logger.info("Retrieving top chunks for the question")
        top_k_chunks = retriever.retrieve_top_k_chunks(parsed_files, args.question, k=1)

        system_prompt, user_prompt = formatter.format_prompts(
            top_k_chunks, args.question
        )

        logger.info(
            "Asking model (default=%s, %d fallbacks available)",
            default_model, len(fallback_models),
        )
        assistant = llm.QAAssistant(
            system_prompt, user_prompt, default_model, fallback_models
        )
        response = assistant.get_answer()

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

    print(response)
    print(f"Model: {assistant.answering_model}")
    logger.info("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
