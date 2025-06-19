import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  FormControlLabel,
  Switch,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  AccountBalance,
  TrendingUp,
  Settings,
  Security
} from '@mui/icons-material';
import axios from 'axios';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function MT5Setup() {
  const [terminals, setTerminals] = useState([]);
  const [symbolMappings, setSymbolMappings] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    server: '',
    login: '',
    password: '',
    riskType: 'fixed',
    riskValue: 0.1,
    enableSLOverride: false,
    enableTPOverride: false,
    enableBELogic: true,
    slBuffer: 5,
    tradeDelay: 0,
    maxSpread: 3,
    enableTrailing: false
  });

  const riskTypes = [
    { value: 'fixed', label: 'Fixed Lot Size' },
    { value: 'percent_balance', label: '% of Balance' },
    { value: 'percent_equity', label: '% of Equity' }
  ];

  useEffect(() => {
    fetchTerminals();
    fetchSymbolMappings();
  }, []);

  const fetchTerminals = async () => {
    try {
      const response = await axios.get('/api/mt5/terminals');
      setTerminals(response.data.terminals || []);
    } catch (error) {
      console.error('Error fetching terminals:', error);
    }
  };

  const fetchSymbolMappings = async () => {
    try {
      const response = await axios.get('/api/mt5/symbols');
      setSymbolMappings(response.data.mappings || []);
    } catch (error) {
      console.error('Error fetching symbol mappings:', error);
    }
  };

  const handleAddTerminal = () => {
    setFormData({
      name: '',
      server: '',
      login: '',
      password: '',
      riskType: 'fixed',
      riskValue: 0.1,
      enableSLOverride: false,
      enableTPOverride: false,
      enableBELogic: true,
      slBuffer: 5,
      tradeDelay: 0,
      maxSpread: 3,
      enableTrailing: false
    });
    setOpenDialog(true);
  };

  const handleSubmit = async () => {
    try {
      await axios.post('/api/mt5/terminals', formData);
      fetchTerminals();
      setOpenDialog(false);
    } catch (error) {
      console.error('Error adding terminal:', error);
    }
  };

  const handleDeleteTerminal = async (terminalId) => {
    try {
      await axios.delete(`/api/mt5/terminals/${terminalId}`);
      fetchTerminals();
    } catch (error) {
      console.error('Error deleting terminal:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'success';
      case 'connecting': return 'warning';
      case 'disconnected': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        MT5/MT4 Terminal Setup
      </Typography>

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Terminal Profiles" />
        <Tab label="Symbol Mapping" />
        <Tab label="Strategy Routing" />
      </Tabs>

      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          {/* Terminal List */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Terminal Profiles
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={handleAddTerminal}
                  >
                    Add Terminal
                  </Button>
                </Box>

                {terminals.length === 0 ? (
                  <Alert severity="info">
                    No MT5 terminals configured. Add a terminal to start automated trading.
                  </Alert>
                ) : (
                  <List>
                    {terminals.map((terminal) => (
                      <ListItem key={terminal.id}>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" gap={1}>
                              <AccountBalance fontSize="small" />
                              {terminal.name}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2">
                                Server: {terminal.server} | Account: {terminal.account}
                              </Typography>
                              <Typography variant="body2">
                                Balance: {formatCurrency(terminal.balance)} | 
                                Equity: {formatCurrency(terminal.equity)}
                              </Typography>
                            </Box>
                          }
                        />
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip
                            label={terminal.status}
                            color={getStatusColor(terminal.status)}
                            size="small"
                          />
                          <IconButton size="small">
                            <Edit />
                          </IconButton>
                          <IconButton 
                            size="small" 
                            onClick={() => handleDeleteTerminal(terminal.id)}
                          >
                            <Delete />
                          </IconButton>
                        </Box>
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Actions */}
          <Grid item xs={12} lg={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Button variant="outlined" startIcon={<TrendingUp />}>
                    Test Connection
                  </Button>
                  <Button variant="outlined" startIcon={<Settings />}>
                    Auto-Detect Terminals
                  </Button>
                  <Button variant="outlined" startIcon={<Security />}>
                    Check EA Status
                  </Button>
                </Box>
                
                <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
                  Terminal Health
                </Typography>
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Last Ping: 2 seconds ago
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    EA Version: v1.2.0
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Active Signals: 3
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Symbol Mapping Configuration
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Map signal provider symbol names to your MT5 broker symbols (e.g., "Gold" → "XAUUSD").
            </Alert>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Signal Symbol"
                  placeholder="Gold, EURUSD, etc."
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="MT5 Symbol"
                  placeholder="XAUUSD, EURUSD, etc."
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <Button variant="contained" fullWidth>
                  Add Mapping
                </Button>
              </Grid>
            </Grid>

            <Typography variant="subtitle1" sx={{ mt: 3, mb: 1 }}>
              Current Mappings
            </Typography>
            <List>
              <ListItem>
                <ListItemText
                  primary="Gold → XAUUSD"
                  secondary="Provider symbol mapped to broker symbol"
                />
                <ListItemSecondaryAction>
                  <IconButton>
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Silver → XAGUSD"
                  secondary="Provider symbol mapped to broker symbol"
                />
                <ListItemSecondaryAction>
                  <IconButton>
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Strategy-Terminal Routing
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Configure which trading strategies connect to which MT5 terminals.
            </Alert>
            
            <Typography variant="subtitle2" sx={{ mb: 2 }}>
              Visual Routing Map
            </Typography>
            <Box
              sx={{
                border: '2px dashed',
                borderColor: 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                minHeight: 200,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Typography color="textSecondary">
                Drag and drop to connect strategies to terminals
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Add Terminal Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add MT5 Terminal</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Terminal Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="MT5 Demo Account"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Server"
                value={formData.server}
                onChange={(e) => setFormData({ ...formData, server: e.target.value })}
                placeholder="MetaQuotes-Demo"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Login"
                value={formData.login}
                onChange={(e) => setFormData({ ...formData, login: e.target.value })}
                placeholder="12345678"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Risk Management
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Risk Type</InputLabel>
                <Select
                  value={formData.riskType}
                  onChange={(e) => setFormData({ ...formData, riskType: e.target.value })}
                >
                  {riskTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Risk Value"
                type="number"
                value={formData.riskValue}
                onChange={(e) => setFormData({ ...formData, riskValue: parseFloat(e.target.value) })}
                helperText={
                  formData.riskType === 'fixed' 
                    ? 'Lot size (e.g., 0.1)'
                    : 'Percentage (e.g., 2 for 2%)'
                }
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Trading Options
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enableSLOverride}
                    onChange={(e) => setFormData({ ...formData, enableSLOverride: e.target.checked })}
                  />
                }
                label="SL Override"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enableTPOverride}
                    onChange={(e) => setFormData({ ...formData, enableTPOverride: e.target.checked })}
                  />
                }
                label="TP Override"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enableBELogic}
                    onChange={(e) => setFormData({ ...formData, enableBELogic: e.target.checked })}
                  />
                }
                label="Break Even Logic"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enableTrailing}
                    onChange={(e) => setFormData({ ...formData, enableTrailing: e.target.checked })}
                  />
                }
                label="Trailing Stop"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>SL Buffer (pips)</Typography>
              <Slider
                value={formData.slBuffer}
                onChange={(e, value) => setFormData({ ...formData, slBuffer: value })}
                min={0}
                max={20}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>Trade Delay (seconds)</Typography>
              <Slider
                value={formData.tradeDelay}
                onChange={(e, value) => setFormData({ ...formData, tradeDelay: value })}
                min={0}
                max={60}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Add Terminal
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}