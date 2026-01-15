"""Run the start command to begin real-time processing."""

import os
import sys
import time

from .config_utils import load_config, load_electrode_coords
from .epoch_block_processor import EpochBlockProcessor
from .build_utils import build_ui_components, BuildError


def run_start():
    """Main entry point for realtime512b processing."""

    # Build UI components first
    print("=" * 60)
    print("Building UI components...")
    print("=" * 60)
    try:
        build_ui_components()
        print("=" * 60)
        print()
    except BuildError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print("\nUI build failed. Cannot continue.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during UI build: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 60)
    print("realtime512b - Starting real-time processing")
    print("=" * 60)
    print()

    # Import these after building UI
    from .file_processors import (
        get_reference_segment,
        process_filtering,
        process_shift_coeffs,
        process_shifting,
        process_stats,
        process_high_activity,
        process_reference_sorting,
        process_spike_sorting,
        process_epoch_block_spike_sorting,
        process_preview,
        process_epoch_block_preview
    )
    
    # Load configuration
    config = load_config()
    
    # Extract configuration parameters
    n_channels = config['n_channels']
    sampling_frequency = config['sampling_frequency']
    segment_duration_sec = config['raw_segment_duration_sec']
    use_bin2py = config['use_bin2py']
    filter_params = config['filter_params']
    detect_threshold_for_spike_stats = config['detect_threshold_for_spike_stats']
    coarse_sorting_detect_threshold = config['coarse_sorting_detect_threshold']
    high_activity_threshold = config['high_activity_threshold']
    
    # Load electrode coordinates
    electrode_coords = load_electrode_coords(n_channels)
    
    # Setup directories
    acquisition_dir = os.path.join(os.getcwd(), "acquisition")
    raw_dir = os.path.join(os.getcwd(), "raw")
    computed_dir = os.path.join(os.getcwd(), "computed")
    
    # Create directories if they don't exist
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(computed_dir, exist_ok=True)
    
    # Create epoch block processor
    epoch_block_processor = EpochBlockProcessor(
        acquisition_dir=acquisition_dir,
        raw_dir=raw_dir,
        n_channels=n_channels,
        sampling_frequency=sampling_frequency,
        segment_duration_sec=segment_duration_sec,
        use_bin2py=use_bin2py
    )
    
    print("=" * 60)
    print("Monitoring for data...")
    print("=" * 60)
    print()
    
    # Main processing loop
    up_to_date_printed = False
    reference_segment_warning_printed = False
    
    while True:
        something_processed = False
        
        # Process acquisition epoch blocks-> raw segments
        if epoch_block_processor.process_epoch_blocks():
            something_processed = True
            up_to_date_printed = False
        
        # Get reference segment
        reference_segment = get_reference_segment()
        
        if reference_segment is None:
            # Wait for reference segment
            if not reference_segment_warning_printed:
                print("Waiting for reference_segment.txt file...")
                print("Please create this file with the path to the reference segment.")
                print("Example content: epoch_block_001/segment_001.bin")
                print()
                reference_segment_warning_printed = True
        else:
            reference_segment_warning_printed = False
            
            # Verify reference segment exists in raw/
            ref_raw_path = os.path.join(raw_dir, reference_segment)
            if not os.path.exists(ref_raw_path):
                if not up_to_date_printed:
                    print(f"Reference segment {reference_segment} not yet in raw/, waiting...")
            else:
                # Process filtering
                if process_filtering(raw_dir, computed_dir, n_channels, filter_params, sampling_frequency):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process shift coefficients (only for reference)
                if process_shift_coeffs(computed_dir, reference_segment, electrode_coords, sampling_frequency):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process shifting
                if process_shifting(computed_dir, n_channels, electrode_coords, sampling_frequency):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process stats
                if process_stats(computed_dir, n_channels, sampling_frequency, detect_threshold_for_spike_stats):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process high activity
                if process_high_activity(computed_dir, n_channels, sampling_frequency, high_activity_threshold):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process reference sorting
                if process_reference_sorting(computed_dir, reference_segment, n_channels, sampling_frequency, electrode_coords, coarse_sorting_detect_threshold):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process spike sorting
                if process_spike_sorting(computed_dir, reference_segment, n_channels, sampling_frequency, electrode_coords, coarse_sorting_detect_threshold):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process epoch block spike sorting
                if process_epoch_block_spike_sorting(raw_dir, computed_dir, n_channels, segment_duration_sec):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process epoch block preview generation
                if process_epoch_block_preview(raw_dir, computed_dir, n_channels, sampling_frequency, segment_duration_sec, electrode_coords):
                    something_processed = True
                    up_to_date_printed = False
                
                # Process preview generation
                if process_preview(computed_dir, reference_segment, n_channels, sampling_frequency, electrode_coords):
                    something_processed = True
                    up_to_date_printed = False
        
        # Print status
        if not something_processed:
            if not up_to_date_printed:
                print("All files are up to date.")
                print()
                up_to_date_printed = True
        
        # Sleep for 5 seconds
        time.sleep(5)


if __name__ == "__main__":
    run_start()
