import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Calendar
} from 'recharts';
import {
  GetApp,
  PictureAsPdf,
  Assessment,
  TrendingUp,
  AccountBalance
} from '@mui/icons-material';
import axios from 'axios';
import { format, subDays, startOfDay } from 'date-fns';

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'];

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('30d');
  const [analytics, setAnalytics] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [pairPerformance, setPairPerformance] = useState([]);
  const [dailyStats, setDailyStats] = useState([]);

  useEffect(() => {
    fetchAnalytics();
    fetchTradeHistory();
    fetchPairPerformance();
    fetchDailyStats();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get('/api/analytics/performance');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchTradeHistory = async () => {
    try {
      const response = await axios.get(`/api/analytics/trades?range=${timeRange}`);
      setTradeHistory(response.data.trades || []);
    } catch (error) {
      console.error('Error fetching trade history:', error);
      // Mock data for demonstration
      setTradeHistory([
        {
          id: 1,
          pair: 'EURUSD',
          type: 'BUY',
          entry: 1.0850,
          exit: 1.0920,
          pips: 70,
          profit: 140,
          date: '2024-12-19'
        },
        {
          id: 2,
          pair: 'XAUUSD',
          type: 'SELL',
          entry: 2018.50,
          exit: 2015.30,
          pips: 32,
          profit: 320,
          date: '2024-12-19'
        }
      ]);
    }
  };

  const fetchPairPerformance = async () => {
    try {
      const response = await axios.get(`/api/analytics/pairs?range=${timeRange}`);
      setPairPerformance(response.data.pairs || []);
    } catch (error) {
      console.error('Error fetching pair performance:', error);
      // Mock data
      setPairPerformance([
        { name: 'EURUSD', trades: 15, winRate: 73, pips: 142 },
        { name: 'XAUUSD', trades: 12, winRate: 67, pips: 89 },
        { name: 'GBPUSD', trades: 8, winRate: 75, pips: 65 },
        { name: 'USDJPY', trades: 6, winRate: 50, pips: -12 },
        { name: 'AUDUSD', trades: 4, winRate: 75, pips: 28 }
      ]);
    }
  };

  const fetchDailyStats = async () => {
    try {
      const response = await axios.get(`/api/analytics/daily?range=${timeRange}`);
      setDailyStats(response.data.daily || []);
    } catch (error) {
      console.error('Error fetching daily stats:', error);
      // Mock data
      const mockData = [];
      for (let i = 30; i >= 0; i--) {
        const date = format(subDays(new Date(), i), 'yyyy-MM-dd');
        mockData.push({
          date,
          trades: Math.floor(Math.random() * 8),
          pips: Math.floor(Math.random() * 100) - 20,
          profit: Math.floor(Math.random() * 1000) - 200
        });
      }
      setDailyStats(mockData);
    }
  };

  const exportToPDF = () => {
    // Implementation for PDF export
    console.log('Exporting to PDF...');
  };

  const exportToCSV = () => {
    // Implementation for CSV export
    const csv = [
      ['Date', 'Pair', 'Type', 'Entry', 'Exit', 'Pips', 'Profit'],
      ...tradeHistory.map(trade => [
        trade.date,
        trade.pair,
        trade.type,
        trade.entry,
        trade.exit,
        trade.pips,
        trade.profit
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'trade_history.csv';
    a.click();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Performance Analytics
        </Typography>
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="7d">7 Days</MenuItem>
              <MenuItem value="30d">30 Days</MenuItem>
              <MenuItem value="90d">90 Days</MenuItem>
              <MenuItem value="1y">1 Year</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            onClick={exportToCSV}
          >
            Export CSV
          </Button>
          <Button
            variant="outlined"
            startIcon={<PictureAsPdf />}
            onClick={exportToPDF}
          >
            Export PDF
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Key Metrics */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Trades
              </Typography>
              <Typography variant="h4">
                {analytics?.total_trades || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                This period
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Win Rate
              </Typography>
              <Typography variant="h4" color="success.main">
                {analytics?.win_rate || 0}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Success ratio
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Profit Factor
              </Typography>
              <Typography variant="h4" color="info.main">
                {analytics?.profit_factor || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Risk/Reward
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Pips
              </Typography>
              <Typography variant="h4" color="warning.main">
                {analytics?.total_pips || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Accumulated
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Equity Curve */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Equity Curve
              </Typography>
              {analytics?.equity_curve && (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={analytics.equity_curve}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Area 
                      type="monotone" 
                      dataKey="equity" 
                      stroke="#667eea" 
                      fill="#667eea"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Daily Performance */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Daily P&L
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dailyStats.slice(-7)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={(value) => format(new Date(value), 'MMM dd')} />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Bar 
                    dataKey="profit" 
                    fill={(entry) => entry.profit >= 0 ? '#4caf50' : '#f44336'}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Pair Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Currency Pair Performance
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Pair</TableCell>
                      <TableCell>Trades</TableCell>
                      <TableCell>Win Rate</TableCell>
                      <TableCell>Total Pips</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pairPerformance.map((pair) => (
                      <TableRow key={pair.name}>
                        <TableCell>{pair.name}</TableCell>
                        <TableCell>{pair.trades}</TableCell>
                        <TableCell>
                          <Chip 
                            label={`${pair.winRate}%`}
                            color={pair.winRate >= 70 ? 'success' : pair.winRate >= 50 ? 'warning' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography 
                            color={pair.pips >= 0 ? 'success.main' : 'error.main'}
                          >
                            {pair.pips >= 0 ? '+' : ''}{pair.pips}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Trade Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Trade Distribution by Pair
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pairPerformance}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="trades"
                  >
                    {pairPerformance.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Trades */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Trade History
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Pair</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Entry</TableCell>
                      <TableCell>Exit</TableCell>
                      <TableCell>Pips</TableCell>
                      <TableCell>Profit</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tradeHistory.slice(0, 10).map((trade) => (
                      <TableRow key={trade.id}>
                        <TableCell>{trade.date}</TableCell>
                        <TableCell>{trade.pair}</TableCell>
                        <TableCell>
                          <Chip 
                            label={trade.type}
                            color={trade.type === 'BUY' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{trade.entry}</TableCell>
                        <TableCell>{trade.exit}</TableCell>
                        <TableCell>
                          <Typography 
                            color={trade.pips >= 0 ? 'success.main' : 'error.main'}
                          >
                            {trade.pips >= 0 ? '+' : ''}{trade.pips}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography 
                            color={trade.profit >= 0 ? 'success.main' : 'error.main'}
                          >
                            {formatCurrency(trade.profit)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}