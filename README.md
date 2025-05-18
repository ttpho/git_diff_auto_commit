
### Overview

This is a Python script designed to read git diff output and leverage Ollama to generate commit messages for each file. When you run this script, commits will be automatically created for all staged files.

<img src="https://github.com/user-attachments/assets/f39344db-10c5-4dbc-a3e6-2ce275d52004" />

### Installation

- [Olama](https://ollama.com/download)

- [Ollama Model](https://ollama.com/library/gemma3)

This script currently uses the `gemma3:4b` model.

```
ollama run gemma3:4b
```

- [Python Ollama](https://github.com/ollama/ollama-python) 
```
pip install ollama
```

### Usage

Place the `auto_commit.py` file in the root directory of your project.
If ollama server is running, run the script using the command

```
python3 auto_commit.py
```

Create a commit for each file. 

```
python3 auto_commit.py single_file
```



### Miscellaneous

Contributions and ideas are welcome, such as:

- Modifying the prompt, model, or LLM provider.

- Generating commit messages for individual files or a single message for all files.
