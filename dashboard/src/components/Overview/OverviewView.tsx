import { useCallback, useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Typography,
  Alert,
  Stack,
} from '@mui/material';
import {
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { usePolling } from '../../hooks/usePolling';
import { api } from '../../services/api';
import type { SegmentWithEpoch } from '../../types';

export function OverviewView() {
  const fetchConfig = useCallback(() => api.getConfig(), []);
  const fetchEpochs = useCallback(() => api.getEpochs(), []);
  const fetchShiftCoeffs = useCallback(() => api.getShiftCoefficients(), []);

  const {
    data: config,
    error: configError,
    isLoading: configLoading,
  } = usePolling(fetchConfig, { interval: 10000 });

  const {
    data: epochsData,
    error: epochsError,
    isLoading: epochsLoading,
  } = usePolling(fetchEpochs, { interval: 5000 });

  const {
    data: shiftCoeffs,
    error: shiftsError,
  } = usePolling(fetchShiftCoeffs, { interval: 10000 });

  // Fetch segments for all epochs - we'll do this differently to avoid hook violations
  // Instead of using hooks in a loop, we'll fetch all segment data separately
  const epochs = epochsData?.epochs || [];
  
  // Create a stable list of all segments by fetching each epoch's segments
  const [allSegments, setAllSegments] = useState<SegmentWithEpoch[]>([]);
  
  useEffect(() => {
    if (!epochs || epochs.length === 0) {
      setAllSegments([]);
      return;
    }

    let isMounted = true;

    const fetchAllSegments = async () => {
      try {
        const segmentPromises = epochs.map(epochId => 
          api.getSegments(epochId).then(data => ({
            epochId,
            segments: data.segments,
          }))
        );
        
        const results = await Promise.all(segmentPromises);
        
        if (isMounted) {
          const combined: SegmentWithEpoch[] = [];
          results.forEach(result => {
            result.segments.forEach(segment => {
              combined.push({
                ...segment,
                epoch: result.epochId,
              });
            });
          });
          setAllSegments(combined);
        }
      } catch (error) {
        console.error('Error fetching segments:', error);
      }
    };

    fetchAllSegments();
    const interval = setInterval(fetchAllSegments, 5000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [epochs]);

  if (configLoading || epochsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (configError || epochsError) {
    return (
      <Alert severity="error">
        Error loading data: {(configError || epochsError)?.message}
      </Alert>
    );
  }

  const totalSegments = allSegments.length;
  const processedSegments = allSegments.filter(
    (s) => s.has_filt && s.has_shifted && s.has_reference_sorting
  ).length;
  const totalDuration = allSegments.reduce((sum, s) => sum + (s.duration_sec || 0), 0);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Overview
      </Typography>

      <Stack spacing={3}>
        {/* Top Row - Config and Status */}
        <Box display="flex" gap={3} flexWrap="wrap">
          <Box flex="1" minWidth="300px">
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <SettingsIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Configuration</Typography>
                </Box>
                {config && (
                  <Stack spacing={1}>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Sampling Frequency:</strong> {config.sampling_frequency} Hz
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Channels:</strong> {config.n_channels}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Filter Range:</strong> {config.filter_params.lowcut} -{' '}
                      {config.filter_params.highcut} Hz
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Filter Order:</strong> {config.filter_params.order}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Spike Threshold:</strong> {config.detect_threshold_for_spike_stats}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Segment Duration:</strong> {config.raw_segment_duration_sec} sec
                    </Typography>
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Box>

          <Box flex="1" minWidth="300px">
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Processing Status
                </Typography>
                <Stack spacing={1} mt={2}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Total Epochs:</strong> {epochs.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Total Segments:</strong> {totalSegments}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Fully Processed:</strong> {processedSegments} / {totalSegments}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Total Duration:</strong> {totalDuration.toFixed(2)} seconds
                  </Typography>
                  {shiftCoeffs && !shiftsError && (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Shift Coefficient X:</strong> {shiftCoeffs.c_x.toExponential(3)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Shift Coefficient Y:</strong> {shiftCoeffs.c_y.toExponential(3)}
                      </Typography>
                    </>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Stack>
    </Box>
  );
}
