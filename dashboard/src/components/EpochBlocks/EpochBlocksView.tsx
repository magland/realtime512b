import {
  CheckCircle as CheckCircleIcon,
  Cancel as ErrorIcon
} from '@mui/icons-material';
import {
  Alert,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  CircularProgress,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePolling } from '../../hooks/usePolling';
import { api } from '../../services/api';
import { navigateWithQuery } from '../../utils/navigation';

export function EpochBlocksView() {
  const fetchEpochBlocks = useCallback(() => api.getEpochBlocks(), []);
  const navigate = useNavigate();

  const {
    data: epochBlocksData,
    error: epochBlocksError,
    isLoading: epochBlocksLoading,
  } = usePolling(fetchEpochBlocks, { interval: 5000 });

  if (epochBlocksLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (epochBlocksError) {
    return (
      <Alert severity="error">
        Error loading epochBlocks: {epochBlocksError.message}
      </Alert>
    );
  }

  const epochBlocks = epochBlocksData?.epochBlocks || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Epoch Blocks
      </Typography>

      <Typography variant="body2" color="text.secondary" gutterBottom>
        Overview of all epoch blocks and their spike sorting progress
      </Typography>

      <Stack spacing={2} mt={3}>
        {epochBlocks.length === 0 ? (
          <Alert severity="info">
            No epoch blocks found. Data will appear here once processing begins.
          </Alert>
        ) : (
          epochBlocks.map((epochBlock) => {
            const progress = epochBlock.num_segments > 0 
              ? (epochBlock.num_segments_sorted / epochBlock.num_segments) * 100 
              : 0;
            const isComplete = epochBlock.has_epoch_block_sorting;

            return (
              <Card key={epochBlock.name}>
                <CardActionArea onClick={() => navigate(navigateWithQuery(`/epochBlocks/${epochBlock.name}`))}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {epochBlock.name}
                        </Typography>
                        <Stack direction="row" spacing={2} alignItems="center">
                          <Typography variant="body2" color="text.secondary">
                            <strong>Segments:</strong> {epochBlock.num_segments}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            <strong>Sorted:</strong> {epochBlock.num_segments_sorted} / {epochBlock.num_segments}
                          </Typography>
                        </Stack>
                      </Box>

                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Processing Status
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                          <Chip
                            size="small"
                            label="EpochBlock Sorting"
                            color={isComplete ? 'success' : 'default'}
                            icon={isComplete ? <CheckCircleIcon /> : <ErrorIcon />}
                          />
                          <Chip
                            size="small"
                            label="EpochBlock Preview"
                            color={epochBlock.has_epoch_block_preview ? 'success' : 'default'}
                            icon={epochBlock.has_epoch_block_preview ? <CheckCircleIcon /> : <ErrorIcon />}
                          />
                        </Stack>
                      </Box>
                    </Box>

                    <Box mt={2}>
                      <Typography variant="caption" color="text.secondary">
                        Segment Sorting Progress: {progress.toFixed(1)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={progress}
                        sx={{ mt: 0.5 }}
                        color={isComplete ? 'success' : 'primary'}
                      />
                    </Box>
                  </CardContent>
                </CardActionArea>
              </Card>
            );
          })
        )}
      </Stack>
    </Box>
  );
}
