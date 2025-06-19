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
  FormControlLabel,
  Switch,
  Alert
} from '@mui/material';
import {
  Add,
  Delete,
  Refresh,
  CloudUpload,
  PhoneAndroid,
  Group
} from '@mui/icons-material';
import axios from 'axios';

export default function TelegramManager() {
  const [sessions, setSessions] = useState([]);
  const [channels, setChannels] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState('session'); // 'session' or 'channel'
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    phone: '',
    apiId: '',
    apiHash: '',
    channelUrl: '',
    channelName: '',
    enabled: true
  });

  useEffect(() => {
    fetchSessions();
    fetchChannels();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await axios.get('/api/telegram/sessions');
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const fetchChannels = async () => {
    try {
      const response = await axios.get('/api/telegram/channels');
      setChannels(response.data.channels || []);
    } catch (error) {
      console.error('Error fetching channels:', error);
    }
  };

  const handleAddSession = () => {
    setDialogType('session');
    setFormData({ phone: '', apiId: '', apiHash: '', enabled: true });
    setOpenDialog(true);
  };

  const handleAddChannel = () => {
    setDialogType('channel');
    setFormData({ channelUrl: '', channelName: '', enabled: true });
    setOpenDialog(true);
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      if (dialogType === 'session') {
        await axios.post('/api/telegram/sessions', {
          phone: formData.phone,
          api_id: formData.apiId,
          api_hash: formData.apiHash
        });
        fetchSessions();
      } else {
        await axios.post('/api/telegram/channels', {
          url: formData.channelUrl,
          name: formData.channelName,
          enabled: formData.enabled
        });
        fetchChannels();
      }
      setOpenDialog(false);
    } catch (error) {
      console.error('Error submitting form:', error);
    }
    setLoading(false);
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await axios.delete(`/api/telegram/sessions/${sessionId}`);
      fetchSessions();
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleDeleteChannel = async (channelId) => {
    try {
      await axios.delete(`/api/telegram/channels/${channelId}`);
      fetchChannels();
    } catch (error) {
      console.error('Error deleting channel:', error);
    }
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
        Telegram Account Manager
      </Typography>

      <Grid container spacing={3}>
        {/* Telegram Sessions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Telegram Sessions
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={handleAddSession}
                >
                  Add Session
                </Button>
              </Box>

              {sessions.length === 0 ? (
                <Alert severity="info">
                  No Telegram sessions configured. Add a session to start monitoring channels.
                </Alert>
              ) : (
                <List>
                  {sessions.map((session) => (
                    <ListItem key={session.id}>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <PhoneAndroid fontSize="small" />
                            {session.phone}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              Last activity: {new Date(session.last_activity).toLocaleString()}
                            </Typography>
                            <Typography variant="body2">
                              Channels: {session.channels?.length || 0}
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip
                        label={session.status}
                        color={getStatusColor(session.status)}
                        size="small"
                      />
                      <ListItemSecondaryAction>
                        <IconButton onClick={() => handleDeleteSession(session.id)}>
                          <Delete />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Monitored Channels */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Monitored Channels
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={handleAddChannel}
                >
                  Add Channel
                </Button>
              </Box>

              {channels.length === 0 ? (
                <Alert severity="info">
                  No channels configured. Add channels to monitor for trading signals.
                </Alert>
              ) : (
                <List>
                  {channels.map((channel) => (
                    <ListItem key={channel.id}>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Group fontSize="small" />
                            {channel.name}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              URL: {channel.url}
                            </Typography>
                            <Typography variant="body2">
                              Last signal: {channel.last_signal || 'None'}
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip
                        label={channel.enabled ? 'Active' : 'Disabled'}
                        color={channel.enabled ? 'success' : 'default'}
                        size="small"
                      />
                      <ListItemSecondaryAction>
                        <IconButton onClick={() => handleDeleteChannel(channel.id)}>
                          <Delete />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Session File Upload */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session File Management
              </Typography>
              <Box display="flex" gap={2} alignItems="center">
                <Button
                  variant="outlined"
                  startIcon={<CloudUpload />}
                  component="label"
                >
                  Upload .session File
                  <input type="file" hidden accept=".session" />
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                >
                  Refresh Sessions
                </Button>
              </Box>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Upload existing Telegram session files to quickly restore connections.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add Session/Channel Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'session' ? 'Add Telegram Session' : 'Add Telegram Channel'}
        </DialogTitle>
        <DialogContent>
          {dialogType === 'session' ? (
            <Box sx={{ pt: 1 }}>
              <TextField
                fullWidth
                label="Phone Number"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+1234567890"
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="API ID"
                value={formData.apiId}
                onChange={(e) => setFormData({ ...formData, apiId: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="API Hash"
                value={formData.apiHash}
                onChange={(e) => setFormData({ ...formData, apiHash: e.target.value })}
                sx={{ mb: 2 }}
              />
              <Alert severity="info" sx={{ mb: 2 }}>
                Get your API credentials from https://my.telegram.org/apps
              </Alert>
            </Box>
          ) : (
            <Box sx={{ pt: 1 }}>
              <TextField
                fullWidth
                label="Channel URL"
                value={formData.channelUrl}
                onChange={(e) => setFormData({ ...formData, channelUrl: e.target.value })}
                placeholder="@forex_signals or https://t.me/forex_signals"
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Display Name"
                value={formData.channelName}
                onChange={(e) => setFormData({ ...formData, channelName: e.target.value })}
                placeholder="Forex Signals Channel"
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  />
                }
                label="Enable monitoring"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={loading}>
            {loading ? 'Adding...' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}