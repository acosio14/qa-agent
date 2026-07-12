
def format(files: dict[str], question: str) -> str:
    for file in files:
        if file == "":
            raise FileNotFoundError("File has no content. Empty value.")
    # Something to think about:
    # I could place this prompt inside llm.py instead.
    # In llm.py I would have to pass in files as well as question.
    # Here in formatter.py I could simply format the files and question correctly.
    # Basically validate and clean them up for the llm.
    # Then pass them to llm and insert them in the prompt

    return files, question