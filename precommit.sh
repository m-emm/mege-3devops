#! /bin/bash

# Format code
isort $(find src -name '*.py') ; black $(find src -name '*.py')

# # Format workflow files
# npx prettier --write  .github/workflows/*.yml
YAML_FILES=()
while IFS= read -r yaml_file; do
    YAML_FILES+=("$yaml_file")
done < <(
    find . \
        -path './.git' -prune -o \
        -path './build' -prune -o \
        -path './dist' -prune -o \
        -path './.tox' -prune -o \
        \( -name '*.yaml' -o -name '*.yml' \) -print
)
if [ ${#YAML_FILES[@]} -gt 0 ]; then
    perl -pi -e 's/[ \t]+$//' "${YAML_FILES[@]}"
fi

PRETTIER_YAML_FILES=()
for yaml_file in "${YAML_FILES[@]}"; do
    case "$yaml_file" in
        ./.github/workflows/*.yml|./.github/workflows/*.yaml|./src/mege_3devops/process_data/process_specs/*.yaml|./src/mege_3devops/process_data/process_specs/*/*.yaml)
            PRETTIER_YAML_FILES+=("$yaml_file")
            ;;
    esac
done

if [ ${#PRETTIER_YAML_FILES[@]} -gt 0 ]; then
    npx prettier --write "${PRETTIER_YAML_FILES[@]}" || exit 1
fi

# Run linting (same as GitHub Actions)
echo "Running flake8 linting (syntax errors and undefined names only)..."
flake8 src/ --count --select=E9,F63,F7,F82 --ignore=F824,F401 --show-source --statistics




echo "Checking for unused imports..."
flake8 --select=F401 --exclude="*/simple.py,build/*,*/adapter_chooser.py,*/_adapter_bridge.py" src/
if [ $? -ne 0 ]; then
    echo "❌ Found unused imports! Please remove them before committing."
    exit 1
fi
echo "✅ No unused imports found."
