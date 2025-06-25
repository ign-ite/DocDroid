import streamlit as st
import os
import sys

# Add the parent directory to the path to import from core and utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.readme_gen import generate_readme
from core.summary_build import clone_and_summarize, summarize_with_github_api, summarize_local_directory
from utils.github_utils import push_readme_and_create_pr, validate_github_token

# Initialize session state for PR functionality
if 'pr_created' not in st.session_state:
    st.session_state.pr_created = False
if 'pr_result' not in st.session_state:
    st.session_state.pr_result = None
if 'pr_success' not in st.session_state:
    st.session_state.pr_success = False
if 'readme_content' not in st.session_state:
    st.session_state.readme_content = ""

st.set_page_config(page_title="README Generator", layout="centered")

# Dark mode adaptive CSS
st.markdown("""
<style>
    /* Main headers that adapt to theme */
    .main-header {
        text-align: center;
        color: var(--text-color);
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: var(--text-color);
        opacity: 0.8;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Success box that adapts to theme */
    .success-box {
        background-color: rgba(40, 167, 69, 0.1);
        border: 1px solid rgba(40, 167, 69, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: var(--text-color);
    }
    
    .success-box h4 {
        color: #28a745;
        margin-bottom: 10px;
    }
    
    /* Error box that adapts to theme */
    .error-box {
        background-color: rgba(220, 53, 69, 0.1);
        border: 1px solid rgba(220, 53, 69, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: var(--text-color);
    }
    
    .error-box h4 {
        color: #dc3545;
        margin-bottom: 10px;
    }
    
    /* Info box that adapts to theme */
    .info-box {
        background-color: rgba(23, 162, 184, 0.1);
        border: 1px solid rgba(23, 162, 184, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: var(--text-color);
    }
    
    .info-box h4 {
        color: #17a2b8;
        margin-bottom: 10px;
    }
    
    /* Code styling that works in both themes */
    .info-box code {
        background-color: rgba(108, 117, 125, 0.2);
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        color: var(--text-color);
    }
    
    /* Links that are visible in both themes */
    .info-box a, .success-box a, .error-box a {
        color: #007bff;
        text-decoration: none;
    }
    
    .info-box a:hover, .success-box a:hover, .error-box a:hover {
        color: #0056b3;
        text-decoration: underline;
    }
    
    /* Footer styling */
    .footer-text {
        text-align: center;
        color: var(--text-color);
        opacity: 0.7;
        margin-top: 2rem;
    }
    
    .footer-text a {
        color: #007bff;
        text-decoration: none;
    }
    
    .footer-text a:hover {
        text-decoration: underline;
    }
    
    /* Ensure all text is visible */
    .stMarkdown, .stText {
        color: var(--text-color);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🚀 README Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Generate professional README.md files from repository contents</div>', unsafe_allow_html=True)

def create_prompt(summary: str, tone: str) -> str:
    """Create the prompt for README generation"""
    return f"""
### Instruction:
Write a {"concise, professional" if tone == "Professional" else "fun, quirky, emoji-rich"} and well-structured README file for a software project.

The README should include the following sections:
1. **Project Title:** A clear and concise name for the project.
2. **Description:** A brief overview of what the project does, its purpose, and key features.
3. **Table of Contents:** (if the README is long, include this for easy navigation)
4. **Installation:** Step-by-step instructions on how to install and set up the project, including prerequisites.
5. **Usage:** Examples and explanations of how to use the project, including code snippets or command-line instructions.
6. **Contributing:** Guidelines for how others can contribute to the project.
7. **Testing:** Instructions on how to run tests.
8. **Contact:** How users can reach the maintainers. Email: varuntheace@gmail.com, LinkedIn: https://www.linkedin.com/in/varun-kumar-88286a143/

**Requirements:**
- Use previous README.md to get the project name correct, if it doesn't exist, create an appropriate name.
- Exclude license information.
- Use clear headings and markdown formatting.
- Make the README engaging and easy to understand.
- Use bullet points, code blocks, and embedded links where appropriate.

{summary}

### Response:
"""

def create_pull_request_with_state(repo_url: str, token: str, readme_content: str):
    """Create pull request and store result in session state"""
    try:
        success, result = push_readme_and_create_pr(repo_url, token, readme_content)
        st.session_state.pr_success = success
        st.session_state.pr_result = result
        st.session_state.pr_created = True
    except Exception as e:
        st.session_state.pr_success = False
        st.session_state.pr_result = f"Error creating PR: {str(e)}"
        st.session_state.pr_created = True

# Main tabs
tab1, tab2 = st.tabs(["🐙 GitHub Repository", "📁 Local Directory"])

with tab1:
    st.markdown("### 🔗 Repository Configuration")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        repo_url = st.text_input("Repository URL", placeholder="https://github.com/username/repo")
    with col2:
        tone = st.selectbox("README Style", options=["Professional", "Fun"], index=0)
    
    use_api = st.checkbox("🔧 Use GitHub API instead of Git clone?")
    github_token = None
    
    if use_api:
        st.markdown("""
        <div class="info-box">
        <h4>✅ GitHub API Mode Activated</h4>
        <p><strong>Benefits:</strong></p>
        <ul>
            <li>Access private repositories</li>
            <li>Create branches and pull requests automatically</li>
            <li>No local cloning required</li>
        </ul>
        <p><strong>🔐 Required Token Permissions:</strong></p>
        <ul>
            <li><code>repo</code> (for private repos) or <code>public_repo</code> (for public repos)</li>
            <li><code>contents:write</code></li>
            <li><code>pull_requests:write</code></li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        github_token = st.text_input("GitHub Access Token", type="password", 
                                   help="Generate token at: https://github.com/settings/tokens")

    if st.button("🚀 Generate README", key="repo", type="primary"):
        if not repo_url:
            st.error("❌ Please enter a repository URL")
        else:
            # Reset PR state when generating new README
            st.session_state.pr_created = False
            st.session_state.pr_result = None
            st.session_state.pr_success = False
            
            with st.spinner("🔍 Analyzing repository..."):
                try:
                    if use_api:
                        summary = summarize_with_github_api(repo_url, github_token)
                    else:
                        summary = clone_and_summarize(repo_url)
                    
                    prompt = create_prompt(summary, tone)
                    
                    with st.spinner("🤖 Generating README with AI..."):
                        readme = generate_readme(prompt).strip()
                        st.session_state.readme_content = readme
                        
                        st.success("✅ README generated successfully!")
                        
                        # Display the generated README
                        st.markdown("### 📝 Generated README")
                        st.text_area("", readme, height=400, key="repo_text")
                        
                        st.markdown("### 👀 Preview")
                        st.markdown(readme)
                        
                        # Download button
                        st.download_button(
                            "📥 Download README.md",
                            readme,
                            file_name="README.md",
                            mime="text/markdown",
                            type="secondary"
                        )
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Pull Request Section
    if st.session_state.readme_content and use_api and github_token:
        st.markdown("---")
        st.markdown("### 🔀 Create Pull Request")
        
        # Validate token first
        with st.spinner("🔍 Validating GitHub token..."):
            is_valid, validation_msg = validate_github_token(github_token, repo_url)
        
        if not is_valid:
            st.error(f"❌ Token validation failed: {validation_msg}")
        else:
            st.success(f"✅ Token validated: {validation_msg}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("📤 Push README & Create PR", key="create_pr_btn", type="primary"):
                    st.session_state.pr_created = False
                    st.session_state.pr_result = None
                    st.session_state.pr_success = False
                    
                    with st.spinner("🔄 Creating branch, pushing README, and opening Pull Request..."):
                        create_pull_request_with_state(repo_url, github_token, st.session_state.readme_content)
            
            with col2:
                if st.button("🔄 Reset PR Status", key="reset_pr_btn"):
                    st.session_state.pr_created = False
                    st.session_state.pr_result = None
                    st.session_state.pr_success = False
                    st.rerun()
            
            # Display PR results
            if st.session_state.pr_created:
                if st.session_state.pr_success:
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>✅ Pull Request Created Successfully!</h4>
                        <p><strong>🔗 PR URL:</strong> <a href="{st.session_state.pr_result}" target="_blank">{st.session_state.pr_result}</a></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>❌ Pull Request Creation Failed</h4>
                        <p><strong>Error:</strong> {st.session_state.pr_result}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("""
                    **💡 Common Solutions:**
                    - Ensure token has proper scope permissions
                    - Check repository access rights
                    - Verify token is not expired
                    """)

with tab2:
    st.markdown("### 📁 Local Directory Configuration")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        local_path = st.text_input("Local Directory Path", placeholder="/path/to/your/project")
    with col2:
        tone2 = st.selectbox("README Style", options=["Professional", "Fun"], index=0, key="tone_local")
    
    if st.button("🚀 Generate README", key="local", type="primary"):
        if not local_path:
            st.error("❌ Please enter a directory path")
        elif not os.path.isdir(local_path):
            st.error("❌ The provided path is not a valid directory")
        else:
            with st.spinner("📂 Analyzing local directory..."):
                try:
                    summary = summarize_local_directory(local_path)
                    prompt = create_prompt(summary, tone2)
                    
                    with st.spinner("🤖 Generating README with AI..."):
                        readme = generate_readme(prompt).strip()
                        
                        st.success("✅ README generated successfully!")
                        
                        st.markdown("### 📝 Generated README")
                        st.text_area("", readme, height=400, key="local_text")
                        
                        st.markdown("### 👀 Preview")
                        st.markdown(readme)
                        
                        st.download_button(
                            "📥 Download README.md",
                            readme,
                            file_name="README.md",
                            mime="text/markdown",
                            type="secondary"
                        )
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div class="footer-text">
    <p>Built with ❤️ using Streamlit | Contact: <a href="mailto:varuntheace@gmail.com">varuntheace@gmail.com</a></p>
</div>
""", unsafe_allow_html=True)
