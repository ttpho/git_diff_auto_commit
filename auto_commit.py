import asyncio
import subprocess
import sys
from ollama import AsyncClient

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
client = AsyncClient()


async def get_changed_files():
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


async def get_diff_for_file(filename, staged=False):
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    cmd.append("--")
    cmd.append(filename)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


async def get_commit_messages(diff, files):
    # Use the Ollama chat model to get commit messages
    if len(diff) == 0 or len(files) == 0:
        return ""
    try:
        messages = [
            {
                'role': 'user',
                'content': prompt.replace("[Git Diff]", diff).replace("[Changed Files and Types]", files),
            },
        ]
        response = await client.chat(model=model, messages=messages)
        return response['message']['content']
    except Exception:
        return ""


async def diff_single_file(file):
    commit_messages = []
    unstaged_diff = (await get_diff_for_file(file, staged=False)).strip()
    staged_diff = (await get_diff_for_file(file, staged=True)).strip()
    messages_staged_diff = (await get_commit_messages(staged_diff, file)).strip()
    messages_unstaged_diff = (await get_commit_messages(unstaged_diff, file)).strip()
    if messages_staged_diff:
        commit_messages.append(messages_staged_diff)
    if messages_unstaged_diff:
        commit_messages.append(messages_unstaged_diff)
    return commit_messages


async def git_commit_everything(message):
    """
    Stages all changes (including new, modified, deleted files), commits with the given message,
    and pushes the commit to the current branch on the default remote ('origin').
    """
    if not message:
        return
    # Stage all changes (new, modified, deleted)
    subprocess.run(['git', 'add', '-A'], check=True)
    # Commit with the provided message
    subprocess.run(['git', 'commit', '-m', message], check=True)


async def git_commit_file(file, message):
    """
    Stages all changes (including new, modified, deleted files), commits with the given message,
    and pushes the commit to the current branch on the default remote ('origin').
    """
    if not message:
        return

    try:
        subprocess.run(['git', 'add', file], check=True)
    except:
        print("An exception occurred")
    # Commit with the provided message
    subprocess.run(['git', 'commit', file, '-m', message], check=True)


async def commit_comment_per_file(files):
    for file in files:
        commit_messages = await diff_single_file(file)
        commit_messages_text = "\n".join(commit_messages)
        print(f"{file}: {commit_messages_text}")
        await git_commit_file(file, commit_messages_text)


async def comit_comment_all(files):
    all_message = []
    for file in files:
        commit_messages = await diff_single_file(file)
        commit_messages_text = "\n".join(commit_messages)
        print(f"{file}: {commit_messages_text}")
        all_message.extend(commit_messages)
    await git_commit_everything(message="\n".join(all_message))


async def main():
    files = await get_changed_files()
    if not files:
        print("No changes detected.")
        return
    is_commit_per_file = True if (
        len(sys.argv) > 1 and sys.argv[1] == 'single') else False
    if is_commit_per_file:
        await commit_comment_per_file(files)
    else:
        await comit_comment_all(files)

if __name__ == "__main__":
    asyncio.run(main())
