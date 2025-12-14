import os
import tempfile
from pathlib import Path

def get_db_path(filename: str, env_var: str = None) -> str:
    """
    Get a cross-platform compatible database path.
    
    Args:
        filename: The name of the database file (e.g., 'supportops_audit.db')
        env_var: Optional environment variable name to check for a custom path
    
    Returns:
        str: Absolute path to the database file
    """
    if env_var:
        custom_path = os.getenv(env_var)
        if custom_path:
            # Check if the directory exists or can be created
            directory = os.path.dirname(custom_path)
            # If path implies current directory (empty dirname), it's fine
            if not directory: 
                return custom_path
                
            try:
                os.makedirs(directory, exist_ok=True)
                return custom_path
            except OSError:
                # If we cannot use the custom path (e.g. permission error for /tmp on Windows), 
                # fallback to safely generated temp path.
                print(f"Warning: Could not create directory for {env_var}='{custom_path}'. Falling back to temporary directory.")
                pass
            
    # Use tempfile to get a valid temporary directory for the OS
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, filename)
