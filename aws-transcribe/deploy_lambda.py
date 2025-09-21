#!/usr/bin/env python3
"""
Deployment script for AWS Transcribe Lambda function
"""

import subprocess
import sys
import os
import json
from datetime import datetime

def run_command(command, description="", capture_output=False):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description or f'Running: {command}'}")
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error: {result.stderr}")
                return False, result.stderr
            return True, result.stdout
        else:
            result = subprocess.run(command, shell=True)
            if result.returncode != 0:
                print(f"❌ Command failed with exit code {result.returncode}")
                return False, f"Exit code: {result.returncode}"
            return True, ""
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, str(e)

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Node.js
    success, output = run_command("node --version", "Checking Node.js version", capture_output=True)
    if not success:
        print("❌ Node.js is not installed. Please install Node.js 18+ first.")
        return False
    print(f"✅ Node.js: {output.strip()}")
    
    # Check npm
    success, output = run_command("npm --version", "Checking npm version", capture_output=True)
    if not success:
        print("❌ npm is not installed.")
        return False
    print(f"✅ npm: {output.strip()}")
    
    # Check Python
    success, output = run_command("python --version", "Checking Python version", capture_output=True)
    if not success:
        print("❌ Python is not installed.")
        return False
    print(f"✅ Python: {output.strip()}")
    
    # Check AWS CLI
    success, output = run_command("aws --version", "Checking AWS CLI", capture_output=True)
    if not success:
        print("⚠️  AWS CLI is not installed. Please install it for better deployment experience.")
    else:
        print(f"✅ AWS CLI: {output.strip()}")
    
    return True

def install_dependencies():
    """Install Node.js and Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Install Node.js dependencies
    if os.path.exists("package.json"):
        success, _ = run_command("npm install", "Installing Node.js dependencies")
        if not success:
            return False
    
    # Install Python dependencies (for local testing)
    if os.path.exists("requirements.txt"):
        success, _ = run_command("pip install -r requirements.txt", "Installing Python dependencies")
        if not success:
            print("⚠️  Failed to install Python dependencies. This might affect local testing.")
    
    return True

def run_tests():
    """Run local tests"""
    print("\n🧪 Running tests...")
    
    if os.path.exists("test_lambda.py"):
        success, _ = run_command("python test_lambda.py", "Running Lambda function tests")
        if not success:
            print("⚠️  Tests failed. You may want to fix issues before deploying.")
            response = input("Continue with deployment anyway? (y/n): ")
            return response.lower().startswith('y')
    else:
        print("⚠️  No test file found. Skipping tests.")
    
    return True

def deploy_to_aws(stage="dev"):
    """Deploy to AWS using Serverless Framework"""
    print(f"\n🚀 Deploying to AWS (stage: {stage})...")
    
    # Check if serverless is installed globally or locally
    success, _ = run_command("npx serverless --version", "Checking Serverless Framework", capture_output=True)
    if not success:
        print("❌ Serverless Framework not found. Installing...")
        success, _ = run_command("npm install -g serverless", "Installing Serverless Framework globally")
        if not success:
            return False
    
    # Deploy using Serverless
    deploy_command = f"npx serverless deploy --stage {stage}"
    success, _ = run_command(deploy_command, f"Deploying to AWS (stage: {stage})")
    
    if success:
        print(f"\n✅ Deployment to {stage} successful!")
        
        # Get deployment info
        info_command = f"npx serverless info --stage {stage}"
        success, output = run_command(info_command, "Getting deployment info", capture_output=True)
        if success:
            print("\n📋 Deployment Information:")
            print(output)
    else:
        print(f"\n❌ Deployment to {stage} failed!")
    
    return success

def remove_deployment(stage="dev"):
    """Remove deployment from AWS"""
    print(f"\n🗑️  Removing deployment from AWS (stage: {stage})...")
    
    remove_command = f"npx serverless remove --stage {stage}"
    success, _ = run_command(remove_command, f"Removing deployment from {stage}")
    
    if success:
        print(f"\n✅ Successfully removed deployment from {stage}!")
    else:
        print(f"\n❌ Failed to remove deployment from {stage}!")
    
    return success

def main():
    """Main deployment function"""
    print("🎤 AWS Transcribe API Deployment Script")
    print("=" * 50)
    print(f"Started at: {datetime.now().isoformat()}")
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        stage = sys.argv[2] if len(sys.argv) > 2 else "dev"
    else:
        print("\nAvailable actions:")
        print("  deploy [stage]  - Deploy to AWS (default stage: dev)")
        print("  remove [stage]  - Remove from AWS (default stage: dev)")
        print("  test           - Run local tests only")
        print("  install        - Install dependencies only")
        
        action = input("\nEnter action (deploy/remove/test/install): ").lower().strip()
        if action == "deploy":
            stage = input("Enter stage (default: dev): ").strip() or "dev"
        elif action == "remove":
            stage = input("Enter stage (default: dev): ").strip() or "dev"
    
    try:
        if action == "install":
            if not check_prerequisites():
                sys.exit(1)
            if not install_dependencies():
                sys.exit(1)
            print("\n✅ Dependencies installed successfully!")
        
        elif action == "test":
            if not check_prerequisites():
                sys.exit(1)
            if not install_dependencies():
                sys.exit(1)
            if not run_tests():
                sys.exit(1)
            print("\n✅ Tests completed successfully!")
        
        elif action == "deploy":
            if not check_prerequisites():
                sys.exit(1)
            if not install_dependencies():
                sys.exit(1)
            if not run_tests():
                response = input("Tests failed. Continue with deployment? (y/n): ")
                if not response.lower().startswith('y'):
                    sys.exit(1)
            if not deploy_to_aws(stage):
                sys.exit(1)
            print(f"\n🎉 Deployment to {stage} completed successfully!")
        
        elif action == "remove":
            confirm = input(f"Are you sure you want to remove the {stage} deployment? (y/n): ")
            if confirm.lower().startswith('y'):
                if not remove_deployment(stage):
                    sys.exit(1)
                print(f"\n✅ Removal from {stage} completed successfully!")
            else:
                print("❌ Removal cancelled.")
        
        else:
            print(f"❌ Unknown action: {action}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()