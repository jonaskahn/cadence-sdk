#!/bin/bash

# Echo SDK Deployment Script
# Deploys the cadence_sdk package to PyPI

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get version from pyproject.toml
get_pyproject_version() {
    grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'
}

# Function to get installed version
get_installed_version() {
    python -c "import cadence_sdk; print(cadence_sdk.__version__)" 2>/dev/null || echo "not installed"
}

# Function to calculate next versions
calculate_next_versions() {
    local current_version=$1
    local major minor patch
    
    IFS='.' read -r major minor patch <<< "$current_version"
    
    local next_patch="$major.$minor.$((patch + 1))"
    local next_minor="$major.$((minor + 1)).0"
    local next_major="$((major + 1)).0.0"
    
    echo "$next_patch $next_minor $next_major"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Please run this script from the sdk directory."
    exit 1
fi

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install poetry first."
    exit 1
fi

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes. Consider committing them before deployment."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled."
        exit 0
    fi
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(get_pyproject_version)
INSTALLED_VERSION=$(get_installed_version)

print_status "Current version in pyproject.toml: $CURRENT_VERSION"
print_status "Currently installed version: $INSTALLED_VERSION"

# Calculate next versions
read -r NEXT_PATCH NEXT_MINOR NEXT_MAJOR <<< "$(calculate_next_versions "$CURRENT_VERSION")"

# Ask for version bump type
echo
echo "Select version bump type:"
echo "1) patch ($CURRENT_VERSION -> $NEXT_PATCH)"
echo "2) minor ($CURRENT_VERSION -> $NEXT_MINOR)"
echo "3) major ($CURRENT_VERSION -> $NEXT_MAJOR)"
echo "4) Skip version bump"
read -p "Enter choice (1-4): " -n 1 -r
echo

case $REPLY in
    1)
        print_status "Bumping patch version..."
        poetry version patch
        ;;
    2)
        print_status "Bumping minor version..."
        poetry version minor
        ;;
    3)
        print_status "Bumping major version..."
        poetry version major
        ;;
    4)
        print_status "Skipping version bump..."
        ;;
    *)
        print_error "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Get new version
NEW_VERSION=$(get_pyproject_version)
print_status "New version: $NEW_VERSION"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
print_status "Building package..."
poetry build

# Check if build was successful
if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    print_error "Build failed. No distribution files found."
    exit 1
fi

print_success "Package built successfully!"

# Show what will be uploaded
echo
print_status "Files to be uploaded:"
ls -la dist/

# Ask for confirmation
echo
read -p "Deploy to PyPI? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Deployment cancelled."
    exit 0
fi

# Deploy to PyPI
print_status "Deploying to PyPI..."
poetry publish

print_success "Package deployed successfully to PyPI!"
print_status "Version $NEW_VERSION is now available on PyPI."

# Optional: Create git tag
read -p "Create git tag for version $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Creating git tag..."
    git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
    print_success "Git tag v$NEW_VERSION created!"
    print_warning "Don't forget to push the tag: git push origin v$NEW_VERSION"
fi

echo
print_success "Deployment completed successfully!"
print_status "Package: cadence_sdk"
print_status "Version: $NEW_VERSION"
print_status "PyPI URL: https://pypi.org/project/cadence_sdk/"
