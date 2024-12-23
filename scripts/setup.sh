#!/bin/bash
# scripts/setup.sh

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print with color
print_color() {
    COLOR=$1
    TEXT=$2
    echo -e "${COLOR}${TEXT}${NC}"
}

# Check for errors
check_error() {
    if [ $? -ne 0 ]; then
        print_color $RED "Error: $1"
        exit 1
    fi
}

# Setup development environment
setup_dev_env() {
    print_color $GREEN "Setting up development environment..."

    # Check if Python 3.11 is installed
    if ! command -v python3.11 &> /dev/null; then
        print_color $RED "Python 3.11 is required but not installed."
        exit 1
    fi

    # Create virtual environment
    python3.11 -m venv venv
    check_error "Failed to create virtual environment"

    # Activate virtual environment
    source venv/bin/activate
    check_error "Failed to activate virtual environment"

    # Install poetry
    curl -sSL https://install.python-poetry.org | python3 -
    check_error "Failed to install poetry"

    # Install dependencies
    poetry install
    check_error "Failed to install dependencies"

    # Setup pre-commit hooks
    poetry run pre-commit install
    check_error "Failed to install pre-commit hooks"

    print_color $GREEN "Development environment setup completed successfully!"
}

# Initialize project structure
init_project() {
    print_color $GREEN "Initializing project structure..."

    # Create necessary directories
    directories=(
        "src/api"
        "src/core"
        "src/utils"
        "src/templates"
        "src/agents/shimon"
        "tests"
        "logs"
        "docs"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        touch "$dir/__init__.py"
    done

    # Create necessary files if they don't exist
    touch README.md
    touch .env.example
    touch .gitignore

    print_color $GREEN "Project structure initialized successfully!"
}

# Run tests
run_tests() {
    print_color $GREEN "Running tests..."
    poetry run pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing
    check_error "Tests failed"
}

# Run linting
run_lint() {
    print_color $GREEN "Running linting..."
    poetry run black src/ tests/
    check_error "Black formatting failed"
    
    poetry run isort src/ tests/
    check_error "Import sorting failed"
    
    poetry run flake8 src/ tests/
    check_error "Flake8 check failed"
    
    poetry run mypy src/ tests/
    check_error "Type checking failed"
}

# Main menu
main_menu() {
    while true; do
        echo
        print_color $YELLOW "=== Development Tools ==="
        echo "1. Setup development environment"
        echo "2. Initialize project structure"
        echo "3. Run tests"
        echo "4. Run linting"
        echo "5. Exit"
        echo

        read -p "Choose an option: " choice

        case $choice in
            1) setup_dev_env ;;
            2) init_project ;;
            3) run_tests ;;
            4) run_lint ;;
            5) exit 0 ;;
            *) print_color $RED "Invalid option" ;;
        esac
    done
}

# Handle command line arguments
if [ $# -eq 0 ]; then
    main_menu
else
    case "$1" in
        "setup") setup_dev_env ;;
        "init") init_project ;;
        "test") run_tests ;;
        "lint") run_lint ;;
        *) print_color $RED "Unknown command: $1" ;;
    esac
fi