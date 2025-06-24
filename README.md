# DocDroid 🤖

A powerful Streamlit application that automatically generates comprehensive README files for your projects by analyzing repository structure and content.

## Description

DocDroid is an intelligent README generator that can analyze both GitHub repositories and local directories to create well-structured, professional documentation. It uses AI-powered content generation through DeepSeek Coder to produce engaging READMEs that include project descriptions, installation instructions, usage examples, and more.

## Features

- **GitHub Integration**: Clone repositories or use GitHub API for analysis
- **Local Directory Support**: Analyze local project directories
- **Multiple Styles**: Choose between professional and fun README styles
- **Automatic PR Creation**: Push generated READMEs back to GitHub with pull requests
- **File Type Support**: Analyzes Python, Markdown, and text files
- **Interactive Preview**: View generated README before downloading

## Installation

### Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) with DeepSeek Coder model installed
- Git (for repository cloning)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/DocDroid.git
cd DocDroid
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Ollama and pull the DeepSeek Coder model:
```bash
# Install Ollama (visit https://ollama.ai/ for installation instructions)
ollama pull deepseek-coder:6.7b-instruct
```

## Usage

### Running the Application

```bash
streamlit run app/main.py
```

The application will open in your browser at `http://localhost:8501`.

### GitHub Repository Analysis

1. Enter a GitHub repository URL
2. Choose your preferred README style (Professional or Fun)
3. Optionally enable GitHub API mode for advanced features:
   - Access private repositories
   - Create automatic pull requests
   - No local cloning required

### Local Directory Analysis

1. Enter the path to your local project directory
2. Choose your README style
3. Generate and download the README

### GitHub Token Setup

For GitHub API features, you'll need a personal access token with these permissions:
- `repo` (for private repos) or `public_repo` (for public repos)
- `contents` (to read/write files)
- `pull_requests` (to create PRs)

## Project Structure

```
DocDroid/
├── app/
│   └── main.py              # Main Streamlit application
├── core/
│   ├── readme_generator.py  # AI-powered README generation
│   └── summary_builder.py   # Repository/directory analysis
├── utils/
│   └── github_utils.py      # GitHub API utilities
├── assets/                  # Optional assets directory
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** and ensure they follow the existing code style
4. **Add tests** if applicable
5. **Commit your changes**: `git commit -m "Add your feature"`
6. **Push to your branch**: `git push origin feature/your-feature-name`
7. **Open a Pull Request**

### Code Standards

- Follow PEP 8 for Python code style
- Add docstrings to all functions and classes
- Handle exceptions appropriately
- Keep functions focused and modular

## Testing

Currently, the project doesn't have automated tests. We welcome contributions to add a comprehensive test suite using pytest.

To run the application locally for testing:

```bash
# Ensure Ollama is running
ollama serve

# In another terminal, run the Streamlit app
streamlit run app/main.py
```

## Contact

For questions, suggestions, or support:

- **Email**: [varuntheace@gmail.com](mailto:varuntheace@gmail.com)
- **LinkedIn**: [Varun Kumar](https://www.linkedin.com/in/varun-kumar-88286a143/)

## Architecture

The application is built with a modular architecture:

- **`app/main.py`**: Contains the Streamlit UI and user interaction logic
- **`core/readme_generator.py`**: Handles AI-powered README content generation
- **`core/summary_builder.py`**: Analyzes repositories and directories to create content summaries
- **`utils/github_utils.py`**: Manages GitHub API interactions for repository operations

This separation allows for easy maintenance, testing, and future enhancements.