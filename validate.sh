#!/bin/bash
# Validation script - Python equivalent to ESLint + Prettier + TypeCheck
# This script runs code quality checks on the Python codebase

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories to check
SRC_DIRS="src scripts"

echo ""
echo "============================================================"
echo "  🔍 RUNNING CODE VALIDATION"
echo "============================================================"
echo ""

# Track overall status
ERRORS=0

# ============================================================
# 1. SYNTAX CHECK (equivalent to TypeScript compilation)
# ============================================================
echo -e "${BLUE}[1/4] 🔧 Python Syntax Check${NC}"
echo "Checking Python syntax (py_compile)..."
echo ""

if python3 -m py_compile src/**/*.py scripts/*.py 2>/dev/null; then
    echo -e "${GREEN}✅ Syntax check passed${NC}"
else
    echo -e "${RED}❌ Syntax errors found${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# ============================================================
# 2. CODE FORMATTING CHECK (equivalent to Prettier)
# ============================================================
echo -e "${BLUE}[2/4] 🎨 Code Formatting Check (Black)${NC}"
echo "Checking code formatting..."
echo ""

if command -v black &> /dev/null; then
    if black --check --line-length 100 $SRC_DIRS 2>&1 | head -20; then
        echo -e "${GREEN}✅ Code formatting is correct${NC}"
    else
        echo -e "${YELLOW}⚠️  Code formatting issues found${NC}"
        echo -e "${YELLOW}💡 Run 'black --line-length 100 $SRC_DIRS' to auto-fix${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Black not installed, skipping...${NC}"
    echo "   Install with: pip install black"
fi
echo ""

# ============================================================
# 3. LINTING (equivalent to ESLint)
# ============================================================
echo -e "${BLUE}[3/4] 🔎 Linting (Flake8)${NC}"
echo "Running linter..."
echo ""

if command -v flake8 &> /dev/null; then
    # Flake8 configuration
    # E501: Line too long (we use Black for this)
    # W503: Line break before binary operator (Black style)
    # F401: Module imported but unused (common in __init__.py)
    if flake8 $SRC_DIRS \
        --max-line-length=100 \
        --extend-ignore=E501,W503,F401 \
        --exclude=__pycache__,.git,venv,env \
        --count \
        --statistics 2>&1 | head -50; then
        echo -e "${GREEN}✅ Linting passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Linting warnings found${NC}"
        # Don't fail on linting warnings, just show them
    fi
else
    echo -e "${YELLOW}⚠️  Flake8 not installed, skipping...${NC}"
    echo "   Install with: pip install flake8"
fi
echo ""

# ============================================================
# 4. TYPE CHECKING (equivalent to TypeScript tsc)
# ============================================================
echo -e "${BLUE}[4/4] 🔍 Type Checking (MyPy)${NC}"
echo "Checking type hints..."
echo ""

if command -v mypy &> /dev/null; then
    # MyPy is optional for now, many Python projects don't have full type coverage
    if mypy $SRC_DIRS \
        --ignore-missing-imports \
        --no-strict-optional \
        --allow-untyped-calls \
        --allow-untyped-defs 2>&1 | head -30; then
        echo -e "${GREEN}✅ Type checking passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Type checking warnings (non-blocking)${NC}"
        # Don't fail on type warnings - Python typing is gradual
    fi
else
    echo -e "${YELLOW}⚠️  MyPy not installed, skipping...${NC}"
    echo "   Install with: pip install mypy"
fi
echo ""

# ============================================================
# SUMMARY
# ============================================================
echo "============================================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CRITICAL CHECKS PASSED${NC}"
    echo "============================================================"
    echo ""
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED ($ERRORS critical issues)${NC}"
    echo "============================================================"
    echo ""
    exit 1
fi
