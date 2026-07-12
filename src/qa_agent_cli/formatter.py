
def format(files: dict[str], question: str) -> str:
    for file in files:
        if file == "":
            raise FileNotFoundError("File has no content. Empty value.")

    prompt_files = f"Files: ```{files}```"
    prompt_question = f"Question: ```{question}```"

    print(prompt_files + "\n" + prompt_question)
    
    prompt = (
        f"You are given the following files inside the brackets [{files}]."
        f"Concisely answer the following question in triple ticks ```{question}``."
        f"The response should be less than or equal to 2 to 3 sentences."
        f"The response should be formatted in the following way:"
        f"Answer: <RESPONSE HERE>."
        f"Model: <MODEL USED HERE>"
    )
    return prompt