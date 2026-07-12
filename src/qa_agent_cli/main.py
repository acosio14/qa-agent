import argparse
from pathlib import Path
import file_parser, formatter, llm

def main():
    parser = argparse.ArgumentParser(
        description="Q&A Agent - Will answer questions about any file."
    )

    parser.add_argument("path", type=str) # filepath or dir_path
    parser.add_argument("question", type=str)
    parser.add_argument("--model") #optional

    args = parser.parse_args()
    
    free_models = {
        "gemma-4-31b": "google/gemma-4-31b-it:free",
        "gemma-4-26b": "google/gemma-4-26b-a4b-it:free",
        "gpt-oss-120": "openai/gpt-oss-120b:free",
        "gpt-oss-20b": "openai/gpt-oss-20b:free",
        "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "nemotron-3-nano-omni": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    }
    model = free_models["gemma-4-31b"]
    if args.model:
        model = free_models.get(args.model)

    files_dict = file_parser.parse(args.path)
    files, question = formatter.format(files_dict, args.question)
    response = llm.QAAssistant(files, question, model).GetAnswer()

    print(response)
    


if __name__ == "__main__":
    main()