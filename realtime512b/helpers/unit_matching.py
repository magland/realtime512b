"""Helper functions for matching spikes to reference sorting using nearest neighbors."""

import numpy as np
from sklearn.neighbors import NearestNeighbors


def nearest_neighbors(data1: np.ndarray, data2: np.ndarray, *, n_neighbors: int):
    """
    For each point in data2, find the nearest neighbors in data1.
    
    Parameters
    ----------
    data1 : np.ndarray
        Reference data array of shape (num_points_1, num_features)
    data2 : np.ndarray
        Query data array of shape (num_points_2, num_features)
    n_neighbors : int
        Number of nearest neighbors to find
    
    Returns
    -------
    np.ndarray
        Array of shape (num_points_2, n_neighbors) with indices into data1
    """
    nbrs = NearestNeighbors(n_neighbors=n_neighbors, algorithm='auto').fit(data1)
    distances, indices = nbrs.kneighbors(data2)
    return indices


def match_spikes_to_reference(
    spike_frames: np.ndarray,
    reference_frames: np.ndarray,
    reference_labels: np.ndarray,
    n_neighbors: int = 10
):
    """
    Match detected spikes to reference sorting using nearest neighbor approach.
    
    For each spike, find the k nearest neighbors in the reference spike frames,
    and assign the most common label among those neighbors.
    
    Parameters
    ----------
    spike_frames : np.ndarray
        Detected spike frames, shape (num_spikes, num_channels)
    reference_frames : np.ndarray
        Reference spike frames, shape (num_ref_spikes, num_channels)
    reference_labels : np.ndarray
        Reference spike labels, shape (num_ref_spikes,)
    n_neighbors : int
        Number of nearest neighbors to use (default: 10)
        
    Returns
    -------
    np.ndarray
        Matched labels for each spike, shape (num_spikes,)
    """
    if len(spike_frames) == 0:
        return np.array([], dtype=np.int32)
    
    if len(reference_frames) == 0:
        raise ValueError("Reference frames cannot be empty")
    
    # Find nearest neighbors in reference for each spike
    nearest_inds = nearest_neighbors(
        reference_frames, 
        spike_frames, 
        n_neighbors=min(n_neighbors, len(reference_frames))
    )
    
    # For each spike, find the most common label among its nearest neighbors
    matched_labels = np.zeros(len(spike_frames), dtype=np.int32)
    for i in range(len(spike_frames)):
        neighbor_labels = reference_labels[nearest_inds[i]]
        unique, counts = np.unique(neighbor_labels, return_counts=True)
        best_label = unique[np.argmax(counts)]
        matched_labels[i] = best_label
    
    return matched_labels
