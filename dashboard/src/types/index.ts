// API Response Types for realtime512b

export interface Config {
  filter_params: {
    lowcut: number;
    highcut: number;
    order: number;
  };
  sampling_frequency: number;
  n_channels: number;
  detect_threshold_for_spike_stats: number;
  coarse_sorting_detect_threshold: number;
  high_activity_threshold: number;
  raw_segment_duration_sec: number;
  use_bin2py: boolean;
}

export interface SegmentInfo {
  filename: string;
  has_filt: boolean;
  has_shifted: boolean;
  has_high_activity: boolean;
  has_stats: boolean;
  has_reference_sorting: boolean;
  has_spike_sorting: boolean;
  has_preview: boolean;
  size_bytes?: number;
  num_frames?: number;
  duration_sec?: number;
}

export interface SegmentsResponse {
  epochBlock: string;
  segments: SegmentInfo[];
}

export interface EpochBlockInfo {
  name: string;
  num_segments: number;
  num_segments_sorted: number;
  has_epoch_block_sorting: boolean;
  has_receptive_fields: boolean;
  has_epoch_block_preview: boolean;
}

export interface EpochBlocksResponse {
  epochBlocks: EpochBlockInfo[];
}

export interface EpochBlockSortingStats {
  num_spikes: number;
  num_units: number;
  num_templates: number;
  duration_sec: number | null;
  min_time_sec: number | null;
  max_time_sec: number | null;
}

export interface EpochBlockDetailResponse {
  epochBlock: string;
  num_segments: number;
  num_segments_sorted: number;
  has_epoch_block_sorting: boolean;
  has_receptive_fields: boolean;
  has_epoch_block_preview: boolean;
  epoch_block_sorting_stats: EpochBlockSortingStats | null;
  segments: string[];
}

export interface ShiftCoefficients {
  c_x: number;
  c_y: number;
}

export interface HighActivityInterval {
  start_sec: number;
  end_sec: number;
}

export interface HighActivityResponse {
  high_activity_intervals: HighActivityInterval[];
}

export interface StatsResponse {
  mean_firing_rates: number[];
  mean_spike_amplitudes: number[];
}

export interface BinaryDataResponse {
  data: Int16Array;
  numFrames: number;
  numChannels: number;
  samplingFrequency: number;
  startSec: number;
  endSec: number;
}

export type DataType = 'raw' | 'filt' | 'shifted';

// Combined segment info with epochBlock
export interface SegmentWithEpochBlock extends SegmentInfo {
  epochBlock: string;
}

// Reference segment response
export interface ReferenceSegmentResponse {
  reference_segment: string | null;
}

// Set reference segment request
export interface SetReferenceSegmentRequest {
  epoch_block_id: string;
  filename: string;
}

// Set reference segment response
export interface SetReferenceSegmentResponse {
  reference_segment: string;
  message: string;
}
