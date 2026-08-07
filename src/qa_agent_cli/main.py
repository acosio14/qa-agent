import argparse
from pathlib import Path
import parser as file_parser
import formatter, llm, retriever

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
    default_model = free_models["gemma-4-31b"]
    fallback_models = list(free_models.values())[1:]
    if args.model:
        default_model = free_models.get(args.model)

    parsed_files = file_parser.parse(args.path)
    top_k_chunks = retriever.retrieve_top_k_chunks(parsed_files, args.question, k=1)
    system_prompt, user_prompt = formatter.format(top_k_chunks, args.question, default_model)
    response = llm.QAAssistant(system_prompt, user_prompt, default_model, fallback_models).GetAnswer()

    print(response)
    


if __name__ == "__main__":
    main()