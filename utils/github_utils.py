import requests
import base64
import time
import difflib
from urllib.parse import urlparse
from typing import Tuple, Dict, List, Optional

def validate_github_token(token: str, repo_url: str) -> Tuple[bool, str]:
    """
    Enhanced token validation with detailed error reporting.
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        user, repo = path_parts[0], path_parts[1].replace(".git", "")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        repo_api = f"https://api.github.com/repos/{user}/{repo}"
        response = requests.get(repo_api, headers=headers)
        
        if response.status_code == 200:
            return True, "Token is valid"
        elif response.status_code == 404:
            return False, "Repository not found or token lacks access"
        elif response.status_code == 401:
            return False, "Invalid token"
        elif response.status_code == 403:
            return False, "Token lacks required permissions"
        else:
            return False, f"API error: {response.status_code}"
            
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def detect_existing_readme(repo_url: str, token: str = None) -> Tuple[bool, str, str]:
    """
    Detect existing README and return its content
    Returns: (exists, content, sha)
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        user, repo = path_parts[0], path_parts[1].replace(".git", "")
        
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # Try different README variations
        readme_variations = ["README.md", "readme.md", "Readme.md", "README.MD"]
        
        for readme_name in readme_variations:
            readme_url = f"https://api.github.com/repos/{user}/{repo}/contents/{readme_name}"
            response = requests.get(readme_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Decode base64 content
                content = base64.b64decode(data["content"]).decode('utf-8')
                return True, content, data["sha"]
        
        return False, "", ""
        
    except Exception as e:
        return False, "", ""

def generate_diff_suggestions(existing_readme: str, new_readme: str) -> Dict:
    """
    Generate diff and improvement suggestions
    """
    # Create unified diff
    diff = list(difflib.unified_diff(
        existing_readme.splitlines(keepends=True),
        new_readme.splitlines(keepends=True),
        fromfile='Current README.md',
        tofile='Generated README.md',
        lineterm=''
    ))
    
    # Analyze improvements
    improvements = analyze_readme_improvements(existing_readme, new_readme)
    
    return {
        "diff": ''.join(diff),
        "improvements": improvements,
        "similarity": difflib.SequenceMatcher(None, existing_readme, new_readme).ratio()
    }

def analyze_readme_improvements(existing: str, new: str) -> List[str]:
    """
    Analyze what improvements the new README offers
    """
    improvements = []
    
    # Check for missing sections
    sections_to_check = [
        ("Installation", ["install", "setup", "getting started"]),
        ("Usage", ["usage", "how to use", "examples"]),
        ("Contributing", ["contribut", "development"]),
        ("Testing", ["test", "testing"]),
        ("License", ["license"]),
        ("Contact", ["contact", "support", "author"])
    ]
    
    for section_name, keywords in sections_to_check:
        existing_has = any(keyword.lower() in existing.lower() for keyword in keywords)
        new_has = any(keyword.lower() in new.lower() for keyword in keywords)
        
        if not existing_has and new_has:
            improvements.append(f"Added {section_name} section")
        elif existing_has and new_has:
            improvements.append(f"Enhanced {section_name} section")
    
    # Check for badges
    if "![" not in existing and "![" in new:
        improvements.append("Added badges and visual elements")
    
    # Check for code blocks
    if "``````" in new:
        improvements.append("Added code examples and syntax highlighting")
    
    # Check for table of contents
    if "table of contents" not in existing.lower() and "table of contents" in new.lower():
        improvements.append("Added table of contents")
    
    return improvements

def fetch_repo_metadata(repo_url: str, token: str = None) -> Dict:
    """
    Fetch comprehensive repository metadata
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        user, repo = path_parts[0], path_parts[1].replace(".git", "")
        
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # Get basic repo info
        repo_api = f"https://api.github.com/repos/{user}/{repo}"
        repo_response = requests.get(repo_api, headers=headers)
        
        if repo_response.status_code != 200:
            return {}
        
        repo_data = repo_response.json()
        
        # Get latest commit info
        commits_api = f"{repo_api}/commits"
        commits_response = requests.get(commits_api, headers=headers, params={"per_page": 1})
        latest_commit = commits_response.json()[0] if commits_response.status_code == 200 and commits_response.json() else {}
        
        # Get latest release
        releases_api = f"{repo_api}/releases/latest"
        release_response = requests.get(releases_api, headers=headers)
        latest_release = release_response.json() if release_response.status_code == 200 else {}
        
        # Get languages
        languages_api = f"{repo_api}/languages"
        languages_response = requests.get(languages_api, headers=headers)
        languages = languages_response.json() if languages_response.status_code == 200 else {}
        
        # Get contributors
        contributors_api = f"{repo_api}/contributors"
        contributors_response = requests.get(contributors_api, headers=headers, params={"per_page": 5})
        contributors = contributors_response.json() if contributors_response.status_code == 200 else []
        
        return {
            "name": repo_data.get("name", ""),
            "description": repo_data.get("description", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "watchers": repo_data.get("watchers_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "license": repo_data.get("license", {}).get("name", "Not specified") if repo_data.get("license") else "Not specified",
            "created_at": repo_data.get("created_at", ""),
            "updated_at": repo_data.get("updated_at", ""),
            "pushed_at": repo_data.get("pushed_at", ""),
            "default_branch": repo_data.get("default_branch", "main"),
            "homepage": repo_data.get("homepage", ""),
            "topics": repo_data.get("topics", []),
            "language": repo_data.get("language", ""),
            "languages": languages,
            "latest_commit": {
                "sha": latest_commit.get("sha", "")[:7] if latest_commit.get("sha") else "",
                "message": latest_commit.get("commit", {}).get("message", "") if latest_commit.get("commit") else "",
                "author": latest_commit.get("commit", {}).get("author", {}).get("name", "") if latest_commit.get("commit") else "",
                "date": latest_commit.get("commit", {}).get("author", {}).get("date", "") if latest_commit.get("commit") else ""
            },
            "latest_release": {
                "tag": latest_release.get("tag_name", ""),
                "name": latest_release.get("name", ""),
                "published_at": latest_release.get("published_at", "")
            },
            "contributors": [
                {
                    "login": contrib.get("login", ""),
                    "contributions": contrib.get("contributions", 0),
                    "avatar_url": contrib.get("avatar_url", "")
                } for contrib in contributors[:5]
            ]
        }
        
    except Exception as e:
        return {}

def push_readme_and_create_pr(repo_url: str, token: str, readme_content: str) -> Tuple[bool, str]:
    """
    Enhanced PR creation with proper error handling and validation.
    """
    try:
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        user, repo = path_parts[0], path_parts[1].replace(".git", "")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        repo_api = f"https://api.github.com/repos/{user}/{repo}"
        
        # Validate repository access first
        repo_response = requests.get(repo_api, headers=headers)
        if repo_response.status_code != 200:
            return False, f"Cannot access repository: {repo_response.status_code}"

        repo_data = repo_response.json()
        default_branch = repo_data.get("default_branch", "main")
        
        # Check if we can write to the repository
        if not repo_data.get("permissions", {}).get("push", False):
            return False, "Token lacks push permissions to repository"

        # Get latest commit SHA
        ref_url = f"{repo_api}/git/ref/heads/{default_branch}"
        ref_response = requests.get(ref_url, headers=headers)
        if ref_response.status_code != 200:
            return False, f"Cannot get branch reference: {ref_response.status_code}"
            
        latest_sha = ref_response.json()["object"]["sha"]

        # Create unique branch name
        branch_name = f"auto-readme-{int(time.time())}"
        
        # Create new branch
        create_ref_url = f"{repo_api}/git/refs"
        branch_response = requests.post(create_ref_url, headers=headers, json={
            "ref": f"refs/heads/{branch_name}",
            "sha": latest_sha
        })
        
        if branch_response.status_code not in [200, 201]:
            return False, f"Failed to create branch: {branch_response.status_code}"

        # Check if README already exists
        readme_api = f"{repo_api}/contents/README.md"
        existing_readme = requests.get(readme_api, headers=headers, params={"ref": default_branch})
        
        content_b64 = base64.b64encode(readme_content.encode()).decode()
        
        # Prepare the content payload
        content_payload = {
            "message": "docs: auto-generate README",
            "content": content_b64,
            "branch": branch_name
        }
        
        # If README exists, we need the SHA for updating
        if existing_readme.status_code == 200:
            content_payload["sha"] = existing_readme.json()["sha"]

        # Push README to new branch
        readme_response = requests.put(readme_api, headers=headers, json=content_payload)
        
        if readme_response.status_code not in [200, 201]:
            return False, f"Failed to push README: {readme_response.status_code}"

        # Create pull request
        pr_api = f"{repo_api}/pulls"
        pr_payload = {
            "title": "📘 Auto-generated README",
            "head": branch_name,
            "base": default_branch,
            "body": "This PR adds an auto-generated `README.md` file.\n\n**Generated by:** README Generator Tool\n\nPlease review the content and merge if it looks good!"
        }
        
        pr_response = requests.post(pr_api, headers=headers, json=pr_payload)
        
        if pr_response.status_code == 201:
            pr_url = pr_response.json().get("html_url")
            return True, pr_url
        else:
            error_msg = pr_response.json().get("message", "Unknown error")
            return False, f"Failed to create PR: {error_msg}"

    except Exception as e:
        return False, f"Error creating PR: {str(e)}"
