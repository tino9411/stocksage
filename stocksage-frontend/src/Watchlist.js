import React from 'react';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import ShowChartIcon from '@mui/icons-material/ShowChart';

const Watchlist = ({ onSelectStock }) => {
  const watchlist = [
    { symbol: 'AAPL', companyName: 'Apple Inc.' },
    { symbol: 'GOOGL', companyName: 'Alphabet Inc.' },
    { symbol: 'MSFT', companyName: 'Microsoft Corporation' },
    { symbol: 'AMZN', companyName: 'Amazon.com, Inc.' },
    { symbol: 'META', companyName: 'Meta Platforms, Inc.' },
  ];

  return (
    <Box sx={{ width: 260, bgcolor: '#202123', borderRight: '1px solid #4d4d4f', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<AddIcon />}
          sx={{
            color: '#fff',
            borderColor: '#fff',
            '&:hover': { borderColor: '#fff', bgcolor: 'rgba(255,255,255,0.1)' },
            textTransform: 'none',
            fontWeight: 'normal',
          }}
        >
          New chat
        </Button>
      </Box>
      <List sx={{ flexGrow: 1, overflowY: 'auto' }}>
        {watchlist.map(stock => (
          <ListItem key={stock.symbol} disablePadding>
            <ListItemButton
              component={Link}
              to={`/${stock.symbol}`}
              onClick={() => onSelectStock(stock.symbol)}
              sx={{
                '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
                borderRadius: 1,
                my: 0.5,
                mx: 1,
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <ShowChartIcon sx={{ color: '#8e8ea0' }} />
              </ListItemIcon>
              <ListItemText 
                primary={stock.symbol}
                primaryTypographyProps={{ fontSize: '14px', fontWeight: 'medium' }}
                secondary={stock.companyName}
                secondaryTypographyProps={{ fontSize: '12px', color: '#8e8ea0' }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default Watchlist;