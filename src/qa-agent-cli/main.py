import argparse
from pathlib import Path
from llm import QAAssistant
from models import UserQuestion, AgentResponse, SystemPrompt, Document, Model

def select_path(path: Path) -> Document:
    return Document(path=path)

def ask_question(question: str) -> UserQuestion:
    return UserQuestion(text=question)

def select_model(model: str) -> Model:
    model = Model.GEMMA_4_31B

    return model

def write_system_prompt(system_prompt: str) -> SystemPrompt:
    return SystemPrompt(text=system_prompt)

def main():
    sys_prompt = SystemPrompt()
    question = UserQuestion()
    model = Model.GEMMA_4_31B

    parser = argparse.ArgumentParser(
        description="Q&A Agent CLI - Will answer questions about any document, file, and/or notes."
    )
    
    parser.add_argument("path") # filepath or directorypath
    parser.add_argument("question")

    parser.add_argument("--model") 
    parser.add_argument("--system-prompt")

    args = parser.parse_args()

    if args.model:
        model = select_model(args.model)
    
    if args.system_prompt: #change system prompt
        sys_prompt = write_system_prompt(args.system_prompt)
    
    if args.question:# Need to combine doc and question and insert into context
        my_path = select_path(args.path)
        my_question = ask_question(args.question)
    
    QAAssistant(
        user_question=sys_prompt,
        system_prompt=question,
        model=model.value,
    )

if __name__ == "__main__":
    main()