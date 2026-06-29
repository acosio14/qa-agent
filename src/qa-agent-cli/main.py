import argparse

def main():
    parser = argparse.ArgumentParser(description="Q&A Agent CLI - Will answer questions about any document, file, and/or notes.")
    
    parser.add_argument("path") # filepath or directorypath
    parser.add_argument("question")

    parser.add_argument("--model") 
    parser.add_argument("--system-prompt")

if __name__ == "__main__":
    main()