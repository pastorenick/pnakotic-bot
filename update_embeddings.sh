#!/bin/bash
# Script to update embeddings when new cards are released

set -e

echo "=========================================="
echo "Updating Card Embeddings"
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Generate embeddings
echo "Generating new embeddings..."
python -m bot.generate_embeddings

echo ""
echo "=========================================="
echo "Embeddings updated successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the changes: git diff data/cache/embeddings.json"
echo "2. Commit: git add data/cache/embeddings.json"
echo "3. Commit: git commit -m 'Update embeddings for new cards'"
echo "4. Push: git push origin main"
echo ""
