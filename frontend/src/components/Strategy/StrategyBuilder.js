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
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  PlayArrow,
  Stop,
  Save,
  Psychology,
  TrendingUp,
  Settings
} from '@mui/icons-material';
import axios from 'axios';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const presetTemplates = [
  {
    id: 1,
    name: 'Scalper Pro',
    description: 'Quick trades with tight SL/TP',
    config: {
      partialTP: true,
      slToBE: true,
      trailingStop: false,
      maxRisk: 1,
      tpRatio: 1.5
    }
  },
  {
    id: 2,
    name: 'Swing Trader',
    description: 'Medium-term position trading',
    config: {
      partialTP: false,
      slToBE: true,
      trailingStop: true,
      maxRisk: 2,
      tpRatio: 3
    }
  },
  {
    id: 3,
    name: 'Intraday',
    description: 'Day trading with adaptive SL',
    config: {
      partialTP: true,
      slToBE: false,
      trailingStop: true,
      maxRisk: 1.5,
      tpRatio: 2
    }
  }
];

const conditionTypes = [
  { value: 'pair', label: 'Currency Pair' },
  { value: 'signal_type', label: 'Signal Type' },
  { value: 'provider', label: 'Signal Provider' },
  { value: 'time', label: 'Time of Day' },
  { value: 'market_condition', label: 'Market Condition' }
];

const actionTypes = [
  { value: 'tp_ratio', label: 'Take Profit Ratio' },
  { value: 'sl_pips', label: 'Stop Loss (Pips)' },
  { value: 'lot_size', label: 'Lot Size' },
  { value: 'delay', label: 'Execution Delay' },
  { value: 'skip', label: 'Skip Signal' }
];

export default function StrategyBuilder() {
  const [strategies, setStrategies] = useState([]);
  const [activeTab, setActiveTab] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState('beginner');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    partialTP: false,
    slToBE: true,
    trailingStop: false,
    maxRisk: 1,
    tpRatio: 2
  });
  const [customRules, setCustomRules] = useState([]);
  const [newRule, setNewRule] = useState({
    condition: '',
    operator: '=',
    value: '',
    action: '',
    actionValue: ''
  });

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await axios.get('/api/strategies');
      setStrategies(response.data.strategies || []);
    } catch (error) {
      console.error('Error fetching strategies:', error);
    }
  };

  const handleCreateFromTemplate = (template) => {
    setSelectedTemplate(template);
    setFormData({
      name: template.name,
      description: template.description,
      ...template.config
    });
    setDialogType('beginner');
    setOpenDialog(true);
  };

  const handleCreateCustom = () => {
    setFormData({
      name: '',
      description: '',
      partialTP: false,
      slToBE: true,
      trailingStop: false,
      maxRisk: 1,
      tpRatio: 2
    });
    setCustomRules([]);
    setDialogType('pro');
    setOpenDialog(true);
  };

  const handleAddRule = () => {
    if (newRule.condition && newRule.action) {
      setCustomRules([...customRules, { ...newRule, id: Date.now() }]);
      setNewRule({
        condition: '',
        operator: '=',
        value: '',
        action: '',
        actionValue: ''
      });
    }
  };

  const handleDeleteRule = (ruleId) => {
    setCustomRules(customRules.filter(rule => rule.id !== ruleId));
  };

  const handleSubmit = async () => {
    try {
      const strategyData = {
        ...formData,
        type: dialogType,
        rules: dialogType === 'pro' ? customRules : [],
        active: true
      };
      
      await axios.post('/api/strategies', strategyData);
      fetchStrategies();
      setOpenDialog(false);
    } catch (error) {
      console.error('Error creating strategy:', error);
    }
  };

  const toggleStrategy = async (strategyId, active) => {
    try {
      await axios.patch(`/api/strategies/${strategyId}`, { active });
      fetchStrategies();
    } catch (error) {
      console.error('Error toggling strategy:', error);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Strategy Builder
      </Typography>

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="My Strategies" />
        <Tab label="Template Library" />
        <Tab label="Backtest Results" />
      </Tabs>

      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Active Strategies</Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={handleCreateCustom}
                  >
                    Create Custom Strategy
                  </Button>
                </Box>

                {strategies.length === 0 ? (
                  <Alert severity="info">
                    No strategies created yet. Start with a template or create a custom strategy.
                  </Alert>
                ) : (
                  <List>
                    {strategies.map((strategy) => (
                      <ListItem key={strategy.id}>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" gap={1}>
                              <Psychology fontSize="small" />
                              {strategy.name}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2">
                                Type: {strategy.type} | Win Rate: {strategy.win_rate}%
                              </Typography>
                              <Typography variant="body2">
                                Trades: {strategy.trades} | Active: {strategy.active ? 'Yes' : 'No'}
                              </Typography>
                            </Box>
                          }
                        />
                        <Box display="flex" alignItems="center" gap={1}>
                          <Switch
                            checked={strategy.active}
                            onChange={(e) => toggleStrategy(strategy.id, e.target.checked)}
                            size="small"
                          />
                          <IconButton size="small">
                            <Edit />
                          </IconButton>
                          <IconButton size="small">
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

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Strategy Performance
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Total Active Strategies
                  </Typography>
                  <Typography variant="h4">
                    {strategies.filter(s => s.active).length}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Average Win Rate
                  </Typography>
                  <Typography variant="h4">
                    {strategies.length > 0 
                      ? Math.round(strategies.reduce((acc, s) => acc + s.win_rate, 0) / strategies.length)
                      : 0}%
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Total Trades
                  </Typography>
                  <Typography variant="h4">
                    {strategies.reduce((acc, s) => acc + s.trades, 0)}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          {presetTemplates.map((template) => (
            <Grid item xs={12} md={4} key={template.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {template.name}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" paragraph>
                    {template.description}
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Chip 
                      label={`TP Ratio: ${template.config.tpRatio}`} 
                      size="small" 
                      sx={{ mr: 1, mb: 1 }} 
                    />
                    <Chip 
                      label={`Risk: ${template.config.maxRisk}%`} 
                      size="small" 
                      sx={{ mr: 1, mb: 1 }} 
                    />
                    {template.config.partialTP && (
                      <Chip label="Partial TP" size="small" sx={{ mr: 1, mb: 1 }} />
                    )}
                    {template.config.slToBE && (
                      <Chip label="SL to BE" size="small" sx={{ mr: 1, mb: 1 }} />
                    )}
                    {template.config.trailingStop && (
                      <Chip label="Trailing Stop" size="small" sx={{ mr: 1, mb: 1 }} />
                    )}
                  </Box>

                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Add />}
                    onClick={() => handleCreateFromTemplate(template)}
                  >
                    Use Template
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Strategy Backtest Results
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Backtest feature coming soon. Connect historical data to simulate strategy performance.
            </Alert>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Strategy</TableCell>
                    <TableCell>Period</TableCell>
                    <TableCell>Trades</TableCell>
                    <TableCell>Win Rate</TableCell>
                    <TableCell>Profit Factor</TableCell>
                    <TableCell>Max Drawdown</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Scalper Pro</TableCell>
                    <TableCell>30 Days</TableCell>
                    <TableCell>156</TableCell>
                    <TableCell>72.5%</TableCell>
                    <TableCell>2.1</TableCell>
                    <TableCell>-4.2%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Swing Trader</TableCell>
                    <TableCell>30 Days</TableCell>
                    <TableCell>28</TableCell>
                    <TableCell>65.2%</TableCell>
                    <TableCell>1.8</TableCell>
                    <TableCell>-7.1%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Strategy Creation Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogType === 'beginner' ? 'Create Strategy from Template' : 'Create Custom Strategy'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Strategy Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>

            {dialogType === 'beginner' ? (
              // Beginner Mode - Simple toggles
              <>
                <Grid item xs={12}>
                  <Typography variant="subtitle1">Trading Options</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.partialTP}
                        onChange={(e) => setFormData({ ...formData, partialTP: e.target.checked })}
                      />
                    }
                    label="Partial Take Profit"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.slToBE}
                        onChange={(e) => setFormData({ ...formData, slToBE: e.target.checked })}
                      />
                    }
                    label="Move SL to Break Even"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.trailingStop}
                        onChange={(e) => setFormData({ ...formData, trailingStop: e.target.checked })}
                      />
                    }
                    label="Trailing Stop"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Max Risk (%)"
                    type="number"
                    value={formData.maxRisk}
                    onChange={(e) => setFormData({ ...formData, maxRisk: parseFloat(e.target.value) })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Take Profit Ratio"
                    type="number"
                    value={formData.tpRatio}
                    onChange={(e) => setFormData({ ...formData, tpRatio: parseFloat(e.target.value) })}
                  />
                </Grid>
              </>
            ) : (
              // Pro Mode - Custom rules
              <>
                <Grid item xs={12}>
                  <Typography variant="subtitle1">Custom Rules</Typography>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Create conditional logic: IF [condition] THEN [action]
                  </Alert>
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Condition</InputLabel>
                    <Select
                      value={newRule.condition}
                      onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
                    >
                      {conditionTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={2}>
                  <FormControl fullWidth>
                    <InputLabel>Operator</InputLabel>
                    <Select
                      value={newRule.operator}
                      onChange={(e) => setNewRule({ ...newRule, operator: e.target.value })}
                    >
                      <MenuItem value="=">=</MenuItem>
                      <MenuItem value="!=">!=</MenuItem>
                      <MenuItem value=">">></MenuItem>
                      <MenuItem value="<"><</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    label="Value"
                    value={newRule.value}
                    onChange={(e) => setNewRule({ ...newRule, value: e.target.value })}
                  />
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Action</InputLabel>
                    <Select
                      value={newRule.action}
                      onChange={(e) => setNewRule({ ...newRule, action: e.target.value })}
                    >
                      {actionTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={1}>
                  <TextField
                    fullWidth
                    label="Value"
                    value={newRule.actionValue}
                    onChange={(e) => setNewRule({ ...newRule, actionValue: e.target.value })}
                  />
                </Grid>
                
                <Grid item xs={12} md={1}>
                  <Button
                    variant="outlined"
                    onClick={handleAddRule}
                    disabled={!newRule.condition || !newRule.action}
                  >
                    Add
                  </Button>
                </Grid>

                {customRules.length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Current Rules
                    </Typography>
                    <List dense>
                      {customRules.map((rule) => (
                        <ListItem key={rule.id}>
                          <ListItemText
                            primary={`IF ${rule.condition} ${rule.operator} ${rule.value} THEN ${rule.action} = ${rule.actionValue}`}
                          />
                          <ListItemSecondaryAction>
                            <IconButton onClick={() => handleDeleteRule(rule.id)}>
                              <Delete />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                )}
              </>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Create Strategy
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}