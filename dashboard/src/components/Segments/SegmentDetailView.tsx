import { useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckIcon,
  Cancel as ErrorIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { usePolling } from '../../hooks/usePolling';
import { api, getPreviewUrl } from '../../services/api';
import { navigateWithQuery } from '../../utils/navigation';

export function SegmentDetailView() {
  const { epochBlockId, filename } = useParams<{ epochBlockId: string; filename: string }>();
  const navigate = useNavigate();

  const fetchSegments = useCallback(() => {
    if (!epochBlockId) return Promise.reject(new Error('No epoch ID'));
    return api.getSegments(epochBlockId);
  }, [epochBlockId]);

  const fetchStats = useCallback(() => {
    if (!epochBlockId || !filename) return Promise.reject(new Error('Missing parameters'));
    return api.getStats(epochBlockId, filename);
  }, [epochBlockId, filename]);

  const fetchHighActivity = useCallback(() => {
    if (!epochBlockId || !filename) return Promise.reject(new Error('Missing parameters'));
    return api.getHighActivity(epochBlockId, filename);
  }, [epochBlockId, filename]);

  const {
    data: segmentsData,
    error: segmentsError,
    isLoading: segmentsLoading,
  } = usePolling(fetchSegments, { interval: 5000 });

  const {
    data: statsData,
    error: statsError,
  } = usePolling(fetchStats, { interval: 10000 });

  const {
    data: highActivityData,
    error: highActivityError,
  } = usePolling(fetchHighActivity, { interval: 10000 });

  if (segmentsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (segmentsError) {
    return (
      <Alert severity="error">
        Error loading segment info: {segmentsError.message}
      </Alert>
    );
  }

  const segment = segmentsData?.segments.find(s => s.filename === filename);

  if (!segment) {
    return (
      <Alert severity="error">
        Segment not found: {epochBlockId}/{filename}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3} gap={2}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(navigateWithQuery('/segments'))}
        >
          Back to Segments
        </Button>
        <Typography variant="h4">
          {epochBlockId}/{filename}
        </Typography>
      </Box>

      <Stack spacing={3}>
        {/* Segment Info Card */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Segment Information
            </Typography>
            <Stack spacing={1} mt={2}>
              {segment.duration_sec !== undefined && (
                <Typography variant="body2">
                  <strong>Duration:</strong> {segment.duration_sec.toFixed(2)} seconds
                </Typography>
              )}
              {segment.num_frames !== undefined && (
                <Typography variant="body2">
                  <strong>Frames:</strong> {segment.num_frames.toLocaleString()}
                </Typography>
              )}
              {segment.size_bytes !== undefined && (
                <Typography variant="body2">
                  <strong>Size:</strong> {(segment.size_bytes / 1024 / 1024).toFixed(2)} MB
                </Typography>
              )}
            </Stack>
          </CardContent>
        </Card>

        {/* Processing Status Card */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Processing Status
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1} mt={2}>
              <Chip
                label="Filtered"
                color={segment.has_filt ? 'success' : 'default'}
                icon={segment.has_filt ? <CheckIcon /> : <ErrorIcon />}
              />
              <Chip
                label="Shifted"
                color={segment.has_shifted ? 'success' : 'default'}
                icon={segment.has_shifted ? <CheckIcon /> : <ErrorIcon />}
              />
              <Chip
                label="Reference Sorting"
                color={segment.has_reference_sorting ? 'success' : 'default'}
                icon={segment.has_reference_sorting ? <CheckIcon /> : <ErrorIcon />}
              />
              <Chip
                label="Spike Sorting"
                color={segment.has_spike_sorting ? 'success' : 'default'}
                icon={segment.has_spike_sorting ? <CheckIcon /> : <ErrorIcon />}
              />
              <Chip
                label="High Activity"
                color={segment.has_high_activity ? 'success' : 'default'}
                icon={segment.has_high_activity ? <CheckIcon /> : <ErrorIcon />}
              />
              <Chip
                label="Statistics"
                color={segment.has_stats ? 'success' : 'default'}
                icon={segment.has_stats ? <CheckIcon /> : <ErrorIcon />}
              />
              <Chip
                label="Preview"
                color={segment.has_preview ? 'success' : 'default'}
                icon={segment.has_preview ? <CheckIcon /> : <ErrorIcon />}
              />
            </Box>
          </CardContent>
        </Card>

        {/* Statistics Card */}
        {segment.has_stats && statsData && !statsError && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Spike Statistics Summary
              </Typography>
              <Stack spacing={2} mt={2}>
                <Typography variant="body2">
                  <strong>Number of Channels:</strong> {statsData.mean_firing_rates.length}
                </Typography>
                <Typography variant="body2">
                  <strong>Mean Firing Rate (across all channels):</strong>{' '}
                  {(statsData.mean_firing_rates.reduce((a, b) => a + b, 0) / statsData.mean_firing_rates.length).toFixed(2)} Hz
                </Typography>
                <Typography variant="body2">
                  <strong>Mean Spike Amplitude (across all channels):</strong>{' '}
                  {(statsData.mean_spike_amplitudes.reduce((a, b) => a + b, 0) / statsData.mean_spike_amplitudes.length).toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  <strong>Max Firing Rate:</strong> {Math.max(...statsData.mean_firing_rates).toFixed(2)} Hz
                </Typography>
                <Typography variant="body2">
                  <strong>Max Spike Amplitude:</strong> {Math.max(...statsData.mean_spike_amplitudes).toFixed(2)}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        )}

        {/* High Activity Intervals Card */}
        {segment.has_high_activity && highActivityData && !highActivityError && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                High Activity Intervals
              </Typography>
              {highActivityData.high_activity_intervals.length === 0 ? (
                <Typography variant="body2" color="text.secondary" mt={2}>
                  No high activity intervals detected.
                </Typography>
              ) : (
                <TableContainer component={Paper} sx={{ mt: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Start (sec)</strong></TableCell>
                        <TableCell><strong>End (sec)</strong></TableCell>
                        <TableCell><strong>Duration (sec)</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {highActivityData.high_activity_intervals.map((interval, index) => (
                        <TableRow key={index}>
                          <TableCell>{interval.start_sec.toFixed(3)}</TableCell>
                          <TableCell>{interval.end_sec.toFixed(3)}</TableCell>
                          <TableCell>{(interval.end_sec - interval.start_sec).toFixed(3)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        )}

        {/* Preview Card */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Preview
              </Typography>
              {segment.has_preview && epochBlockId && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<OpenInNewIcon />}
                  onClick={() => window.open(getPreviewUrl(epochBlockId, segment.filename), '_blank')}
                >
                  Open in New Tab
                </Button>
              )}
            </Box>
            {segment.has_preview && epochBlockId ? (
              <Paper sx={{ p: 0, height: 'calc(100vh - 400px)', minHeight: '600px' }}>
                <iframe
                  src={getPreviewUrl(epochBlockId, segment.filename)}
                  style={{
                    width: '100%',
                    height: '100%',
                    border: 'none',
                  }}
                  title={`Preview of ${segment.filename}`}
                />
              </Paper>
            ) : (
              <Alert severity="info">
                Preview not available yet. Previews are generated after all processing steps complete.
              </Alert>
            )}
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
