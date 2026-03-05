# Realtime512b Experiment

This directory contains a realtime512b experiment for processing multi-electrode neural data.

## Directory Structure

```
.
├── realtime512b.yaml           # Configuration file
├── electrode_coords.txt        # Electrode coordinates (x, y)
├── reference_segment.txt       # Reference segment path (created after data processing)
├── acquisition/                # Input data directory
│   └── epoch_block_*/          # Epoch blocks (from data acquisition)
├── raw/                        # Processed raw segments
│   └── epoch_block_*/
│       └── segment_*.bin       # Raw binary data segments
└── computed/                   # All computed/derived data
    ├── filt/                   # Filtered data
    ├── shifted/                # Time-shifted data
    ├── stats/                  # Channel statistics
    ├── high_activity/          # High activity intervals
    ├── shift_coeffs.yaml       # Time shift coefficients
    ├── reference_sorting/      # Reference spike sorting
    ├── spike_sorting/          # Per-segment spike sorting
    ├── epoch_block_spike_sorting/  # Combined spike sorting
    ├── receptive_fields/       # Receptive field analysis
    ├── preview/                # Segment previews
    └── epoch_block_preview/    # Epoch block previews
```

## Configuration

### realtime512b.yaml

Contains experiment parameters:
- `sampling_frequency`: Sampling rate in Hz (e.g., 20000)
- `n_channels`: Number of electrode channels (e.g., 512)
- `raw_segment_duration_sec`: Duration of each segment in seconds (e.g., 10.0)
- `use_bin2py`: Whether to use bin2py for reading acquisition data (boolean)
- `filter_params`: Bandpass filter settings
  - `lowcut`: Low cutoff frequency in Hz (e.g., 300)
  - `highcut`: High cutoff frequency in Hz (e.g., 4000)
  - `order`: Filter order (e.g., 4)
- `detect_threshold_for_spike_stats`: Threshold for spike detection in stats (e.g., -40)
- `coarse_sorting_detect_threshold`: Threshold for spike detection in sorting (e.g., -80)
- `high_activity_threshold`: Threshold for high activity detection (e.g., 3)

### electrode_coords.txt

Plain text file with one line per channel, containing x and y coordinates separated by whitespace:
```
x1 y1
x2 y2
...
```
Must have exactly `n_channels` lines.

### reference_segment.txt

Created after initial processing to specify which segment to use as reference for spike sorting.
Contains a single line with the path to the reference segment:
```
epoch_block_001/segment_002.bin
```

## Data Formats

### Raw Binary Data (.bin files)

- **Format**: Binary files containing int16 data
- **Shape**: `(num_samples, n_channels)` stored in row-major (C) order
- **Location**: `raw/epoch_block_*/segment_*.bin`
- **Reading in Python**:
  ```python
  import numpy as np
  data = np.fromfile(filepath, dtype=np.int16).reshape(-1, n_channels)
  ```

### Filtered Data (.filt files)

- **Format**: Same as raw .bin files (int16, multi-channel)
- **Location**: `computed/filt/epoch_block_*/segment_*.bin.filt`
- **Content**: Bandpass filtered version of raw data

### Shifted Data (.shifted files)

- **Format**: Same as raw .bin files (int16, multi-channel)
- **Location**: `computed/shifted/epoch_block_*/segment_*.bin.filt.shifted`
- **Content**: Time-aligned data using optimized shift coefficients

### Statistics (.stats.json files)

- **Format**: JSON
- **Location**: `computed/stats/epoch_block_*/segment_*.stats.json`
- **Structure**:
  ```json
  {
    "mean_firing_rates": [rate1, rate2, ...],      // n_channels values
    "mean_spike_amplitudes": [amp1, amp2, ...]     // n_channels values
  }
  ```

### High Activity Intervals (.high_activity.json files)

- **Format**: JSON
- **Location**: `computed/high_activity/epoch_block_*/segment_*.high_activity.json`
- **Structure**:
  ```json
  {
    "high_activity_intervals": [
      {"start_sec": 1.2, "end_sec": 3.4},
      {"start_sec": 5.6, "end_sec": 7.8}
    ]
  }
  ```

### Spike Sorting Data

Each spike sorting directory contains:

#### templates.npy
- **Format**: NumPy array (float32)
- **Shape**: `(num_units, n_channels)`
- **Content**: Average spike waveform for each unit across all channels

#### spike_times.npy
- **Format**: NumPy array (float64)
- **Shape**: `(num_spikes,)`
- **Content**: Spike times in seconds
- **Note**: For epoch_block_spike_sorting, times are relative to epoch block start

#### spike_labels.npy
- **Format**: NumPy array (int32)
- **Shape**: `(num_spikes,)`
- **Content**: Unit labels for each spike (1-based indexing)

#### spike_amplitudes.npy
- **Format**: NumPy array (float32)
- **Shape**: `(num_spikes,)`
- **Content**: Amplitude of each spike

### Spike Sorting Types

#### Reference Sorting
- **Location**: `computed/reference_sorting/epoch_block_*/segment_*.bin/`
- **Method**: Coarse sorting using Isosplit clustering
- **Purpose**: Establishes unit templates for the reference segment

#### Spike Sorting (Per-Segment)
- **Location**: `computed/spike_sorting/epoch_block_*/segment_*.bin/`
- **Method**: Spike detection + nearest neighbor matching to reference units
- **Purpose**: Identifies spikes in each segment using reference templates

#### Epoch Block Spike Sorting
- **Location**: `computed/epoch_block_spike_sorting/epoch_block_*/`
- **Method**: Combines all segment spike sortings for an epoch block
- **Content**: Concatenated spike times/labels/amplitudes, averaged templates

### Receptive Fields

#### receptive_fields.npy
- **Format**: NumPy array (float32)
- **Shape**: `(num_units, num_timepoints, width, height, channels)`
  - `num_units`: Number of sorted units
  - `num_timepoints`: Typically 60
  - `width`: Typically 127
  - `height`: Typically 203
  - `channels`: 3 (RGB)
- **Location**: `computed/receptive_fields/epoch_block_*/receptive_fields.npy`
- **Content**: Spatiotemporal receptive field for each unit

### Preview Files (.figpack)

- **Format**: Figpack bundle (JSON + binary data)
- **Location**: 
  - Segment: `computed/preview/epoch_block_*/segment_*.figpack`
  - Epoch block: `computed/epoch_block_preview/epoch_block_*/epoch_block.figpack`
- **Content**: Interactive visualizations (templates, autocorrelograms, movies, etc.)

### Info Files (.info)

- **Format**: JSON
- **Naming**: Same as associated file but with `.info` extension
- **Structure**:
  ```json
  {
    "elapsed_time_sec": 12.34
  }
  ```
- **Purpose**: Records processing time for each computed artifact

### Shift Coefficients

#### shift_coeffs.yaml
- **Format**: YAML
- **Location**: `computed/shift_coeffs.yaml`
- **Structure**:
  ```yaml
  c_x: 1.23e-05
  c_y: 4.56e-05
  ```
- **Content**: Optimized time shift coefficients for spatial alignment

## Processing Pipeline

The processing pipeline runs automatically when you execute `realtime512b start`:

1. **Epoch Block Processing**: Converts acquisition data to raw segments
2. **Filtering**: Applies bandpass filter to raw data
3. **Shift Coefficient Optimization**: Computes optimal time shifts using reference segment
4. **Time Shifting**: Applies time shifts to filtered data
5. **Statistics**: Computes channel firing rates and spike amplitudes
6. **High Activity Detection**: Identifies periods of high neural activity
7. **Reference Sorting**: Performs clustering on reference segment
8. **Spike Sorting**: Matches spikes in all segments to reference units
9. **Epoch Block Spike Sorting**: Combines segment sortings into epoch block sorting
10. **Receptive Fields**: Computes receptive fields from spike data
11. **Preview Generation**: Creates visualization figpacks

### Dependencies

The pipeline respects these dependencies:
- Filtering requires raw segments
- Shift coefficients require reference segment + filtered data
- Shifting requires filtered data + shift coefficients
- Stats require filtered data
- High activity requires filtered data
- Reference sorting requires shifted data + high activity
- Spike sorting requires reference sorting + shifted data + high activity
- Epoch block sorting requires all segment sortings to be complete
- Receptive fields require epoch block sorting
- Previews require various computed artifacts depending on view type

### Processing Mode

Processing runs iteratively:
- Checks for new/missing files every 5 seconds
- Processes one file at a time (returns after each file)
- Prints status when all files are up to date

## Working with This Experiment

### For AI Assistants

When working with this experiment:

1. **File Relationships**: Understand the naming convention:
   - Raw: `epoch_block_001/segment_002.bin`
   - Filtered: `computed/filt/epoch_block_001/segment_002.bin.filt`
   - Shifted: `computed/shifted/epoch_block_001/segment_002.bin.filt.shifted`
   - Stats: `computed/stats/epoch_block_001/segment_002.stats.json`
   - Sorting: `computed/spike_sorting/epoch_block_001/segment_002.bin/`

2. **Data Loading**: Use appropriate methods for each format:
   - Binary (.bin, .filt, .shifted): `np.fromfile(..., dtype=np.int16).reshape(-1, n_channels)`
   - NumPy (.npy): `np.load(filepath)`
   - JSON (.json): `json.load(open(filepath))`
   - YAML (.yaml): `yaml.safe_load(open(filepath))`

3. **Time Units**: 
   - Spike times are in seconds
   - Convert to sample indices: `sample_index = spike_time * sampling_frequency`

4. **Coordinates**: Electrode coordinates are in (x, y) format from electrode_coords.txt

5. **Units**: Spike labels are 1-based (first unit is label 1, not 0)

### Key Files to Check

- **Configuration**: `realtime512b.yaml`
- **Reference Segment**: `reference_segment.txt` (if it exists)
- **Latest Processing**: Check timestamps of files in `computed/` directories
- **Errors**: Check terminal output from `realtime512b start`

### Common Operations

**Get number of segments in an epoch block**:
```python
import os
segment_files = [f for f in os.listdir('raw/epoch_block_001') if f.endswith('.bin')]
num_segments = len(segment_files)
```

**Load spike sorting for a segment**:
```python
import numpy as np
sorting_dir = 'computed/spike_sorting/epoch_block_001/segment_002.bin'
spike_times = np.load(f'{sorting_dir}/spike_times.npy')
spike_labels = np.load(f'{sorting_dir}/spike_labels.npy')
templates = np.load(f'{sorting_dir}/templates.npy')
```

**Check if reference sorting is complete**:
```python
import os
ref_segment = open('reference_segment.txt').read().strip()
sorting_dir = f'computed/reference_sorting/{ref_segment}'
required = ['templates.npy', 'spike_times.npy', 'spike_labels.npy', 'spike_amplitudes.npy']
complete = all(os.path.exists(f'{sorting_dir}/{f}') for f in required)
```

## Additional Notes

- All binary data uses int16 format for memory efficiency
- Templates and receptive fields use float32 for precision
- Spike times use float64 for temporal precision
- Processing creates .info files to track computation time
- The system is designed for real-time processing as data arrives
- Files are processed incrementally (one at a time) to allow monitoring progress
