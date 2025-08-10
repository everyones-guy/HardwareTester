#!/bin/bash

# Define the destination folder
MODELS_DIR="models"

# Create the models directory if it doesn't exist
mkdir -p $MODELS_DIR

# Split the models.py file into separate files
# The script looks for "class " followed by a capital letter to detect each model
awk '/^class [A-Z]/ { 
    out="'$MODELS_DIR'/" $2 ".py";
    print "Creating file: " out;
    if (f) close(f); 
    f=out; 
} 
{ 
    print > f 
}' models.py

# Create __init__.py in the models directory to make it a module
echo "from .base import db" > $MODELS_DIR/__init__.py

# Append all imports to __init__.py
grep -E "^from|^import" models.py | while read -r line; do
    echo "$line" >> $MODELS_DIR/__init__.py
done

# Add imports for all models to __init__.py
find $MODELS_DIR -type f -name "*.py" ! -name "__init__.py" | while read -r file; do
    model_name=$(basename "$file" .py)
    echo "from .${model_name} import ${model_name}" >> $MODELS_DIR/__init__.py
done

# Clean up: Add base.py for shared mixins or base classes
cat <<EOF > $MODELS_DIR/base.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
EOF

# Remove the original models.py if everything worked correctly
echo "Do you want to remove the original models.py? (y/n)"
read -r choice
if [[ $choice == "y" ]]; then
    rm models.py
    echo "models.py removed."
else
    echo "models.py retained."
fi

echo "Models successfully reorganized into the '$MODELS_DIR' folder."

