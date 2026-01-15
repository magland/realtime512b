# realtime512b

Real-time processing of multi-electrode neural data.

This is a restructured and reimplemented version of the realtime512 package.

## Installation

```bash
pip install -e .
```

For bin2py support:
```bash
pip install -e ".[bin2py]"
```

For full support (including clustering):
```bash
pip install -e ".[full]"
```

## Usage

### Initialize a new experiment

Create a new directory for your experiment and run:

```bash
cd experiment1
realtime512b init
```

This will:
1. Prompt you for configuration parameters
2. Ask you to place an `electrode_coords.txt` file in the directory
3. Create a `realtime512b.yaml` configuration file
4. Create the `acquisition/` directory

### Start real-time processing

```bash
realtime512b start
```

This will:
1. Monitor the `acquisition/` directory for new epochs
2. Process epochs into raw segments
3. Wait for a `reference_segment.txt` file
4. Generate computed data (filtered, shifted, statistics, etc.)

### Serve data via HTTP API (coming soon)

```bash
realtime512b serve
```

## Directory Structure

After initialization and processing, your experiment directory will contain:

```
experiment1/
├── realtime512b.yaml           # Configuration
├── electrode_coords.txt        # Electrode coordinates (512 lines, x y per line)
├── reference_segment.txt       # Reference segment path (e.g., epoch_001/segment_001.bin)
├── acquisition/                # Input data organized by epochs
│   └── epoch_001/              # Each epoch contains .bin files or bin2py folder
├── raw/                        # Rechunked raw segments
│   └── epoch_001/
│       ├── segment_001.bin
│       ├── segment_002.bin
│       └── ...
└── computed/                   # Computed data products
    ├── shift_coeffs.yaml
    ├── filt/                   # Filtered data
    │   └── epoch_001/
    │       ├── segment_001.bin.filt
    │       └── ...
    ├── shifted/                # Time-shifted data
    │   └── epoch_001/
    │       ├── segment_001.bin.shifted
    │       └── ...
    ├── stats/                  # Spike statistics
    │   └── epoch_001/
    │       ├── segment_001.bin.stats.json
    │       └── ...
    ├── high_activity/          # High activity intervals
    │   └── epoch_001/
    │       ├── segment_001.bin.high_activity.json
    │       └── ...
    └── reference_sorting/      # Spike sorting on reference segment
        └── epoch_001/
            └── segment_001.bin/
                ├── spike_times.npy
                ├── spike_labels.npy
                ├── spike_amplitudes.npy
                └── templates.npy
```

## Configuration

The `realtime512b.yaml` file contains all processing parameters:

```yaml
coarse_sorting_detect_threshold: -80
detect_threshold_for_spike_stats: -40
filter_params:
  highcut: 4000
  lowcut: 300
  order: 4
high_activity_threshold: 3
n_channels: 512
raw_segment_duration_sec: 10.0
sampling_frequency: 20000
use_bin2py: true
```
