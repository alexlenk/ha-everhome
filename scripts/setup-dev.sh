#!/bin/bash
# Development environment setup script for Everhome integration

set -e

echo "🚀 Setting up Everhome Integration Development Environment"
echo "========================================================="

# Check if we're in the right directory
if [[ ! -f "custom_components/everhome/manifest.json" ]]; then
    echo "❌ Please run this script from the ha-everhome repository root"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" && ! -d ".venv" ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created at ./venv"
else
    echo "✅ Virtual environment already exists"
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
fi

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install test dependencies
echo ""
echo "📚 Installing test dependencies..."
pip install -r requirements_test.txt

# Install pre-commit hooks if available
if command -v pre-commit >/dev/null 2>&1; then
    echo ""
    echo "🪝 Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
    echo "✅ Pre-commit hooks installed"
fi

# Create directories for coverage reports
mkdir -p htmlcov

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run tests: ./scripts/test.sh"
echo "  3. Format code: black custom_components/ tests/"
echo "  4. Sort imports: isort custom_components/ tests/"
echo "  5. Type check: mypy custom_components/everhome/"
echo ""
echo "🔧 Available scripts:"
echo "  - ./scripts/test.sh       - Run full test suite"
echo "  - ./scripts/setup-dev.sh  - This setup script"