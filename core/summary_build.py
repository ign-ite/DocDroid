import os
import tempfile
import requests
from urllib.parse import urlparse
from git import Repo

def clone_and_summarize(repo_url: str) -> str:
    """
    Clone a repository and create a summary of its structure and content.
    
    Args:
        repo_url (str): URL of the repository to clone
        
    Returns:
        str: Summary of the repository structure and file contents
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            Repo.clone_from(repo_url, tmpdir)
            summary = "### Project Structure:\n"
            
            # Get project structure
            for root, _, files in os.walk(tmpdir):
                for f in files:
                    if f.endswith((".py", ".md", ".txt")):
                        rel_path = os.path.relpath(os.path.join(root, f), tmpdir)
                        summary += f"- {rel_path}\n"
            
            summary += "\n### File Snippets:\n"
            
            # Get file content snippets
            for root, _, files in os.walk(tmpdir):
                for f in files:
                    if f.endswith((".py", ".md", ".txt")):
                        filepath = os.path.join(root, f)
                        rel_path = os.path.relpath(filepath, tmpdir)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as file:
                                content = file.read(800)
                                summary += f"\n#### {rel_path}\n```python\n{content}\n```\n"
                        except:
                            continue
            
            return summary
        except Exception as e:
            raise Exception(f"Failed to clone and summarize repository: {str(e)}")

def summarize_with_github_api(repo_url: str, token: str = None) -> str:
    """
    Summarize a GitHub repository using the GitHub API.
    
    Args:
        repo_url (str): URL of the GitHub repository
        token (str, optional): GitHub access token for authentication
        
    Returns:
        str: Summary of the repository structure and file contents
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            return "Invalid GitHub repository URL."
        
        user, repo = path_parts[0], path_parts[1].replace(".git", "")

        headers = {"Authorization": f"token {token}"} if token else {}
        api_url = f"https://api.github.com/repos/{user}/{repo}/contents"

        summary = "### Project Structure:\n"
        file_snippets = "\n### File Snippets:\n"
        readme_section = ""

        file_limit = 30
        processed_files = 0
        char_budget = 12000
        current_chars = 0

        def walk_github_dir(path=""):
            nonlocal summary, file_snippets, readme_section, processed_files, current_chars
            if processed_files >= file_limit or current_chars >= char_budget:
                return

            url = f"{api_url}/{path}" if path else api_url
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                return

            contents = resp.json()
            for item in contents:
                if processed_files >= file_limit or current_chars >= char_budget:
                    return

                if item["type"] == "file" and item["name"].endswith((".py", ".md", ".txt")):
                    file_path = item["path"]
                    raw_resp = requests.get(item["download_url"], headers=headers)
                    if raw_resp.status_code == 200:
                        snippet = raw_resp.text[:500]
                        current_chars += len(snippet)
                        processed_files += 1
                        summary += f"- {file_path}\n"

                        if item["name"].lower() == "readme.md":
                            readme_section = f"\n### Existing README.md (for reference only):\n```markdown\n{snippet}\n```\n"
                        else:
                            file_snippets += f"\n#### {file_path}\n```python\n{snippet}\n```\n"
                elif item["type"] == "dir":
                    walk_github_dir(item["path"])

        walk_github_dir()
        return summary + file_snippets + readme_section
    
    except Exception as e:
        raise Exception(f"Failed to summarize repository via GitHub API: {str(e)}")

def summarize_local_directory(local_path: str) -> str:
    """
    Create a summary of a local directory structure and content.
    
    Args:
        local_path (str): Path to the local directory
        
    Returns:
        str: Summary of the directory structure and file contents
    """
    try:
        summary = "### Project Structure:\n"
        
        # Get project structure
        for root, _, files in os.walk(local_path):
            for f in files:
                if f.endswith((".py", ".md", ".txt")):
                    rel_path = os.path.relpath(os.path.join(root, f), local_path)
                    summary += f"- {rel_path}\n"

        summary += "\n### File Snippets:\n"
        
        # Get file content snippets
        for root, _, files in os.walk(local_path):
            for f in files:
                if f.endswith((".py", ".md", ".txt")):
                    filepath = os.path.join(root, f)
                    rel_path = os.path.relpath(filepath, local_path)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as file:
                            content = file.read(800)
                            summary += f"\n#### {rel_path}\n```python\n{content}\n```\n"
                    except:
                        continue
        
        return summary
    
    except Exception as e:
        raise Exception(f"Failed to summarize local directory: {str(e)}")