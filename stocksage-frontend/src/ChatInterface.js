import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import SendIcon from '@mui/icons-material/Send';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Avatar from '@mui/material/Avatar';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

const CustomRenderer = ({ content }) => {
  const renderContent = (text) => {
    const parts = [];
    let lastIndex = 0;

    const patterns = [
      { regex: /\[section\](.*?)\[\/section\]/g, component: (match, i) => <Typography key={i} variant="h4">{match[1]}</Typography> },
      { regex: /\[subsection\](.*?)\[\/subsection\]/g, component: (match, i) => <Typography key={i} variant="h5">{match[1]}</Typography> },
      { regex: /\[p\](.*?)\[\/p\]/g, component: (match, i) => <Typography key={i} paragraph>{match[1]}</Typography> },
      { regex: /\[list\](.*?)\[\/list\]/g, component: (match, i) => (
        <ul key={i}>
          {match[1].split('[item]').filter(Boolean).map((item, index) => (
            <li key={index}>{item.replace('[/item]', '')}</li>
          ))}
        </ul>
      )},
      { regex: /\[table\](.*?)\[\/table\]/g, component: (match, i) => {
        const rows = match[1].split('[row]').filter(Boolean);
        const header = rows.shift().replace('[header]', '').replace('[/header]', '').split('|');
        return (
          <Table key={i}>
            <TableHead>
              <TableRow>
                {header.map((cell, index) => (
                  <TableCell key={index}>{cell}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {row.replace('[/row]', '').split('|').map((cell, cellIndex) => (
                    <TableCell key={cellIndex}>{cell}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );
      }},
      { regex: /\[code\](.*?)\[\/code\]/g, component: (match, i) => (
        <Box key={i} sx={{ backgroundColor: '#f5f5f5', padding: 2, borderRadius: 1, fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
          {match[1]}
        </Box>
      )},
    ];

    patterns.forEach(({ regex, component }) => {
      const matches = text.matchAll(regex);
      for (const match of matches) {
        if (match.index > lastIndex) {
          parts.push(text.substring(lastIndex, match.index));
        }
        parts.push(component(match, parts.length));
        lastIndex = match.index + match[0].length;
      }
    });

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  return <>{renderContent(content)}</>;
};



const ChatInterface = ({ selectedStock }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
  
    useEffect(() => {
      if (selectedStock) {
        setMessages([]);
      }
    }, [selectedStock]);
  
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
  
    // Set base URL for axios
    axios.defaults.baseURL = 'http://127.0.0.1:5000';
    axios.defaults.withCredentials = true;
  
    const handleSubmit = async (e) => {
      e.preventDefault();
      if (!input.trim() || !selectedStock) return;
  
      const userMessage = { type: 'user', content: input };
      setMessages(prev => [...prev, userMessage]);
      setInput('');
      setIsLoading(true);
  
      try {
        const response = await axios.post('/api/chat', {
          message: input,
          stock: selectedStock,
          conversation_history: messages.map(msg => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.content
          }))
        }, {
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        console.log("Response from server:", response.data);
  
        const assistantMessage = { type: 'assistant', content: response.data.message };
        setMessages(prev => [...prev, assistantMessage]);
      } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage = { type: 'error', content: 'Sorry, there was an error processing your request.' };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    };
  
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', maxWidth: '800px', mx: 'auto', width: '100%' }}>
        <Box sx={{ flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
          {messages.map((message, index) => (
            <Box 
              key={index} 
              sx={{ 
                py: 2, 
                px: 2,
                bgcolor: message.type === 'user' ? 'background.default' : 'background.paper',
                borderBottom: '1px solid #4d4d4f',
              }}
            >
              <Box sx={{ display: 'flex', maxWidth: '800px', mx: 'auto', gap: 2 }}>
                <Avatar sx={{ bgcolor: message.type === 'user' ? '#5436DA' : '#11A37F' }}>
                  {message.type === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  {message.type === 'user' ? (
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </Typography>
                  ) : (
                    <div dangerouslySetInnerHTML={{ __html: message.content }} />
                  )}
                </Box>
              </Box>
            </Box>
          ))}
          <div ref={messagesEndRef} />
        </Box>
        <Box component="form" onSubmit={handleSubmit} sx={{ p: 2, borderTop: '1px solid #4d4d4f' }}>
          <TextField
            fullWidth
            variant="outlined"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={selectedStock ? `Ask about ${selectedStock}...` : "Select a stock to start chatting"}
            disabled={!selectedStock || isLoading}
            InputProps={{
              endAdornment: (
                <IconButton type="submit" disabled={!input.trim() || isLoading}>
                  {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
                </IconButton>
              ),
              sx: {
                bgcolor: '#40414F',
                '& fieldset': { border: 'none' },
              }
            }}
          />
        </Box>
      </Box>
    );
  };
  
  export default ChatInterface;