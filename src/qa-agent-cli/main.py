import argparse
from pathlib import Path

def select_path(path: Path) -> None:
    ...

def ask_question(question: str) -> None:
    ...

def select_model(model: str) -> None:
    ...

def write_system_prompt(system_prompt: str) -> None:
    ...

def main():
    parser = argparse.ArgumentParser(description="Q&A Agent CLI - Will answer questions about any document, file, and/or notes.")
    
    parser.add_argument("path") # filepath or directorypath
    parser.add_argument("question")

    parser.add_argument("--model") 
    parser.add_argument("--system-prompt")

    args = parser.parse_args()

    if args.model:
        select_model(args.model)
    
    if args.system_prompt: #change system prompt
        write_system_prompt(args.system_prompt)
    
    if args.question:
        select_path(args.path)
        ask_question(args.question)

if __name__ == "__main__":
    main()