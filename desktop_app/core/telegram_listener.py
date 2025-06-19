"""
Telegram listener for monitoring channels and receiving signals
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime

try:
    from telethon import TelegramClient, events
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
    from telethon.tl.types import Channel, Chat, User
except ImportError:
    # Graceful fallback if telethon is not installed
    TelegramClient = None
    events = None
    SessionPasswordNeededError = Exception
    PhoneCodeInvalidError = Exception
    Channel = Chat = User = object

from config.settings import settings
from models.signal_model import RawSignal
from core.logger import get_logger

logger = get_logger(__name__)

class TelegramListener:
    """Handles Telegram API integration and signal monitoring"""
    
    def __init__(self):
        self.client = None
        self.is_running = False
        self.connected = False
        self.session_file = settings.sessions_dir / f"{settings.telegram.session_name}.session"
        self.signal_callback = None
        self.monitored_channels = set()
        
        # Get API credentials from environment or config
        self.api_id, self.api_hash = settings.get_api_credentials()
        
    def set_signal_callback(self, callback: Callable[[RawSignal], None]):
        """Set callback function for received signals"""
        self.signal_callback = callback
    
    async def initialize(self) -> bool:
        """Initialize Telegram client"""
        try:
            if not TelegramClient:
                logger.error("Telethon library not available")
                return False
                
            if not self.api_id or not self.api_hash:
                logger.error("Telegram API credentials not configured")
                return False
            
            # Create client with session file
            self.client = TelegramClient(
                str(self.session_file),
                int(self.api_id),
                self.api_hash
            )
            
            # Connect to Telegram
            await self.client.connect()
            
            # Check if we're authorized
            if not await self.client.is_user_authorized():
                logger.warning("Telegram client not authorized")
                return False
            
            # Register event handlers
            self.register_event_handlers()
            
            self.connected = True
            logger.info("Telegram client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return False
    
    def create_session(self, phone: str, api_id: str, api_hash: str) -> bool:
        """Create a new Telegram session"""
        try:
            if not TelegramClient:
                logger.error("Telethon library not available")
                return False
            
            # Run the session creation in a new event loop
            return asyncio.run(self._create_session_async(phone, api_id, api_hash))
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    async def _create_session_async(self, phone: str, api_id: str, api_hash: str) -> bool:
        """Async session creation"""
        try:
            client = TelegramClient(
                str(self.session_file),
                int(api_id),
                api_hash
            )
            
            await client.connect()
            
            if not await client.is_user_authorized():
                # Send code request
                await client.send_code_request(phone)
                
                # In a real implementation, you'd need to get the code from user input
                # For now, log that manual intervention is needed
                logger.info("Verification code sent. Manual intervention required.")
                return False
            
            # Update stored credentials
            settings.telegram.api_id = api_id
            settings.telegram.api_hash = api_hash
            settings.telegram.phone_number = phone
            settings.save_config()
            
            await client.disconnect()
            return True
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return False
    
    def register_event_handlers(self):
        """Register Telegram event handlers"""
        if not self.client:
            return
        
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            """Handle incoming messages"""
            try:
                await self.process_message(event)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def process_message(self, event):
        """Process incoming Telegram message"""
        try:
            # Get message details
            message = event.message
            sender = await event.get_sender()
            chat = await event.get_chat()
            
            # Check if message is from a monitored channel
            if not self.is_monitored_channel(chat):
                return
            
            # Create raw signal object
            raw_signal = RawSignal(
                text=message.text or "",
                source_id=str(chat.id),
                source_name=getattr(chat, 'title', getattr(chat, 'username', 'Unknown')),
                message_id=message.id,
                timestamp=message.date or datetime.now(),
                sender_id=str(sender.id) if sender else None,
                has_media=bool(message.media),
                media_type=str(type(message.media).__name__) if message.media else None
            )
            
            # Download media if present and it's an image
            if message.media and hasattr(message.media, 'photo'):
                try:
                    media_path = await self.download_media(message, chat.id)
                    raw_signal.media_path = media_path
                except Exception as e:
                    logger.error(f"Error downloading media: {e}")
            
            logger.info(f"Received signal from {raw_signal.source_name}: {raw_signal.text[:50]}...")
            
            # Call signal callback if set
            if self.signal_callback:
                self.signal_callback(raw_signal)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def download_media(self, message, chat_id: int) -> Optional[str]:
        """Download media from message"""
        try:
            # Create media directory
            media_dir = settings.app_dir / "media" / str(chat_id)
            media_dir.mkdir(parents=True, exist_ok=True)
            
            # Download media
            file_path = await self.client.download_media(
                message,
                file=str(media_dir)
            )
            
            if file_path:
                logger.info(f"Downloaded media: {file_path}")
                return str(file_path)
                
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
        
        return None
    
    def is_monitored_channel(self, chat) -> bool:
        """Check if chat is a monitored channel"""
        if not chat:
            return False
        
        chat_identifier = None
        
        # Try to get username or title
        if hasattr(chat, 'username') and chat.username:
            chat_identifier = f"@{chat.username}"
        elif hasattr(chat, 'title') and chat.title:
            chat_identifier = chat.title
        
        # Check against monitored channels
        for channel in settings.telegram.channels:
            if channel == chat_identifier or channel == str(chat.id):
                return True
        
        return False
    
    async def join_channel(self, channel_identifier: str) -> bool:
        """Join a Telegram channel"""
        try:
            if not self.client:
                return False
            
            # Try to join the channel
            entity = await self.client.get_entity(channel_identifier)
            await self.client(JoinChannelRequest(entity))
            
            logger.info(f"Joined channel: {channel_identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining channel {channel_identifier}: {e}")
            return False
    
    async def leave_channel(self, channel_identifier: str) -> bool:
        """Leave a Telegram channel"""
        try:
            if not self.client:
                return False
            
            entity = await self.client.get_entity(channel_identifier)
            await self.client(LeaveChannelRequest(entity))
            
            logger.info(f"Left channel: {channel_identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Error leaving channel {channel_identifier}: {e}")
            return False
    
    async def discover_channels(self) -> List[Dict[str, str]]:
        """Discover available channels"""
        try:
            if not self.client:
                return []
            
            channels = []
            
            # Get dialogs (conversations)
            async for dialog in self.client.iter_dialogs():
                if isinstance(dialog.entity, Channel):
                    channel_info = {
                        'id': str(dialog.entity.id),
                        'title': dialog.entity.title or 'Unknown',
                        'username': dialog.entity.username or '',
                        'participants_count': getattr(dialog.entity, 'participants_count', 0)
                    }
                    channels.append(channel_info)
            
            logger.info(f"Discovered {len(channels)} channels")
            return channels
            
        except Exception as e:
            logger.error(f"Error discovering channels: {e}")
            return []
    
    def start_monitoring(self) -> bool:
        """Start monitoring channels"""
        try:
            if not self.client:
                logger.error("Client not initialized")
                return False
            
            if self.is_running:
                logger.warning("Monitoring already running")
                return True
            
            # Run the client
            asyncio.create_task(self._run_client())
            self.is_running = True
            
            logger.info("Started Telegram monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return False
    
    async def _run_client(self):
        """Run the Telegram client"""
        try:
            if not await self.initialize():
                logger.error("Failed to initialize client")
                return
            
            # Run until disconnected
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error running client: {e}")
        finally:
            self.is_running = False
            self.connected = False
    
    def stop_monitoring(self):
        """Stop monitoring channels"""
        try:
            if self.client and self.client.is_connected():
                asyncio.create_task(self.client.disconnect())
            
            self.is_running = False
            self.connected = False
            
            logger.info("Stopped Telegram monitoring")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected and self.client and self.client.is_connected()
    
    def test_connection(self) -> bool:
        """Test Telegram connection"""
        try:
            if not self.client:
                return asyncio.run(self.initialize())
            
            return self.is_connected()
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, str]:
        """Get session information"""
        info = {
            'session_file': str(self.session_file),
            'exists': self.session_file.exists(),
            'connected': self.is_connected(),
            'phone': settings.telegram.phone_number or 'Not set'
        }
        return info
