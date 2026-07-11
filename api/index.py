import os
import sys

# Add root directory to sys.path so 'backend' can be imported
# Try parent directory (normal) and current directory (if flattened by Vercel bundling)
current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)
sys.path.append(current_dir)

# Import the FastAPI application
from backend.app.main import app
