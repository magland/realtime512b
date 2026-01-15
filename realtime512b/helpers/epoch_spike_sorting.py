"""Helper function for combining segment spike sortings into epoch spike sorting."""

import numpy as np


def compute_epoch_spike_sorting(
    segment_sortings,
    segment_duration_sec,
    num_channels
):
    """
    Combine spike sortings from multiple segments into an epoch-level sorting.
    
    Parameters
    ----------
    segment_sortings : list of dict
        List of segment sorting data, each dict containing:
        - 'spike_times': np.ndarray of spike times (in seconds, relative to segment start)
        - 'spike_labels': np.ndarray of spike labels
        - 'spike_amplitudes': np.ndarray of spike amplitudes
        - 'templates': np.ndarray of templates (num_units, num_channels)
        - 'segment_num': int, the segment number (1-based)
    segment_duration_sec : float
        Duration of each segment in seconds
    num_channels : int
        Number of channels
        
    Returns
    -------
    templates : np.ndarray
        Combined templates of shape (num_units, num_channels), computed as 
        weighted mean of segment templates by spike count
    spike_times : np.ndarray
        Combined spike times in seconds (with segment offsets added)
    spike_labels : np.ndarray
        Combined spike labels
    spike_amplitudes : np.ndarray
        Combined spike amplitudes
    """
    if not segment_sortings:
        # Return empty results
        return (
            np.zeros((0, num_channels), dtype=np.float32),
            np.array([], dtype=np.float32),
            np.array([], dtype=np.int32),
            np.array([], dtype=np.float32)
        )
    
    # Sort segments by segment number
    segment_sortings = sorted(segment_sortings, key=lambda x: x['segment_num'])
    
    # Collect all spike data with offsets
    all_spike_times = []
    all_spike_labels = []
    all_spike_amplitudes = []
    
    for seg_data in segment_sortings:
        segment_num = seg_data['segment_num']
        segment_offset_sec = (segment_num - 1) * segment_duration_sec
        
        # Add time offset to spike times
        offset_spike_times = seg_data['spike_times'] + segment_offset_sec
        
        all_spike_times.append(offset_spike_times)
        all_spike_labels.append(seg_data['spike_labels'])
        all_spike_amplitudes.append(seg_data['spike_amplitudes'])
    
    # Concatenate all spike data
    spike_times = np.concatenate(all_spike_times)
    spike_labels = np.concatenate(all_spike_labels)
    spike_amplitudes = np.concatenate(all_spike_amplitudes)
    
    # Get unique labels to determine number of units
    unique_labels = np.unique(spike_labels)
    num_units = len(unique_labels)
    
    if num_units == 0:
        return (
            np.zeros((0, num_channels), dtype=np.float32),
            spike_times,
            spike_labels,
            spike_amplitudes
        )
    
    # Compute weighted mean templates for each unit
    templates = np.zeros((num_units, num_channels), dtype=np.float32)
    
    for i, label in enumerate(unique_labels):
        # Collect templates and spike counts for this label from each segment
        template_sum = np.zeros(num_channels, dtype=np.float32)
        total_spike_count = 0
        
        for seg_data in segment_sortings:
            seg_spike_labels = seg_data['spike_labels']
            seg_templates = seg_data['templates']
            
            # Count spikes with this label in this segment
            spike_count = np.sum(seg_spike_labels == label)
            
            if spike_count > 0:
                # Find which template index corresponds to this label in this segment
                # The templates are ordered by sorted unique labels
                seg_unique_labels = np.unique(seg_spike_labels)
                if label in seg_unique_labels:
                    label_idx = np.where(seg_unique_labels == label)[0][0]
                    if label_idx < len(seg_templates):
                        # Weight this segment's template by its spike count
                        template_sum += seg_templates[label_idx] * spike_count
                        total_spike_count += spike_count
        
        # Compute weighted mean
        if total_spike_count > 0:
            templates[i] = template_sum / total_spike_count
    
    print(f'Combined {len(spike_times)} spikes from {len(segment_sortings)} segments into {num_units} units')
    
    return templates, spike_times, spike_labels, spike_amplitudes
