#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Docker on various systems
install_docker() {
    print_color $YELLOW "Docker not found. Installing Docker..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # For Ubuntu/Debian systems
        sudo apt update
        sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        sudo systemctl start docker
        sudo systemctl enable docker
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # For macOS
        if command_exists brew; then
            brew install --cask docker
        else
            print_color $RED "Homebrew not found. Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
        open /Applications/Docker.app
        print_color $YELLOW "Docker installed. Please ensure Docker is running and then run this script again."
        exit 0
    else
        print_color $RED "Unsupported OS. Please install Docker manually: https://docs.docker.com/get-docker/"
        exit 1
    fi
}

# Function to build and run Docker container
run_docker_setup() {
    print_color $GREEN "Building the Docker image..."
    docker build -t safeguardian_app .

    print_color $GREEN "Running the Docker container..."
    docker run -d -p 8501:8501 --name safeguardian_app_container safeguardian_app

    print_color $GREEN "Docker container is running. Access the app at http://localhost:8501"
}

# Function to check Docker installation
check_docker_installation() {
    if ! command_exists docker; then
        install_docker
        print_color $YELLOW "Please log out and log back in for Docker permissions to take effect, then run this script again."
        exit 0
    else
        print_color $GREEN "Docker is installed."
    fi
}

# Function to check and install Python dependencies
check_python_dependencies() {
    print_color $GREEN "Checking Python dependencies..."
    if ! command_exists pip; then
        print_color $RED "pip not found. Please install Python and pip."
        exit 1
    fi
    pip install -r requirements.txt
}

# Main logic
print_color $GREEN "Starting SafeGuardianAI setup..."

check_docker_installation
check_python_dependencies

# Check if the container is already running
if docker ps -a --format '{{.Names}}' | grep -q "^safeguardian_app_container$"; then
    print_color $YELLOW "SafeGuardianAI container already exists. Stopping and removing..."
    docker stop safeguardian_app_container
    docker rm safeguardian_app_container
fi

run_docker_setup

print_color $GREEN "Setup complete! SafeGuardianAI is now running."
print_color $GREEN "Access the application at http://localhost:8501"
