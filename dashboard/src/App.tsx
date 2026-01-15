import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/Layout/AppLayout';
import { OverviewView } from './components/Overview/OverviewView';
import { EpochBlocksView } from './components/EpochBlocks/EpochBlocksView';
import { EpochBlockDetailView } from './components/EpochBlocks/EpochBlockDetailView';
import { SegmentsView } from './components/Segments/SegmentsView';
import { SegmentDetailView } from './components/Segments/SegmentDetailView';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppLayout>
        <Routes>
          <Route path="/" element={<OverviewView />} />
          <Route path="/epochBlocks" element={<EpochBlocksView />} />
          <Route path="/epochBlocks/:epochBlockId" element={<EpochBlockDetailView />} />
          <Route path="/segments" element={<SegmentsView />} />
          <Route path="/segments/:epochBlockId/:filename" element={<SegmentDetailView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </ThemeProvider>
  );
}

export default App;
