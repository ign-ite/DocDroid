import streamlit as st
import pandas as pd
import subprocess
import requests
from urllib.parse import urlparse
from git import Repo
import tempfile
import base64
import os

st.set_page_config(page_title="README Generator", layout="centered")

st.markdown("<b><h2 style='text-align: center;'>README Generator</h2></b>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Generate a consolidated file from repository or local directory contents</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["GitHub Repository", "Local Directory"])

def generate_readme(prompt: str):
    process = subprocess.Popen(
        ["ollama", "run", "deepseek-coder:6.7b-instruct"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate(input=prompt.encode())
    return stdout.decode()

def clone_and_summarize(repo_url: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        Repo.clone_from(repo_url, tmpdir)
        summary = "### Project Structure:\n"
        for root, _, files in os.walk(tmpdir):
            for f in files:
                if f.endswith((".py", ".md", ".txt")):
                    rel_path = os.path.relpath(os.path.join(root, f), tmpdir)
                    summary += f"- {rel_path}\n"
        summary += "\n### File Snippets:\n"
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

def summarize_with_github_api(repo_url, token=None):
    import requests
    from urllib.parse import urlparse

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


def push_readme_and_create_pr(repo_url, token, readme_content):
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").split("/")
    user, repo = path_parts[0], path_parts[1].replace(".git", "")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    repo_api = f"https://api.github.com/repos/{user}/{repo}"

    repo_data = requests.get(repo_api, headers=headers).json()
    default_branch = repo_data.get("default_branch", "main")

    ref_url = f"{repo_api}/git/ref/heads/{default_branch}"
    ref_data = requests.get(ref_url, headers=headers).json()
    latest_sha = ref_data["object"]["sha"]

    branch_name = "auto-readme"
    create_ref_url = f"{repo_api}/git/refs"
    requests.post(create_ref_url, headers=headers, json={
        "ref": f"refs/heads/{branch_name}",
        "sha": latest_sha
    })

    readme_api = f"https://api.github.com/repos/{user}/{repo}/contents/README.md"
    content_b64 = base64.b64encode(readme_content.encode()).decode()
    requests.put(readme_api, headers=headers, json={
        "message": "auto: generate README",
        "content": content_b64,
        "branch": branch_name
    })

    pr_api = f"https://api.github.com/repos/{user}/{repo}/pulls"
    pr_resp = requests.post(pr_api, headers=headers, json={
        "title": "Auto-generated README 📘",
        "head": branch_name,
        "base": default_branch,
        "body": "This PR adds an auto-generated `README.md`. Feel free to review and merge."
    })

    return pr_resp.json().get("html_url", None)

with tab1:
    repo_url = st.text_input("Repository URL", placeholder="https://github.com/username/repo")
    
    tone = st.radio(
        "Choose README Style",
        options=["Professional", "Fun"],
        index=0,
        horizontal=True
    )

    use_api = st.checkbox("Use GitHub API instead of Git clone?")
    github_token = None
    if use_api:
        st.markdown("""
        ✅ **GitHub API Mode Activated**

        - This mode uses GitHub’s API instead of `git clone`.
        - Allows you to:
            - Access private repos
            - Create a new branch
            - Upload the `README.md`
            - Open a Pull Request for review
        
        🔍 **What this means:**
        - We fetch only `.py`, `.md`, and `.txt` files individually via HTTP requests.
        - The full repository is *not* cloned.
        - Token is used only to authorize access and allow pushing back changes (like creating a PR).
                             
        🔐 **Token Permissions Needed**:
            - `repo` or `public_repo`
            - `contents`
            - `pull_requests`
        """)
        github_token = st.text_input("GitHub Access Token (optional)", type="password")
        

    if st.button("Generate README", key="repo"):
        with st.spinner("Cloning and analyzing repository..."):
            if use_api:
                summary = summarize_with_github_api(repo_url, github_token)    
            else:    
                summary = clone_and_summarize(repo_url)

        prompt = f"""
### Instruction:
Write a {"concise, professional" if tone == "Professional" else "fun, quirky, emoji-rich"} and well-structured README file for a software project. The README should include the following sections:

1. **Project Title:** A clear and concise name for the project.
2. **Description:** A brief overview of what the project does, its purpose, and key features.
3. **Table of Contents:** (if the README is long, include this for easy navigation)
4. **Installation:** Step-by-step instructions on how to install and set up the project, including prerequisites.
5. **Usage:** Examples and explanations of how to use the project, including code snippets or command-line instructions.
6. **Contributing:** Guidelines for how others can contribute to the project, including code standards, pull request process, and where to ask questions.
7. **Testing:** Instructions on how to run tests, including any testing frameworks or commands used.
8. **Contact:** How users can reach the maintainers or get support. Email is varuntheace@gmail.com and linkedIn is https://www.linkedin.com/in/varun-kumar-88286a143/

**Requirements:**
- Exclude any license information or license section.
- Use clear headings and markdown formatting.
- Make the README engaging and easy to understand for both beginners and experienced users.
- Where appropriate, use bullet points, code blocks, and links to external resources.
- Where links are being used, make them embedded. 
{summary}

### Response:
"""
        with st.spinner("Generating README with DeepSeek..."):
            readme = generate_readme(prompt).strip()

        st.text_area("Generated README", readme, height=500, key="repo_text")
        st.markdown("### 📄 Preview")
        st.markdown(readme, unsafe_allow_html=True)
        st.download_button("Download README.md", readme, file_name="README.md")
        if use_api and github_token:
            if st.button("📤 Push README & Create PR"):
                with st.spinner("Pushing to GitHub and creating Pull Request..."):
                    try:
                        pr_url = push_readme_and_create_pr(repo_url, github_token, readme)
                        if pr_url:
                            st.success(f"✅ Pull Request created: [View PR]({pr_url})")
                        else:
                            st.warning("⚠️ Failed to create PR. Check token permissions or repository access.")
                    except Exception as e:
                        st.error(f"❌ Error while creating PR: {str(e)}")


with tab2:
    local_path = st.text_input("Local Directory Path", placeholder="/path/to/your/project")

    tone2 = st.radio(
        "Choose README Style",
        options=["Professional", "Fun"],
        index=0,
        horizontal=True,
        key="tone_local"
    )

    if st.button("Generate README", key="local"):
        if not os.path.isdir(local_path):
            st.error("The provided path is not a valid directory.")
        else:
            with st.spinner("Analyzing local directory..."):
                summary = "### Project Structure:\n"
                for root, _, files in os.walk(local_path):
                    for f in files:
                        if f.endswith((".py", ".md", ".txt")):
                            rel_path = os.path.relpath(os.path.join(root, f), local_path)
                            summary += f"- {rel_path}\n"

                summary += "\n### File Snippets:\n"
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

                prompt = f"""
### Instruction:
Write a {"concise, professional" if tone2 == "Professional" else "fun, quirky, emoji-rich"} and well-structured README file for a software project. The README should include the following sections:

1. **Project Title:** A clear and concise name for the project.
2. **Description:** A brief overview of what the project does, its purpose, and key features.
3. **Table of Contents:** (if the README is long, include this for easy navigation)
4. **Installation:** Step-by-step instructions on how to install and set up the project, including prerequisites.
5. **Usage:** Examples and explanations of how to use the project, including code snippets or command-line instructions.
6. **Contributing:** Guidelines for how others can contribute to the project, including code standards, pull request process, and where to ask questions.
7. **Testing:** Instructions on how to run tests, including any testing frameworks or commands used.
8. **Contact:** How users can reach the maintainers or get support. Email is varuntheace@gmail.com and linkedIn is https://www.linkedin.com/in/varun-kumar-88286a143/

**Requirements:**
- Exclude any license information or license section.
- Use clear headings and markdown formatting.
- Make the README engaging and easy to understand for both beginners and experienced users.
- Where appropriate, use bullet points, code blocks, and links to external resources.
- Where links are being used, make them embedded. 
{summary}

### Response:
"""

                with st.spinner("Generating README with DeepSeek..."):
                    readme = generate_readme(prompt).strip()

                st.text_area("Generated README", readme, height=500, key="local_text")
                st.markdown("### 📄 Preview")
                st.markdown(readme, unsafe_allow_html=True)
                st.download_button("Download README.md", readme, file_name="README.md")

