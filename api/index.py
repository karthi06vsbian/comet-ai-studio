import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent.parent.resolve())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from server import app
