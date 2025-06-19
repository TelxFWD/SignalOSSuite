# SignalOS React Frontend

This is the React.js frontend for the SignalOS Forex Signal Automation Platform.

## Features

- **Authentication & Licensing**: JWT-based secure login with license management
- **Telegram Account Manager**: Session management and channel configuration  
- **MT5/MT4 Terminal Setup**: Multi-terminal configuration with risk management
- **Strategy Builder**: Beginner templates and advanced custom rule builder
- **Performance Analytics**: Real-time charts, equity curves, and trade analysis
- **Configuration Management**: Profile backup/restore and settings sync

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

The app will open at http://localhost:3000

### Build for Production

```bash
npm run build
```

## Architecture

- **React 18** with functional components and hooks
- **Material-UI** for consistent design system
- **React Router** for client-side routing
- **Socket.IO** for real-time updates
- **Recharts** for data visualization
- **Axios** for API communication

## API Integration

The frontend communicates with the Flask backend via REST API and WebSocket connections:

- Authentication endpoints: `/api/auth/*`
- Telegram management: `/api/telegram/*`
- MT5 configuration: `/api/mt5/*`
- Analytics data: `/api/analytics/*`
- Strategy management: `/api/strategies/*`

## Components Structure

```
src/
├── components/
│   ├── Auth/           # Login and registration
│   ├── Dashboard/      # Main dashboard with widgets
│   ├── Telegram/       # Telegram session management
│   ├── MT5/           # MT5 terminal configuration
│   ├── Strategy/      # Strategy builder (beginner/pro)
│   ├── Analytics/     # Performance charts and reports
│   ├── Settings/      # Application settings
│   └── Layout/        # Navigation and layout wrapper
├── contexts/          # React context providers
└── utils/            # Helper functions
```

## Real-time Features

- Live system health monitoring
- Real-time trade updates via WebSocket
- Automatic reconnection handling
- Connection status indicators