import os
import tempfile
import requests
from urllib.parse import urlparse
from git import Repo
import time

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
    Enhanced GitHub API summarization with proper error handling and rate limiting.
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            return "Invalid GitHub repository URL."

        user, repo = path_parts[0], path_parts[1].replace(".git", "")
        
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        api_url = f"https://api.github.com/repos/{user}/{repo}/contents"
        
        def make_request_with_retry(url, max_retries=3):
            """Make API request with retry logic for rate limiting."""
            for attempt in range(max_retries):
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    return response
                elif response.status_code in [403, 429]:  # Rate limited
                    retry_after = response.headers.get('retry-after')
                    if retry_after:
                        time.sleep(int(retry_after))
                    else:
                        time.sleep(60)  # Wait 1 minute
                    continue
                elif response.status_code == 404:
                    return None
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            return None

        summary = "### Project Structure:\n"
        file_snippets = "\n### File Snippets:\n"
        readme_section = ""
        
        file_limit = 20  # Reduced to avoid timeouts
        processed_files = 0
        char_budget = 8000  # Reduced budget
        current_chars = 0

        def walk_github_dir(path=""):
            nonlocal summary, file_snippets, readme_section, processed_files, current_chars
            
            if processed_files >= file_limit or current_chars >= char_budget:
                return

            url = f"{api_url}/{path}" if path else api_url
            response = make_request_with_retry(url)
            
            if not response:
                return

            try:
                contents = response.json()
            except:
                return

            for item in contents:
                if processed_files >= file_limit or current_chars >= char_budget:
                    return

                if item["type"] == "file" and item["name"].endswith((".py", ".md", ".txt", ".js", ".json")):
                    file_path = item["path"]
                    
                    # Use download_url for better reliability
                    if "download_url" in item and item["download_url"]:
                        content_response = make_request_with_retry(item["download_url"])
                        if content_response:
                            snippet = content_response.text[:400]  # Smaller snippets
                            current_chars += len(snippet)
                            processed_files += 1
                            
                            summary += f"- {file_path}\n"
                            
                            if item["name"].lower() == "readme.md":
                                readme_section = f"\n### Existing README.md:\n``````\n"
                            else:
                                file_snippets += f"\n#### {file_path}\n``````\n"
                
                elif item["type"] == "dir" and processed_files < file_limit:
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