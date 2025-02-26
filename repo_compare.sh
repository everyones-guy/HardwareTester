#!/bin/bash

# Ensure a ZIP file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <zip-file>"
    exit 1
fi

ZIP_FILE="$1"
TEMP_DIR="/tmp/code_diff"
OUTPUT_DIFF="/tmp/diff_output.txt"

# Ensure main branch is checked out
git checkout main || { echo "Failed to checkout main"; exit 1; }

# Clean and extract the ZIP file
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
unzip -q "$ZIP_FILE" -d "$TEMP_DIR"

# Run git diff against extracted files
git diff --no-index --stat -- "$TEMP_DIR" . > "$OUTPUT_DIFF"

# Extract metrics
TOTAL_FILES_CHANGED=$(grep -E "files? changed" "$OUTPUT_DIFF" | awk '{print $1}')
TOTAL_INSERTIONS=$(grep -o "[0-9]* insertions" "$OUTPUT_DIFF" | awk '{sum+=$1} END {print sum}')
TOTAL_DELETIONS=$(grep -o "[0-9]* deletions" "$OUTPUT_DIFF" | awk '{sum+=$1} END {print sum}')
TOTAL_MODIFICATIONS=$((TOTAL_INSERTIONS + TOTAL_DELETIONS))

# Identify added and deleted files
FILES_ADDED=$(git diff --no-index --name-status "$TEMP_DIR" . | grep "^A" | wc -l)
FILES_DELETED=$(git diff --no-index --name-status "$TEMP_DIR" . | grep "^D" | wc -l)
FILES_MODIFIED=$((TOTAL_FILES_CHANGED - FILES_ADDED - FILES_DELETED))

# Display results
echo "================= DIFF METRICS ================="
echo "Total Files Changed:    ${TOTAL_FILES_CHANGED:-0}"
echo "Total Lines Added:      ${TOTAL_INSERTIONS:-0}"
echo "Total Lines Removed:    ${TOTAL_DELETIONS:-0}"
echo "Total Modifications:    ${TOTAL_MODIFICATIONS:-0}"
echo "Files Added:            ${FILES_ADDED:-0}"
echo "Files Deleted:          ${FILES_DELETED:-0}"
echo "Files Modified:         ${FILES_MODIFIED:-0}"
echo "==============================================="

# Clean up
rm -rf "$TEMP_DIR"
