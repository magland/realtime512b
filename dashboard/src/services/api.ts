import axios from 'axios';
import type {
  Config,
  EpochsResponse,
  EpochDetailResponse,
  SegmentsResponse,
  ShiftCoefficients,
  HighActivityResponse,
  StatsResponse,
  BinaryDataResponse,
  DataType,
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

  async getEpochs(): Promise<EpochsResponse> {
    const response = await axios.get<EpochsResponse>(`${this.baseURL}/epochs`);
    return response.data;
  }

  async getEpochDetail(epochId: string): Promise<EpochDetailResponse> {
    const response = await axios.get<EpochDetailResponse>(`${this.baseURL}/epochs/${epochId}`);
    return response.data;
  }

  async getSegments(epochId: string): Promise<SegmentsResponse> {
    const response = await axios.get<SegmentsResponse>(
      `${this.baseURL}/epochs/${epochId}/segments`
    );
    return response.data;
  }

  async getShiftCoefficients(): Promise<ShiftCoefficients> {
    const response = await axios.get<ShiftCoefficients>(
      `${this.baseURL}/shift_coefficients`
    );
    return response.data;
  }

  async getHighActivity(epochId: string, filename: string): Promise<HighActivityResponse> {
    const response = await axios.get<HighActivityResponse>(
      `${this.baseURL}/high_activity/${epochId}/${filename}`
    );
    return response.data;
  }

  async getStats(epochId: string, filename: string): Promise<StatsResponse> {
    const response = await axios.get<StatsResponse>(
      `${this.baseURL}/stats/${epochId}/${filename}`
    );
    return response.data;
  }

  async getBinaryData(
    dataType: DataType,
    epochId: string,
    filename: string,
    startSec?: number,
    endSec?: number
  ): Promise<BinaryDataResponse> {
    const params = new URLSearchParams();
    if (startSec !== undefined) params.append('start_sec', startSec.toString());
    if (endSec !== undefined) params.append('end_sec', endSec.toString());

    const url = `${this.baseURL}/${dataType}/${epochId}/${filename}${
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
}

// Initialize API with custom URL from query parameter if provided, otherwise use default
const customServerUrl = getServerUrlFromQuery();
export const getApiUrl = () => {
  return customServerUrl || API_BASE_URL;
};
export const api = new Realtime512bAPI(getApiUrl());

// Helper to get preview URL for a segment
export const getPreviewUrl = (epochId: string, filename: string) => {
  const apiUrl = getApiUrl();
  return `${apiUrl}/preview/${epochId}/${filename}/index.html?ext_dev_x=figpack-realtime512b:http://localhost:5174/figpack_realtime512b.js`;
};

// Helper to get preview URL for an epoch
export const getEpochPreviewUrl = (epochId: string) => {
  const apiUrl = getApiUrl();
  return `${apiUrl}/epoch_preview/${epochId}/index.html?ext_dev_x=figpack-realtime512b:http://localhost:5174/figpack_realtime512b.js`;
};
