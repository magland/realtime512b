"""Run the init command to set up a new experiment directory."""

import os
import sys
import yaml


def run_init():
    """Initialize a new experiment directory."""
    config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
    
    # Check if config already exists
    if os.path.exists(config_path):
        print("Configuration file already exists: realtime512b.yaml")
        print("If you want to reinitialize, please delete the existing config file first.")
        return
    
    # Check if directory is empty (allow electrode_coords.txt)
    dir_contents = [f for f in os.listdir(os.getcwd()) 
                    if f not in ("electrode_coords.txt",)]
    if len(dir_contents) > 0:
        print("❌ Error: Current directory is not empty.")
        print("Please run this command in an empty directory.")
        sys.exit(1)
    
    print("=" * 60)
    print("Initializing realtime512b experiment")
    print("=" * 60)
    print()
    
    # Collect configuration parameters with defaults
    config = {}
    
    # Sampling frequency
    fs_input = input("Enter sampling frequency (Hz) [default: 20000]: ").strip()
    config['sampling_frequency'] = int(fs_input) if fs_input else 20000
    
    # Number of channels
    n_channels_input = input("Enter number of channels [default: 512]: ").strip()
    config['n_channels'] = int(n_channels_input) if n_channels_input else 512
    
    # Raw segment duration
    duration_input = input("Enter raw segment duration (seconds) [default: 10.0]: ").strip()
    config['raw_segment_duration_sec'] = float(duration_input) if duration_input else 10.0
    
    # Use bin2py
    bin2py_input = input("Use bin2py for reading acquisition data? (y/n) [default: y]: ").strip().lower()
    config['use_bin2py'] = bin2py_input != 'n'
    
    # Filter parameters
    print("\nFilter parameters:")
    lowcut_input = input("  Lowcut frequency (Hz) [default: 300]: ").strip()
    highcut_input = input("  Highcut frequency (Hz) [default: 4000]: ").strip()
    order_input = input("  Filter order [default: 4]: ").strip()
    
    config['filter_params'] = {
        'lowcut': int(lowcut_input) if lowcut_input else 300,
        'highcut': int(highcut_input) if highcut_input else 4000,
        'order': int(order_input) if order_input else 4
    }
    
    # Detection thresholds
    print("\nDetection thresholds:")
    spike_stats_input = input("  Spike stats detect threshold [default: -40]: ").strip()
    config['detect_threshold_for_spike_stats'] = int(spike_stats_input) if spike_stats_input else -40
    
    coarse_sorting_input = input("  Coarse sorting detect threshold [default: -80]: ").strip()
    config['coarse_sorting_detect_threshold'] = int(coarse_sorting_input) if coarse_sorting_input else -80
    
    # High activity threshold
    high_activity_input = input("\nHigh activity threshold [default: 3]: ").strip()
    config['high_activity_threshold'] = int(high_activity_input) if high_activity_input else 3
    
    print()
    print("=" * 60)
    print("Configuration summary:")
    print("=" * 60)
    print(yaml.dump(config, default_flow_style=False))
    
    # Prompt for electrode coordinates file
    print("=" * 60)
    print("Please copy the electrode_coords.txt file to this directory.")
    print(f"The file must contain exactly {config['n_channels']} lines,")
    print("each with an x and y coordinate separated by whitespace.")
    print()
    input("Press Enter when the file is ready...")
    
    # Validate electrode_coords.txt
    electrode_coords_path = os.path.join(os.getcwd(), "electrode_coords.txt")
    if not os.path.exists(electrode_coords_path):
        print("❌ Error: electrode_coords.txt not found.")
        sys.exit(1)
    
    if not _validate_electrode_coords(electrode_coords_path, config['n_channels']):
        sys.exit(1)
    
    print("✓ electrode_coords.txt validated successfully")
    print()
    
    # Create config file
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✓ Configuration file created: {config_path}")
    
    # Create acquisition directory
    acquisition_dir = os.path.join(os.getcwd(), "acquisition")
    os.makedirs(acquisition_dir, exist_ok=True)
    print(f"✓ Created directory: {acquisition_dir}")
    
    print()
    print("=" * 60)
    print("Initialization complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Copy your acquisition data into acquisition/epoch_block_XXX/ directories")
    print("2. Run 'realtime512b start' to begin processing")
    print()


def _validate_electrode_coords(filepath, expected_channels):
    """Validate electrode_coords.txt file."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Remove empty lines
        lines = [line.strip() for line in lines if line.strip()]
        
        if len(lines) != expected_channels:
            print(f"❌ Error: electrode_coords.txt has {len(lines)} lines, "
                  f"expected {expected_channels}")
            return False
        
        # Validate each line has two numbers
        for i, line in enumerate(lines, 1):
            parts = line.split()
            if len(parts) != 2:
                print(f"❌ Error: Line {i} does not have exactly 2 values: {line}")
                return False
            try:
                float(parts[0])
                float(parts[1])
            except ValueError:
                print(f"❌ Error: Line {i} does not contain valid numbers: {line}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating electrode_coords.txt: {e}")
        return False
