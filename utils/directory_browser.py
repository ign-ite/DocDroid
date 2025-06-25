import os
import streamlit as st
from pathlib import Path
from typing import List, Optional

def get_drives() -> List[str]:
    """Get available drives on Windows, or root directories on Unix"""
    drives = []
    
    if os.name == 'nt':  # Windows
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:  # Unix/Linux/Mac
        drives = ["/"]
        # Add common mount points
        common_mounts = ["/home", "/Users", "/mnt", "/media"]
        for mount in common_mounts:
            if os.path.exists(mount):
                drives.append(mount)
    
    return drives

def get_directories(path: str) -> List[str]:
    """Get all directories in the given path"""
    try:
        if not os.path.exists(path):
            return []
        
        directories = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                directories.append(item)
        
        return sorted(directories)
    except (PermissionError, OSError):
        return []

def get_common_project_directories() -> List[str]:
    """Get common project directories for quick access"""
    common_dirs = []
    
    # Get user home directory
    home = str(Path.home())
    common_dirs.append(("🏠 Home", home))
    
    # Common project locations
    project_locations = [
        ("💻 Desktop", os.path.join(home, "Desktop")),
        ("📁 Documents", os.path.join(home, "Documents")),
        ("⚡ Projects", os.path.join(home, "Projects")),
        ("🐙 GitHub", os.path.join(home, "GitHub")),
        ("📂 Code", os.path.join(home, "Code")),
        ("🔧 Development", os.path.join(home, "Development")),
    ]
    
    for name, path in project_locations:
        if os.path.exists(path):
            common_dirs.append((name, path))
    
    return common_dirs

def is_project_directory(path: str) -> bool:
    """Check if a directory looks like a project directory"""
    if not os.path.exists(path):
        return False
    
    project_indicators = [
        # Configuration files
        'package.json', 'requirements.txt', 'Pipfile', 'pyproject.toml',
        'Cargo.toml', 'pom.xml', 'build.gradle', 'composer.json',
        # Version control
        '.git', '.gitignore',
        # Documentation
        'README.md', 'readme.md', 'README.txt',
        # Source directories
        'src', 'lib', 'app', 'main.py', 'index.js', 'main.js'
    ]
    
    try:
        items = os.listdir(path)
        return any(indicator in items for indicator in project_indicators)
    except (PermissionError, OSError):
        return False

def render_directory_browser() -> Optional[str]:
    """Render the directory browser interface"""
    st.markdown("### 📂 Directory Browser")
    
    # Initialize session state
    if 'current_path' not in st.session_state:
        st.session_state.current_path = str(Path.home())
    if 'selected_path' not in st.session_state:
        st.session_state.selected_path = ""
    
    # Quick access buttons
    st.markdown("**🚀 Quick Access:**")
    common_dirs = get_common_project_directories()
    
    cols = st.columns(min(len(common_dirs), 4))
    for i, (name, path) in enumerate(common_dirs):
        with cols[i % 4]:
            if st.button(name, key=f"quick_{i}"):
                st.session_state.current_path = path
                st.rerun()
    
    # Current path display and navigation
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"**📍 Current Location:** `{st.session_state.current_path}`")
    
    with col2:
        if st.button("⬆️ Parent", key="parent_dir"):
            parent = str(Path(st.session_state.current_path).parent)
            if parent != st.session_state.current_path:  # Prevent going above root
                st.session_state.current_path = parent
                st.rerun()
    
    # Manual path input
    with st.expander("✏️ Enter Path Manually"):
        manual_path = st.text_input(
            "Directory Path", 
            value=st.session_state.current_path,
            key="manual_path_input"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Navigate", key="navigate_manual"):
                if os.path.exists(manual_path) and os.path.isdir(manual_path):
                    st.session_state.current_path = manual_path
                    st.rerun()
                else:
                    st.error("❌ Invalid directory path")
        with col2:
            if st.button("✅ Select This Path", key="select_manual"):
                if os.path.exists(manual_path) and os.path.isdir(manual_path):
                    st.session_state.selected_path = manual_path
                    st.success(f"✅ Selected: {manual_path}")
                    return manual_path
                else:
                    st.error("❌ Invalid directory path")
    
    # Directory listing
    st.markdown("**📁 Directories:**")
    
    try:
        directories = get_directories(st.session_state.current_path)
        
        if not directories:
            st.info("📭 No subdirectories found in this location")
        else:
            # Create a grid layout for directories
            cols_per_row = 3
            for i in range(0, len(directories), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, directory in enumerate(directories[i:i+cols_per_row]):
                    with cols[j]:
                        dir_path = os.path.join(st.session_state.current_path, directory)
                        
                        # Check if it's a project directory
                        is_project = is_project_directory(dir_path)
                        icon = "🚀" if is_project else "📁"
                        
                        # Navigation button
                        if st.button(f"{icon} {directory}", key=f"nav_{i}_{j}"):
                            st.session_state.current_path = dir_path
                            st.rerun()
                        
                        # Select button for project directories
                        if is_project:
                            if st.button(f"✅ Select", key=f"select_{i}_{j}"):
                                st.session_state.selected_path = dir_path
                                st.success(f"✅ Selected: {directory}")
                                return dir_path
    
    except PermissionError:
        st.error("❌ Permission denied - Cannot access this directory")
    except Exception as e:
        st.error(f"❌ Error accessing directory: {str(e)}")
    
    # Selected path display
    if st.session_state.selected_path:
        st.markdown("---")
        st.markdown("**🎯 Selected Directory:**")
        st.code(st.session_state.selected_path)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Clear Selection", key="clear_selection"):
                st.session_state.selected_path = ""
                st.rerun()
        with col2:
            if st.button("✅ Use This Path", key="confirm_selection"):
                return st.session_state.selected_path
    
    return None

def render_project_preview(path: str):
    """Show a preview of the selected project directory"""
    if not path or not os.path.exists(path):
        return
    
    st.markdown("### 👀 Project Preview")
    
    try:
        items = os.listdir(path)
        
        # Categorize files
        config_files = []
        source_files = []
        doc_files = []
        other_files = []
        
        file_categories = {
            'config': ['.json', '.toml', '.yaml', '.yml', '.ini', '.cfg', 'requirements.txt', 'Pipfile', 'package.json'],
            'source': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.rs', '.go', '.php', '.rb'],
            'docs': ['.md', '.txt', '.rst', '.doc', '.pdf']
        }
        
        for item in items[:20]:  # Limit to first 20 items
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                ext = os.path.splitext(item)[1].lower()
                if any(ext.endswith(cfg_ext) for cfg_ext in file_categories['config']) or item in file_categories['config']:
                    config_files.append(item)
                elif ext in file_categories['source']:
                    source_files.append(item)
                elif ext in file_categories['docs']:
                    doc_files.append(item)
                else:
                    other_files.append(item)
        
        # Display categorized files
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if config_files:
                st.markdown("**⚙️ Configuration:**")
                for file in config_files[:5]:
                    st.markdown(f"- {file}")
        
        with col2:
            if source_files:
                st.markdown("**💻 Source Files:**")
                for file in source_files[:5]:
                    st.markdown(f"- {file}")
        
        with col3:
            if doc_files:
                st.markdown("**📚 Documentation:**")
                for file in doc_files[:5]:
                    st.markdown(f"- {file}")
        
        # Show project statistics
        total_files = len([f for f in items if os.path.isfile(os.path.join(path, f))])
        total_dirs = len([d for d in items if os.path.isdir(os.path.join(path, d))])
        
        st.markdown(f"**📊 Project Stats:** {total_files} files, {total_dirs} directories")
        
    except Exception as e:
        st.error(f"❌ Error previewing directory: {str(e)}")
