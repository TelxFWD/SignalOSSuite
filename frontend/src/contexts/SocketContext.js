import React, { createContext, useContext, useEffect, useState } from 'react';
import io from 'socket.io-client';
import { useAuth } from './AuthContext';

const SocketContext = createContext();

export function useSocket() {
  return useContext(SocketContext);
}

export function SocketProvider({ children }) {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [healthData, setHealthData] = useState(null);
  const [signalData, setSignalData] = useState(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      const newSocket = io('/', {
        transports: ['websocket'],
        autoConnect: true
      });

      newSocket.on('connect', () => {
        setConnected(true);
        console.log('Connected to SignalOS WebSocket');
      });

      newSocket.on('disconnect', () => {
        setConnected(false);
        console.log('Disconnected from SignalOS WebSocket');
      });

      newSocket.on('health_update', (data) => {
        setHealthData(data);
      });

      newSocket.on('signal_update', (data) => {
        setSignalData(data);
      });

      newSocket.on('status', (data) => {
        console.log('Status update:', data);
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
        setSocket(null);
        setConnected(false);
      };
    }
  }, [isAuthenticated]);

  const emitEvent = (event, data) => {
    if (socket && connected) {
      socket.emit(event, data);
    }
  };

  const requestHealthUpdate = () => {
    emitEvent('get_health');
  };

  const requestSignalUpdate = () => {
    emitEvent('get_signals');
  };

  const value = {
    socket,
    connected,
    healthData,
    signalData,
    emitEvent,
    requestHealthUpdate,
    requestSignalUpdate
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
}