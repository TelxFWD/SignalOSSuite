import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Button,
  Paper
} from '@mui/material';
import {
  TrendingUp,
  Speed,
  AccountBalance,
  SignalCellularAlt,
  CheckCircle,
  Error,
  Warning
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useSocket } from '../../contexts/SocketContext';
import axios from 'axios';

function StatCard({ title, value, subtitle, icon, color = 'primary' }) {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {subtitle}
            </Typography>
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function SystemStatus({ status, label }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'success';
      case 'warning': return 'warning';
      case 'offline': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return <CheckCircle />;
      case 'warning': return <Warning />;
      case 'offline': return <Error />;
      default: return null;
    }
  };

  return (
    <Chip
      icon={getStatusIcon(status)}
      label={label}
      color={getStatusColor(status)}
      variant="outlined"
      size="small"
    />
  );
}

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [telegramSessions, setTelegramSessions] = useState([]);
  const [mt5Terminals, setMt5Terminals] = useState([]);
  const { healthData, connected, requestHealthUpdate, socket } = useSocket();

  useEffect(() => {
    // Fetch initial data
    const fetchData = async () => {
      try {
        const [analyticsRes, telegramRes, mt5Res] = await Promise.all([
          axios.get('/api/analytics/performance'),
          axios.get('/api/telegram/sessions'),
          axios.get('/api/mt5/terminals')
        ]);

        setAnalytics(analyticsRes.data);
        setTelegramSessions(telegramRes.data.sessions);
        setMt5Terminals(mt5Res.data.terminals);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchData();
    requestHealthUpdate();

    // Set up periodic health updates
    const interval = setInterval(requestHealthUpdate, 30000);
    
    // Listen for real-time signal updates
    if (socket) {
      socket.on('new_signal', (signal) => {
        console.log('New signal received:', signal);
        // Update UI with new signal
      });
      
      socket.on('health_update', (data) => {
        console.log('Health update received:', data);
      });
    }
    
    return () => {
      clearInterval(interval);
      if (socket) {
        socket.off('new_signal');
        socket.off('health_update');
      }
    };
  }, [requestHealthUpdate]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Trades"
            value={analytics?.total_trades || 0}
            subtitle="This month"
            icon={<TrendingUp />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Win Rate"
            value={analytics ? `${analytics.win_rate}%` : '0%'}
            subtitle="Success ratio"
            icon={<Speed />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Profit Factor"
            value={analytics?.profit_factor || 0}
            subtitle="Risk/Reward"
            icon={<AccountBalance />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Pips"
            value={analytics?.total_pips || 0}
            subtitle="Accumulated"
            icon={<SignalCellularAlt />}
            color="warning"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Equity Curve */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Equity Curve
              </Typography>
              {analytics?.equity_curve && (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={analytics.equity_curve}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="equity" 
                      stroke="#667eea" 
                      strokeWidth={2} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box sx={{ mb: 2 }}>
                <SystemStatus 
                  status={connected ? 'online' : 'offline'} 
                  label="WebSocket Connection" 
                />
              </Box>
              <Box sx={{ mb: 2 }}>
                <SystemStatus 
                  status={telegramSessions.length > 0 ? 'online' : 'offline'} 
                  label="Telegram Session" 
                />
              </Box>
              <Box sx={{ mb: 2 }}>
                <SystemStatus 
                  status={mt5Terminals.some(t => t.status === 'connected') ? 'online' : 'offline'} 
                  label="MT5 Terminal" 
                />
              </Box>
              
              {healthData && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    CPU Usage
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={healthData.cpu_percent || 0} 
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Memory Usage
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={healthData.memory_percent || 0} 
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                MT5 Terminals
              </Typography>
              <List>
                {mt5Terminals.map((terminal) => (
                  <ListItem key={terminal.id}>
                    <ListItemText
                      primary={terminal.name}
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            Balance: {formatCurrency(terminal.balance)}
                          </Typography>
                          <Typography variant="body2">
                            Equity: {formatCurrency(terminal.equity)}
                          </Typography>
                        </Box>
                      }
                    />
                    <Chip 
                      label={terminal.status} 
                      color={terminal.status === 'connected' ? 'success' : 'error'}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Telegram Sessions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Telegram Sessions
              </Typography>
              <List>
                {telegramSessions.map((session) => (
                  <ListItem key={session.id}>
                    <ListItemText
                      primary={session.phone}
                      secondary={`${session.channels.length} channels monitored`}
                    />
                    <Chip 
                      label={session.status} 
                      color={session.status === 'connected' ? 'success' : 'error'}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                <Button variant="outlined" size="small">
                  Add Session
                </Button>
                <Button 
                  variant="outlined" 
                  size="small"
                  onClick={() => socket?.emit('simulate_signal')}
                  disabled={!connected}
                >
                  Test Signal
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}