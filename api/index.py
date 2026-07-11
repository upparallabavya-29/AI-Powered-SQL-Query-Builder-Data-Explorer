import os
import sys

# Add root directory to sys.path so 'backend' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the FastAPI application
from backend.app.main import app
