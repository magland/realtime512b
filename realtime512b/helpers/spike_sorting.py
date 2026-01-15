"""Helper functions for spike sorting using nearest neighbor matching to reference."""

import numpy as np
from .coarse_sorting import detect_spikes_single_channel, compute_template_peak_channel_x_coordinate
from .unit_matching import match_spikes_to_reference


def compute_spike_sorting(
    shifted_data,
    high_activity_intervals,
    reference_spike_frames,
    reference_spike_labels,
    sampling_frequency_hz,
    electrode_coords,
    detect_threshold=-80
):
    """
    Perform spike sorting by detecting spikes and matching them to reference sorting.
    
    Parameters
    ----------
    shifted_data : np.ndarray
        Shifted data array of shape (num_frames, num_channels)
    high_activity_intervals : list of tuple
        List of (start_sec, end_sec) tuples for high activity periods to exclude
    reference_spike_frames : np.ndarray
        Reference spike frames of shape (num_ref_spikes, num_channels)
    reference_spike_labels : np.ndarray
        Reference spike labels of shape (num_ref_spikes,)
    sampling_frequency_hz : float
        Sampling frequency in Hz
    electrode_coords : np.ndarray
        Electrode coordinates array of shape (num_channels, 2)
    detect_threshold : float
        Spike detection threshold (default: -80)
        
    Returns
    -------
    templates : np.ndarray
        Spike templates of shape (num_units, num_channels)
    spike_times : np.ndarray
        Spike times in seconds
    spike_labels : np.ndarray
        Unit labels for each spike (matched to reference)
    spike_amplitudes : np.ndarray
        Spike amplitudes
    """
    num_frames, num_channels = shifted_data.shape
    
    # Create mask for low activity frames
    low_activity_mask = np.ones(num_frames, dtype=bool)
    for start_sec, end_sec in high_activity_intervals:
        start_frame = int(start_sec * sampling_frequency_hz)
        end_frame = int(end_sec * sampling_frequency_hz)
        start_frame = max(0, start_frame)
        end_frame = min(num_frames, end_frame)
        low_activity_mask[start_frame:end_frame] = False
    
    # Set high activity frames to zero
    shifted_data_low_activity = shifted_data.copy()
    shifted_data_low_activity[~low_activity_mask, :] = 0
    
    # Detect spikes on minimum across channels
    data_min = np.min(shifted_data_low_activity, axis=1)
    spike_inds = detect_spikes_single_channel(
        data=data_min,
        threshold=detect_threshold,
        sign=-1,
        window_size=10
    )
    
    print(f'Detected {len(spike_inds)} spikes')
    
    if len(spike_inds) == 0:
        # Return empty results
        return (
            np.zeros((0, num_channels), dtype=np.float32),
            np.array([], dtype=np.float32),
            np.array([], dtype=np.int32),
            np.array([], dtype=np.float32)
        )
    
    # Extract spike frames
    frames = shifted_data_low_activity[spike_inds, :].astype(np.float32)
    
    # Match spikes to reference sorting
    print(f'Matching {len(frames)} spikes to {len(reference_spike_frames)} reference spikes...')
    spike_labels = match_spikes_to_reference(
        spike_frames=frames,
        reference_frames=reference_spike_frames,
        reference_labels=reference_spike_labels,
        n_neighbors=10
    )
    
    # Get unique labels to determine number of units
    unique_labels = np.unique(spike_labels)
    num_units = len(unique_labels)
    
    print(f'Matched spikes to {num_units} units')
    
    # Compute spike amplitudes (negative of minimum value across channels)
    spike_amplitudes = -np.min(frames, axis=1).astype(np.float32)
    
    # Compute templates for each unit
    # Create a mapping from label to index for template array
    label_to_idx = {label: idx for idx, label in enumerate(sorted(unique_labels))}
    templates = np.zeros((num_units, num_channels), dtype=np.float32)
    
    for label in unique_labels:
        idx = label_to_idx[label]
        label_mask = spike_labels == label
        # Use median like in coarse_sorting
        templates[idx, :] = np.median(frames[label_mask, :], axis=0)
    
    # Sort templates by peak channel x-coordinate to match reference ordering
    if num_units > 0:
        template_x_coords = compute_template_peak_channel_x_coordinate(templates, np.array(electrode_coords))
        sorted_indices = np.argsort(template_x_coords[:, 0])
        templates = templates[sorted_indices, :]
        
        # Create mapping from old labels to new sorted labels
        sorted_labels = sorted(unique_labels)
        old_to_new = np.zeros(int(np.max(spike_labels)) + 1, dtype=np.int32)
        for new_idx, old_idx in enumerate(sorted_indices):
            old_label = sorted_labels[old_idx]
            old_to_new[old_label] = sorted_labels[new_idx]
        
        # Remap spike labels to sorted order
        spike_labels = old_to_new[spike_labels].astype(np.int32)
    
    # Convert spike times to seconds
    spike_times = spike_inds.astype(np.float32) / sampling_frequency_hz
    
    return templates, spike_times, spike_labels, spike_amplitudes
