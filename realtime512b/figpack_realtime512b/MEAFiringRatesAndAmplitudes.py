"""MEA Firing Rates and Amplitudes view for realtime512b."""

from typing import Union

import numpy as np

import figpack
from .figpack_realtime512b_extension import figpack_realtime512b_extension


class MEAFiringRatesAndAmplitudes(figpack.ExtensionView):
    def __init__(
        self,
        electrode_coords: Union[np.ndarray, list[list[float]]],
        mean_firing_rates: np.ndarray,
        mean_spike_amplitudes: np.ndarray
    ):
        super().__init__(
            extension=figpack_realtime512b_extension, view_type="realtime512b.MEAFiringRatesAndAmplitudes"
        )

        # Validate that arrays are 2D (num_frames x num_channels)
        if mean_firing_rates.ndim != 2:
            raise ValueError(f"mean_firing_rates must be 2D array (num_frames, num_channels), got shape {mean_firing_rates.shape}")
        if mean_spike_amplitudes.ndim != 2:
            raise ValueError(f"mean_spike_amplitudes must be 2D array (num_frames, num_channels), got shape {mean_spike_amplitudes.shape}")
        
        # Validate shapes match
        if mean_firing_rates.shape != mean_spike_amplitudes.shape:
            raise ValueError(
                f"mean_firing_rates shape {mean_firing_rates.shape} must match "
                f"mean_spike_amplitudes shape {mean_spike_amplitudes.shape}"
            )
        
        num_frames, num_channels = mean_firing_rates.shape
        
        # Validate electrode coordinates
        electrode_coords_array = np.array(electrode_coords, dtype=np.float32)
        if electrode_coords_array.ndim != 2 or electrode_coords_array.shape[1] != 2:
            raise ValueError(
                f"electrode_coords must have shape (num_channels, 2), got {electrode_coords_array.shape}"
            )
        if electrode_coords_array.shape[0] != num_channels:
            raise ValueError(
                f"Number of electrode coordinates ({electrode_coords_array.shape[0]}) "
                f"must match number of channels ({num_channels})"
            )
        
        self.electrode_coords = electrode_coords_array
        self.mean_firing_rates = mean_firing_rates.astype(np.float32)
        self.mean_spike_amplitudes = mean_spike_amplitudes.astype(np.float32)
        self.num_frames = num_frames
        self.num_channels = num_channels

    def write_to_zarr_group(self, group: figpack.Group) -> None:
        """
        Write the data to a Zarr group

        Args:
            group: Zarr group to write data into
        """
        super().write_to_zarr_group(group)

        group.attrs["num_frames"] = self.num_frames
        group.attrs["num_channels"] = self.num_channels
        group.create_dataset("electrode_coords", data=self.electrode_coords)
        group.create_dataset("mean_firing_rates", data=self.mean_firing_rates)
        group.create_dataset("mean_spike_amplitudes", data=self.mean_spike_amplitudes)
