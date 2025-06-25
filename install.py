#!/usr/bin/env python3
"""
DocDroid- Automated Installation Script
Installs all dependencies including Ollama, Python packages, and sets up the environment
"""

import os
import sys
import subprocess
import platform
import urllib.request
import shutil
import json
from pathlib import Path

class ReadmeGeneratorInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.python_version = sys.version_info
        
    def log(self, message, level="INFO"):
        """Log installation progress"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m", 
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        print(f"{colors.get(level, '')}{level}: {message}{colors['RESET']}")
    
    def run_command(self, command, shell=True):
        """Run system command with error handling"""
        try:
            result = subprocess.run(command, shell=shell, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"Command failed: {command}", "ERROR")
                self.log(f"Error: {result.stderr}", "ERROR")
                return False
            return True
        except Exception as e:
            self.log(f"Exception running command {command}: {str(e)}", "ERROR")
            return False
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        self.log("Checking Python version...")
        if self.python_version < (3, 8):
            self.log("Python 3.8+ is required. Please upgrade Python.", "ERROR")
            return False
        self.log(f"Python {self.python_version.major}.{self.python_version.minor} detected ✓", "SUCCESS")
        return True
    
    def install_python_packages(self):
        """Install required Python packages"""
        self.log("Installing Python dependencies...")
        
        requirements = [
            "streamlit>=1.28.0",
            "requests>=2.31.0",
            "pathlib",
            "urllib3",
            "gitpython",
            "python-dotenv",
            "openai",  # For OpenAI API if needed
            "anthropic",  # For Claude API if needed
        ]
        
        for package in requirements:
            self.log(f"Installing {package}...")
            if not self.run_command(f"{sys.executable} -m pip install {package}"):
                self.log(f"Failed to install {package}", "ERROR")
                return False
        
        self.log("Python packages installed successfully ✓", "SUCCESS")
        return True
    
    def install_ollama(self):
        """Install Ollama based on the operating system"""
        self.log("Installing Ollama...")
        
        if self.system == "linux":
            return self._install_ollama_linux()
        elif self.system == "darwin":  # macOS
            return self._install_ollama_macos()
        elif self.system == "windows":
            return self._install_ollama_windows()
        else:
            self.log(f"Unsupported operating system: {self.system}", "ERROR")
            return False
    
    def _install_ollama_linux(self):
        """Install Ollama on Linux"""
        self.log("Installing Ollama for Linux...")
        
        # Download and run Ollama install script
        install_command = "curl -fsSL https://ollama.ai/install.sh | sh"
        if not self.run_command(install_command):
            self.log("Failed to install Ollama", "ERROR")
            return False
        
        # Start Ollama service
        self.run_command("sudo systemctl enable ollama")
        self.run_command("sudo systemctl start ollama")
        
        self.log("Ollama installed successfully on Linux ✓", "SUCCESS")
        return True
    
    def _install_ollama_macos(self):
        """Install Ollama on macOS"""
        self.log("Installing Ollama for macOS...")
        
        # Check if Homebrew is available
        if self.run_command("which brew"):
            self.log("Installing via Homebrew...")
            if not self.run_command("brew install ollama"):
                self.log("Homebrew installation failed, trying direct download...", "WARNING")
                return self._install_ollama_direct_macos()
        else:
            return self._install_ollama_direct_macos()
        
        self.log("Ollama installed successfully on macOS ✓", "SUCCESS")
        return True
    
    def _install_ollama_direct_macos(self):
        """Direct Ollama installation for macOS"""
        download_url = "https://ollama.ai/download/Ollama-darwin.zip"
        try:
            self.log("Downloading Ollama for macOS...")
            urllib.request.urlretrieve(download_url, "Ollama-darwin.zip")
            
            # Extract and install
            self.run_command("unzip Ollama-darwin.zip")
            self.run_command("sudo cp -R Ollama.app /Applications/")
            self.run_command("rm -rf Ollama-darwin.zip Ollama.app")
            
            self.log("Please start Ollama from Applications folder", "INFO")
            return True
        except Exception as e:
            self.log(f"Direct installation failed: {str(e)}", "ERROR")
            return False
    
    def _install_ollama_windows(self):
        """Install Ollama on Windows"""
        self.log("Installing Ollama for Windows...")
        
        download_url = "https://ollama.ai/download/OllamaSetup.exe"
        try:
            self.log("Downloading Ollama installer...")
            urllib.request.urlretrieve(download_url, "OllamaSetup.exe")
            
            self.log("Running Ollama installer...")
            self.run_command("OllamaSetup.exe /S")  # Silent install
            
            # Clean up
            os.remove("OllamaSetup.exe")
            
            self.log("Ollama installed successfully on Windows ✓", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Windows installation failed: {str(e)}", "ERROR")
            return False
    
    def download_llm_models(self):
        """Download recommended LLM models"""
        self.log("Downloading recommended LLM models...")
        
        models = [
            "llama3.2:3b",  # Fast, good for README generation
            "codellama:7b",  # Code-focused model
            "mistral:7b"     # Alternative general model
        ]
        
        for model in models:
            self.log(f"Downloading {model}... (This may take a while)")
            if not self.run_command(f"ollama pull {model}"):
                self.log(f"Failed to download {model}, continuing...", "WARNING")
            else:
                self.log(f"{model} downloaded successfully ✓", "SUCCESS")
        
        return True
    
    def setup_environment(self):
        """Set up environment variables and configuration"""
        self.log("Setting up environment...")
        
        # Create .env file
        env_content = """# README Generator Configuration
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        # Create startup script
        if self.system == "windows":
            startup_script = """@echo off
echo Starting README Generator...
echo.
echo Starting Ollama service...
start /B ollama serve
timeout /t 5 /nobreak > nul
echo.
echo Starting Streamlit app...
streamlit run main.py
pause
"""
            with open("start.bat", "w") as f:
                f.write(startup_script)
        else:
            startup_script = """#!/bin/bash
echo "Starting README Generator..."
echo ""
echo "Starting Ollama service..."
ollama serve &
sleep 5
echo ""
echo "Starting Streamlit app..."
streamlit run main.py
"""
            with open("start.sh", "w") as f:
                f.write(startup_script)
            os.chmod("start.sh", 0o755)
        
        self.log("Environment setup complete ✓", "SUCCESS")
        return True
    
    def verify_installation(self):
        """Verify that everything is installed correctly"""
        self.log("Verifying installation...")
        
        # Check Ollama
        if not self.run_command("ollama --version"):
            self.log("Ollama verification failed", "ERROR")
            return False
        
        # Check Python packages
        try:
            import streamlit
            import requests
            self.log("Python packages verified ✓", "SUCCESS")
        except ImportError as e:
            self.log(f"Python package verification failed: {str(e)}", "ERROR")
            return False
        
        # Check if models are available
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        if "llama3.2" in result.stdout or "mistral" in result.stdout:
            self.log("LLM models verified ✓", "SUCCESS")
        else:
            self.log("No LLM models found", "WARNING")
        
        self.log("Installation verification complete ✓", "SUCCESS")
        return True
    
    def install(self):
        """Main installation process"""
        self.log("=" * 50)
        self.log("README Generator - Automated Installation")
        self.log("=" * 50)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Installing Python packages", self.install_python_packages),
            ("Installing Ollama", self.install_ollama),
            ("Downloading LLM models", self.download_llm_models),
            ("Setting up environment", self.setup_environment),
            ("Verifying installation", self.verify_installation)
        ]
        
        for step_name, step_func in steps:
            self.log(f"\n--- {step_name} ---")
            if not step_func():
                self.log(f"Installation failed at: {step_name}", "ERROR")
                return False
        
        self.log("\n" + "=" * 50)
        self.log("🎉 Installation completed successfully!", "SUCCESS")
        self.log("=" * 50)
        
        # Show next steps
        self.log("\nNext steps:")
        if self.system == "windows":
            self.log("1. Run 'start.bat' to launch the application")
        else:
            self.log("1. Run './start.sh' to launch the application")
        self.log("2. Open http://localhost:8501 in your browser")
        self.log("3. Start generating amazing READMEs!")
        
        return True

if __name__ == "__main__":
    installer = ReadmeGeneratorInstaller()
    success = installer.install()
    sys.exit(0 if success else 1)
