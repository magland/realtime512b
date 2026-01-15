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

export function EpochsView() {
  const fetchEpochs = useCallback(() => api.getEpochs(), []);
  const navigate = useNavigate();

  const {
    data: epochsData,
    error: epochsError,
    isLoading: epochsLoading,
  } = usePolling(fetchEpochs, { interval: 5000 });

  if (epochsLoading) {
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

  const epochs = epochsData?.epochs || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Epochs
      </Typography>

      <Typography variant="body2" color="text.secondary" gutterBottom>
        Overview of all epochs and their spike sorting progress
      </Typography>

      <Stack spacing={2} mt={3}>
        {epochs.length === 0 ? (
          <Alert severity="info">
            No epochs found. Data will appear here once processing begins.
          </Alert>
        ) : (
          epochs.map((epoch) => {
            const progress = epoch.num_segments > 0 
              ? (epoch.num_segments_sorted / epoch.num_segments) * 100 
              : 0;
            const isComplete = epoch.has_epoch_sorting;

            return (
              <Card key={epoch.name}>
                <CardActionArea onClick={() => navigate(navigateWithQuery(`/epochs/${epoch.name}`))}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {epoch.name}
                        </Typography>
                        <Stack direction="row" spacing={2} alignItems="center">
                          <Typography variant="body2" color="text.secondary">
                            <strong>Segments:</strong> {epoch.num_segments}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            <strong>Sorted:</strong> {epoch.num_segments_sorted} / {epoch.num_segments}
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
                            label="Epoch Sorting"
                            color={isComplete ? 'success' : 'default'}
                            icon={isComplete ? <CheckCircleIcon /> : <ErrorIcon />}
                          />
                          <Chip
                            size="small"
                            label="Epoch Preview"
                            color={epoch.has_epoch_preview ? 'success' : 'default'}
                            icon={epoch.has_epoch_preview ? <CheckCircleIcon /> : <ErrorIcon />}
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
