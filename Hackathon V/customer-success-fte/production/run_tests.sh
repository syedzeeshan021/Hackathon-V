#!/bin/bash
# Customer Success FTE - Test Runner
# ===================================
# Run all tests for the production agent.

set -e

echo "========================================"
echo "  Customer Success FTE - Test Suite"
echo "========================================"
echo ""

# Change to project directory
cd "$(dirname "$0")/.."

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r production/requirements.txt 2>/dev/null || true

# Run unit tests
echo ""
echo "Running unit tests..."
echo "----------------------------------------"
python -m pytest production/tests/test_agent.py -v --tb=short

# Run with coverage
echo ""
echo "Running tests with coverage..."
echo "----------------------------------------"
python -m pytest production/tests/ -v --cov=production/agent --cov-report=term-missing --cov-report=html:coverage_report

echo ""
echo "========================================"
echo "  Test Suite Complete!"
echo "========================================"
echo ""
echo "Coverage report: coverage_report/index.html"
