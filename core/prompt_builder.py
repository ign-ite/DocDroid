from typing import Dict, Optional

def create_enhanced_prompt_with_metadata(summary: str, metadata: Dict, tone: str, existing_readme: str = "") -> str:
    """
    Create enhanced prompt with repository metadata
    """
    # Safely format metadata with fallbacks
    name = metadata.get('name', 'Unknown Project')
    description = metadata.get('description', 'No description available')
    stars = metadata.get('stars', 0)
    forks = metadata.get('forks', 0)
    language = metadata.get('language', 'Not specified')
    license_info = metadata.get('license', 'Not specified')
    pushed_at = metadata.get('pushed_at', 'Unknown')
    topics = metadata.get('topics', [])
    
    # Format contributors safely
    contributors = metadata.get('contributors', [])
    contributors_text = ""
    if contributors:
        contributors_text = "\n".join([f"- {contrib.get('login', 'Unknown')} ({contrib.get('contributions', 0)} contributions)" for contrib in contributors[:5]])
    else:
        contributors_text = "- No contributor data available"
    
    # Format languages safely
    languages = metadata.get('languages', {})
    languages_text = format_languages(languages)
    
    # Format release info safely
    latest_release = metadata.get('latest_release', {})
    release_tag = latest_release.get('tag', 'No releases')
    release_date = latest_release.get('published_at', 'N/A')
    
    # Build metadata section
    metadata_section = f"""### Repository Metadata:
- **Name:** {name}
- **Description:** {description}
- **Stars:** {stars} ⭐
- **Forks:** {forks} 🍴
- **Language:** {language}
- **License:** {license_info}
- **Last Updated:** {pushed_at}
- **Topics:** {', '.join(topics) if topics else 'No topics'}

### Latest Release:
- **Version:** {release_tag}
- **Release Date:** {release_date}

### Top Contributors:
{contributors_text}

### Programming Languages Used:
{languages_text}"""

    # Handle existing README section
    existing_section = ""
    if existing_readme and existing_readme.strip():
        existing_section = f"""
### Existing README Content:
{existing_readme}
"""

    # Create the complete prompt
    tone_instruction = "concise, professional" if tone == "Professional" else "fun, quirky, emoji-rich"
    
    prompt = f"""### Instruction:
Write a {tone_instruction} and well-structured README file for a software project.

Use the repository metadata to create accurate badges, statistics, and project information.

{metadata_section}
{existing_section}

**Requirements:**
- Include relevant badges (stars, forks, license, etc.)
- Use the actual project name from metadata
- Include accurate statistics and information
- Create installation instructions based on the primary language
- Add contributor acknowledgments
- Include release information if available
- Make the README engaging and informative
- Contact: varuntheace@gmail.com, LinkedIn: https://www.linkedin.com/in/varun-kumar-88286a143/

### Project Analysis:
{summary}

### Response:
"""
    
    return prompt

def format_languages(languages: Dict) -> str:
    """Format programming languages with percentages"""
    if not languages or not isinstance(languages, dict):
        return "- No language data available"
    
    total = sum(languages.values())
    if total == 0:
        return "- No language data available"
    
    formatted = []
    for lang, bytes_count in languages.items():
        try:
            percentage = (bytes_count / total) * 100
            formatted.append(f"- {lang}: {percentage:.1f}%")
        except (TypeError, ZeroDivisionError):
            formatted.append(f"- {lang}: Unknown%")
    
    return '\n'.join(formatted) if formatted else "- No language data available"

def create_basic_prompt(summary: str, tone: str) -> str:
    """Create the basic prompt for README generation (fallback)"""
    tone_instruction = "concise, professional" if tone == "Professional" else "fun, quirky, emoji-rich"
    
    return f"""### Instruction:
Write a {tone_instruction} and well-structured README file for a software project.

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

### Project Analysis:
{summary}

### Response:
"""

def create_prompt_for_local_directory(summary: str, tone: str, project_name: str = "") -> str:
    """Create prompt specifically for local directory analysis"""
    tone_instruction = "concise, professional" if tone == "Professional" else "fun, quirky, emoji-rich"
    project_section = f"- **Project Name:** {project_name}\n" if project_name else ""
    
    return f"""### Instruction:
Write a {tone_instruction} and well-structured README file for a local software project.

{project_section}
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
- Create an appropriate project name based on the directory structure if not provided
- Exclude license information
- Use clear headings and markdown formatting
- Make the README engaging and easy to understand
- Use bullet points, code blocks, and embedded links where appropriate
- Focus on the actual functionality based on the code analysis

### Project Analysis:
{summary}

### Response:
"""

def create_diff_improvement_prompt(existing_readme: str, improvements: list, tone: str) -> str:
    """Create prompt for improving existing README based on detected gaps"""
    tone_instruction = "professional and concise" if tone == "Professional" else "fun and engaging"
    improvements_text = '\n'.join([f"- {improvement}" for improvement in improvements]) if improvements else "- General improvements needed"
    
    return f"""### Instruction:
Improve the existing README file by addressing the following identified gaps and improvements.

### Current README:
{existing_readme}

### Identified Improvements Needed:
{improvements_text}

**Requirements:**
- Maintain the existing structure and tone where appropriate
- Add the missing sections identified in the improvements
- Enhance existing sections that need improvement
- Keep the {tone_instruction} tone
- Preserve any existing badges, links, or formatting that works well
- Contact: varuntheace@gmail.com, LinkedIn: https://www.linkedin.com/in/varun-kumar-88286a143/

### Response:
"""
