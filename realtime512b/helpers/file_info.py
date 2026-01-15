"""Helper functions for creating and managing .info files."""

import json
import time
from datetime import datetime


def create_info_file(filepath, elapsed_time_sec):
    """
    Create a .info JSON file for a data file.
    
    Parameters
    ----------
    filepath : str
        Path to the data file (e.g., "segment_001.bin")
    elapsed_time_sec : float
        Elapsed time in seconds for creating the file
    """
    info_path = filepath + ".info"
    
    info_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "elapsed_time_sec": elapsed_time_sec
    }
    
    with open(info_path, 'w') as f:
        json.dump(info_data, f, indent=2)
