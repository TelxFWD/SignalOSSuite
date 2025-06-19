import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip
} from '@mui/material';
import {
  Save,
  Download,
  Upload,
  RestartAlt,
  Backup,
  Security,
  Notifications,
  CloudSync
} from '@mui/icons-material';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState(0);
  const [settings, setSettings] = useState({
    // General Settings
    theme: 'dark',
    language: 'en',
    timezone: 'UTC',
    autoSync: true,
    notifications: true,
    
    // Trading Settings
    defaultRisk: 1,
    maxDailyLoss: 5,
    tradingHours: { start: '08:00', end: '17:00' },
    enableShadowMode: false,
    confirmTrades: true,
    
    // API Settings
    telegramNotifications: true,
    emailAlerts: true,
    webhookUrl: '',
    
    // Security Settings
    twoFactorAuth: false,
    sessionTimeout: 30,
    ipWhitelist: []
  });
  const [openBackupDialog, setOpenBackupDialog] = useState(false);
  const [profiles, setProfiles] = useState([
    { id: 1, name: 'Conservative', type: 'risk', active: false },
    { id: 2, name: 'Aggressive', type: 'risk', active: true },
    { id: 3, name: 'Scalping Setup', type: 'strategy', active: false }
  ]);

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleNestedSettingChange = (parent, key, value) => {
    setSettings(prev => ({
      ...prev,
      [parent]: {
        ...prev[parent],
        [key]: value
      }
    }));
  };

  const handleSaveSettings = async () => {
    try {
      // Save settings to backend
      console.log('Saving settings:', settings);
      // Show success message
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  const handleExportConfig = () => {
    const config = {
      settings,
      profiles,
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `signalos_config_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
  };

  const handleImportConfig = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const config = JSON.parse(e.target.result);
          setSettings(config.settings || settings);
          setProfiles(config.profiles || profiles);
          // Show success message
        } catch (error) {
          console.error('Error importing config:', error);
          // Show error message
        }
      };
      reader.readAsText(file);
    }
  };

  const handleResetToDefaults = () => {
    // Reset to default settings
    setSettings({
      theme: 'dark',
      language: 'en',
      timezone: 'UTC',
      autoSync: true,
      notifications: true,
      defaultRisk: 1,
      maxDailyLoss: 5,
      tradingHours: { start: '08:00', end: '17:00' },
      enableShadowMode: false,
      confirmTrades: true,
      telegramNotifications: true,
      emailAlerts: true,
      webhookUrl: '',
      twoFactorAuth: false,
      sessionTimeout: 30,
      ipWhitelist: []
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings & Configuration
      </Typography>

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="General" />
        <Tab label="Trading" />
        <Tab label="Notifications" />
        <Tab label="Security" />
        <Tab label="Profiles" />
      </Tabs>

      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Application Settings
                </Typography>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={settings.theme}
                    onChange={(e) => handleSettingChange('theme', e.target.value)}
                  >
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="auto">Auto</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={settings.language}
                    onChange={(e) => handleSettingChange('language', e.target.value)}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Spanish</MenuItem>
                    <MenuItem value="fr">French</MenuItem>
                    <MenuItem value="de">German</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={settings.timezone}
                    onChange={(e) => handleSettingChange('timezone', e.target.value)}
                  >
                    <MenuItem value="UTC">UTC</MenuItem>
                    <MenuItem value="EST">Eastern Time</MenuItem>
                    <MenuItem value="PST">Pacific Time</MenuItem>
                    <MenuItem value="GMT">Greenwich Mean Time</MenuItem>
                  </Select>
                </FormControl>

                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoSync}
                      onChange={(e) => handleSettingChange('autoSync', e.target.checked)}
                    />
                  }
                  label="Auto Sync with Desktop App"
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Health
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Desktop App Status
                  </Typography>
                  <Chip label="Connected" color="success" size="small" />
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Last Sync
                  </Typography>
                  <Typography variant="body2">
                    2 minutes ago
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Configuration Version
                  </Typography>
                  <Typography variant="body2">
                    v1.2.3
                  </Typography>
                </Box>

                <Button
                  variant="outlined"
                  startIcon={<RestartAlt />}
                  fullWidth
                >
                  Force Sync
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Management
                </Typography>

                <TextField
                  fullWidth
                  label="Default Risk Per Trade (%)"
                  type="number"
                  value={settings.defaultRisk}
                  onChange={(e) => handleSettingChange('defaultRisk', parseFloat(e.target.value))}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Max Daily Loss (%)"
                  type="number"
                  value={settings.maxDailyLoss}
                  onChange={(e) => handleSettingChange('maxDailyLoss', parseFloat(e.target.value))}
                  sx={{ mb: 2 }}
                />

                <Typography variant="subtitle2" gutterBottom>
                  Trading Hours
                </Typography>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Start Time"
                      type="time"
                      value={settings.tradingHours.start}
                      onChange={(e) => handleNestedSettingChange('tradingHours', 'start', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="End Time"
                      type="time"
                      value={settings.tradingHours.end}
                      onChange={(e) => handleNestedSettingChange('tradingHours', 'end', e.target.value)}
                    />
                  </Grid>
                </Grid>

                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableShadowMode}
                      onChange={(e) => handleSettingChange('enableShadowMode', e.target.checked)}
                    />
                  }
                  label="Enable Shadow Mode (Test Only)"
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.confirmTrades}
                      onChange={(e) => handleSettingChange('confirmTrades', e.target.checked)}
                    />
                  }
                  label="Require Trade Confirmation"
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Market Conditions
                </Typography>
                
                <Alert severity="info" sx={{ mb: 2 }}>
                  Configure automatic trading based on market conditions and volatility.
                </Alert>

                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Pause trading during high impact news"
                  sx={{ mb: 1 }}
                />

                <FormControlLabel
                  control={<Switch />}
                  label="Reduce lot size during high volatility"
                  sx={{ mb: 1 }}
                />

                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Skip trades outside London/New York sessions"
                  sx={{ mb: 1 }}
                />

                <TextField
                  fullWidth
                  label="Max Spread (pips)"
                  type="number"
                  defaultValue={3}
                  sx={{ mt: 2 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Alert Preferences
                </Typography>

                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.telegramNotifications}
                      onChange={(e) => handleSettingChange('telegramNotifications', e.target.checked)}
                    />
                  }
                  label="Telegram Notifications"
                  sx={{ mb: 1 }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.emailAlerts}
                      onChange={(e) => handleSettingChange('emailAlerts', e.target.checked)}
                    />
                  }
                  label="Email Alerts"
                  sx={{ mb: 1 }}
                />

                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Trade Execution Alerts"
                  sx={{ mb: 1 }}
                />

                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="System Error Notifications"
                  sx={{ mb: 1 }}
                />

                <FormControlLabel
                  control={<Switch />}
                  label="Daily Summary Reports"
                  sx={{ mb: 1 }}
                />

                <TextField
                  fullWidth
                  label="Webhook URL"
                  value={settings.webhookUrl}
                  onChange={(e) => handleSettingChange('webhookUrl', e.target.value)}
                  placeholder="https://your-webhook-url.com"
                  sx={{ mt: 2 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Notification Schedule
                </Typography>

                <Alert severity="info" sx={{ mb: 2 }}>
                  Configure when you want to receive notifications based on your timezone.
                </Alert>

                <Typography variant="subtitle2" gutterBottom>
                  Quiet Hours
                </Typography>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Start"
                      type="time"
                      defaultValue="22:00"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="End"
                      type="time"
                      defaultValue="08:00"
                    />
                  </Grid>
                </Grid>

                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Weekend Notifications"
                  sx={{ mb: 1 }}
                />

                <FormControlLabel
                  control={<Switch />}
                  label="Emergency Override"
                  sx={{ mb: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Security Settings
                </Typography>

                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.twoFactorAuth}
                      onChange={(e) => handleSettingChange('twoFactorAuth', e.target.checked)}
                    />
                  }
                  label="Two-Factor Authentication"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Session Timeout (minutes)"
                  type="number"
                  value={settings.sessionTimeout}
                  onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />

                <Button variant="outlined" fullWidth sx={{ mb: 1 }}>
                  Change Password
                </Button>

                <Button variant="outlined" fullWidth sx={{ mb: 1 }}>
                  Download API Keys
                </Button>

                <Button variant="outlined" color="error" fullWidth>
                  Revoke All Sessions
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Access Control
                </Typography>

                <Typography variant="subtitle2" gutterBottom>
                  IP Whitelist
                </Typography>
                <TextField
                  fullWidth
                  label="Add IP Address"
                  placeholder="192.168.1.1"
                  sx={{ mb: 2 }}
                />

                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="192.168.1.100"
                      secondary="Home Network"
                    />
                    <ListItemSecondaryAction>
                      <IconButton size="small">
                        <Security />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                </List>

                <Alert severity="warning" sx={{ mt: 2 }}>
                  Enable IP restrictions only if you access SignalOS from fixed locations.
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={4}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Configuration Profiles
                  </Typography>
                  <Button
                    variant="outlined"
                    startIcon={<Backup />}
                    onClick={() => setOpenBackupDialog(true)}
                  >
                    Backup & Restore
                  </Button>
                </Box>

                <List>
                  {profiles.map((profile) => (
                    <ListItem key={profile.id}>
                      <ListItemText
                        primary={profile.name}
                        secondary={`Type: ${profile.type}`}
                      />
                      <Chip
                        label={profile.active ? 'Active' : 'Inactive'}
                        color={profile.active ? 'success' : 'default'}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <ListItemSecondaryAction>
                        <IconButton size="small">
                          <Download />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>

                <Button variant="outlined" fullWidth sx={{ mt: 2 }}>
                  Create New Profile
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={handleExportConfig}
                  fullWidth
                  sx={{ mb: 1 }}
                >
                  Export Configuration
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<Upload />}
                  component="label"
                  fullWidth
                  sx={{ mb: 1 }}
                >
                  Import Configuration
                  <input
                    type="file"
                    hidden
                    accept=".json"
                    onChange={handleImportConfig}
                  />
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<CloudSync />}
                  fullWidth
                  sx={{ mb: 1 }}
                >
                  Sync with Desktop
                </Button>

                <Button
                  variant="outlined"
                  color="warning"
                  onClick={handleResetToDefaults}
                  fullWidth
                >
                  Reset to Defaults
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Save Settings Button */}
      <Box display="flex" justifyContent="flex-end" mt={3}>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={handleSaveSettings}
          size="large"
        >
          Save Settings
        </Button>
      </Box>

      {/* Backup Dialog */}
      <Dialog open={openBackupDialog} onClose={() => setOpenBackupDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Backup & Restore</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Create a backup of your current configuration or restore from a previous backup.
          </Typography>
          
          <Box display="flex" flexDirection="column" gap={2}>
            <Button variant="outlined" startIcon={<Download />}>
              Create Full Backup
            </Button>
            <Button variant="outlined" startIcon={<Upload />} component="label">
              Restore from Backup
              <input type="file" hidden accept=".json" />
            </Button>
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            Backups include all settings, profiles, and configuration data.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBackupDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}