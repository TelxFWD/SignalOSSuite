# SignalOS Desktop Application

## Overview

SignalOS is a next-generation Forex signal automation platform designed as a Windows desktop application. It provides an all-in-one solution for retail and funded traders to receive, parse, and execute trading signals from multiple sources including Telegram, Discord, and WhatsApp. The application features AI-powered signal parsing, MetaTrader 5 integration, and real-time monitoring capabilities.

## System Architecture

### Frontend Architecture
- **Web Framework**: React.js 18 with Material-UI component library
- **Application Type**: Modern web application with responsive dashboard interface
- **Main Components**:
  - Authentication system with JWT token management
  - Real-time dashboard with WebSocket connections
  - Telegram account manager for session and channel configuration
  - MT5 terminal setup with multi-account support
  - Strategy builder with beginner and professional modes
  - Performance analytics with interactive charts
  - Settings management with configuration profiles
  - Mobile-responsive layout with dark theme

### Backend Architecture
- **Web Server**: Flask with SocketIO for real-time WebSocket communication
- **API Layer**: RESTful API with comprehensive endpoints for all frontend features
- **Core Engine**: Python-based modular architecture with separate components for:
  - Signal listening and collection
  - AI-powered signal parsing
  - Signal execution engine
  - MetaTrader 5 synchronization
  - Health monitoring system
- **Communication**: WebSocket for real-time updates + REST API for data operations
- **Security**: JWT authentication with CORS support for web clients
- **Threading**: Multi-threaded design with worker threads for background operations

### Configuration Management
- **Settings System**: Centralized configuration using dataclasses
- **File Storage**: Local configuration files stored in user's home directory
- **Backup System**: Automatic configuration backups with restore capabilities

## Key Components

### 1. Signal Processing Pipeline
- **Raw Signal Collection**: Multi-source signal ingestion (Telegram, Discord, WhatsApp)
- **AI Parser**: NLP-powered signal parsing using spaCy and custom regex patterns
- **OCR Support**: Image-based signal extraction using EasyOCR
- **Signal Engine**: Processes parsed signals and generates execution commands

### 2. External Integrations
- **Telegram Integration**: Telethon-based listener for real-time channel monitoring
- **MetaTrader 5 Sync**: File-based communication system for trade execution
- **Authentication**: JWT-based user authentication with cloud API integration

### 3. User Interface Components
- **Dashboard**: Real-time signal monitoring and statistics
- **Configuration Panels**: Setup wizards for Telegram, MT5, and parser settings
- **Health Monitor**: System status and performance monitoring
- **Login System**: Secure user authentication with token management

### 4. Core Services
- **Logger**: Comprehensive logging system with file rotation
- **Health Monitor**: System diagnostics and performance tracking
- **Config Manager**: Settings management with backup/restore capabilities

## Data Flow

1. **Signal Collection**: External sources (Telegram channels) → Raw signals
2. **Signal Processing**: Raw signals → AI Parser → Parsed signals
3. **Signal Validation**: Parsed signals → Validation engine → Execution signals
4. **Trade Execution**: Execution signals → JSON files → MetaTrader 5 EA
5. **Monitoring**: All stages monitored through health system and dashboard

## External Dependencies

### Core Dependencies
- **PySide2**: GUI framework for desktop interface
- **Telethon**: Telegram API integration
- **spaCy**: Natural language processing for signal parsing
- **EasyOCR**: Optical character recognition for image signals
- **psutil**: System monitoring and resource tracking
- **requests**: HTTP client for API communications
- **PyJWT**: JWT token handling for authentication

### Development Dependencies
- **PyInstaller**: Application packaging for Windows distribution
- **pytest**: Testing framework (implied for production)

### System Requirements
- Python 3.11+
- Windows operating system (primary target)
- MetaTrader 5 terminal (for trade execution)

## Deployment Strategy

### Development Phase
- **Environment**: Replit for modular development and testing
- **Package Management**: Standard pip with requirements.txt approach
- **Testing**: Local development with MT5 demo accounts

### Production Deployment
- **Packaging**: PyInstaller for standalone Windows executable
- **Distribution**: Direct download from SaaS platform
- **Updates**: Automatic update mechanism through central API
- **Installation**: Self-contained installer with minimal dependencies

### Configuration Management
- **Local Storage**: User configuration in `~/.signalos/` directory
- **Cloud Sync**: Optional configuration synchronization with SaaS backend
- **Backup Strategy**: Local backups with cloud storage integration

## Changelog
- June 19, 2025: Initial setup
- June 19, 2025: Comprehensive core module review and enhancement completed
  - Fixed signal parser for Gold/XAU formats (3/4 signals now parsing successfully)
  - Enhanced stealth mode implementation with proper SL/TP removal
  - Created production-ready MT5 Expert Advisor (SignalOS_EA.mq5)
  - Implemented comprehensive health monitoring system
  - Added configuration import/export functionality
  - Enhanced SL buffer logic working correctly
  - Signal execution engine fully operational
  - Created retry queue system for failed signals
  - Added configuration templates (Beginner, Aggressive, Demo)
  - Implemented advanced logging and validation systems
- December 19, 2024: Migration from Replit Agent to Replit environment completed
  - Converted desktop application to web-based interface
  - Fixed Flask dependencies and package installation
  - Configured proper host binding (0.0.0.0) for Replit compatibility
  - Implemented mock psutil for health monitoring functionality
  - Updated security configuration for production environment
  - Created web templates and static asset directories
  - Fixed SocketIO configuration for real-time updates
- December 19, 2024: Comprehensive React.js frontend implementation completed
  - Built complete web dashboard following Section 2 specifications
  - Implemented JWT authentication with login/register functionality
  - Created Telegram session manager with channel configuration
  - Developed MT5 terminal setup with risk management and symbol mapping
  - Built strategy builder with beginner templates and pro custom rules
  - Added performance analytics with real-time charts and trade history
  - Implemented settings management with profile backup/restore
  - Added WebSocket integration for real-time system monitoring
  - Created responsive Material-UI interface with dark theme
  - Configured comprehensive API endpoints for all dashboard features

## User Preferences

Preferred communication style: Simple, everyday language.