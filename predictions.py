"""Hockey Predictions - Streamlit Remote Entry Point."""
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main app
import src.app