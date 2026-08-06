# take the clean content and wrap it in the envelope for the model
# Add the tags, the path, the truncation notice
# Produce the final string

def format(chunks: list[dict[str]], question: str, model: str) -> tuple[str, str]:

    for chunk in chunks[0]:
        filename = chunk["filename"]
        text = chunk["text"]
        section = chunk["section"]

        # Create formated chunk with text, filename, and section.
        formatted_chunk = f"Chunk Text: {text}, file: {filename}"
        if section != "" or section != None:
            formatted_chunk = formatted_chunk + f", section: {section}"

    system_prompt: str = (
        "You are a helpful and articulate Q&A assistant. "
        "You take in one or multiple files chunks. "
        "You only answer questions based on the chunks provided. "
        "If you can't find and source the documents, you politely "
        "tell user 'I don't know', 'Answer not in docs', etc. "
        "When giving an answer, always look for the information in the "
        "file chunks and attempt to give a citation or explicit location/source."
    )

    user_prompt = (
        f"Given file chunk inside the brackets [{chunks}]. "
        f"Concisely answer the question inside the triple ticks."
        f"The response should be less than or equal to 2 to 3 sentences. "
        f"You are using the llm in parentheses ({model.split(':')[0]}). "
        f"```{question}```"
        f"The response should be formatted in the following way: "
        f"Answer: <RESPONSE HERE>.\n"
        f"Model: <MODEL HERE>\n"
    )
    return system_prompt, user_prompt