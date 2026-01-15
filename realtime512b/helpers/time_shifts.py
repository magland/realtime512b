import os
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np


def optimize_time_shift(
    filtered_data_file_path,
    *,
    electrode_coords,
    sampling_frequency_hz: float,
    duration_sec: float,
):
    num_channels = len(electrode_coords)
    num_timesteps = os.path.getsize(filtered_data_file_path) // (num_channels * 2)

    # Use memmap to avoid loading entire file into memory
    filtered_data = np.memmap(
        filtered_data_file_path,
        dtype=np.int16,
        mode="r",
        shape=(num_timesteps, num_channels),
    )
    print(f"Size of filtered data file: {num_timesteps * num_channels * 2} bytes")

    # First stage: broad search
    # shift is in seconds per spatial unit
    # fov is around 400 spatial units
    # c_x = 1 corresponds to 20000 * 400 samples shift across the array
    # c_x = 1e-6 corresponds to 8 samples shift across the array
    c_x_range = np.linspace(-2e-6, 2e-6, 21)  # seconds per spatial unit
    c_y_range = np.linspace(-2e-6, 2e-6, 21)  # seconds per spatial unit

    optimization_results = optimize_time_shift_coefficients(
        filtered_data=filtered_data,
        electrode_coords=electrode_coords,
        sampling_frequency_hz=20000.0,
        duration_sec=0.5,
        c_x_range=c_x_range,
        c_y_range=c_y_range,
    )

    # Second stage: refined search around best coefficients
    print(f"  Refining optimization around best coefficients...")
    c_x_best = optimization_results["best_c_x"]
    c_y_best = optimization_results["best_c_y"]
    c_x_range = np.linspace(c_x_best - 5e-7, c_x_best + 5e-7, 21)
    c_y_range = np.linspace(c_y_best - 5e-7, c_y_best + 5e-7, 21)

    optimization_results = optimize_time_shift_coefficients(
        filtered_data=filtered_data,
        electrode_coords=electrode_coords,
        sampling_frequency_hz=sampling_frequency_hz,
        duration_sec=duration_sec,
        c_x_range=c_x_range,
        c_y_range=c_y_range,
    )

    print(
        f"  Optimal coefficients: c_x={optimization_results['best_c_x']:.6e}, "
        f"c_y={optimization_results['best_c_y']:.6e}"
    )
    print(
        f"  Alignment score: {optimization_results['best_score']} coincidences (higher is better)"
    )

    c_x = optimization_results["best_c_x"]
    c_y = optimization_results["best_c_y"]

    return float(c_x), float(c_y)


def optimize_time_shift_coefficients(
    filtered_data,
    electrode_coords,
    sampling_frequency_hz,
    duration_sec,
    c_x_range,
    c_y_range,
):
    """
    Optimize time shift coefficients by maximizing variance of averaged channels.
    """
    # Default ranges if not provided
    if c_x_range is None:
        raise ValueError("c_x_range must be provided")
    if c_y_range is None:
        raise ValueError("c_y_range must be provided")

    # Extract data segment
    num_samples = int(duration_sec * sampling_frequency_hz)
    num_samples = min(num_samples, filtered_data.shape[0])
    data_segment = filtered_data[:num_samples, :]

    print(f"\nOptimizing time shift coefficients by maximizing variance:")
    print(f"  Data segment: {num_samples} samples ({duration_sec} sec)")
    print(
        f"  Grid: {len(c_x_range)} x {len(c_y_range)} = {len(c_x_range) * len(c_y_range)} points"
    )

    # Grid search
    best_score = 0  # Higher is better
    best_c_x = 0
    best_c_y = 0

    grid_results = []

    print(f"\nRunning grid search for optimal time shift coefficients...")
    
    # Create list of all (c_x, c_y) combinations
    combinations = [(c_x, c_y) for c_x in c_x_range for c_y in c_y_range]
    total_combinations = len(combinations)
    
    # Create worker function with fixed parameters
    worker_func = partial(
        _compute_score_worker,
        data_segment=data_segment,
        electrode_coords=electrode_coords,
        sampling_frequency_hz=sampling_frequency_hz
    )
    
    # Parallelize computation using ProcessPoolExecutor with progress reporting
    print(f"  Processing {total_combinations} combinations in parallel...")
    with ProcessPoolExecutor() as executor:
        scores = []
        completed = 0
        for score in executor.map(worker_func, combinations):
            scores.append(score)
            completed += 1
            if completed % 50 == 0 or completed == total_combinations:
                print(f"    Progress: {completed}/{total_combinations} ({100*completed//total_combinations}%)")
    
    # Process results
    for (c_x, c_y), score in zip(combinations, scores):
        grid_results.append(
            {"c_x": c_x, "c_y": c_y, "score": score if np.isfinite(score) else None}
        )
        
        if score > best_score:  # Higher is better
            best_score = score
            best_c_x = c_x
            best_c_y = c_y

    if not np.isfinite(best_score):
        print(f"\nWARNING: No valid scores found! Returning default coefficients.")
        return {
            "best_c_x": 0.0,
            "best_c_y": 0.0,
            "best_score": None,
            "grid_results": grid_results,
            "c_x_range": c_x_range,
            "c_y_range": c_y_range,
            "duration_sec": duration_sec,
        }

    print(f"\nOptimization complete!")
    print(f"  Optimal c_x: {best_c_x:.6e} sec/unit")
    print(f"  Optimal c_y: {best_c_y:.6e} sec/unit")
    print(f"  Best score: {best_score:.2f} (higher is better)")

    results = {
        "best_c_x": best_c_x,
        "best_c_y": best_c_y,
        "best_score": best_score,
        "grid_results": grid_results,
        "c_x_range": c_x_range,
        "c_y_range": c_y_range,
        "duration_sec": duration_sec,
    }

    return results


def _compute_score_worker(combination, data_segment, electrode_coords, sampling_frequency_hz):
    """
    Worker function for parallel processing of score computation.
    
    Parameters:
    -----------
    combination : tuple
        (c_x, c_y) tuple
    data_segment : np.ndarray
        Data segment to process
    electrode_coords : list
        Electrode coordinates
    sampling_frequency_hz : float
        Sampling frequency
        
    Returns:
    --------
    float
        Computed score
    """
    c_x, c_y = combination
    return compute_score(data_segment, electrode_coords, c_x, c_y, sampling_frequency_hz)

def compute_score(data, electrode_coords, c_x, c_y, sampling_frequency_hz):
    # Apply time shifts
    shifted_data = apply_time_shifts_for_optimization(
        data, electrode_coords, sampling_frequency_hz, c_x, c_y
    )

    if shifted_data.size == 0:
        # Invalid shift range
        return float("inf")

    # Average across all channels
    averaged_data = np.mean(shifted_data.astype(np.float32), axis=1)

    # Compute and return variance
    # Higher variance indicates better alignment (synchronized spikes sum constructively)
    return np.var(averaged_data)


def apply_time_shifts_for_optimization(
    data, electrode_coords, sampling_frequency_hz, c_x, c_y
):
    num_timesteps, num_channels = data.shape

    # Calculate time shifts in samples for each channel
    time_shifts_samples = []
    for ch in range(num_channels):
        x, y = electrode_coords[ch]
        time_shift_sec = c_x * x + c_y * y
        time_shift_samples = int(round(time_shift_sec * sampling_frequency_hz))
        time_shifts_samples.append(time_shift_samples)

    # Find min and max shifts to determine crop region
    min_shift = min(time_shifts_samples)
    max_shift = max(time_shifts_samples)

    # Allocate output array (same size initially)
    shifted_data = np.zeros_like(data, dtype=data.dtype)

    # Apply shifts by rolling each channel
    for ch in range(num_channels):
        shift = time_shifts_samples[ch]
        # Roll shifts the data: positive shift moves data forward in time
        shifted_data[:, ch] = np.roll(data[:, ch], shift)

    # Crop to avoid edge effects
    # Remove the wrap-around region at both ends
    crop_start = max(0, max_shift)
    crop_end = num_timesteps - max(0, -min_shift)

    if crop_start >= crop_end:
        # Return empty array if shifts are too large
        return np.array([])

    cropped_data = shifted_data[crop_start:crop_end, :]

    return cropped_data


def apply_time_shifts(data, electrode_coords, sampling_frequency_hz, c_x, c_y):
    """
    Apply time shifts to channels based on electrode coordinates.
    Time shift formula: t = c_x * x + c_y * y (in seconds)

    This function shifts each channel by rolling the data without interpolation,
    avoiding edge effects by cropping the output to a safe region.

    Parameters:
    -----------
    data : np.ndarray
        Input data of shape (num_timesteps, num_channels)
    electrode_coords : list of tuples
        List of (x, y) coordinates for each electrode
    sampling_frequency_hz : float
        Sampling frequency in Hz
    c_x : float
        Coefficient for x coordinate
    c_y : float
        Coefficient for y coordinate

    Returns:
    --------
    np.ndarray
        Time-shifted data with adjusted shape to avoid edge effects
    """
    num_timesteps, num_channels = data.shape

    print(f"Applying time shifts with c_x={c_x}, c_y={c_y}...")

    # Calculate time shifts in samples for each channel
    time_shifts_samples = []
    for ch in range(num_channels):
        x, y = electrode_coords[ch]
        time_shift_sec = c_x * x + c_y * y
        time_shift_samples = int(round(time_shift_sec * sampling_frequency_hz))
        time_shifts_samples.append(time_shift_samples)

    # Find min and max shifts to determine crop region
    min_shift = min(time_shifts_samples)
    max_shift = max(time_shifts_samples)

    print(
        f"Time shifts range: [{min_shift}, {max_shift}] samples "
        f"([{min_shift/sampling_frequency_hz:.6f}, {max_shift/sampling_frequency_hz:.6f}] seconds)"
    )

    # Allocate output array (same size initially)
    shifted_data = np.zeros_like(data, dtype=data.dtype)

    # Apply shifts by rolling each channel
    for ch in range(num_channels):
        shift = time_shifts_samples[ch]
        # Roll shifts the data: positive shift moves data forward in time
        shifted_data[:, ch] = np.roll(data[:, ch], shift)

    return shifted_data
