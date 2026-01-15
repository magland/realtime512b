import { useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Typography,
  Alert,
  Stack,
  Button,
  Chip,
  Divider,
  Grid,
  Paper,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  OpenInNew as OpenInNewIcon,
  Cancel as ErrorIcon,
} from '@mui/icons-material';
import { usePolling } from '../../hooks/usePolling';
import { api, getEpochPreviewUrl } from '../../services/api';
import { navigateWithQuery } from '../../utils/navigation';

export function EpochDetailView() {
  const { epochId } = useParams<{ epochId: string }>();
  const navigate = useNavigate();

  const fetchEpochDetail = useCallback(() => {
    if (!epochId) return Promise.reject(new Error('No epoch ID provided'));
    return api.getEpochDetail(epochId);
  }, [epochId]);

  const {
    data: epochData,
    error: epochError,
    isLoading: epochLoading,
  } = usePolling(fetchEpochDetail, { interval: 5000 });

  if (epochLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (epochError) {
    return (
      <Alert severity="error">
        Error loading epoch details: {epochError.message}
      </Alert>
    );
  }

  if (!epochData) {
    return (
      <Alert severity="warning">
        Epoch not found
      </Alert>
    );
  }

  const progress = epochData.num_segments > 0
    ? (epochData.num_segments_sorted / epochData.num_segments) * 100
    : 0;

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(navigateWithQuery('/epochs'))}
          variant="outlined"
        >
          Back to Epochs
        </Button>
        <Typography variant="h4">
          {epochData.epoch}
        </Typography>
      </Box>

      <Stack spacing={3}>
        {/* Status Card */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Status</Typography>
              <Stack direction="row" spacing={1}>
                <Chip
                  size="small"
                  label="Epoch Sorting"
                  color={epochData.has_epoch_sorting ? 'success' : 'default'}
                  icon={epochData.has_epoch_sorting ? <CheckCircleIcon /> : <ErrorIcon />}
                />
                <Chip
                  size="small"
                  label="Epoch Preview"
                  color={epochData.has_epoch_preview ? 'success' : 'default'}
                  icon={epochData.has_epoch_preview ? <CheckCircleIcon /> : <ErrorIcon />}
                />
              </Stack>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Total Segments
                </Typography>
                <Typography variant="h5">
                  {epochData.num_segments}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Segments Sorted
                </Typography>
                <Typography variant="h5">
                  {epochData.num_segments_sorted}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Sorting Progress
                </Typography>
                <Typography variant="h5">
                  {progress.toFixed(1)}%
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Epoch Sorting
                </Typography>
                <Typography variant="h5">
                  {epochData.has_epoch_sorting ? 'Yes' : 'No'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Epoch Preview
                </Typography>
                <Typography variant="h5">
                  {epochData.has_epoch_preview ? 'Yes' : 'No'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Epoch Sorting Statistics */}
        {epochData.epoch_sorting_stats && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Epoch Spike Sorting Statistics
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Total Spikes
                  </Typography>
                  <Typography variant="h5">
                    {epochData.epoch_sorting_stats.num_spikes.toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Number of Units
                  </Typography>
                  <Typography variant="h5">
                    {epochData.epoch_sorting_stats.num_units}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Number of Templates
                  </Typography>
                  <Typography variant="h5">
                    {epochData.epoch_sorting_stats.num_templates}
                  </Typography>
                </Grid>
                {epochData.epoch_sorting_stats.duration_sec !== null && (
                  <Grid item xs={12} sm={6} md={4}>
                    <Typography variant="body2" color="text.secondary">
                      Total Duration
                    </Typography>
                    <Typography variant="h5">
                      {epochData.epoch_sorting_stats.duration_sec.toFixed(2)} sec
                    </Typography>
                  </Grid>
                )}
                {epochData.epoch_sorting_stats.min_time_sec !== null && (
                  <Grid item xs={12} sm={6} md={4}>
                    <Typography variant="body2" color="text.secondary">
                      First Spike Time
                    </Typography>
                    <Typography variant="h5">
                      {epochData.epoch_sorting_stats.min_time_sec.toFixed(3)} sec
                    </Typography>
                  </Grid>
                )}
                {epochData.epoch_sorting_stats.max_time_sec !== null && (
                  <Grid item xs={12} sm={6} md={4}>
                    <Typography variant="body2" color="text.secondary">
                      Last Spike Time
                    </Typography>
                    <Typography variant="h5">
                      {epochData.epoch_sorting_stats.max_time_sec.toFixed(3)} sec
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Epoch Preview Card */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Epoch Preview
              </Typography>
              {epochData.has_epoch_preview && epochId && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<OpenInNewIcon />}
                  onClick={() => window.open(getEpochPreviewUrl(epochId), '_blank')}
                >
                  Open in New Tab
                </Button>
              )}
            </Box>
            {epochData.has_epoch_preview && epochId ? (
              <Paper sx={{ p: 0, height: 'calc(100vh - 400px)', minHeight: '600px' }}>
                <iframe
                  src={getEpochPreviewUrl(epochId)}
                  style={{
                    width: '100%',
                    height: '100%',
                    border: 'none',
                  }}
                  title={`Epoch Preview for ${epochData.epoch}`}
                />
              </Paper>
            ) : (
              <Alert severity="info">
                Epoch preview not available yet. Previews are generated after epoch spike sorting completes.
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Segments List */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Segments ({epochData.segments.length})
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Stack spacing={1}>
              {epochData.segments.map((segment, index) => (
                <Box
                  key={segment}
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  p={1.5}
                  sx={{
                    bgcolor: index % 2 === 0 ? 'action.hover' : 'transparent',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="body2">
                    {segment}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
