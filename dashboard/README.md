# realtime512b Dashboard

Web-based dashboard for monitoring and visualizing realtime512b neural data processing.

## Features

- **Overview**: View experiment configuration, processing status across all epochs and segments
- **Segments Explorer**: Browse all segments across epochs in a flat list with processing status indicators
- **Segment Details**: View detailed information, spike statistics, and high activity intervals for individual segments

## Architecture

The dashboard is adapted for realtime512b's epoch-based organization:
- Data is organized in epochs: `raw/epoch_001/segment_001.bin`, etc.
- API endpoints include epoch parameters
- Flat segment listing shows all segments across epochs (e.g., "epoch_001/segment_001.bin")

## Prerequisites

- Node.js >= 18
- npm (comes with Node.js)

## Installation

```bash
cd dashboard
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Connecting to a Server

By default, the dashboard connects to `http://localhost:5000/api`.

To connect to a different server, add the `serverUrl` query parameter:

```
http://localhost:5173/?serverUrl=http://192.168.1.100:5000
```

## Usage

### 1. Start the API Server

In your experiment directory:

```bash
cd experiment1
realtime512b serve
```

This starts the API server at `http://localhost:5000`

### 2. Open the Dashboard

Navigate to `http://localhost:5173` in your browser.

### Views

**Overview**
- Displays experiment configuration (sampling frequency, channels, filter parameters)
- Shows overall processing status across all epochs
- Displays shift coefficients and total duration

**Segments**
- Lists all segments across all epochs in a flat view
- Format: "epoch_001/segment_001.bin", "epoch_001/segment_002.bin", etc.
- Shows processing status chips (Filtered, Shifted, Reference Sorting, High Activity, Statistics)
- Click any segment to view details

**Segment Detail**
- Displays segment metadata (duration, frames, file size)
- Shows processing status
- Displays spike statistics summary (mean firing rates, amplitudes)
- Lists high activity intervals in a table

## API Endpoints Used

- `GET /api/config` - Experiment configuration
- `GET /api/epochs` - List of available epochs
- `GET /api/epochs/<epoch_id>/segments` - Segments in an epoch
- `GET /api/shift_coefficients` - Time shift coefficients
- `GET /api/stats/<epoch_id>/<filename>` - Spike statistics
- `GET /api/high_activity/<epoch_id>/<filename>` - High activity intervals

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Technology Stack

- React 18
- TypeScript
- Material-UI (MUI)
- React Router
- Axios
- Vite

## Differences from realtime512 Dashboard

This dashboard is adapted for realtime512b's epoch-based organization:
- No focus units feature (simplified)
- No preview/figpack support
- Uses "reference_sorting" instead of "coarse_sorting"
- Flat segment listing across epochs instead of hierarchical navigation
- Minimal stats display (tables and basic summaries, no complex visualizations)
