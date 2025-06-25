import streamlit as st
import os
import sys

# Add the parent directory to the path to import from core and utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.readme_gen import generate_readme
from core.summary_build import clone_and_summarize, summarize_with_github_api, summarize_local_directory
from core.prompt_builder import create_enhanced_prompt_with_metadata, create_basic_prompt
from utils.github_utils import (
    push_readme_and_create_pr, 
    validate_github_token, 
    detect_existing_readme, 
    generate_diff_suggestions, 
    fetch_repo_metadata
)
from utils.directory_browser import render_directory_browser, render_project_preview


# Initialize session state for PR functionality
if 'pr_created' not in st.session_state:
    st.session_state.pr_created = False
if 'pr_result' not in st.session_state:
    st.session_state.pr_result = None
if 'pr_success' not in st.session_state:
    st.session_state.pr_success = False
if 'readme_content' not in st.session_state:
    st.session_state.readme_content = ""

st.set_page_config(page_title="DocDroid", layout="centered")

# Dark mode adaptive CSS
st.markdown("""
<style>
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
    
    .info-box code {
        background-color: rgba(108, 117, 125, 0.2);
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        color: var(--text-color);
    }
    
    .info-box a, .success-box a, .error-box a {
        color: #007bff;
        text-decoration: none;
    }
    
    .info-box a:hover, .success-box a:hover, .error-box a:hover {
        color: #0056b3;
        text-decoration: underline;
    }
    
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🚀🧑‍⚕️ DocDroid </div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Generate professional README.md files with AI-powered insights</div>', unsafe_allow_html=True)

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
            <li>Fetch repository metadata for richer READMEs</li>
            <li>Detect existing README and suggest improvements</li>
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
            
            with st.spinner("🔍 Analyzing repository and fetching metadata..."):
                try:
                    # Fetch repository metadata if using API
                    metadata = {}
                    has_existing = False
                    existing_content = ""
                    diff_data = None
                    
                    if use_api and github_token:
                        metadata = fetch_repo_metadata(repo_url, github_token)
                        has_existing, existing_content, _ = detect_existing_readme(repo_url, github_token)
                    
                    # Get repository summary
                    if use_api:
                        summary = summarize_with_github_api(repo_url, github_token)
                    else:
                        summary = clone_and_summarize(repo_url)
                    
                    # Create prompt based on available data
                    if metadata:
                        prompt = create_enhanced_prompt_with_metadata(
                            summary, metadata, tone, existing_content if has_existing else ""
                        )
                    else:
                        prompt = create_basic_prompt(summary, tone)
                    
                    with st.spinner("🤖 Generating enhanced README with AI..."):
                        readme = generate_readme(prompt).strip()
                        st.session_state.readme_content = readme
                        
                        st.success("✅ Enhanced README generated successfully!")
                        
                        # Show metadata insights if available
                        if metadata:
                            st.markdown("### 📊 Repository Insights")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("⭐ Stars", metadata.get('stars', 0))
                            with col2:
                                st.metric("🍴 Forks", metadata.get('forks', 0))
                            with col3:
                                st.metric("👀 Watchers", metadata.get('watchers', 0))
                            with col4:
                                st.metric("🐛 Issues", metadata.get('open_issues', 0))
                        
                        # Show diff if existing README found
                        if has_existing:
                            st.markdown("### 📊 Comparison with Existing README")
                            diff_data = generate_diff_suggestions(existing_content, readme)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**Similarity:** {diff_data['similarity']:.1%}")
                            with col2:
                                st.info(f"**Improvements:** {len(diff_data['improvements'])}")
                            
                            if diff_data['improvements']:
                                st.markdown("**🚀 Detected Improvements:**")
                                for improvement in diff_data['improvements']:
                                    st.markdown(f"- {improvement}")
                            
                            with st.expander("📋 View Detailed Diff"):
                                if diff_data['diff']:
                                    st.code(diff_data['diff'], language='diff')
                                else:
                                    st.info("No significant differences detected")
                        
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
    
    # Always use directory browser (with built-in manual input)
    from utils.directory_browser import render_directory_browser, render_project_preview
    
    selected_path = render_directory_browser()
    
    # Show project preview if path is selected
    if selected_path:
        render_project_preview(selected_path)
    
    # Tone selector
    tone2 = st.selectbox("README Style", options=["Professional", "Fun"], index=0, key="tone_local")
    
    # Rest of the generation logic...
    if st.button("🚀 Generate Local README", key="local", type="primary"):
        if not selected_path:
            st.error("❌ Please select a local directory")
        else:
            # Reset PR state when generating new README
            st.session_state.pr_created = False
            st.session_state.pr_result = None
            st.session_state.pr_success = False
            
            with st.spinner("🔍 Analyzing local directory..."):
                try:
                    # Get local directory summary
                    summary = summarize_local_directory(selected_path)
                    
                    # Create prompt for local directory
                    prompt = create_prompt_for_local_directory(summary, tone2, os.path.basename(selected_path))
                    
                    with st.spinner("🤖 Generating README for local directory..."):
                        readme = generate_readme(prompt).strip()
                        st.session_state.readme_content = readme
                        
                        st.success("✅ Local README generated successfully!")
                        
                        # Display the generated README
                        st.markdown("### 📝 Generated README")
                        st.text_area("", readme, height=400, key="local_text")
                        
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

# Footer
st.markdown("---")
st.markdown("""
<div class="footer-text">
    <p>Built with ❤️ by <a href="https://www.linkedin.com/in/varun-kumar-88286a143/">Varunkumar</a> | Contact: <a href="mailto:varuntheace@gmail.com">varuntheace@gmail.com</a></p>
</div>
""", unsafe_allow_html=True)
