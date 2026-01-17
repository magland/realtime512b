#!/usr/bin/env python3
"""
Visualize detected event (spike) frames using ClusterLens.

This script loads spike timing data from the spike sorting output and extracts
the corresponding frames from the raw data file, then visualizes them using
ClusterLens with UMAP dimensionality reduction.

Usage:
    python extract_event_frames.py

Example:
    python extract_event_frames.py --epoch epoch_001 --segment segment_002.bin
"""

import argparse
import os
import sys
import numpy as np
import yaml
from figpack_experimental.views import ClusterLens


def load_config():
    """Load configuration from realtime512b.yaml in current directory."""
    config_path = "realtime512b.yaml"
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please run this script from an experiment directory."
        )
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def extract_event_frames(
    shifted_path,
    spike_times_path,
    spike_labels_path,
    n_channels,
    sampling_frequency
):
    """
    Extract frames at spike times from shifted data.
    
    Parameters
    ----------
    shifted_path : str
        Path to shifted .shifted file
    spike_times_path : str
        Path to spike_times.npy file
    spike_labels_path : str
        Path to spike_labels.npy file
    n_channels : int
        Number of channels in the data
    sampling_frequency : float
        Sampling frequency in Hz
    
    Returns
    -------
    frames : np.ndarray
        Array of shape (num_spikes, num_channels) containing the frames
    labels : np.ndarray
        Array of shape (num_spikes,) containing the cluster labels
    """
    # Check if files exist
    if not os.path.exists(shifted_path):
        raise FileNotFoundError(f"Shifted data file not found: {shifted_path}")
    
    if not os.path.exists(spike_times_path):
        raise FileNotFoundError(f"Spike times file not found: {spike_times_path}")
    
    if not os.path.exists(spike_labels_path):
        raise FileNotFoundError(f"Spike labels file not found: {spike_labels_path}")
    
    # Load spike times (in seconds)
    print(f"Loading spike times from {spike_times_path}...")
    spike_times = np.load(spike_times_path)
    num_spikes = len(spike_times)
    print(f"  Found {num_spikes} spikes")
    
    # Load spike labels
    print(f"Loading spike labels from {spike_labels_path}...")
    spike_labels = np.load(spike_labels_path)
    print(f"  Found {len(spike_labels)} labels")
    
    # Convert spike times to frame indices
    spike_inds = (spike_times * sampling_frequency).astype(int)
    
    # Load shifted data
    print(f"Loading shifted data from {shifted_path}...")
    shifted_data = np.fromfile(shifted_path, dtype=np.int16)
    num_frames = len(shifted_data) // n_channels
    shifted_data = shifted_data.reshape(num_frames, n_channels)
    print(f"  Shifted data shape: {shifted_data.shape}")
    
    # Validate spike indices
    valid_mask = (spike_inds >= 0) & (spike_inds < num_frames)
    if not np.all(valid_mask):
        num_invalid = np.sum(~valid_mask)
        print(f"  Warning: {num_invalid} spikes are out of bounds and will be skipped")
        spike_inds = spike_inds[valid_mask]
        spike_labels = spike_labels[valid_mask]
    
    # Extract frames at spike times
    print(f"Extracting {len(spike_inds)} event frames...")
    frames = shifted_data[spike_inds, :].astype(np.float32)
    print(f"  Event frames shape: {frames.shape}")
    print(f"  Data type: {frames.dtype}")
    
    return frames, spike_labels


def main():
    parser = argparse.ArgumentParser(
        description="Visualize detected event frames using ClusterLens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize from default segment
  python extract_event_frames.py
  
  # Specify different segment
  python extract_event_frames.py --segment segment_001.bin
  
  # Specify different epoch
  python extract_event_frames.py --epoch epoch_002
"""
    )
    
    parser.add_argument(
        "--epoch",
        type=str,
        default="epoch_001",
        help="Epoch block name (default: epoch_001)"
    )
    
    parser.add_argument(
        "--segment",
        type=str,
        default="segment_002.bin",
        help="Segment file name (default: segment_002.bin)"
    )
    
    parser.add_argument(
        "--use-reference-sorting",
        action="store_true",
        help="Use reference sorting instead of regular spike sorting"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    n_channels = config['n_channels']
    sampling_frequency = config['sampling_frequency']
    
    print("=" * 70)
    print("Event Frames ClusterLens Visualization")
    print("=" * 70)
    print(f"Epoch: {args.epoch}")
    print(f"Segment: {args.segment}")
    print(f"Channels: {n_channels}")
    print(f"Sampling frequency: {sampling_frequency} Hz")
    print()
    
    # Construct paths
    segment_name = args.segment.replace('.bin', '')
    shifted_path = os.path.join("computed", "shifted", args.epoch, args.segment + ".filt.shifted")
    
    if args.use_reference_sorting:
        # For reference sorting, path is different
        spike_times_path = os.path.join(
            "computed",
            "reference_sorting",
            args.epoch,
            args.segment,
            "spike_times.npy"
        )
    else:
        # For regular spike sorting
        spike_times_path = os.path.join(
            "computed",
            "spike_sorting",
            args.epoch,
            args.segment,
            "spike_times.npy"
        )
    
    # Determine spike labels path (same directory as spike_times_path)
    spike_labels_path = spike_times_path.replace("spike_times.npy", "spike_labels.npy")
    
    try:
        frames, labels = extract_event_frames(
            shifted_path=shifted_path,
            spike_times_path=spike_times_path,
            spike_labels_path=spike_labels_path,
            n_channels=n_channels,
            sampling_frequency=sampling_frequency
        )
        
        print()
        print("=" * 70)
        print("Creating ClusterLens Visualization")
        print("=" * 70)
        print(f"Data shape: {frames.shape}")
        print(f"Number of spikes: {frames.shape[0]}")
        print(f"Number of channels (dimensions): {frames.shape[1]}")
        print(f"Number of unique clusters: {len(np.unique(labels))}")
        print(f"Cluster labels range: {np.min(labels)} to {np.max(labels)}")
        print()
        
        # Create ClusterLens view with cluster labels
        view = ClusterLens(data=frames, cluster_labels=labels)
        title = f"Event Frames - {args.epoch}/{args.segment}"
        print(f"Opening ClusterLens view: {title}")
        view.show(title=title, open_in_browser=True)
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR!")
        print("=" * 70)
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
