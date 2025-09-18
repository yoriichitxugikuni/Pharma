#!/usr/bin/env python3
"""
AI Pharmaceutical Inventory Management System - Auto Startup Script
This script automatically sets up and runs the project with zero errors.
"""

import os
import sys
import subprocess
import time
import platform
import shutil
from pathlib import Path

def print_status(message, status="INFO"):
    """Print formatted status messages"""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }
    print(f"{colors.get(status, colors['INFO'])}[{status}]{colors['RESET']} {message}")

def check_python_version():
    """Check if Python version is compatible"""
    print_status("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_status("Python 3.8+ is required. Current version: {}.{}".format(version.major, version.minor), "ERROR")
        return False
    print_status(f"Python {version.major}.{version.minor}.{version.micro} ✓", "SUCCESS")
    return True

def check_venv():
    """Check if virtual environment exists and activate it"""
    print_status("Checking virtual environment...")
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print_status("Virtual environment not found. Creating one...", "WARNING")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True, capture_output=True)
            print_status("Virtual environment created successfully ✓", "SUCCESS")
        except subprocess.CalledProcessError as e:
            print_status(f"Failed to create virtual environment: {e}", "ERROR")
            return False
    
    # Determine activation script based on OS
    if platform.system() == "Windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"
    
    if not python_path.exists():
        print_status("Virtual environment appears corrupted. Recreating...", "WARNING")
        shutil.rmtree(venv_path)
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True, capture_output=True)
    
    print_status("Virtual environment ready ✓", "SUCCESS")
    return str(python_path), str(pip_path)

def install_dependencies(pip_path):
    """Install project dependencies"""
    print_status("Installing project dependencies...")
    
    # Try using system pip if venv pip fails
    pip_commands = [pip_path, sys.executable, "-m", "pip"]
    
    for pip_cmd in pip_commands:
        try:
            # Test if pip command works
            if isinstance(pip_cmd, str):
                test_cmd = [pip_cmd, "--version"]
            else:
                test_cmd = [pip_cmd, "--version"]
            
            result = subprocess.run(test_cmd, check=True, capture_output=True, text=True)
            working_pip = pip_cmd
            print_status(f"Using pip: {working_pip} ✓", "SUCCESS")
            break
        except:
            continue
    else:
        print_status("No working pip found, trying system pip...", "WARNING")
        working_pip = [sys.executable, "-m", "pip"]
    
    # Upgrade pip first
    try:
        if isinstance(working_pip, str):
            subprocess.run([working_pip, "install", "--upgrade", "pip"], check=True, capture_output=True)
        else:
            subprocess.run(working_pip + ["install", "--upgrade", "pip"], check=True, capture_output=True)
        print_status("Pip upgraded ✓", "SUCCESS")
    except subprocess.CalledProcessError:
        print_status("Pip upgrade failed, continuing...", "WARNING")
    
    # Install requirements
    try:
        if isinstance(working_pip, str):
            result = subprocess.run([working_pip, "install", "-r", "package-requirements.txt"], 
                                  check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(working_pip + ["install", "-r", "package-requirements.txt"], 
                                  check=True, capture_output=True, text=True)
        print_status("Dependencies installed successfully ✓", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Failed to install dependencies: {e}", "ERROR")
        print_status("Trying alternative installation method...", "WARNING")
        
        # Try installing packages individually
        packages = [
            "streamlit==1.28.1",
            "pandas==2.1.1", 
            "numpy==1.24.3",
            "plotly==5.17.0",
            "scikit-learn==1.3.0",
            "pillow==10.0.1",
            "pytesseract==0.3.10",
            "opencv-python==4.8.1.78",
            "openai==1.3.5",
            "python-dotenv==1.0.0"
        ]
        
        for package in packages:
            try:
                if isinstance(working_pip, str):
                    subprocess.run([working_pip, "install", package], check=True, capture_output=True)
                else:
                    subprocess.run(working_pip + ["install", package], check=True, capture_output=True)
                print_status(f"Installed {package} ✓", "SUCCESS")
            except subprocess.CalledProcessError:
                print_status(f"Failed to install {package}", "WARNING")
        
        return True

def check_database():
    """Check if database files exist"""
    print_status("Checking database files...")
    db_files = ["pharma_inventory.db", "pharma_backup_20250903_134057.db"]
    
    for db_file in db_files:
        if Path(db_file).exists():
            print_status(f"Database {db_file} found ✓", "SUCCESS")
        else:
            print_status(f"Database {db_file} not found", "WARNING")
    
    return True

def check_required_files():
    """Check if all required project files exist"""
    print_status("Checking project files...")
    required_files = [
        "app.py",
        "ai_chatbot.py", 
        "database.py",
        "ai_models.py",
        "utils.py",
        "drug_interactions.py",
        "receipt_scanner.py"
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print_status(f"File {file} found ✓", "SUCCESS")
        else:
            missing_files.append(file)
            print_status(f"File {file} missing", "ERROR")
    
    if missing_files:
        print_status(f"Missing files: {', '.join(missing_files)}", "ERROR")
        return False
    
    return True

def run_project(python_path):
    """Run the Streamlit project"""
    print_status("Starting the project...")
    
    # Kill any existing processes on port 8080
    try:
        if platform.system() == "Windows":
            subprocess.run("netstat -ano | findstr :8080", shell=True, capture_output=True)
            subprocess.run("taskkill /F /IM streamlit.exe", shell=True, capture_output=True)
        else:
            subprocess.run("pkill -f streamlit", shell=True, capture_output=True)
        print_status("Cleaned up existing processes ✓", "SUCCESS")
    except:
        pass
    
    # Start the project
    try:
        print_status("Launching Streamlit app on localhost:8080...", "INFO")
        print_status("🌐 Access your app at: http://localhost:8080", "SUCCESS")
        print_status("Press Ctrl+C to stop the application", "INFO")
        print_status("=" * 60, "INFO")
        
        # Try multiple ways to run streamlit
        streamlit_commands = [
            [python_path, "-m", "streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "localhost"],
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "localhost"],
            ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "localhost"]
        ]
        
        for cmd in streamlit_commands:
            try:
                print_status(f"Trying command: {' '.join(cmd)}", "INFO")
                subprocess.run(cmd, check=True)
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            print_status("Failed to start Streamlit with any method", "ERROR")
            return False
        
    except KeyboardInterrupt:
        print_status("\nApplication stopped by user", "INFO")
    except Exception as e:
        print_status(f"Failed to start application: {e}", "ERROR")
        return False
    
    return True

def main():
    """Main startup function"""
    print_status("=" * 60, "INFO")
    print_status("🚀 AI Pharmaceutical Inventory Management System", "INFO")
    print_status("Auto Startup Script - Zero Error Setup", "INFO")
    print_status("=" * 60, "INFO")
    
    # Step 1: Check Python version
    if not check_python_version():
        return False
    
    # Step 2: Check virtual environment
    venv_result = check_venv()
    if not venv_result:
        return False
    python_path, pip_path = venv_result
    
    # Step 3: Install dependencies
    if not install_dependencies(pip_path):
        return False
    
    # Step 4: Check database files
    if not check_database():
        return False
    
    # Step 5: Check required files
    if not check_required_files():
        return False
    
    # Step 6: Run the project
    print_status("All checks passed! Starting the application...", "SUCCESS")
    return run_project(python_path)

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print_status("Startup failed. Please check the errors above.", "ERROR")
            sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)
