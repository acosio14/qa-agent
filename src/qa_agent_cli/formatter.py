
def format(files: dict[str], question: str) -> str:
    for file in files:
        if file == "":
            raise FileNotFoundError("File has no content. Empty value.")

    prompt_files = f"Files: ```{files}```"
    prompt_question = f"Question: ```{question}```"

    print(prompt_files + "\n" + prompt_question)

    return prompt_files + prompt_question