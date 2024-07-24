import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Watchlist from './Watchlist';
import ChatInterface from './ChatInterface';

const theme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#343541',
      paper: '#444654',
    },
    text: {
      primary: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Söhne", "Helvetica Neue", "Arial", sans-serif',
  },
});

const App = () => {
  const [selectedStock, setSelectedStock] = useState(null);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
          <Watchlist onSelectStock={setSelectedStock} />
          <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflowY: 'hidden' }}>
            <Routes>
              <Route 
                path="/:stockSymbol?" 
                element={<ChatInterface selectedStock={selectedStock} />} 
              />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;