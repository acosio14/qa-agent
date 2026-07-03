import argparse
from pathlib import Path
import file_parser, formatter, llm

def main():
    parser = argparse.ArgumentParser(
        description="Q&A Agent - Will answer questions about any file."
    )

    parser.add_argument("path") # filepath or dir_path
    parser.add_argument("question")
    parser.add_argument("--model") #optional

    args = parser.parse_args()
    
    free_models = {
        "gemma-4-31b": "google/gemma-4-31b-it:free", 
        "minstral_7b": "minstralai/mistral-7b-instruct:free"
    }
    model = free_models["gemma-4-31b"]
    if args.model:
        model = free_models.get(args.model)

    dict_variable = file_parser.parse(args.path)
    formatted_question = formatter.format(dict_variable, args.question)
    llm.QAAssistant(formatted_question, model).GetAnswer()
    


if __name__ == "__main__":
    main()