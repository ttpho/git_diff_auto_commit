import subprocess
from ollama import chat
from ollama import ChatResponse

model = "gemma3:4b"
prompt = f"""
Given the following Git diff and the list of changed files (with file types), suggest a single concise and relevant commit message that best summarizes all the changes made. Use a conventional commit style (e.g., feat:, fix:, chore:, docs:, refactor:). The message should be no longer than 72 characters.
Just return the commit messages without any additional text or explanation, without any Markdown formatting.
Input:
    Git Diff:
        [Git Diff]

    Changed Files and Types:
        [Changed Files and Types]

Instructions:
    1. Analyze the diff and the list of changed files/types.
    2. Summarize all changes into a single logical commit.
    3. Write a concise commit message (max 72 characters) in the conventional commit style
"""

def get_changed_files():
    # Git add all 
    subprocess.run(
        ["git", "add", "."],
        capture_output=True, text=True
    )
    # Get all staged and unstaged files (excluding untracked)
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True
    )
    unstaged = set(result.stdout.splitlines())
    result = subprocess.run(
        ["git", "diff", "--name-only", "--staged"],
        capture_output=True, text=True
    )
    staged = set(result.stdout.splitlines())
    # Union of both sets
    return sorted(unstaged | staged)

def get_diff_for_file(filename, staged=False):
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    cmd.append("--")
    cmd.append(filename)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def get_commit_messages(diff, files):
    # Use the Ollama chat model to get commit messages
    if len(diff) == 0 or len(files) == 0:
        return ""
    try:
        response: ChatResponse = chat(model=model, messages=[
        {
            'role': 'user',
            'content': prompt.replace("[Git Diff]", diff).replace("[Changed Files and Types]", files),
        },
    ])
        return response['message']['content']
    except Exception:
        return ""
    
def diff_single_file(file): 
    commit_messages = []
    unstaged_diff = get_diff_for_file(file, staged=False).strip()
    staged_diff = get_diff_for_file(file, staged=True).strip()
    messages_staged_diff = get_commit_messages(staged_diff, file).strip()
    messages_unstaged_diff = get_commit_messages(unstaged_diff, file).strip()
    if messages_staged_diff:
        commit_messages.append(messages_staged_diff)
    if messages_unstaged_diff:
        commit_messages.append(messages_unstaged_diff)
    return commit_messages
    ""
def git_commit_everything(message):
    """
    Stages all changes (including new, modified, deleted files), commits with the given message,
    and pushes the commit to the current branch on the default remote ('origin').
    """
    # Stage all changes (new, modified, deleted)
    subprocess.run(['git', 'add', '-A'], check=True)
    # Commit with the provided message
    subprocess.run(['git', 'commit', '-m', message], check=True)
    
def main():
    files = get_changed_files()
    if not files:
        print("No changes detected.")
        return
    for file in files:
        commit_messages = diff_single_file(file)
        single_message = "\n".join(commit_messages)
        print(f"{file}\n{single_message}")
        git_commit_everything(single_message)

if __name__ == "__main__":
    main()