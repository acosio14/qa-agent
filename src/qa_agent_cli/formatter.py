# take the clean content and wrap it in the envelope for the model
# Add the tags, the path, the truncation notice
# Produce the final string

def format(files: dict[str], question: str) -> str:
    for file in files:
        if file == "":
            raise FileNotFoundError("File has no content. Empty value.")

    return files, question