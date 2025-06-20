import streamlit as st
import pandas as pd
import subprocess
from git import Repo
import tempfile
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

with tab1:
    repo_url = st.text_input("Repository URL", placeholder="https://github.com/username/repo")
    
    tone = st.radio(
        "Choose README Style",
        options=["Professional", "Fun"],
        index=0,
        horizontal=True
    )

    if st.button("Generate README", key="repo"):
        with st.spinner("Cloning and analyzing repository..."):
            summary = clone_and_summarize(repo_url)

        # 🔥 Prompt Templates
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
            readme = generate_readme(prompt)

        st.text_area("Generated README", readme.strip(), height=500)
        st.download_button("Download README.md", readme.strip(), file_name="README.md")
