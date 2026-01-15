"""Templates View for realtime512b."""

from typing import Union

import numpy as np

import figpack
from .figpack_realtime512b_extension import figpack_realtime512b_extension
from figpack_spike_sorting.spike_sorting_extension import spike_sorting_extension


class TemplatesView(figpack.ExtensionView):
    def __init__(
        self,
        templates: np.ndarray,
        electrode_coords: Union[np.ndarray, list[list[float]]],
    ):
        super().__init__(
            extension=figpack_realtime512b_extension, view_type="realtime512b.TemplatesView"
        )

        setattr(self, "other_extensions", [spike_sorting_extension])

        # Validate inputs
        if templates.ndim != 2:
            raise ValueError(f"templates must be 2D array, got shape {templates.shape}")

        num_electrodes = len(electrode_coords)
        if templates.shape[1] != num_electrodes:
            raise ValueError(
                f"templates second dimension ({templates.shape[1]}) must match number of electrodes ({num_electrodes})"
            )
        
        num_templates = templates.shape[0]

        self.templates = templates.astype(np.float32)
        self.electrode_coords = np.array(electrode_coords, dtype=np.float32)
        self.num_templates = num_templates
        self.num_channels = num_electrodes

    def write_to_zarr_group(self, group: figpack.Group) -> None:
        """
        Write the data to a Zarr group

        Args:
            group: Zarr group to write data into
        """
        super().write_to_zarr_group(group)

        # Store metadata
        group.attrs["num_templates"] = self.num_templates
        group.attrs["num_channels"] = self.num_channels

        # Store electrode coordinates
        group.create_dataset("electrode_coords", data=self.electrode_coords)

        # Store templates
        group.create_dataset("templates", data=self.templates)
