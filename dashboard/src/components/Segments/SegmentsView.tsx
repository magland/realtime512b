import { useCallback, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Typography,
  Chip,
  Alert,
  Button,
  Stack,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as ErrorIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { usePolling } from '../../hooks/usePolling';
import { api } from '../../services/api';
import { navigateWithQuery } from '../../utils/navigation';
import type { SegmentWithEpoch } from '../../types';

export function SegmentsView() {
  const navigate = useNavigate();

  const fetchEpochs = useCallback(() => api.getEpochs(), []);

  const {
    data: epochsData,
    error: epochsError,
    isLoading: epochsLoading,
  } = usePolling(fetchEpochs, { interval: 5000 });

  // Fetch segments for all epochs - avoid hook violations
  const epochs = epochsData?.epochs || [];
  const [allSegments, setAllSegments] = useState<SegmentWithEpoch[]>([]);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  useEffect(() => {
    if (!epochs || epochs.length === 0) {
      setAllSegments([]);
      setHasLoadedOnce(false);
      return;
    }

    let isMounted = true;

    const fetchAllSegments = async () => {
      try {
        const segmentPromises = epochs.map(epochInfo =>
          api.getSegments(epochInfo.name).then(data => ({
            epochId: epochInfo.name,
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
          // Sort by epoch then filename
          combined.sort((a, b) => {
            const epochCompare = a.epoch.localeCompare(b.epoch);
            if (epochCompare !== 0) return epochCompare;
            return a.filename.localeCompare(b.filename);
          });
          setAllSegments(combined);
          setHasLoadedOnce(true);
        }
      } catch (error) {
        console.error('Error fetching segments:', error);
        setHasLoadedOnce(true);
      }
    };

    fetchAllSegments();
    const interval = setInterval(fetchAllSegments, 5000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [epochs]);

  const isLoading = epochsLoading || !hasLoadedOnce;

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (epochsError) {
    return (
      <Alert severity="error">
        Error loading epochs: {epochsError.message}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Segments
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          variant="outlined"
          onClick={() => window.location.reload()}
        >
          Refresh
        </Button>
      </Box>

      {allSegments.length === 0 ? (
        <Alert severity="info">
          No segments found. Waiting for data to be processed...
        </Alert>
      ) : (
        <Stack spacing={2}>
          {allSegments.map((segment) => (
            <Card
              key={`${segment.epoch}/${segment.filename}`}
              variant="outlined"
              sx={{
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  boxShadow: 3,
                },
              }}
              onClick={() => navigate(navigateWithQuery(`/segments/${segment.epoch}/${encodeURIComponent(segment.filename)}`))}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" flexWrap="wrap" gap={2}>
                  <Box flex="1" minWidth="200px">
                    <Typography variant="h6" gutterBottom>
                      {segment.epoch}/{segment.filename}
                    </Typography>
                    <Stack spacing={0.5}>
                      {segment.duration_sec !== undefined && (
                        <Typography variant="body2" color="text.secondary">
                          <strong>Duration:</strong> {segment.duration_sec.toFixed(2)} seconds
                        </Typography>
                      )}
                      {segment.num_frames !== undefined && (
                        <Typography variant="body2" color="text.secondary">
                          <strong>Frames:</strong> {segment.num_frames.toLocaleString()}
                        </Typography>
                      )}
                      {segment.size_bytes !== undefined && (
                        <Typography variant="body2" color="text.secondary">
                          <strong>Size:</strong> {(segment.size_bytes / 1024 / 1024).toFixed(2)} MB
                        </Typography>
                      )}
                    </Stack>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Processing Status
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      <Chip
                        size="small"
                        label="Filtered"
                        color={segment.has_filt ? 'success' : 'default'}
                        icon={segment.has_filt ? <CheckIcon /> : <ErrorIcon />}
                      />
                      <Chip
                        size="small"
                        label="Shifted"
                        color={segment.has_shifted ? 'success' : 'default'}
                        icon={segment.has_shifted ? <CheckIcon /> : <ErrorIcon />}
                      />
                      <Chip
                        size="small"
                        label="Reference Sorting"
                        color={segment.has_reference_sorting ? 'success' : 'default'}
                        icon={segment.has_reference_sorting ? <CheckIcon /> : <ErrorIcon />}
                      />
                      <Chip
                        size="small"
                        label="Spike Sorting"
                        color={segment.has_spike_sorting ? 'success' : 'default'}
                        icon={segment.has_spike_sorting ? <CheckIcon /> : <ErrorIcon />}
                      />
                      <Chip
                        size="small"
                        label="High Activity"
                        color={segment.has_high_activity ? 'success' : 'default'}
                        icon={segment.has_high_activity ? <CheckIcon /> : <ErrorIcon />}
                      />
                      <Chip
                        size="small"
                        label="Statistics"
                        color={segment.has_stats ? 'success' : 'default'}
                        icon={segment.has_stats ? <CheckIcon /> : <ErrorIcon />}
                      />
                      <Chip
                        size="small"
                        label="Preview"
                        color={segment.has_preview ? 'success' : 'default'}
                        icon={segment.has_preview ? <CheckIcon /> : <ErrorIcon />}
                      />
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  );
}
