# Control loop, prompt building, orchestration

class QAAgent():
    def __init__(self, model, dir_path):
        self.model = model
        self.dir_path = dir_path

    # Both create_role and create_context can parse the files and come up with
    # a role and context to give to the LLM
    def _create_role(self):
        ...

    def _create_context(self):
        ...   

    # With the created role, context, and given question,
    # combines them into a messages and sends it to llm class?
    # which should hold the various models? Or do I need a repo?
    def create_prompt(self, role, context, question):
        ...