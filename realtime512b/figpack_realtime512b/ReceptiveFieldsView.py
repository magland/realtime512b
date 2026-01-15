"""Receptive Fields View for realtime512b."""

from typing import Union

import numpy as np

import figpack
from .figpack_realtime512b_extension import figpack_realtime512b_extension


class ReceptiveFieldsView(figpack.ExtensionView):
    def __init__(
        self,
        receptive_fields: np.ndarray
    ):
        """
        Initialize a Receptive Fields view
        
        Args:
            receptive_fields: 5D array with shape (num_units, num_timepoints, width, height, channels)
                             - Dim 0: Unit index
                             - Dim 1: Timepoint (e.g., 60)
                             - Dim 2: X spatial coordinate (e.g., 127)
                             - Dim 3: Y spatial coordinate (e.g., 203)
                             - Dim 4: Color channel (3 for RGB)
        """
        super().__init__(
            extension=figpack_realtime512b_extension, view_type="realtime512b.ReceptiveFieldsView"
        )
        
        # Validate inputs
        if receptive_fields.ndim != 5:
            raise ValueError(f"receptive_fields must be 5D array, got shape {receptive_fields.shape}")
        
        num_units, num_timepoints, width, height, num_channels = receptive_fields.shape
        
        if num_channels != 3:
            raise ValueError(f"Expected 3 color channels, got {num_channels}")
        
        self.receptive_fields = receptive_fields.astype(np.float32)
        self.num_units = num_units
        self.num_timepoints = num_timepoints
        self.width = width
        self.height = height
        self.num_channels = num_channels
    
    def write_to_zarr_group(self, group: figpack.Group) -> None:
        """
        Write the data to a Zarr group
        
        Args:
            group: Zarr group to write data into
        """
        super().write_to_zarr_group(group)
        
        # Store metadata
        group.attrs["num_units"] = self.num_units
        group.attrs["num_timepoints"] = self.num_timepoints
        group.attrs["width"] = self.width
        group.attrs["height"] = self.height
        group.attrs["num_channels"] = self.num_channels
        
        # Store receptive fields data with chunking optimized for unit-based access
        # Chunk by one unit at a time, all timepoints, and reasonable spatial chunks
        chunks = (1, self.num_timepoints, min(64, self.width), min(64, self.height), self.num_channels)
        
        group.create_dataset("receptive_fields", data=self.receptive_fields, chunks=chunks)
