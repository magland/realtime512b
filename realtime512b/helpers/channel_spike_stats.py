import numpy as np


def compute_channel_spike_stats(*, data, sampling_frequency_hz, threshold: float):
    num_frames = data.shape[0]
    num_channels = data.shape[1]
    duration_sec = num_frames / sampling_frequency_hz
    
    # Convert data to float32 once for all channels
    data_float = data.astype(np.float32)
    
    # Detect spikes on all channels at once
    spike_mask = detect_spikes_multichannel(data_float, threshold=threshold, sign=-1, window_size=10)
    
    # Count spikes per channel
    num_spikes = spike_mask.sum(axis=0)
    mean_firing_rates = (num_spikes.astype(np.float32) / duration_sec)

    # Compute mean spike amplitudes
    # Set non-spike values to NaN so we can use nanmean
    spike_values = np.where(spike_mask, data_float, np.nan)
    mean_spike_amplitudes = -np.nanmean(spike_values, axis=0)
    
    # Handle channels with no spikes (nanmean returns nan)
    mean_spike_amplitudes = np.nan_to_num(mean_spike_amplitudes, nan=0.0).astype(np.float32)
    
    return mean_firing_rates, mean_spike_amplitudes

def detect_spikes_multichannel(data: np.ndarray, *, threshold: float, sign: int, window_size: int):
    """
    Vectorized spike detection across all channels.
    
    Returns:
        Boolean mask of shape (num_frames, num_channels) where True indicates a spike
    """
    if sign == -1:
        return detect_spikes_multichannel(-data, threshold=-threshold, sign=1, window_size=window_size)
    elif sign != 1:
        raise ValueError("sign must be either 1 or -1")
    
    # Find all candidates above threshold (boolean mask)
    candidates = data > threshold

    # For each candidate, check if it's a local maximum within the window
    # Use a sliding window approach
    pad_width = window_size // 2

    # Pad data to handle boundaries
    data = data.astype(np.float32)  # ensure float for -inf
    data_padded = np.pad(data, ((pad_width, pad_width), (0, 0)), mode='constant', constant_values=-np.inf)
    
    # Create a mask for local maxima
    is_local_max = np.ones_like(data, dtype=bool)
    
    # Check each offset in the window
    for offset in range(-pad_width, pad_width + 1):
        if offset == 0:
            continue
        # Shift data and compare
        shifted = data_padded[pad_width + offset : pad_width + offset + data.shape[0], :]
        if offset < 0:
            # For earlier time points, allow ties (>=)
            is_local_max &= data >= shifted
        else:
            # For later time points, require strict greater than (>)
            is_local_max &= data > shifted
    
    # Combine: must be above threshold AND local maximum
    spike_mask = candidates & is_local_max
    
    return spike_mask

def detect_spikes_single_channel(*, data, threshold: float, sign: int, window_size: int):
    # Use the multichannel function
    data2 = data.reshape(-1, 1)  # make it 2D
    spike_mask = detect_spikes_multichannel(data2, threshold=threshold, sign=sign, window_size=window_size)
    spike_inds = np.where(spike_mask[:, 0])[0]
    return spike_inds
