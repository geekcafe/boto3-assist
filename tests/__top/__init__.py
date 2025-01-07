"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import sys
from pathlib import Path

## needed for discovery based top level execution
print("👋 init test paths for __top")
root_directory = Path(__file__).resolve().parent.parent.parent
src_directory = os.path.join(root_directory, "src")

sys.path.insert(0, src_directory)
print("")
for p in sys.path:
    print(f"👉 {p}")
