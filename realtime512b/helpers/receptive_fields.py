"""Helper function for computing receptive fields from spike data."""

import numpy as np
import subprocess
import os
import yaml
import visionloader as vl

def load_stas(sta_dir, datafile_name) -> np.ndarray:
    print(f'Loading STAs from {sta_dir} for datafile {datafile_name}')
    vcd = vl.load_vision_data(sta_dir, datafile_name, include_sta=True)

    ls_ids = vcd.get_cell_ids()
    print(f'Found {len(ls_ids)} cells in the STA data.')
    n_cells = len(ls_ids)
    sta = getattr(vcd.get_sta_for_cell(ls_ids[0]), 'red')
    sta = np.moveaxis(sta, 2, 0)
    n_frames, n_height, n_width = sta.shape[0], sta.shape[1], sta.shape[2]
    n_channels = 3

    stas = np.zeros((n_cells, n_frames, n_height, n_width, n_channels))
    ls_channels = ['red', 'green', 'blue']
    for i in range(n_cells):
        for j, channel in enumerate(ls_channels):
            sta = getattr(vcd.get_sta_for_cell(ls_ids[i]), channel) # ht x wt x t
            sta = np.moveaxis(sta, 2, 0) # t x ht x wt
            stas[i, :, :, :, j] = sta
    stas = np.array(stas)
    return stas


def compute_receptive_fields(parent_dir, epoch_block_name) -> np.ndarray:
    """
    Compute receptive fields for all units.
    
    This is a placeholder implementation that generates random noise.
    The actual implementation will be filled in by a colleague.
    
    Parameters
    ----------
    spike_times : np.ndarray
        Spike times in seconds, shape (num_spikes,)
    spike_labels : np.ndarray
        Spike unit labels (1-based), shape (num_spikes,)
    acquisition_dir : str
        Path to the acquisition directory for this epoch block
        
    Returns
    -------
    receptive_fields : np.ndarray
        5-dimensional array with shape (num_units, num_timepoints, width, height, channels)
        - Dim 0: Unit index (number of units in the sorting)
        - Dim 1: Timepoint (typically 60)
        - Dim 2: X spatial coordinate (typically 127)
        - Dim 3: Y spatial coordinate (typically 203)
        - Dim 4: Color channel (3: RGB)
    """
    # Load config to get exp_name
    config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    exp_name = config.get("exp_name")
    sta_script_path = '/home/vyomr/Desktop/gitrepos/realtime512b/realtime512b/helpers/compute_sta.sh'

    # Call external script to compute STA with subprocess
    sta_out_path = os.path.join(parent_dir, epoch_block_name, 'rt512', f'{epoch_block_name}.sta')

    if not os.path.exists(sta_out_path):
        print(f'Computing receptive fields for {exp_name} epoch block: {epoch_block_name}')
        subprocess.run(['bash', sta_script_path, exp_name, epoch_block_name], check=True)
    else:
        print(f'STA already computed for {exp_name} epoch block: {epoch_block_name}.')
    
    sta_dir = os.path.dirname(sta_out_path)
    stas = load_stas(sta_dir, epoch_block_name)
    return stas
