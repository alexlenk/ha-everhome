#!/bin/bash
# Local test runner script for Everhome integration
# This ensures tests work locally before running in CI

set -e

echo "🧪 Running Everhome Integration Tests Locally"
echo "============================================="

# Check if we're in the right directory
if [[ ! -f "custom_components/everhome/manifest.json" ]]; then
    echo "❌ Please run this script from the ha-everhome repository root"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "venv" && ! -d ".venv" && -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  No virtual environment detected. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
else
    echo "✅ Virtual environment detected"
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
fi

# Install test dependencies
echo ""
echo "📦 Installing test dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements_test.txt

# Run code formatting checks
echo ""
echo "🎨 Checking code formatting with Black..."
black --check --diff custom_components/ tests/ || {
    echo "❌ Code formatting issues found. Run: black custom_components/ tests/"
    exit 1
}

# Run import sorting checks
echo ""
echo "📚 Checking import sorting with isort..."
isort --check --diff custom_components/ tests/ || {
    echo "❌ Import sorting issues found. Run: isort custom_components/ tests/"
    exit 1
}

# Run type checking
echo ""
echo "🔍 Running type checks with mypy..."
mypy custom_components/everhome/ || {
    echo "❌ Type checking failed"
    exit 1
}

# Run linting
echo ""
echo "🔍 Running linting with flake8..."
flake8 custom_components/ tests/ || {
    echo "❌ Linting failed"
    exit 1
}

# Run tests with coverage
echo ""
echo "🧪 Running tests with pytest and coverage..."
pytest tests/ -v --cov=custom_components.everhome --cov-report=term-missing --cov-report=html --cov-report=xml || {
    echo "❌ Tests failed"
    exit 1
}

echo ""
echo "✅ All tests passed! Your code is ready for CI."
echo "📊 Coverage report available at: htmlcov/index.html"