import os
import importlib

# Get the directory of the current file
package_dir = os.path.dirname(__file__)

# Loop through all files in the directory
for filename in os.listdir(package_dir):
    # Check if the file is a Python file and not the __init__.py file
    if filename.endswith(".py") and filename != "__init__.py":
        # Remove the .py extension to get the module name
        module_name = filename[:-3]
        # Import the module dynamically
        module = importlib.import_module(f".{module_name}", package=__name__)
        # Get all attributes from the module and add them to the current namespace
        for attr in dir(module):
            if not attr.startswith("_"):  # Skip private attributes
                globals()[attr] = getattr(module, attr)
