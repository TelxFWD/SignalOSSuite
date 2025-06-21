"""
SignalOS Trading Service
Main orchestration service that coordinates all trading components
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from .execution_engine import ExecutionEngine, TradingOrder
from .advanced_execution_engine import AdvancedExecutionEngine, AdvancedTradingOrder
from .risk_manager import RiskManager, RiskSettings
from .advanced_risk_manager import AdvancedRiskManager
from .mt5_bridge import MT5Bridge
from .enhanced_signal_parser import EnhancedSignalParser, ParsedSignal, ParseConfidence
from .news_filter import NewsFilter, NewsFilterSettings, TimeWindowSettings

logger = logging.getLogger(__name__)

class TradingService:
    """Main trading service orchestrating all components"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.signal_parser = EnhancedSignalParser()
        self.risk_manager = AdvancedRiskManager()
        self.news_filter = NewsFilter()
        self.mt5_bridge = MT5Bridge(self.config.get('mt5', {}))
        self.execution_engine = AdvancedExecutionEngine(self.mt5_bridge, self.risk_manager)
        
        # Service state
        self.is_running = False
        self.active_providers = {}
        self.telegram_sessions = {}
        self.processing_queue = asyncio.Queue()
        
        # Statistics
        self.stats = {
            'signals_received': 0,
            'signals_processed': 0,
            'signals_executed': 0,
            'signals_blocked': 0,
            'orders_active': 0,
            'total_profit_loss': 0.0
        }
        
    async def start_service(self):
        """Start the trading service"""
        try:
            logger.info("Starting SignalOS Trading Service...")
            
            self.is_running = True
            
            # Start background tasks
            asyncio.create_task(self._process_signal_queue())
            asyncio.create_task(self._monitor_account())
            asyncio.create_task(self._update_statistics())
            
            logger.info("Trading Service started successfully")
            
        except Exception as e:
            logger.error(f"Error starting trading service: {e}")
            raise
    
    async def stop_service(self):
        """Stop the trading service"""
        try:
            logger.info("Stopping SignalOS Trading Service...")
            
            self.is_running = False
            
            # Close all positions if emergency stop
            if self.risk_manager.settings.emergency_close_all:
                await self._emergency_close_all_positions()
            
            logger.info("Trading Service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading service: {e}")
    
    async def process_telegram_signal(self, message_text: str, provider_id: str, 
                                    channel_id: str, message_id: str = None) -> Dict[str, Any]:
        """Process incoming Telegram signal with advanced filtering"""
        try:
            self.stats['signals_received'] += 1
            
            # Parse the signal
            parsed_signal = self.signal_parser.parse_signal(
                text=message_text,
                provider_id=provider_id,
                message_id=message_id
            )
            
            if parsed_signal.confidence == ParseConfidence.INVALID:
                self.stats['signals_blocked'] += 1
                return {
                    "status": "invalid",
                    "message": "Could not parse signal",
                    "signal_id": parsed_signal.signal_id
                }
            
            # Convert to signal data for filtering
            signal_data = {
                'id': parsed_signal.signal_id,
                'pair': parsed_signal.pair,
                'action': parsed_signal.action,
                'entry': parsed_signal.entry_price,
                'sl': parsed_signal.stop_loss,
                'provider_id': provider_id,
                'raw_text': message_text
            }
            
            # Check news and time filters
            blocked, block_reason = await self.news_filter.should_block_signal(signal_data)
            if blocked:
                self.stats['signals_blocked'] += 1
                return {
                    "status": "blocked",
                    "message": f"Signal blocked: {block_reason}",
                    "signal_id": parsed_signal.signal_id
                }
            
            # Add to processing queue
            await self.processing_queue.put({
                'type': 'new_signal',
                'parsed_signal': parsed_signal,
                'provider_id': provider_id,
                'channel_id': channel_id,
                'timestamp': datetime.utcnow(),
                'raw_text': message_text
            })
            
            return {
                "status": "queued",
                "message": "Signal queued for processing",
                "signal_id": parsed_signal.signal_id,
                "confidence": parsed_signal.confidence.value
            }
            
        except Exception as e:
            logger.error(f"Error processing Telegram signal: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_signal_edit(self, message_text: str, original_message_id: str,
                                 provider_id: str, channel_id: str) -> Dict[str, Any]:
        """Process edited Telegram signal"""
        try:
            # Parse the edited signal
            parsed_signal = self.signal_parser.parse_signal_edit(
                text=message_text,
                original_message_id=original_message_id,
                provider_id=provider_id
            )
            
            # Add to processing queue
            await self.processing_queue.put({
                'type': 'signal_edit',
                'parsed_signal': parsed_signal,
                'provider_id': provider_id,
                'channel_id': channel_id,
                'original_message_id': original_message_id,
                'timestamp': datetime.utcnow()
            })
            
            return {
                "status": "queued",
                "message": "Signal edit queued for processing",
                "signal_id": parsed_signal.signal_id
            }
            
        except Exception as e:
            logger.error(f"Error processing signal edit: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_provider_command(self, command: str, provider_id: str, 
                                     signal_id: str = None) -> Dict[str, Any]:
        """Process advanced provider command"""
        try:
            result = await self.execution_engine.process_provider_command_advanced(
                command, provider_id, signal_id
            )
            
            # Update statistics
            if result.get('status') == 'success':
                orders_affected = result.get('orders_affected', 0)
                logger.info(f"Provider command '{command}' affected {orders_affected} orders")
            
            return {
                "status": "success",
                "message": f"Command processed: {command}",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error processing provider command: {e}")
            return {"status": "error", "message": str(e)}
    
    async def add_telegram_session(self, session_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add new Telegram session"""
        try:
            session_id = session_config.get('session_id')
            
            # Store session configuration
            self.telegram_sessions[session_id] = {
                'phone': session_config.get('phone'),
                'api_id': session_config.get('api_id'),
                'api_hash': session_config.get('api_hash'),
                'status': 'connecting',
                'channels': [],
                'created_at': datetime.utcnow()
            }
            
            # Initialize Telegram client (placeholder - would use real Telethon/Pyrogram)
            # await self._initialize_telegram_session(session_id, session_config)
            
            return {
                "status": "success",
                "message": "Telegram session added",
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error adding Telegram session: {e}")
            return {"status": "error", "message": str(e)}
    
    async def add_mt5_terminal(self, terminal_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add new MT5 terminal"""
        try:
            terminal_id = terminal_config.get('terminal_id')
            
            result = await self.mt5_bridge.connect_terminal(
                terminal_id=terminal_id,
                login=terminal_config.get('login'),
                password=terminal_config.get('password'),
                server=terminal_config.get('server')
            )
            
            if result.get('status') == 'success':
                # Update account info
                account_info = await self.mt5_bridge.get_account_info(terminal_id)
                if account_info:
                    self.risk_manager.update_account_info(
                        balance=account_info.get('balance', 10000),
                        equity=account_info.get('equity', 10000)
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding MT5 terminal: {e}")
            return {"status": "error", "message": str(e)}
    
    async def update_risk_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update risk management settings"""
        try:
            self.risk_manager.update_risk_settings(settings)
            
            return {
                "status": "success",
                "message": "Risk settings updated"
            }
            
        except Exception as e:
            logger.error(f"Error updating risk settings: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status with advanced metrics"""
        try:
            # Get advanced risk status
            risk_status = self.risk_manager.get_advanced_risk_status()
            
            # Get MT5 status
            mt5_status = self.mt5_bridge.get_terminal_status()
            
            # Get active orders
            active_orders = self.execution_engine.get_active_orders()
            
            # Get parser statistics
            parser_stats = self.signal_parser.get_parse_statistics()
            
            # Get news filter status
            news_status = self.news_filter.get_filter_status()
            
            return {
                "service_running": self.is_running,
                "risk_status": risk_status,
                "mt5_status": mt5_status,
                "news_filter_status": news_status,
                "active_orders_count": len(active_orders),
                "telegram_sessions": len(self.telegram_sessions),
                "parser_statistics": parser_stats,
                "service_statistics": self.stats,
                "advanced_features": {
                    "smart_entry_enabled": True,
                    "multi_tp_support": True,
                    "trailing_stops": True,
                    "provider_commands": True,
                    "news_filtering": news_status['news_filter_enabled'],
                    "time_windows": news_status['time_filter_enabled'],
                    "advanced_risk_management": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_signal_queue(self):
        """Background task to process signal queue"""
        while self.is_running:
            try:
                # Get next item from queue
                item = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                
                if item['type'] == 'new_signal':
                    await self._handle_new_signal(item)
                elif item['type'] == 'signal_edit':
                    await self._handle_signal_edit(item)
                
                self.stats['signals_processed'] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing signal queue: {e}")
    
    async def _handle_new_signal(self, item: Dict[str, Any]):
        """Handle new trading signal with advanced processing"""
        try:
            parsed_signal = item['parsed_signal']
            
            # Convert to enhanced signal data format
            signal_data = {
                'id': parsed_signal.signal_id,
                'pair': parsed_signal.pair,
                'action': parsed_signal.action,
                'entry': parsed_signal.entry_price,
                'sl': parsed_signal.stop_loss,
                'tp': parsed_signal.take_profits[0] if parsed_signal.take_profits else None,
                'take_profits': parsed_signal.take_profits,
                'lot_size': parsed_signal.lot_size,
                'provider_id': parsed_signal.provider_id,
                'order_type': parsed_signal.order_type,
                'raw_text': item.get('raw_text', ''),
                'risk_percent': parsed_signal.risk_percent
            }
            
            # Advanced risk check
            risk_allowed, risk_reason = await self.risk_manager.check_signal_advanced(signal_data)
            if not risk_allowed:
                self.stats['signals_blocked'] += 1
                logger.warning(f"Signal {parsed_signal.signal_id} blocked by risk manager: {risk_reason}")
                return
            
            # Calculate lot size if not specified
            if not signal_data['lot_size']:
                signal_data['lot_size'] = self.risk_manager.calculate_lot_size(signal_data)
            
            # Process through advanced execution engine
            result = await self.execution_engine.process_advanced_signal(signal_data)
            
            if result['status'] == 'success':
                self.stats['signals_executed'] += 1
                self.stats['orders_active'] += 1
                
                # Record trade for risk tracking
                self.risk_manager.record_trade_advanced({
                    'provider_id': signal_data['provider_id'],
                    'pair': signal_data['pair'],
                    'lot_size': signal_data['lot_size'],
                    'status': 'opened',
                    'profit_loss': 0  # Will be updated when closed
                })
                
            elif result['status'] in ['blocked', 'queued', 'conditional']:
                if result['status'] == 'blocked':
                    self.stats['signals_blocked'] += 1
                    
            logger.info(f"Signal {parsed_signal.signal_id} processed: {result['status']}")
            
        except Exception as e:
            logger.error(f"Error handling new signal: {e}")
    
    async def _handle_signal_edit(self, item: Dict[str, Any]):
        """Handle edited signal"""
        try:
            parsed_signal = item['parsed_signal']
            original_message_id = item['original_message_id']
            
            # Find original order by message ID
            # This would require tracking message ID to order ID mapping
            
            # For now, log the edit
            logger.info(f"Signal edit detected for message {original_message_id}")
            
            # If modification data is available, apply it
            if parsed_signal.modification_type:
                modifications = json.loads(parsed_signal.modification_type)
                # Apply modifications to existing orders
                # This would require more sophisticated order tracking
                
        except Exception as e:
            logger.error(f"Error handling signal edit: {e}")
    
    async def _monitor_account(self):
        """Background task to monitor account status"""
        while self.is_running:
            try:
                # Update account info from MT5
                for terminal_id in self.mt5_bridge.terminals.keys():
                    account_info = await self.mt5_bridge.get_account_info(terminal_id)
                    if account_info:
                        self.risk_manager.update_account_info(
                            balance=account_info.get('balance', 10000),
                            equity=account_info.get('equity', 10000)
                        )
                        break  # Use first available terminal
                
                # Check risk limits
                risk_status = self.risk_manager.get_risk_status()
                if not risk_status['trading_allowed']:
                    logger.warning("Trading stopped due to risk limits")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring account: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _update_statistics(self):
        """Background task to update statistics"""
        while self.is_running:
            try:
                # Update active orders count
                active_orders = self.execution_engine.get_active_orders()
                self.stats['orders_active'] = len(active_orders)
                
                # Calculate total P/L (simplified)
                # In real implementation, this would sum actual trade results
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
                await asyncio.sleep(120)  # Wait longer on error
    
    async def _emergency_close_all_positions(self):
        """Emergency close all open positions"""
        try:
            logger.warning("Emergency close all positions initiated")
            
            for terminal_id in self.mt5_bridge.terminals.keys():
                await self.mt5_bridge.emergency_close_all(terminal_id)
            
            # Clear active orders
            self.execution_engine.active_orders.clear()
            self.stats['orders_active'] = 0
            
        except Exception as e:
            logger.error(f"Error in emergency close all: {e}")
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active orders"""
        return self.execution_engine.get_active_orders()
    
    def get_provider_orders(self, provider_id: str) -> List[Dict[str, Any]]:
        """Get orders for specific provider"""
        return self.execution_engine.get_active_orders(provider_id)
    
    async def manual_close_order(self, order_id: str) -> Dict[str, Any]:
        """Manually close an order"""
        try:
            order = self.execution_engine.active_orders.get(order_id)
            if not order:
                return {"status": "error", "message": "Order not found"}
            
            if order.mt5_ticket and self.mt5_bridge:
                result = await self.mt5_bridge.close_order(order.mt5_ticket)
            else:
                result = {"status": "success"}  # Simulation mode
            
            if result["status"] == "success":
                del self.execution_engine.active_orders[order_id]
                self.stats['orders_active'] -= 1
                logger.info(f"Order {order_id} closed manually")
            
            return result
            
        except Exception as e:
            logger.error(f"Error closing order manually: {e}")
            return {"status": "error", "message": str(e)}
    
    async def replay_signal(self, signal_text: str, provider_id: str) -> Dict[str, Any]:
        """Replay a missed or failed signal"""
        try:
            logger.info(f"Replaying signal from provider {provider_id}")
            
            # Process as new signal
            return await self.process_telegram_signal(
                message_text=signal_text,
                provider_id=provider_id,
                channel_id="replay",
                message_id=f"replay_{datetime.utcnow().timestamp()}"
            )
            
        except Exception as e:
            logger.error(f"Error replaying signal: {e}")
            return {"status": "error", "message": str(e)}