import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Q&A bot for docs, files, notes, etc')
    parser.add_argument('dir_path', help='Directory Path with all files to add to context.')
    parser.add_argument('--role', help='Agent role')
    parser.add_argument('--context', help='Extra initial context to add to help the agent')
    parser.add_argument('--question', help='Question to ask')

    args = parser.parse_args() 

    Path(args.dir_path)    

if __name__ == "__main__":
    main()