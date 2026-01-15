import numpy as np



def detect_high_activity_intervals(data_path, *, num_channels: int, num_frames: int, sampling_frequency_hz: float, high_activity_threshold=3, baseline_percentile=10):
    # If high_activity_threshold is 0, return empty list (no high activity detection)
    if high_activity_threshold == 0:
        return []
    
    # Memory-map the file instead of loading it all into memory
    filtered_data = np.memmap(data_path, dtype=np.int16, mode='r', shape=(num_frames, num_channels))

    segment_duration_ms = 20.0
    fs = sampling_frequency_hz
    num_timesteps = num_frames
    
    segment_size = int(segment_duration_ms * fs / 1000.0)  # Convert ms to samples
    min_consecutive = 3
    
    # Calculate number of segments
    num_segments = (num_timesteps + segment_size - 1) // segment_size
    
    # Compute variance for each segment
    variances = np.zeros(num_segments)
    for i in range(num_segments):
        segment_start = i * segment_size
        variances[i] = compute_segment_variance(filtered_data, segment_start, segment_size)
    
    # Calculate baseline variance as the specified percentile of segment variances
    baseline_variance = np.percentile(variances, baseline_percentile)

    # Calculate threshold as baseline_variance * high_activity_threshold
    threshold = baseline_variance * high_activity_threshold
    print(f'Using variance threshold of {threshold:.2f} for high activity detection (baseline variance: {baseline_variance:.2f})')
    
    # Classify segments as high activity
    high_activity_flags = variances > threshold
    
    # Group adjacent high activity segments (with minimum consecutive requirement)
    segment_intervals = group_adjacent_segments(high_activity_flags, min_consecutive=min_consecutive)
    
    # Convert segment indices to time (seconds)
    time_intervals = []
    for start_seg, end_seg in segment_intervals:
        start_time_sec = start_seg * segment_duration_ms / 1000.0
        end_time_sec = (end_seg + 1) * segment_duration_ms / 1000.0
        time_intervals.append((start_time_sec, end_time_sec))
    
    return time_intervals

def compute_segment_variance(data, segment_start, segment_size):
    """
    Compute average per-channel variance for a single segment.
    
    Parameters:
    -----------
    data : np.ndarray
        Filtered data of shape (num_timesteps, num_channels)
    segment_start : int
        Starting index of segment
    segment_size : int
        Number of samples in segment
    
    Returns:
    --------
    float
        Average per-channel variance across the segment
    """
    segment_end = min(segment_start + segment_size, data.shape[0])
    segment_data = data[segment_start:segment_end, :]
    
    # Compute variance for each channel, then average across channels
    channel_variances = np.var(segment_data, axis=0)
    avg_variance = np.mean(channel_variances)
    
    return avg_variance

def group_adjacent_segments(high_activity_flags, min_consecutive=3):
    """
    Group adjacent high activity segments into intervals.
    
    Parameters:
    -----------
    high_activity_flags : np.ndarray
        Boolean array indicating high activity segments
    min_consecutive : int
        Minimum number of consecutive high activity segments required
    
    Returns:
    --------
    list of tuples
        List of (start_segment, end_segment) tuples (inclusive)
    """
    intervals = []
    in_interval = False
    start_segment = 0
    
    for i, is_high in enumerate(high_activity_flags):
        if is_high and not in_interval:
            # Start of new interval
            start_segment = i
            in_interval = True
        elif not is_high and in_interval:
            # End of interval - check if it meets minimum length
            interval_length = i - start_segment
            if interval_length >= min_consecutive:
                intervals.append((start_segment, i - 1))
            in_interval = False
    
    # Handle case where last segment is high activity
    if in_interval:
        interval_length = len(high_activity_flags) - start_segment
        if interval_length >= min_consecutive:
            intervals.append((start_segment, len(high_activity_flags) - 1))
    
    return intervals
