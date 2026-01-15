"""Configuration utilities for loading and validating config files."""

import os
import sys
import yaml


def load_config():
    """Load and validate the configuration file."""
    config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
    
    if not os.path.exists(config_path):
        print("❌ Error: No configuration file found.")
        print("Please run 'realtime512b init' first to initialize the experiment.")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Configuration loaded:")
    print(yaml.dump(config, default_flow_style=False))
    
    # Validate required fields
    _validate_config(config)
    
    return config


def _validate_config(config):
    """Validate that all required configuration fields are present."""
    required_fields = [
        'sampling_frequency',
        'n_channels',
        'raw_segment_duration_sec',
        'use_bin2py',
        'filter_params',
        'detect_threshold_for_spike_stats',
        'coarse_sorting_detect_threshold',
        'high_activity_threshold'
    ]
    
    for field in required_fields:
        if field not in config:
            print(f"❌ Error: Missing required field '{field}' in configuration.")
            sys.exit(1)
    
    # Validate filter_params
    filter_params = config['filter_params']
    if not isinstance(filter_params, dict):
        print("❌ Error: filter_params must be a dictionary.")
        sys.exit(1)
    
    required_filter_fields = ['lowcut', 'highcut', 'order']
    for field in required_filter_fields:
        if field not in filter_params:
            print(f"❌ Error: Missing required field '{field}' in filter_params.")
            sys.exit(1)
    
    # Validate numeric values
    if not isinstance(config['sampling_frequency'], (int, float)):
        print("❌ Error: sampling_frequency must be numeric.")
        sys.exit(1)
    
    if not isinstance(config['n_channels'], int):
        print("❌ Error: n_channels must be an integer.")
        sys.exit(1)
    
    if config['detect_threshold_for_spike_stats'] >= 0:
        print("❌ Error: detect_threshold_for_spike_stats must be negative.")
        sys.exit(1)
    
    if config['coarse_sorting_detect_threshold'] >= 0:
        print("❌ Error: coarse_sorting_detect_threshold must be negative.")
        sys.exit(1)
    
    if config['high_activity_threshold'] < 0:
        print("❌ Error: high_activity_threshold must be non-negative.")
        sys.exit(1)


def load_electrode_coords(n_channels):
    """Load and validate electrode coordinates."""
    coords_path = os.path.join(os.getcwd(), "electrode_coords.txt")
    
    if not os.path.exists(coords_path):
        print("❌ Error: electrode_coords.txt not found.")
        sys.exit(1)
    
    coords = []
    with open(coords_path, 'r') as f:
        lines = f.readlines()
    
    lines = [line.strip() for line in lines if line.strip()]
    
    if len(lines) != n_channels:
        print(f"❌ Error: electrode_coords.txt has {len(lines)} lines, expected {n_channels}")
        sys.exit(1)
    
    for i, line in enumerate(lines, 1):
        parts = line.split()
        if len(parts) != 2:
            print(f"❌ Error: Line {i} does not have exactly 2 values")
            sys.exit(1)
        try:
            x = float(parts[0])
            y = float(parts[1])
            coords.append((x, y))
        except ValueError:
            print(f"❌ Error: Line {i} does not contain valid numbers")
            sys.exit(1)
    
    print(f"✓ Loaded {len(coords)} electrode coordinates")
    return coords
