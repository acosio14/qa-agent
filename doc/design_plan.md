# Flow

1. Setup environment variables
2. Load files / format / store in memory
3. User asks question
4. Extract content from files
5. Create Prompt / Send to LLM
6. Send message prompt to Claude Model
7. Return Answer 


# Development Plan

- LLM file and Claude SDK
- Load File / formatter / store in memory
    - File format: Markdown
    - Data types:
        - Section: source_path, heading, heading_path, content
- Content Extractor
- Agent control loop/orchestration
- System prompt
- Main / CLI argsparser
