
### Overview

This is a Python script designed to read git diff output and leverage Ollama to generate commit messages for each file. When you run this script, commits will be automatically created for all staged files.

### Installation

- [Python Ollama](https://github.com/ollama/ollama-python) 
- [Olama Server](https://ollama.com/download)
- [Ollama Model](https://ollama.com/library/gemma3)

This script currently uses the `gemma3:4b` model.

### Usage

Place the `auto_commit.py` file in the root directory of your project.
If ollama server is running, run the script using the command

```
python3 auto_commit.py
```

### Miscellaneous

Contributions and ideas are welcome, such as:

- Modifying the prompt, model, or LLM provider.

- Generating commit messages for individual files or a single message for all files.
