import subprocess

def generate_readme(prompt: str) -> str:
    """
    Generate README content using DeepSeek Coder model via Ollama.
    
    Args:
        prompt (str): The prompt containing project information and instructions
        
    Returns:
        str: Generated README content
    """
    try:
        process = subprocess.Popen(
            ["ollama", "run", "deepseek-coder:6.7b-instruct"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(input=prompt.encode())
        
        if stderr:
            print(f"Warning: {stderr.decode()}")
            
        return stdout.decode()
    except Exception as e:
        raise Exception(f"Failed to generate README: {str(e)}")