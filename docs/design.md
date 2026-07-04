# Q&A Agent Design Decisions

## Overview

The Q&A Agent CLI is meant help in answering questions about a file or a directory of files. The CLI should be simple and minimal where there is only three commands that it needs, not including the help command. These are:
- `--path`: used to select the path of the file or directory of files.
- `--question`: question that is asked about file(s)
- `--model`: (optional) used to select a LLM. If not used, the model defaults to gemma-4b-31b.

This is a bare bone application. For that reason the CLI commands where keep to a minimum. Also, this does not store conversation. It is a one-shot question and answer, and any following quesiton will not have knowledge of the previous ones. This design decision was done to, again, keep the CLI simple and minimal, with no need to add a complex database that stores history. Ideally, with enough context the one-shot question can be enough to give the right answer without any following questions being needed.

The application itself is separated into four distinct modules: `file_parser`, `formatter`, `llm`, and `main`.
-`file_parser`: Used to parse the input file(s) and convert them into a `dict[str]` data structure. This module should open the files one by one and read each content in chunks before appending to the data strucutre.
-`formatter`: This module takes the parsed file and input question and combines them into a correctly formatted prompt for the LLM. Also, the formatter is where the parsed file and question are validated to assure no missing files, questions, or junk input.
Formatted prompt: " You are going to be asked a question about file(s) inside the triple backticks. Respond clearly in no longer than a paragraph. Paragraph should have 15 character long lines before going to the next line. Following the response to the question, show the source or sources of the file in this way: Source: Filename.txt:line 1: 'preview text...'.The question is the following in parenthesis ({Question}) and the file(s) are ```{files}```"
-`llm`: This is the main API for the LLM. It is a class for the Q&A Agent that has the system_prompt, user_question, and model as attributes. Its single method is GetAnswer() which takes the prompt and sends it to the LLM through an API and recieves a response. The prompted question is given outside the file. This only has the system_prompt text, and all other attributes are inputted.
`main`: Is where the orchestration of all files occurs. It takes in the user inputs for the CLI commands and directs them to the `file_parser`, `formatter` and `llm` to give back a response in the terminal.


### Potential Ideas
- Command/functionality that takes the given question and a separate LLM from the Q&A one edits it to a better formatted question. Basically a Question Generator and a Q&A LLM.
- A system prompt optional command: could give user the ability to modify the system prompt to their needs.
- Add a DB and allow for a convesation style chatbot CLI.