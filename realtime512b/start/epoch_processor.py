"""Epoch processor for converting acquisition epochs into raw segments."""

import os
import time
import numpy as np

from ..helpers.file_info import create_info_file


class EpochProcessor:
    """
    Processes acquisition epochs and converts them into fixed-duration raw segments.
    
    In bin2py mode, acquisition epochs are bin2py folders.
    In direct mode, acquisition epochs contain .bin files.
    """
    
    def __init__(self, acquisition_dir, raw_dir, n_channels, 
                 sampling_frequency, segment_duration_sec, use_bin2py):
        self.acquisition_dir = acquisition_dir
        self.raw_dir = raw_dir
        self.n_channels = n_channels
        self.sampling_frequency = sampling_frequency
        self.segment_duration_sec = segment_duration_sec
        self.use_bin2py = use_bin2py
        self.samples_per_segment = int(sampling_frequency * segment_duration_sec)
        self.bytes_per_sample = 2 * n_channels  # int16 format
    
    def process_epochs(self):
        """
        Process any new valid epochs from acquisition/ to raw/.
        Returns True if any processing was done.
        """
        valid_epochs = self._get_valid_epochs()
        
        if not valid_epochs:
            return False
        
        something_processed = False
        
        for epoch_name in valid_epochs:
            # Check if this epoch has already been processed
            raw_epoch_dir = os.path.join(self.raw_dir, epoch_name)
            if os.path.exists(raw_epoch_dir):
                # Epoch already processed, skip
                continue
            
            print(f"Processing epoch: {epoch_name}")
            
            # Read epoch data
            print(f"  Reading data from {epoch_name}...")
            epoch_path = os.path.join(self.acquisition_dir, epoch_name)
            data = self._read_epoch_data(epoch_path)
            print(f"  Read data from {epoch_name}: {data.shape} shape" if data is not None else f"  Failed to read data from {epoch_name}")
            
            if data is None:
                print(f"  Warning: Could not read data from {epoch_name}, skipping")
                continue
            
            # Create output directory
            os.makedirs(raw_epoch_dir, exist_ok=True)
            
            # Chunk into segments
            num_segments = self._chunk_to_segments(data, raw_epoch_dir)
            
            print(f"  Created {num_segments} segments in {raw_epoch_dir}")
            something_processed = True
        
        return something_processed
    
    def _get_valid_epochs(self):
        """
        Get list of valid epoch directories.
        An epoch is valid if all its files are more than 5 seconds old.
        """
        if not os.path.exists(self.acquisition_dir):
            return []
        
        # Get all directories in acquisition/
        all_epochs = sorted([
            name for name in os.listdir(self.acquisition_dir)
            if os.path.isdir(os.path.join(self.acquisition_dir, name))
        ])
        
        valid_epochs = []
        current_time = time.time()
        
        for epoch_name in all_epochs:
            epoch_path = os.path.join(self.acquisition_dir, epoch_name)
            
            # Check all files in the epoch directory
            all_files_old = True
            has_files = False
            
            for root, dirs, files in os.walk(epoch_path):
                for filename in files:
                    has_files = True
                    filepath = os.path.join(root, filename)
                    mtime = os.path.getmtime(filepath)
                    if current_time - mtime < 5:
                        all_files_old = False
                        break
                if not all_files_old:
                    break
            
            # Epoch is valid if it has files and all are old enough
            if has_files and all_files_old:
                valid_epochs.append(epoch_name)
        
        return valid_epochs
    
    def _read_epoch_data(self, epoch_path):
        """
        Read data from an epoch directory.
        Returns numpy array of shape (n_samples, n_channels) or None if error.
        """
        if self.use_bin2py:
            return self._read_epoch_bin2py(epoch_path)
        else:
            return self._read_epoch_binary(epoch_path)
    
    def _read_epoch_bin2py(self, epoch_path):
        """Read epoch data using bin2py."""
        try:
            import bin2py
            
            # Use a reasonable chunk size for reading
            RW_BLOCKSIZE = 100000
            
            with bin2py.PyBinFileReader(epoch_path, chunk_samples=RW_BLOCKSIZE, is_row_major=True) as pbfr:
                total_samples = pbfr.length
                n_electrodes = pbfr.num_electrodes
                
                # Preallocate array (excluding channel 0 which is TTL)
                # We expect n_electrodes channels, where channel 0 is TTL
                data = np.zeros((total_samples, n_electrodes), dtype=np.float32)
                
                # Read data in chunks
                data_offset = 0
                for chunk_start in range(0, total_samples, RW_BLOCKSIZE):
                    n_samples_to_get = min(RW_BLOCKSIZE, total_samples - chunk_start)
                    chunk = pbfr.get_data(chunk_start, n_samples_to_get)
                    
                    # chunk is [electrodes, samples], skip channel 0 and transpose
                    chunk_data = chunk[1:, :].T  # Now [samples, electrodes]
                    
                    data[data_offset:data_offset + n_samples_to_get, :] = chunk_data
                    data_offset += n_samples_to_get
                
                print(f"  Read {total_samples} samples from bin2py folder")
                return data
                
        except Exception as e:
            print(f"  Error reading bin2py folder: {e}")
            return None
    
    def _read_epoch_binary(self, epoch_path):
        """Read epoch data from .bin files."""
        try:
            # Get all .bin files in the epoch directory
            bin_files = sorted([
                f for f in os.listdir(epoch_path)
                if f.endswith('.bin')
            ])
            
            if not bin_files:
                print(f"  No .bin files found in {epoch_path}")
                return None
            
            # Read and concatenate all .bin files
            data_parts = []
            for bin_file in bin_files:
                filepath = os.path.join(epoch_path, bin_file)
                file_data = np.fromfile(filepath, dtype=np.int16)
                
                # Reshape to (n_samples, n_channels)
                if len(file_data) % self.n_channels != 0:
                    print(f"  Warning: {bin_file} size is not a multiple of n_channels")
                    continue
                
                file_data = file_data.reshape(-1, self.n_channels)
                data_parts.append(file_data)
            
            if not data_parts:
                return None
            
            # Concatenate all parts
            data = np.concatenate(data_parts, axis=0)
            print(f"  Read {data.shape[0]} samples from {len(bin_files)} .bin files")
            return data
            
        except Exception as e:
            print(f"  Error reading binary files: {e}")
            return None
    
    def _chunk_to_segments(self, data, output_dir):
        """
        Chunk data into fixed-duration segments and save them.
        Returns the number of segments created.
        """
        n_samples = data.shape[0]
        n_segments = n_samples // self.samples_per_segment
        
        for i in range(n_segments):
            segment_num = i + 1
            start_idx = i * self.samples_per_segment
            end_idx = start_idx + self.samples_per_segment
            
            segment_data = data[start_idx:end_idx, :]
            
            # Convert to int16 if needed
            if segment_data.dtype != np.int16:
                segment_data = segment_data.astype(np.int16)
            
            # Save segment with timing
            segment_filename = f"segment_{segment_num:03d}.bin"
            segment_path = os.path.join(output_dir, segment_filename)
            
            start_time = time.time()
            segment_data.tofile(segment_path)
            elapsed_time = time.time() - start_time
            
            # Create .info file
            create_info_file(segment_path, elapsed_time)
        
        return n_segments
