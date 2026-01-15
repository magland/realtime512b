"""EpochBlock processor for converting acquisition epoch blocksinto raw segments."""

import os
import time
import numpy as np

from ..helpers.file_info import create_info_file


class EpochBlockProcessor:
    """
    Processes acquisition epoch blocksand converts them into fixed-duration raw segments.
    
    In bin2py mode, acquisition epoch blocksare bin2py folders.
    In direct mode, acquisition epoch blockscontain .bin files.
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
    
    def process_epoch_blocks(self):
        """
        Process any new valid epoch blocksfrom acquisition/ to raw/.
        Returns True if any processing was done.
        """
        valid_epoch_blocks = self._get_valid_epoch_blocks()
        
        if not valid_epoch_blocks:
            return False
        
        something_processed = False
        
        for epoch_block_name in valid_epoch_blocks:
            # Check if this epoch block has already been processed
            raw_epoch_block_dir = os.path.join(self.raw_dir, epoch_block_name)
            if os.path.exists(raw_epoch_block_dir):
                # EpochBlock already processed, skip
                continue
            
            print(f"Processing epoch_block: {epoch_block_name}")
            
            # Read epoch block data
            print(f"  Reading data from {epoch_block_name}...")
            epoch_block_path = os.path.join(self.acquisition_dir, epoch_block_name)
            data = self._read_epoch_block_data(epoch_block_path)
            print(f"  Read data from {epoch_block_name}: {data.shape} shape" if data is not None else f"  Failed to read data from {epoch_block_name}")
            
            if data is None:
                print(f"  Warning: Could not read data from {epoch_block_name}, skipping")
                continue
            
            # Create output directory
            os.makedirs(raw_epoch_block_dir, exist_ok=True)
            
            # Chunk into segments
            num_segments = self._chunk_to_segments(data, raw_epoch_block_dir)
            
            print(f"  Created {num_segments} segments in {raw_epoch_block_dir}")
            something_processed = True
        
        return something_processed
    
    def _get_valid_epoch_blocks(self):
        """
        Get list of valid epoch block directories.
        An epoch block is valid if all its files are more than 5 seconds old.
        """
        if not os.path.exists(self.acquisition_dir):
            return []
        
        # Get all directories in acquisition/
        all_epoch_blocks = sorted([
            name for name in os.listdir(self.acquisition_dir)
            if os.path.isdir(os.path.join(self.acquisition_dir, name))
        ])

        valid_epoch_blocks = []
        current_time = time.time()
        
        for epoch_block_name in all_epoch_blocks:
            epoch_block_path = os.path.join(self.acquisition_dir, epoch_block_name)
            
            # Check all files in the epoch block directory
            all_files_old = True
            has_files = False
            
            for root, dirs, files in os.walk(epoch_block_path):
                for filename in files:
                    has_files = True
                    filepath = os.path.join(root, filename)
                    mtime = os.path.getmtime(filepath)
                    if current_time - mtime < 5:
                        all_files_old = False
                        break
                if not all_files_old:
                    break
            
            # EpochBlock is valid if it has files and all are old enough
            if has_files and all_files_old:
                valid_epoch_blocks.append(epoch_block_name)
        
        return valid_epoch_blocks
    
    def _read_epoch_block_data(self, epoch_block_path):
        """
        Read data from an epoch block directory.
        Returns numpy array of shape (n_samples, n_channels) or None if error.
        """
        if self.use_bin2py:
            return self._read_epoch_block_bin2py(epoch_block_path)
        else:
            return self._read_epoch_block_binary(epoch_block_path)
    
    def _read_epoch_block_bin2py(self, epoch_block_path):
        """Read epoch block data using bin2py."""
        try:
            import bin2py
            
            # Use a reasonable chunk size for reading
            RW_BLOCKSIZE = 100000
            
            with bin2py.PyBinFileReader(epoch_block_path, chunk_samples=RW_BLOCKSIZE, is_row_major=True) as pbfr:
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
    
    def _read_epoch_block_binary(self, epoch_block_path):
        """Read epoch block data from .bin files."""
        try:
            # Get all .bin files in the epoch block directory
            bin_files = sorted([
                f for f in os.listdir(epoch_block_path)
                if f.endswith('.bin')
            ])
            
            if not bin_files:
                print(f"  No .bin files found in {epoch_block_path}")
                return None
            
            # Read and concatenate all .bin files
            data_parts = []
            for bin_file in bin_files:
                filepath = os.path.join(epoch_block_path, bin_file)
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
