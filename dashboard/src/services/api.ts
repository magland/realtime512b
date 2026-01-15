import axios from 'axios';
import type {
  Config,
  EpochBlocksResponse,
  EpochBlockDetailResponse,
  SegmentsResponse,
  ShiftCoefficients,
  HighActivityResponse,
  StatsResponse,
  BinaryDataResponse,
  DataType,
  ReferenceSegmentResponse,
  SetReferenceSegmentRequest,
  SetReferenceSegmentResponse,
} from '../types';

const API_BASE_URL = 'http://localhost:5000/api';

// Get server URL from query parameter if provided
function getServerUrlFromQuery(): string | null {
  const params = new URLSearchParams(window.location.search);
  const serverUrl = params.get('serverUrl');
  if (serverUrl) {
    // Ensure the URL ends with /api if not already present
    return serverUrl.endsWith('/api') ? serverUrl : `${serverUrl}/api`;
  }
  return null;
}

class Realtime512bAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async getConfig(): Promise<Config> {
    const response = await axios.get<Config>(`${this.baseURL}/config`);
    return response.data;
  }

  async getEpochBlocks(): Promise<EpochBlocksResponse> {
    const response = await axios.get<EpochBlocksResponse>(`${this.baseURL}/epoch_blocks`);
    return response.data;
  }

  async getEpochBlockDetail(epochBlockId: string): Promise<EpochBlockDetailResponse> {
    const response = await axios.get<EpochBlockDetailResponse>(`${this.baseURL}/epoch_blocks/${epochBlockId}`);
    return response.data;
  }

  async getSegments(epochBlockId: string): Promise<SegmentsResponse> {
    const response = await axios.get<SegmentsResponse>(
      `${this.baseURL}/epoch_blocks/${epochBlockId}/segments`
    );
    return response.data;
  }

  async getShiftCoefficients(): Promise<ShiftCoefficients> {
    const response = await axios.get<ShiftCoefficients>(
      `${this.baseURL}/shift_coefficients`
    );
    return response.data;
  }

  async getHighActivity(epochBlockId: string, filename: string): Promise<HighActivityResponse> {
    const response = await axios.get<HighActivityResponse>(
      `${this.baseURL}/high_activity/${epochBlockId}/${filename}`
    );
    return response.data;
  }

  async getStats(epochBlockId: string, filename: string): Promise<StatsResponse> {
    const response = await axios.get<StatsResponse>(
      `${this.baseURL}/stats/${epochBlockId}/${filename}`
    );
    return response.data;
  }

  async getBinaryData(
    dataType: DataType,
    epochBlockId: string,
    filename: string,
    startSec?: number,
    endSec?: number
  ): Promise<BinaryDataResponse> {
    const params = new URLSearchParams();
    if (startSec !== undefined) params.append('start_sec', startSec.toString());
    if (endSec !== undefined) params.append('end_sec', endSec.toString());

    const url = `${this.baseURL}/${dataType}/${epochBlockId}/${filename}${
      params.toString() ? '?' + params.toString() : ''
    }`;

    const response = await axios.get(url, {
      responseType: 'arraybuffer',
    });

    const data = new Int16Array(response.data);
    
    // Axios lowercases header names
    const headers = response.headers;
    const numFrames = parseInt(headers['x-num-frames'] || '0');
    const numChannels = parseInt(headers['x-num-channels'] || '0');
    const samplingFrequency = parseInt(headers['x-sampling-frequency'] || '0');
    const actualStartSec = parseFloat(headers['x-start-sec'] || '0');
    const actualEndSec = parseFloat(headers['x-end-sec'] || '0');

    return {
      data,
      numFrames,
      numChannels,
      samplingFrequency,
      startSec: actualStartSec,
      endSec: actualEndSec,
    };
  }

  async getReferenceSegment(): Promise<ReferenceSegmentResponse> {
    const response = await axios.get<ReferenceSegmentResponse>(
      `${this.baseURL}/reference_segment`
    );
    return response.data;
  }

  async setReferenceSegment(request: SetReferenceSegmentRequest): Promise<SetReferenceSegmentResponse> {
    const response = await axios.post<SetReferenceSegmentResponse>(
      `${this.baseURL}/reference_segment`,
      request
    );
    return response.data;
  }
}

// Initialize API with custom URL from query parameter if provided, otherwise use default
const customServerUrl = getServerUrlFromQuery();
export const getApiUrl = () => {
  return customServerUrl || API_BASE_URL;
};
export const api = new Realtime512bAPI(getApiUrl());

// Helper to get preview URL for a segment
export const getPreviewUrl = (epochBlockId: string, filename: string) => {
  const apiUrl = getApiUrl();
  return `${apiUrl}/preview/${epochBlockId}/${filename}/index.html?ext_dev_x=figpack-realtime512b:http://localhost:5174/figpack_realtime512b.js`;
};

// Helper to get preview URL for an epochBlock
export const getEpochBlockPreviewUrl = (epochBlockId: string) => {
  const apiUrl = getApiUrl();
  return `${apiUrl}/epoch_block_preview/${epochBlockId}/index.html?ext_dev_x=figpack-realtime512b:http://localhost:5174/figpack_realtime512b.js`;
};
