# CLI entry point, wires everything 

import argparse
from pathlib import Path
import logging

def main():
    parser = argparse.ArgumentParser(description='Q&A bot for docs, files, notes, etc')
    parser.add_argument('dir_path', help='Directory Path with all files to add to context.')
    parser.add_argument('--role', help='Agent role')
    parser.add_argument('--context', help='Extra initial context to add to help the agent')
    parser.add_argument('--question', help='Question to ask')
    parser.add_argument('--model', default='claude-opus-4.6', help='LLM model to select' )

    args = parser.parse_args() 

    dir_path = Path(args.dir_path)
    if not dir_path.is_dir():
        logging.error("directory path does not exist.")


if __name__ == "__main__":
    main()