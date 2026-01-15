"""Cluster Separation View for realtime512b."""

from typing import Union

import numpy as np

import figpack
from .figpack_realtime512b_extension import figpack_realtime512b_extension
from figpack_spike_sorting.spike_sorting_extension import spike_sorting_extension


class ClusterSeparationViewItem:
    """
    Represents a single pair of clusters and their separation data.
    """
    def __init__(
        self,
        unit_id_1: Union[str, int],
        unit_id_2: Union[str, int],
        projections_1: np.ndarray,
        projections_2: np.ndarray,
    ):
        """
        Create a separation item for a pair of units.
        
        Parameters
        ----------
        unit_id_1 : str or int
            ID of the first unit
        unit_id_2 : str or int
            ID of the second unit
        projections_1 : np.ndarray
            Projection values for spikes from unit 1
        projections_2 : np.ndarray
            Projection values for spikes from unit 2
        """
        self.unit_id_1 = str(unit_id_1)
        self.unit_id_2 = str(unit_id_2)
        self.projections_1 = np.array(projections_1, dtype=np.float32)
        self.projections_2 = np.array(projections_2, dtype=np.float32)
        
        # Validate
        if self.projections_1.ndim != 1:
            raise ValueError("projections_1 must be 1D array")
        if self.projections_2.ndim != 1:
            raise ValueError("projections_2 must be 1D array")


class ClusterSeparationView(figpack.ExtensionView):
    def __init__(
        self,
        separation_items: list[ClusterSeparationViewItem],
    ):
        """
        Create a view showing cluster separation for pairs of units.
        
        Parameters
        ----------
        separation_items : list[ClusterSeparationViewItem]
            List of separation items
        """
        super().__init__(
            extension=figpack_realtime512b_extension, 
            view_type="realtime512b.ClusterSeparationView"
        )

        setattr(self, "other_extensions", [spike_sorting_extension])

        # Validate inputs
        if not isinstance(separation_items, list):
            raise ValueError("separation_items must be a list")
        
        for item in separation_items:
            if not isinstance(item, ClusterSeparationViewItem):
                raise ValueError("All items must be ClusterSeparationViewItem instances")
        
        self.separation_items = separation_items
        self.num_items = len(separation_items)

    def write_to_zarr_group(self, group: figpack.Group) -> None:
        """
        Write the data to a Zarr group

        Args:
            group: Zarr group to write data into
        """
        super().write_to_zarr_group(group)

        # Store metadata
        group.attrs["num_items"] = self.num_items

        # Build consolidated arrays
        unit_ids_1 = []
        unit_ids_2 = []
        projection_starts_1 = [0]
        projection_starts_2 = [0]
        all_projections_1 = []
        all_projections_2 = []
        
        for item in self.separation_items:
            unit_ids_1.append(int(item.unit_id_1))
            unit_ids_2.append(int(item.unit_id_2))
            
            all_projections_1.extend(item.projections_1)
            all_projections_2.extend(item.projections_2)
            
            projection_starts_1.append(len(all_projections_1))
            projection_starts_2.append(len(all_projections_2))
        
        # Store consolidated datasets
        group.create_dataset("unit_ids_1", data=np.array(unit_ids_1, dtype=np.int32))
        group.create_dataset("unit_ids_2", data=np.array(unit_ids_2, dtype=np.int32))
        group.create_dataset("projection_starts_1", data=np.array(projection_starts_1, dtype=np.int32))
        group.create_dataset("projection_starts_2", data=np.array(projection_starts_2, dtype=np.int32))
        group.create_dataset("projections_1", data=np.array(all_projections_1, dtype=np.float32))
        group.create_dataset("projections_2", data=np.array(all_projections_2, dtype=np.float32))
