import {
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as ErrorIcon,
  OpenInNew as OpenInNewIcon
} from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { usePolling } from '../../hooks/usePolling';
import { api, getEpochBlockPreviewUrl } from '../../services/api';
import { navigateWithQuery } from '../../utils/navigation';

export function EpochBlockDetailView() {
  const { epochBlockId } = useParams<{ epochBlockId: string }>();
  const navigate = useNavigate();

  const fetchEpochBlockDetail = useCallback(() => {
    if (!epochBlockId) return Promise.reject(new Error('No epoch ID provided'));
    return api.getEpochBlockDetail(epochBlockId);
  }, [epochBlockId]);

  const {
    data: epochBlockData,
    error: epochBlockError,
    isLoading: epochBlockLoading,
  } = usePolling(fetchEpochBlockDetail, { interval: 5000 });

  if (epochBlockLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (epochBlockError) {
    return (
      <Alert severity="error">
        Error loading epoch block details: {epochBlockError.message}
      </Alert>
    );
  }

  if (!epochBlockData) {
    return (
      <Alert severity="warning">
        EpochBlock not found
      </Alert>
    );
  }

  const progress = epochBlockData.num_segments > 0
    ? (epochBlockData.num_segments_sorted / epochBlockData.num_segments) * 100
    : 0;

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(navigateWithQuery('/epochBlocks'))}
          variant="outlined"
        >
          Back to EpochBlocks
        </Button>
        <Typography variant="h4">
          {epochBlockData.epochBlock}
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
                  label="EpochBlock Sorting"
                  color={epochBlockData.has_epoch_block_sorting ? 'success' : 'default'}
                  icon={epochBlockData.has_epoch_block_sorting ? <CheckCircleIcon /> : <ErrorIcon />}
                />
                <Chip
                  size="small"
                  label="Receptive Fields"
                  color={epochBlockData.has_receptive_fields ? 'success' : 'default'}
                  icon={epochBlockData.has_receptive_fields ? <CheckCircleIcon /> : <ErrorIcon />}
                />
                <Chip
                  size="small"
                  label="EpochBlock Preview"
                  color={epochBlockData.has_epoch_block_preview ? 'success' : 'default'}
                  icon={epochBlockData.has_epoch_block_preview ? <CheckCircleIcon /> : <ErrorIcon />}
                />
              </Stack>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Total Segments
                </Typography>
                <Typography variant="h5">
                  {epochBlockData.num_segments}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Segments Sorted
                </Typography>
                <Typography variant="h5">
                  {epochBlockData.num_segments_sorted}
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
                  EpochBlock Sorting
                </Typography>
                <Typography variant="h5">
                  {epochBlockData.has_epoch_block_sorting ? 'Yes' : 'No'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Receptive Fields
                </Typography>
                <Typography variant="h5">
                  {epochBlockData.has_receptive_fields ? 'Yes' : 'No'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  EpochBlock Preview
                </Typography>
                <Typography variant="h5">
                  {epochBlockData.has_epoch_block_preview ? 'Yes' : 'No'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* EpochBlock Sorting Statistics */}
        {epochBlockData.epoch_block_sorting_stats && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                EpochBlock Spike Sorting Statistics
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Total Spikes
                  </Typography>
                  <Typography variant="h5">
                    {epochBlockData.epoch_block_sorting_stats.num_spikes.toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Number of Units
                  </Typography>
                  <Typography variant="h5">
                    {epochBlockData.epoch_block_sorting_stats.num_units}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Number of Templates
                  </Typography>
                  <Typography variant="h5">
                    {epochBlockData.epoch_block_sorting_stats.num_templates}
                  </Typography>
                </Grid>
                {epochBlockData.epoch_block_sorting_stats.duration_sec !== null && (
                  <Grid item xs={12} sm={6} md={4}>
                    <Typography variant="body2" color="text.secondary">
                      Total Duration
                    </Typography>
                    <Typography variant="h5">
                      {epochBlockData.epoch_block_sorting_stats.duration_sec.toFixed(2)} sec
                    </Typography>
                  </Grid>
                )}
                {epochBlockData.epoch_block_sorting_stats.min_time_sec !== null && (
                  <Grid item xs={12} sm={6} md={4}>
                    <Typography variant="body2" color="text.secondary">
                      First Spike Time
                    </Typography>
                    <Typography variant="h5">
                      {epochBlockData.epoch_block_sorting_stats.min_time_sec.toFixed(3)} sec
                    </Typography>
                  </Grid>
                )}
                {epochBlockData.epoch_block_sorting_stats.max_time_sec !== null && (
                  <Grid item xs={12} sm={6} md={4}>
                    <Typography variant="body2" color="text.secondary">
                      Last Spike Time
                    </Typography>
                    <Typography variant="h5">
                      {epochBlockData.epoch_block_sorting_stats.max_time_sec.toFixed(3)} sec
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* EpochBlock Preview Card */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                EpochBlock Preview
              </Typography>
              {epochBlockData.has_epoch_block_preview && epochBlockId && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<OpenInNewIcon />}
                  onClick={() => window.open(getEpochBlockPreviewUrl(epochBlockId), '_blank')}
                >
                  Open in New Tab
                </Button>
              )}
            </Box>
            {epochBlockData.has_epoch_block_preview && epochBlockId ? (
              <Paper sx={{ p: 0, height: 'calc(100vh - 400px)', minHeight: '600px' }}>
                <iframe
                  src={getEpochBlockPreviewUrl(epochBlockId)}
                  style={{
                    width: '100%',
                    height: '100%',
                    border: 'none',
                  }}
                  title={`EpochBlock Preview for ${epochBlockData.epochBlock}`}
                />
              </Paper>
            ) : (
              <Alert severity="info">
                EpochBlock preview not available yet. Previews are generated after epoch block spike sorting completes.
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Segments List */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Segments ({epochBlockData.segments.length})
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Stack spacing={1}>
              {epochBlockData.segments.map((segment, index) => (
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
