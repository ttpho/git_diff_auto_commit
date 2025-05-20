import asyncio
import os
import subprocess
import sys
from ollama import AsyncClient

model = "gemma3:4b"
prompt = f"""
Given the following Git diff and the list of changed files (with file types), suggest a single concise and relevant commit message that best summarizes all the changes made. 
Use a conventional commit style (e.g., feat:, fix:, chore:, docs:, refactor:). 
The message should be no longer than 72 characters.
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
client = AsyncClient()

async def get_changed_files(repository_path):
    # Git add all
    subprocess.run(
        ["git", "add", "."],
        capture_output=True, text=True, cwd=repository_path
    )
    # Get all staged and unstaged files (excluding untracked)
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True, cwd=repository_path
    )
    unstaged = set(result.stdout.splitlines())
    result = subprocess.run(
        ["git", "diff", "--name-only", "--staged"],
        capture_output=True, text=True, cwd=repository_path
    )
    staged = set(result.stdout.splitlines())
    # Union of both sets
    return sorted(unstaged | staged)


async def get_diff_for_file(file_path, repository_path, staged=False):
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    cmd.append("--")
    cmd.append(file_path)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=repository_path)
    return result.stdout

def replace_backticks(text):
  """Replaces all occurrences of ``` with an empty string.

  Args:
    text: The input string.

  Returns:
    The string with all ``` delimiters replaced by empty strings.
  """
  return text.replace("```", "")

async def get_commit_messages(diff, file_with_type):
    # Use the Ollama chat model to get commit messages
    if len(diff) == 0 or len(file_with_type) == 0:
        return ""
    try:
        messages = [
            {
                'role': 'user',
                'content': prompt.replace("[Git Diff]", diff).replace("[Changed Files and Types]", file_with_type),
            },
        ]
        response = await client.chat(model=model, messages=messages)
        content = response['message']['content']
        return replace_backticks(content)
    except Exception:
        return ""


def status_file(file_path, repository_path):
    """
    Creates a descriptive commit message for changes to a single file,
    detecting if it was added, modified, or deleted.
    """
    try:
        # Check if the file is new (not tracked yet)
        status_new_process = subprocess.run(
            ['git', 'status', '--porcelain', file_path],
            capture_output=True, text=True, check=True, cwd=repository_path,
        )
        if status_new_process.stdout.strip().startswith("??"):
            return "Add"

        # Check if the file was deleted
        status_deleted_process = subprocess.run(
            ['git', 'diff', '--staged', '--name-status', file_path],
            capture_output=True, text=True, check=True, cwd=repository_path,
        )
        if status_deleted_process.stdout.strip().startswith("D"):
            return "Remove"

        # If not new or deleted, assume it's modified
        return "Update"

    except:
        return ""


async def diff_single_file(file_path, repository_path):
    commit_messages = []
    status = status_file(file_path, repository_path).strip()
    file_name = os.path.basename(file_path).strip()
    file_with_type = f"{status} : {file_name}"
    unstaged_diff = (await get_diff_for_file(file_path, repository_path, staged=False)).strip()
    staged_diff = (await get_diff_for_file(file_path, repository_path, staged=True)).strip()
    messages_staged_diff = (await get_commit_messages(staged_diff, file_with_type)).strip()
    messages_unstaged_diff = (await get_commit_messages(unstaged_diff, file_with_type)).strip()
    if messages_staged_diff:
        commit_messages.append(messages_staged_diff)
    if messages_unstaged_diff:
        commit_messages.append(messages_unstaged_diff)
    return commit_messages


async def git_commit_everything(message, repository_path):
    """
    Stages all changes (including new, modified, deleted files), commits with the given message,
    and pushes the commit to the current branch on the default remote ('origin').
    """
    if not message:
        return
    # Stage all changes (new, modified, deleted)
    subprocess.run(['git', 'add', '-A'], check=True, cwd=repository_path,)
    # Commit with the provided message
    subprocess.run(['git', 'commit', '-m', message], check=True, cwd=repository_path,)


async def git_commit_file(file_path, repository_path, message):
    """
    Stages all changes (including new, modified, deleted files), commits with the given message,
    and pushes the commit to the current branch on the default remote ('origin').
    """
    if not message:
        return

    try:
        subprocess.run(['git', 'add', file_path], check=True, cwd=repository_path,)
    except:
        print("An exception occurred")
    # Commit with the provided message
    subprocess.run(['git', 'commit', file_path, '-m', message], check=True, cwd=repository_path,)


async def commit_comment_per_file(all_file_path, repository_path):
    for file_path in all_file_path:
        commit_messages = await diff_single_file(file_path, repository_path)
        commit_messages_text = "\n".join(commit_messages)
        print(f"{file_path}: {commit_messages_text}")
        await git_commit_file(file_path, repository_path, commit_messages_text)


async def commit_comment_all(all_file_path, repository_path):
    all_message = []
    for file_path in all_file_path:
        commit_messages = await diff_single_file(file_path, repository_path)
        commit_messages_text = "\n".join(commit_messages)
        print(f"{file_path}: {commit_messages_text}")
        all_message.extend(commit_messages)
    await git_commit_everything(message="\n".join(all_message), repository_path = repository_path)


async def main():
    repository_path = sys.argv[1] if len(sys.argv) > 1  else None
    is_commit_per_file = True if (len(sys.argv) > 2 and sys.argv[2] == 'single') else False

    all_file_path = await get_changed_files(repository_path)
    if not all_file_path:
        print("No changes detected.")
        return
    
    if is_commit_per_file:
        await commit_comment_per_file(all_file_path, repository_path)
    else:
        await commit_comment_all(all_file_path, repository_path)

if __name__ == "__main__":
    asyncio.run(main())
