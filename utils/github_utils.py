import requests
import base64
from urllib.parse import urlparse

def push_readme_and_create_pr(repo_url: str, token: str, readme_content: str) -> str:
    """
    Push a README file to a GitHub repository and create a pull request.
    
    Args:
        repo_url (str): URL of the GitHub repository
        token (str): GitHub access token
        readme_content (str): Content of the README file
        
    Returns:
        str: URL of the created pull request, or None if failed
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        user, repo = path_parts[0], path_parts[1].replace(".git", "")

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        repo_api = f"https://api.github.com/repos/{user}/{repo}"

        # Get default branch
        repo_data = requests.get(repo_api, headers=headers).json()
        default_branch = repo_data.get("default_branch", "main")

        # Get latest commit SHA
        ref_url = f"{repo_api}/git/ref/heads/{default_branch}"
        ref_data = requests.get(ref_url, headers=headers).json()
        latest_sha = ref_data["object"]["sha"]

        # Create new branch
        branch_name = "auto-readme"
        create_ref_url = f"{repo_api}/git/refs"
        requests.post(create_ref_url, headers=headers, json={
            "ref": f"refs/heads/{branch_name}",
            "sha": latest_sha
        })

        # Push README to new branch
        readme_api = f"https://api.github.com/repos/{user}/{repo}/contents/README.md"
        content_b64 = base64.b64encode(readme_content.encode()).decode()
        requests.put(readme_api, headers=headers, json={
            "message": "auto: generate README",
            "content": content_b64,
            "branch": branch_name
        })

        # Create pull request
        pr_api = f"https://api.github.com/repos/{user}/{repo}/pulls"
        pr_resp = requests.post(pr_api, headers=headers, json={
            "title": "Auto-generated README 📘",
            "head": branch_name,
            "base": default_branch,
            "body": "This PR adds an auto-generated `README.md`. Feel free to review and merge."
        })

        return pr_resp.json().get("html_url", None)
    
    except Exception as e:
        raise Exception(f"Failed to push README and create PR: {str(e)}")

def validate_github_token(token: str, repo_url: str) -> bool:
    """
    Validate if a GitHub token has the necessary permissions for a repository.
    
    Args:
        token (str): GitHub access token
        repo_url (str): URL of the GitHub repository
        
    Returns:
        bool: True if token is valid and has necessary permissions
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        user, repo = path_parts[0], path_parts[1].replace(".git", "")

        headers = {"Authorization": f"token {token}"}
        repo_api = f"https://api.github.com/repos/{user}/{repo}"
        
        response = requests.get(repo_api, headers=headers)
        return response.status_code == 200
    
    except Exception:
        return False