import os
import numpy as np

def get_litke_triggers(bin_path, RW_BLOCKSIZE=2000000, TTL_THRESHOLD=-1000):
    import bin2py
    epoch_starts = []
    epoch_ends = []
    with bin2py.PyBinFileReader(bin_path, chunk_samples=RW_BLOCKSIZE, is_row_major=True) as pbfr:
        array_id = pbfr.header.array_id
        n_samples = pbfr.length
        for start_idx in range(0, n_samples, RW_BLOCKSIZE):
            n_samples_to_get = min(RW_BLOCKSIZE, n_samples - start_idx)
            samples = pbfr.get_data_for_electrode(0, start_idx, n_samples_to_get)
            # Find the threshold crossings at the beginning and end of each epoch.
            below_threshold = (samples < TTL_THRESHOLD)
            above_threshold = np.logical_not(below_threshold)
            # Epoch starts.
            above_to_below_threshold = np.logical_and.reduce([
                above_threshold[:-1],
                below_threshold[1:]
            ])
            trigger_indices = np.argwhere(above_to_below_threshold) + start_idx
            epoch_starts.append(trigger_indices[:, 0])
            below_to_above_threshold = np.logical_and.reduce([
                below_threshold[:-1],
                above_threshold[1:]
            ])
            trigger_indices = np.argwhere(below_to_above_threshold) + start_idx
            epoch_ends.append(trigger_indices[:, 0])
    epoch_starts = np.concatenate(epoch_starts, axis=0)
    epoch_ends = np.concatenate(epoch_ends, axis=0)
    return epoch_starts, epoch_ends, array_id, n_samples

def save_spike_times_vision_format(
    raw_data_path,          # Path to raw epoch block folder
    spike_times,            # 1D array of spike times (samples or seconds)
    spike_labels,           # 1D array of cluster labels (int, 1-based for Vision)
    vision_path,            # Directory to save Vision files
    vision_dset_name,       # Dataset name (e.g. "data000")
    neuron_time_offset=0    # Optional offset to add to spike times
):
    """
    Save spike times and cluster labels in Vision .neurons and .globals format.
    """
    import visionwriter as vw
    # Remove existing files if present
    neurons_file = os.path.join(vision_path, vision_dset_name + '.neurons')
    globals_file = os.path.join(vision_path, vision_dset_name + '.globals')
    if os.path.exists(neurons_file):
        os.remove(neurons_file)
    if os.path.exists(globals_file):
        os.remove(globals_file)

    # Extract TTL times from raw data
    ttl_times, _, array_id, n_samples = get_litke_triggers(raw_data_path)

    # Write .globals file (Litke format)
    with vw.GlobalsFileWriter(vision_path, vision_dset_name) as gfw:
        gfw.write_simplified_litke_array_globals_file(
            array_id & 0xFFF,  # Litke array ID mask
            0,                 # start_sample
            0,                 # start_time
            'Realtime512b export',
            '',
            0,
            n_samples
        )

    # Organize spikes by cell ID. realtime512b uses 1-based IDs just like Vision so don't need to increment.
    spikes_by_cell_id = {}
    for spike_time, spike_id in zip(spike_times, spike_labels):
        cell_id = int(spike_id)
        if cell_id not in spikes_by_cell_id:
            spikes_by_cell_id[cell_id] = []
        spikes_by_cell_id[cell_id].append(spike_time + neuron_time_offset)

    # Convert lists to numpy arrays
    spikes_by_cell_id_np = {cid: np.array(times) for cid, times in spikes_by_cell_id.items()}

    # Write .neurons file
    with vw.NeuronsFileWriter(vision_path, vision_dset_name) as nfw:
        nfw.write_neuron_file(spikes_by_cell_id_np, ttl_times, n_samples)

    print(f"Saved Vision .neurons and .globals files to {vision_path} for dataset {vision_dset_name}")