"""Helper function for computing receptive fields from spike data."""

import numpy as np


def compute_receptive_fields(
    spike_times: np.ndarray,
    spike_labels: np.ndarray,
    acquisition_dir: str
) -> np.ndarray:
    """
    Compute receptive fields for all units.
    
    This is a placeholder implementation that generates random noise.
    The actual implementation will be filled in by a colleague.
    
    Parameters
    ----------
    spike_times : np.ndarray
        Spike times in seconds, shape (num_spikes,)
    spike_labels : np.ndarray
        Spike unit labels (1-based), shape (num_spikes,)
    acquisition_dir : str
        Path to the acquisition directory for this epoch block
        
    Returns
    -------
    receptive_fields : np.ndarray
        5-dimensional array with shape (num_units, num_timepoints, width, height, channels)
        - Dim 0: Unit index (number of units in the sorting)
        - Dim 1: Timepoint (typically 60)
        - Dim 2: X spatial coordinate (typically 127)
        - Dim 3: Y spatial coordinate (typically 203)
        - Dim 4: Color channel (3: RGB)
    """
    # Get number of units from spike labels
    unique_labels = np.unique(spike_labels)
    num_units = len(unique_labels)
    
    # Define receptive field dimensions
    num_timepoints = 60
    width = 127
    height = 203
    num_channels = 3
    
    # Placeholder: generate random noise
    # Shape: (units, timepoints, x, y, channels)
    receptive_fields = np.random.randn(
        num_units, num_timepoints, width, height, num_channels
    ).astype(np.float32)
    
    # Scale to a reasonable range for visualization (0-255)
    receptive_fields = (receptive_fields * 50 + 128).clip(0, 255).astype(np.float32)
    
    print(f"Generated receptive fields with shape {receptive_fields.shape}")
    
    return receptive_fields
