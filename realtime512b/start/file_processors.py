"""File processors for creating computed data products."""

import os
import json
import time
import yaml
import numpy as np

from ..helpers.bandpass_filter import apply_bandpass_filter
from ..helpers.time_shifts import optimize_time_shift, apply_time_shifts
from ..helpers.high_activity_intervals import detect_high_activity_intervals
from ..helpers.channel_spike_stats import compute_channel_spike_stats
from ..helpers.coarse_sorting import compute_coarse_sorting
from ..helpers.spike_sorting import compute_spike_sorting
from ..helpers.epoch_block_spike_sorting import compute_epoch_block_spike_sorting
from ..helpers.file_info import create_info_file
from ..helpers.generate_preview import generate_preview, generate_epoch_block_preview


def get_reference_segment():
    """
    Read the reference_segment.txt file and return the path.
    Returns None if file doesn't exist or is invalid.
    """
    ref_path = os.path.join(os.getcwd(), "reference_segment.txt")
    
    if not os.path.exists(ref_path):
        return None
    
    with open(ref_path, 'r') as f:
        content = f.read().strip()
    
    if not content:
        return None
    
    return content


def is_reference_segment(epoch_block_name, segment_name, reference_segment):
    """Check if this segment is the reference segment."""
    if reference_segment is None:
        return False
    
    segment_path = f"{epoch_block_name}/{segment_name}"
    return segment_path == reference_segment


def process_filtering(raw_dir, computed_dir, n_channels, filter_params, sampling_frequency):
    """
    Create filtered versions of raw segments.
    Applies bandpass filter to raw data.
    Returns True if any processing was done.
    """
    something_processed = False
    
    # Find all raw segments
    if not os.path.exists(raw_dir):
        return False
    
    for epoch_block_name in sorted(os.listdir(raw_dir)):
        epoch_block_path = os.path.join(raw_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_path):
            continue
        
        for segment_name in sorted(os.listdir(epoch_block_path)):
            if not segment_name.endswith('.bin'):
                continue
            
            # Check if filtered version exists
            filt_dir = os.path.join(computed_dir, 'filt', epoch_block_name)
            filt_path = os.path.join(filt_dir, f"{segment_name}.filt")
            
            if os.path.exists(filt_path):
                continue
            
            # Create filtered version
            os.makedirs(filt_dir, exist_ok=True)
            
            raw_path = os.path.join(epoch_block_path, segment_name)
            
            # Apply bandpass filter with timing
            print(f"Filtering {epoch_block_name}/{segment_name}...")
            start_time = time.time()
            apply_bandpass_filter(
                input_path=raw_path,
                output_path=filt_path,
                num_channels=n_channels,
                lowcust=filter_params['lowcut'],
                highcut=filter_params['highcut'],
                fs=sampling_frequency,
                order=filter_params['order']
            )
            elapsed_time = time.time() - start_time
            
            # Create .info file
            create_info_file(filt_path, elapsed_time)
            
            print(f"Created filtered: {epoch_block_name}/{segment_name}.filt")
            something_processed = True
            return True  # Process one at a time
    
    return something_processed


def process_shift_coeffs(computed_dir, reference_segment, electrode_coords, sampling_frequency):
    """
    Create shift_coeffs.yaml based on reference segment.
    Optimizes time shift coefficients using variance maximization.
    Returns True if coefficients were created.
    """
    if reference_segment is None:
        return False
    
    coeffs_path = os.path.join(computed_dir, "shift_coeffs.yaml")
    
    if os.path.exists(coeffs_path):
        return False
    
    # Check if reference segment filtered version exists
    ref_filt_path = os.path.join(computed_dir, 'filt', f"{reference_segment}.filt")
    
    if not os.path.exists(ref_filt_path):
        return False
    
    # Optimize shift coefficients
    print(f"Optimizing shift coefficients using {reference_segment}...")
    c_x, c_y = optimize_time_shift(
        filtered_data_file_path=ref_filt_path,
        electrode_coords=electrode_coords,
        sampling_frequency_hz=sampling_frequency,
        duration_sec=0.5
    )
    
    # Write coefficients to file
    coeffs = {
        'c_x': float(c_x),
        'c_y': float(c_y)
    }
    
    with open(coeffs_path, 'w') as f:
        yaml.dump(coeffs, f)
    
    print(f"Created shift_coeffs.yaml with c_x={c_x:.6e}, c_y={c_y:.6e}")
    return True


def process_shifting(computed_dir, n_channels, electrode_coords, sampling_frequency):
    """
    Create shifted versions of filtered segments.
    Applies time shifts based on optimized coefficients.
    Returns True if any processing was done.
    """
    # Check if shift coeffs exist
    coeffs_path = os.path.join(computed_dir, "shift_coeffs.yaml")
    if not os.path.exists(coeffs_path):
        return False
    
    # Load shift coefficients
    with open(coeffs_path, 'r') as f:
        coeffs = yaml.safe_load(f)
    c_x = coeffs['c_x']
    c_y = coeffs['c_y']
    
    something_processed = False
    
    filt_dir = os.path.join(computed_dir, 'filt')
    if not os.path.exists(filt_dir):
        return False
    
    for epoch_block_name in sorted(os.listdir(filt_dir)):
        epoch_block_path = os.path.join(filt_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_path):
            continue
        
        for filt_name in sorted(os.listdir(epoch_block_path)):
            if not filt_name.endswith('.filt'):
                continue
            
            # Check if shifted version exists
            shifted_dir = os.path.join(computed_dir, 'shifted', epoch_block_name)
            shifted_path = os.path.join(shifted_dir, f"{filt_name}.shifted")
            
            if os.path.exists(shifted_path):
                continue
            
            # Create shifted version
            os.makedirs(shifted_dir, exist_ok=True)
            
            filt_path = os.path.join(epoch_block_path, filt_name)
            
            # Apply time shifts with timing
            segment_name = filt_name.replace('.filt', '')
            print(f"Applying time shifts to {epoch_block_name}/{segment_name}...")
            start_time = time.time()
            filt_data = np.fromfile(filt_path, dtype=np.int16).reshape(-1, n_channels)
            shifted_data = apply_time_shifts(
                data=filt_data,
                electrode_coords=electrode_coords,
                sampling_frequency_hz=sampling_frequency,
                c_x=c_x,
                c_y=c_y
            )
            shifted_data.astype(np.int16).tofile(shifted_path)
            elapsed_time = time.time() - start_time
            
            # Create .info file
            create_info_file(shifted_path, elapsed_time)
            
            print(f"Created shifted: {epoch_block_name}/{segment_name}.shifted")
            something_processed = True
            return True  # Process one at a time
    
    return something_processed


def process_stats(computed_dir, n_channels, sampling_frequency, detect_threshold_for_spike_stats):
    """
    Create stats files from filtered segments.
    Computes channel spike statistics (firing rates and amplitudes).
    Returns True if any processing was done.
    """
    something_processed = False
    
    filt_dir = os.path.join(computed_dir, 'filt')
    if not os.path.exists(filt_dir):
        return False
    
    for epoch_block_name in sorted(os.listdir(filt_dir)):
        epoch_block_path = os.path.join(filt_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_path):
            continue
        
        for filt_name in sorted(os.listdir(epoch_block_path)):
            if not filt_name.endswith('.filt'):
                continue
            
            # Check if stats file exists
            stats_dir = os.path.join(computed_dir, 'stats', epoch_block_name)
            stats_name = filt_name.replace('.filt', '.stats.json')
            stats_path = os.path.join(stats_dir, stats_name)
            
            if os.path.exists(stats_path):
                continue
            
            # Create stats file
            os.makedirs(stats_dir, exist_ok=True)
            
            filt_path = os.path.join(epoch_block_path, filt_name)
            segment_name = filt_name.replace('.bin.filt', '')
            
            print(f"Computing channel spike stats: {epoch_block_name}/{segment_name}.stats.json")
            start_time = time.time()
            filt_data = np.fromfile(filt_path, dtype=np.int16).reshape(-1, n_channels)
            mean_firing_rates, mean_spike_amplitudes = compute_channel_spike_stats(
                data=filt_data,
                sampling_frequency_hz=sampling_frequency,
                threshold=detect_threshold_for_spike_stats
            )
            
            stats_data = {
                "mean_firing_rates": mean_firing_rates.tolist(),
                "mean_spike_amplitudes": mean_spike_amplitudes.tolist()
            }
            
            with open(stats_path, 'w') as f:
                json.dump(stats_data, f, indent=2)
            elapsed_time = time.time() - start_time
            
            # Create .info file
            create_info_file(stats_path, elapsed_time)
            
            print(f"Created stats: {epoch_block_name}/{segment_name}.stats.json")
            something_processed = True
            return True  # Process one at a time
    
    return something_processed


def process_high_activity(computed_dir, n_channels, sampling_frequency, high_activity_threshold):
    """
    Create high_activity files from filtered segments.
    Detects periods of high activity using variance thresholding.
    Returns True if any processing was done.
    """
    something_processed = False
    
    filt_dir = os.path.join(computed_dir, 'filt')
    if not os.path.exists(filt_dir):
        return False
    
    for epoch_block_name in sorted(os.listdir(filt_dir)):
        epoch_block_path = os.path.join(filt_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_path):
            continue
        
        for filt_name in sorted(os.listdir(epoch_block_path)):
            if not filt_name.endswith('.filt'):
                continue
            
            # Check if high_activity file exists
            ha_dir = os.path.join(computed_dir, 'high_activity', epoch_block_name)
            ha_name = filt_name.replace('.filt', '.high_activity.json')
            ha_path = os.path.join(ha_dir, ha_name)
            
            if os.path.exists(ha_path):
                continue
            
            # Create high_activity file
            os.makedirs(ha_dir, exist_ok=True)
            
            filt_path = os.path.join(epoch_block_path, filt_name)
            segment_name = filt_name.replace('.bin.filt', '')
            
            print(f"Computing high activity intervals: {epoch_block_name}/{segment_name}.high_activity.json")
            start_time = time.time()
            num_frames = os.path.getsize(filt_path) // (2 * n_channels)
            high_activity_intervals = detect_high_activity_intervals(
                data_path=filt_path,
                num_channels=n_channels,
                num_frames=num_frames,
                sampling_frequency_hz=sampling_frequency,
                high_activity_threshold=high_activity_threshold
            )
            
            num_intervals = len(high_activity_intervals)
            print(f"  Found {num_intervals} high activity intervals.")
            if num_intervals > 0:
                total_high_activity_duration_sec = sum(end - start for start, end in high_activity_intervals)
                total_duration_sec = num_frames / sampling_frequency
                print(f"  Total high activity duration: {total_high_activity_duration_sec:.2f} sec out of {total_duration_sec:.2f} sec.")
            
            ha_data = {
                "high_activity_intervals": [
                    {"start_sec": start, "end_sec": end} for start, end in high_activity_intervals
                ]
            }
            
            with open(ha_path, 'w') as f:
                json.dump(ha_data, f, indent=2)
            elapsed_time = time.time() - start_time
            
            # Create .info file
            create_info_file(ha_path, elapsed_time)
            
            print(f"Created high_activity: {epoch_block_name}/{segment_name}.high_activity.json")
            something_processed = True
            return True  # Process one at a time
    
    return something_processed


def process_reference_sorting(computed_dir, reference_segment, n_channels, sampling_frequency, electrode_coords, coarse_sorting_detect_threshold):
    """
    Create reference sorting data for the reference segment.
    Performs coarse spike sorting using Isosplit clustering.
    Returns True if any processing was done.
    """
    if reference_segment is None:
        return False
    
    # Check if shifted version of reference exists
    shifted_path = os.path.join(computed_dir, 'shifted', f"{reference_segment}.filt.shifted")
    
    if not os.path.exists(shifted_path):
        return False
    
    # Check if high activity file exists
    high_activity_path = os.path.join(computed_dir, 'high_activity', f"{reference_segment}.high_activity.json")
    if not os.path.exists(high_activity_path):
        return False
    
    # Check if sorting directory exists
    sorting_dir = os.path.join(computed_dir, 'reference_sorting', reference_segment)
    
    if os.path.exists(sorting_dir):
        # Check if all files exist
        required_files = ['spike_times.npy', 'spike_labels.npy', 
                         'spike_amplitudes.npy', 'templates.npy']
        all_exist = all(os.path.exists(os.path.join(sorting_dir, f)) for f in required_files)
        if all_exist:
            return False
    
    # Create sorting directory
    os.makedirs(sorting_dir, exist_ok=True)
    
    # Load shifted data
    print(f"Computing coarse sorting: {reference_segment}")
    start_time = time.time()
    shifted_data = np.fromfile(shifted_path, dtype=np.int16).reshape(-1, n_channels)
    
    # Load high activity intervals
    with open(high_activity_path, 'r') as f:
        high_activity_data = json.load(f)
    high_activity_intervals = [
        (item['start_sec'], item['end_sec']) for item in high_activity_data['high_activity_intervals']
    ]
    
    # Perform coarse sorting
    templates, spike_times, spike_labels, spike_amplitudes = compute_coarse_sorting(
        shifted_data=shifted_data,
        high_activity_intervals=high_activity_intervals,
        sampling_frequency_hz=sampling_frequency,
        electrode_coords=electrode_coords,
        detect_threshold=coarse_sorting_detect_threshold,
        num_nearest_neighbors=20,
        num_clusters=100
    )
    elapsed_time = time.time() - start_time
    
    # Save outputs
    templates_path = os.path.join(sorting_dir, 'templates.npy')
    spike_times_path = os.path.join(sorting_dir, 'spike_times.npy')
    spike_labels_path = os.path.join(sorting_dir, 'spike_labels.npy')
    spike_amplitudes_path = os.path.join(sorting_dir, 'spike_amplitudes.npy')
    
    np.save(templates_path, templates)
    np.save(spike_times_path, spike_times)
    np.save(spike_labels_path, spike_labels)
    np.save(spike_amplitudes_path, spike_amplitudes)
    
    # Create .info file for the sorting directory (corresponds to the segment .bin file)
    create_info_file(sorting_dir.rstrip('/') + '.bin', elapsed_time)
    
    print(f"  Saved {len(spike_times)} spikes with {len(templates)} templates")
    print(f"Created reference_sorting: {reference_segment}")
    return True


def process_spike_sorting(computed_dir, reference_segment, n_channels, sampling_frequency, electrode_coords, coarse_sorting_detect_threshold):
    """
    Create spike sorting data for all segments by matching to reference sorting.
    Uses spike detection + nearest neighbor matching instead of clustering.
    Returns True if any processing was done.
    """
    if reference_segment is None:
        return False
    
    # Check if reference sorting exists
    reference_sorting_dir = os.path.join(computed_dir, 'reference_sorting', reference_segment)
    required_ref_files = ['spike_times.npy', 'spike_labels.npy', 'spike_amplitudes.npy', 'templates.npy']
    all_ref_exist = all(os.path.exists(os.path.join(reference_sorting_dir, f)) for f in required_ref_files)
    
    if not all_ref_exist:
        # Reference sorting not ready yet
        return False
    
    # Load reference sorting data
    ref_spike_times = np.load(os.path.join(reference_sorting_dir, 'spike_times.npy'))
    ref_spike_labels = np.load(os.path.join(reference_sorting_dir, 'spike_labels.npy'))
    
    # Load reference shifted data to extract spike frames
    ref_shifted_path = os.path.join(computed_dir, 'shifted', f"{reference_segment}.filt.shifted")
    if not os.path.exists(ref_shifted_path):
        return False
    
    ref_shifted_data = np.fromfile(ref_shifted_path, dtype=np.int16).reshape(-1, n_channels)
    
    # Extract reference spike frames
    ref_spike_inds = (ref_spike_times * sampling_frequency).astype(int)
    ref_spike_frames = ref_shifted_data[ref_spike_inds, :].astype(np.float32)
    
    something_processed = False
    
    # Find all shifted files
    shifted_dir = os.path.join(computed_dir, 'shifted')
    if not os.path.exists(shifted_dir):
        return False
    
    for epoch_block_name in sorted(os.listdir(shifted_dir)):
        epoch_block_path = os.path.join(shifted_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_path):
            continue
        
        for shifted_name in sorted(os.listdir(epoch_block_path)):
            if not shifted_name.endswith('.shifted'):
                continue
            
            # Extract segment name
            segment_name = shifted_name.replace('.filt.shifted', '')
            
            # Check if spike sorting already exists
            sorting_dir = os.path.join(computed_dir, 'spike_sorting', epoch_block_name, segment_name)
            
            if os.path.exists(sorting_dir):
                # Check if all files exist
                required_files = ['spike_times.npy', 'spike_labels.npy',
                                 'spike_amplitudes.npy', 'templates.npy']
                all_exist = all(os.path.exists(os.path.join(sorting_dir, f)) for f in required_files)
                if all_exist:
                    continue
            
            # Check if high activity file exists
            high_activity_path = os.path.join(computed_dir, 'high_activity', epoch_block_name, segment_name + '.high_activity.json')
            if not os.path.exists(high_activity_path):
                continue
            
            # Create spike sorting directory
            os.makedirs(sorting_dir, exist_ok=True)
            
            # Load shifted data
            shifted_path = os.path.join(epoch_block_path, shifted_name)
            print(f"Computing spike sorting: {epoch_block_name}/{segment_name}")
            start_time = time.time()
            shifted_data = np.fromfile(shifted_path, dtype=np.int16).reshape(-1, n_channels)
            
            # Load high activity intervals
            with open(high_activity_path, 'r') as f:
                high_activity_data = json.load(f)
            high_activity_intervals = [
                (item['start_sec'], item['end_sec']) for item in high_activity_data['high_activity_intervals']
            ]
            
            # Perform spike sorting
            templates, spike_times, spike_labels, spike_amplitudes = compute_spike_sorting(
                shifted_data=shifted_data,
                high_activity_intervals=high_activity_intervals,
                reference_spike_frames=ref_spike_frames,
                reference_spike_labels=ref_spike_labels,
                sampling_frequency_hz=sampling_frequency,
                electrode_coords=electrode_coords,
                detect_threshold=coarse_sorting_detect_threshold
            )
            elapsed_time = time.time() - start_time
            
            # Save outputs
            templates_path = os.path.join(sorting_dir, 'templates.npy')
            spike_times_path = os.path.join(sorting_dir, 'spike_times.npy')
            spike_labels_path = os.path.join(sorting_dir, 'spike_labels.npy')
            spike_amplitudes_path = os.path.join(sorting_dir, 'spike_amplitudes.npy')
            
            np.save(templates_path, templates)
            np.save(spike_times_path, spike_times)
            np.save(spike_labels_path, spike_labels)
            np.save(spike_amplitudes_path, spike_amplitudes)
            
            # Create .info file for the sorting directory (corresponds to the segment .bin file)
            create_info_file(sorting_dir.rstrip('/') + '.bin', elapsed_time)
            
            print(f"  Saved {len(spike_times)} spikes with {len(templates)} templates")
            print(f"Created spike_sorting: {epoch_block_name}/{segment_name}")
            something_processed = True
            return True  # Process one at a time
    
    return something_processed


def process_preview(computed_dir, reference_segment, n_channels, sampling_frequency, electrode_coords):
    """
    Create preview figpacks for segments.
    Generates basic previews for all segments (stats, movie, timeseries).
    For the reference segment, also includes sorting views (templates, autocorrelograms, etc.).
    Returns True if any processing was done.
    """
    something_processed = False
    
    filt_dir = os.path.join(computed_dir, 'filt')
    if not os.path.exists(filt_dir):
        return False
    
    for epoch_block_name in sorted(os.listdir(filt_dir)):
        epoch_block_path = os.path.join(filt_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_path):
            continue
        
        for filt_name in sorted(os.listdir(epoch_block_path)):
            if not filt_name.endswith('.filt'):
                continue
            
            # Extract segment name (remove .bin.filt suffix)
            segment_name = filt_name.replace('.bin.filt', '.bin')
            
            # Check if preview exists
            preview_dir = os.path.join(computed_dir, 'preview', epoch_block_name)
            preview_name = segment_name + '.figpack'
            preview_path = os.path.join(preview_dir, preview_name)
            
            if os.path.exists(preview_path):
                continue
            
            # Check dependencies
            filt_path = os.path.join(epoch_block_path, filt_name)
            shifted_path = os.path.join(computed_dir, 'shifted', epoch_block_name, filt_name + '.shifted')
            stats_path = os.path.join(computed_dir, 'stats', epoch_block_name, segment_name + '.stats.json')
            high_activity_path = os.path.join(computed_dir, 'high_activity', epoch_block_name, segment_name + '.high_activity.json')
            
            if not os.path.exists(filt_path):
                continue
            if not os.path.exists(shifted_path):
                continue
            if not os.path.exists(stats_path):
                continue
            if not os.path.exists(high_activity_path):
                continue
            
            # Check if this is the reference segment
            reference_sorting_path = None
            spike_sorting_path = None
            segment_path = f"{epoch_block_name}/{segment_name}"
            
            if reference_segment == segment_path:
                # This is the reference segment - check for sorting data
                potential_sorting_dir = os.path.join(computed_dir, 'reference_sorting', segment_path)
                required_files = ['templates.npy', 'spike_times.npy',
                                'spike_labels.npy', 'spike_amplitudes.npy']
                all_exist = all(os.path.exists(os.path.join(potential_sorting_dir, f)) for f in required_files)
                if all_exist:
                    reference_sorting_path = potential_sorting_dir
                else:
                    # Reference segment but sorting not ready yet
                    continue
            
            # Check for spike sorting data (for all segments)
            potential_spike_sorting_dir = os.path.join(computed_dir, 'spike_sorting', segment_path)
            required_files = ['templates.npy', 'spike_times.npy',
                            'spike_labels.npy', 'spike_amplitudes.npy']
            all_ss_exist = all(os.path.exists(os.path.join(potential_spike_sorting_dir, f)) for f in required_files)
            if all_ss_exist:
                spike_sorting_path = potential_spike_sorting_dir
            
            # Load high activity intervals
            with open(high_activity_path, 'r') as f:
                high_activity_data = json.load(f)
            high_activity_intervals = [
                (item['start_sec'], item['end_sec']) for item in high_activity_data['high_activity_intervals']
            ]
            
            # Create preview directory
            os.makedirs(preview_dir, exist_ok=True)
            
            # Generate preview
            print(f"Generating preview figpack: {epoch_block_name}/{segment_name}.figpack")
            start_time = time.time()
            generate_preview(
                epoch_block_name=epoch_block_name,
                segment_name=segment_name,
                filt_path=filt_path,
                shift_path=shifted_path,
                high_activity_intervals=high_activity_intervals,
                stats_path=stats_path,
                reference_sorting_path=reference_sorting_path,
                spike_sorting_path=spike_sorting_path,
                n_channels=n_channels,
                sampling_frequency=sampling_frequency,
                electrode_coords=electrode_coords,
                preview_path=preview_path
            )
            elapsed_time = time.time() - start_time
            
            # Create .info file for the preview directory (corresponds to the segment .bin file)
            create_info_file(os.path.join(preview_dir, segment_name), elapsed_time)
            
            print(f"Created preview: {epoch_block_name}/{segment_name}.figpack")
            something_processed = True
            return True  # Process one at a time
    
    return something_processed


def process_epoch_block_spike_sorting(raw_dir, computed_dir, n_channels, segment_duration_sec):
    """
    Create epoch_block-level spike sorting by combining segment spike sortings.
    Pieces together spike times, labels, and amplitudes from all segments,
    and computes templates as weighted mean of segment templates.
    Only processes epoch blocks where all segments have completed spike sorting.
    Returns True if any processing was done.
    """
    something_processed = False
    
    # Check if raw directory exists
    if not os.path.exists(raw_dir):
        return False
    
    # Check if spike_sorting directory exists
    spike_sorting_dir = os.path.join(computed_dir, 'spike_sorting')
    if not os.path.exists(spike_sorting_dir):
        return False
    
    # Iterate through epoch blocks in raw/ directory
    for epoch_block_name in sorted(os.listdir(raw_dir)):
        epoch_block_path = os.path.join(raw_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_path):
            continue
        
        # Check if epoch block spike sorting already exists
        epoch_block_sorting_dir = os.path.join(computed_dir, 'epoch_block_spike_sorting', epoch_block_name)
        
        if os.path.exists(epoch_block_sorting_dir):
            # Check if all files exist
            required_files = ['spike_times.npy', 'spike_labels.npy',
                             'spike_amplitudes.npy', 'templates.npy']
            all_exist = all(os.path.exists(os.path.join(epoch_block_sorting_dir, f)) for f in required_files)
            if all_exist:
                continue
        
        # Get all segments in this epoch_block
        segment_files = sorted([
            f for f in os.listdir(epoch_block_path)
            if f.endswith('.bin')
        ])
        
        if not segment_files:
            continue
        
        # Check if all segments have spike sorting completed
        segment_sortings = []
        all_segments_ready = True
        
        for segment_file in segment_files:
            segment_name = segment_file  # e.g., "segment_001.bin"
            segment_sorting_path = os.path.join(spike_sorting_dir, epoch_block_name, segment_name)
            
            # Check if sorting exists for this segment
            required_files = ['spike_times.npy', 'spike_labels.npy',
                             'spike_amplitudes.npy', 'templates.npy']
            all_files_exist = all(os.path.exists(os.path.join(segment_sorting_path, f)) for f in required_files)
            
            if not all_files_exist:
                all_segments_ready = False
                break
            
            # Extract segment number from filename (e.g., "segment_001.bin" -> 1)
            try:
                segment_num = int(segment_name.replace('segment_', '').replace('.bin', ''))
            except ValueError:
                all_segments_ready = False
                break
            
            # Load sorting data for this segment
            spike_times = np.load(os.path.join(segment_sorting_path, 'spike_times.npy'))
            spike_labels = np.load(os.path.join(segment_sorting_path, 'spike_labels.npy'))
            spike_amplitudes = np.load(os.path.join(segment_sorting_path, 'spike_amplitudes.npy'))
            templates = np.load(os.path.join(segment_sorting_path, 'templates.npy'))
            
            segment_sortings.append({
                'spike_times': spike_times,
                'spike_labels': spike_labels,
                'spike_amplitudes': spike_amplitudes,
                'templates': templates,
                'segment_num': segment_num
            })
        
        if not all_segments_ready:
            continue
        
        # All segments ready - compute epoch block spike sorting
        print(f"Computing epoch block spike sorting: {epoch_block_name}")
        start_time = time.time()
        
        templates, spike_times, spike_labels, spike_amplitudes = compute_epoch_block_spike_sorting(
            segment_sortings=segment_sortings,
            segment_duration_sec=segment_duration_sec,
            num_channels=n_channels
        )
        
        elapsed_time = time.time() - start_time
        
        # Save outputs
        os.makedirs(epoch_block_sorting_dir, exist_ok=True)
        
        templates_path = os.path.join(epoch_block_sorting_dir, 'templates.npy')
        spike_times_path = os.path.join(epoch_block_sorting_dir, 'spike_times.npy')
        spike_labels_path = os.path.join(epoch_block_sorting_dir, 'spike_labels.npy')
        spike_amplitudes_path = os.path.join(epoch_block_sorting_dir, 'spike_amplitudes.npy')
        
        np.save(templates_path, templates)
        np.save(spike_times_path, spike_times)
        np.save(spike_labels_path, spike_labels)
        np.save(spike_amplitudes_path, spike_amplitudes)
        
        # Create .info file
        create_info_file(epoch_block_sorting_dir.rstrip('/') + '.bin', elapsed_time)
        
        print(f"  Saved {len(spike_times)} spikes with {len(templates)} templates")
        print(f"Created epoch_block_spike_sorting: {epoch_block_name}")
        something_processed = True
        return True  # Process one at a time
    
    return something_processed


def process_epoch_block_preview(raw_dir, computed_dir, n_channels, sampling_frequency, segment_duration_sec, electrode_coords):
    """
    Create epoch block preview figpacks based on epoch block spike sorting.
    Generates previews showing templates, autocorrelograms, cluster separation,
    and time-binned firing rates across segments.
    Returns True if any processing was done.
    """
    something_processed = False
    
    # Check if raw directory exists
    if not os.path.exists(raw_dir):
        return False
    
    # Check if epoch_block_spike_sorting directory exists
    epoch_block_sorting_dir = os.path.join(computed_dir, 'epoch_block_spike_sorting')
    if not os.path.exists(epoch_block_sorting_dir):
        return False
    
    # Iterate through epoch blocks with completed spike sorting
    for epoch_block_name in sorted(os.listdir(epoch_block_sorting_dir)):
        epoch_block_sorting_path = os.path.join(epoch_block_sorting_dir, epoch_block_name)
        if not os.path.isdir(epoch_block_sorting_path):
            continue
        
        # Check if all required sorting files exist
        required_files = ['spike_times.npy', 'spike_labels.npy',
                         'spike_amplitudes.npy', 'templates.npy']
        all_exist = all(os.path.exists(os.path.join(epoch_block_sorting_path, f)) for f in required_files)
        if not all_exist:
            continue
        
        # Check if preview already exists
        epoch_block_preview_dir = os.path.join(computed_dir, 'epoch_block_preview', epoch_block_name)
        preview_path = os.path.join(epoch_block_preview_dir, 'epoch_block.figpack')
        
        if os.path.exists(preview_path):
            continue
        
        # Get number of segments in this epoch_block
        raw_epoch_block_dir = os.path.join(raw_dir, epoch_block_name)
        if not os.path.exists(raw_epoch_block_dir):
            continue
        
        segment_files = sorted([f for f in os.listdir(raw_epoch_block_dir) if f.endswith('.bin')])
        num_segments = len(segment_files)
        
        if num_segments == 0:
            continue
        
        # Create preview directory
        os.makedirs(epoch_block_preview_dir, exist_ok=True)
        
        # Generate epoch block preview
        print(f"Generating epoch block preview figpack: {epoch_block_name}/epoch_block.figpack")
        start_time = time.time()
        
        generate_epoch_block_preview(
            epoch_block_name=epoch_block_name,
            epoch_block_sorting_path=epoch_block_sorting_path,
            computed_dir=computed_dir,
            n_channels=n_channels,
            sampling_frequency=sampling_frequency,
            segment_duration_sec=segment_duration_sec,
            num_segments=num_segments,
            electrode_coords=electrode_coords,
            preview_path=preview_path
        )
        
        elapsed_time = time.time() - start_time
        
        # Create .info file
        create_info_file(os.path.join(epoch_block_preview_dir, 'epoch_block'), elapsed_time)
        
        print(f"Created epoch_block_preview: {epoch_block_name}/epoch_block.figpack")
        something_processed = True
        return True  # Process one at a time
    
    return something_processed
