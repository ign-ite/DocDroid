import streamlit as st
import os
import sys

# Add the parent directory to the path to import from core and utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.readme_gen import generate_readme
from core.summary_build import clone_and_summarize, summarize_with_github_api, summarize_local_directory
from utils.github_utils import push_readme_and_create_pr

st.set_page_config(page_title="README Generator", layout="centered")

st.markdown("<b><h2 style='text-align: center;'>README Generator</h2></b>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Generate a consolidated file from repository or local directory contents</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["GitHub Repository", "Local Directory"])

def create_prompt(summary: str, tone: str) -> str:
    """Create the prompt for README generation"""
    return f"""
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
- Use previous README.md to get the name of the project correct, if README.md does not exist, come up with your own project name. 
- Exclude any license information or license section.
- Use clear headings and markdown formatting.
- Make the README engaging and easy to understand for both beginners and experienced users.
- Where appropriate, use bullet points, code blocks, and links to external resources.
- Where links are being used, make them embedded. 
{summary}

### Response:
"""

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

        - This mode uses GitHub's API instead of `git clone`.
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

        prompt = create_prompt(summary, tone)
        
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
                summary = summarize_local_directory(local_path)

                prompt = create_prompt(summary, tone2)

                with st.spinner("Generating README with DeepSeek..."):
                    readme = generate_readme(prompt).strip()

                st.text_area("Generated README", readme, height=500, key="local_text")
                st.markdown("### 📄 Preview")
                st.markdown(readme, unsafe_allow_html=True)
                st.download_button("Download README.md", readme, file_name="README.md")