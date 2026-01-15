# realtime512b

Real-time processing of multi-electrode neural data.

## Installation

```bash
pip install -e .
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
1. Monitor the `acquisition/` directory for new epoch blocks
2. Process epoch blocks into raw segments
3. Wait for a `reference_segment.txt` file
4. Generate computed data (filtered, shifted, statistics, etc.)

### Serve data via HTTP API

```bash
cd experiment1
realtime512b serve
```

### Open the dashboard

With the server running, open the dashboard in your web browser at
[https://](https://realtime512b-dashboard.vercel.app/)

You will be able to monitor the processing status and visualize data.

### Specifying the reference segment

After some initial processing runs, you will need to specify the reference segment by creating a `reference_segment.txt` file in the experiment directory. The file should contain one line with the text

```
epoch_block_name/segment_002.bin
```

where `epoch_block_name` is the name of the epoch block containing the reference segment, and `segment_002.bin` is the filename of the segment to use as reference.

You may want to use the second segment as the reference to avoid any startup artifacts in the first segment.

The reference segment will be used for the reference spike sorting and other reference computations.