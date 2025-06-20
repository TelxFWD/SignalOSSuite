"""
SignalOS MT5 Bridge
Communication layer with MetaTrader 5 terminals
"""
import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class MT5Bridge:
    """MetaTrader 5 communication bridge"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.terminals = {}  # Active terminal connections
        self.ea_path = self.config.get("ea_path", "experts/SignalOS_EA.ex5")
        self.json_path = self.config.get("json_path", "Files/SignalOS")
        
    async def connect_terminal(self, terminal_id: str, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to MT5 terminal"""
        try:
            terminal_config = {
                "terminal_id": terminal_id,
                "login": login,
                "server": server,
                "status": "connecting",
                "last_ping": datetime.utcnow()
            }
            
            # Store terminal configuration
            self.terminals[terminal_id] = terminal_config
            
            # Send connection command to EA
            command = {
                "action": "connect",
                "terminal_id": terminal_id,
                "login": login,
                "server": server,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            
            if result.get("status") == "success":
                terminal_config["status"] = "connected"
                logger.info(f"Connected to MT5 terminal: {terminal_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error connecting to terminal {terminal_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_current_price(self, pair: str, terminal_id: str = None) -> float:
        """Get current market price for a pair"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "get_price",
                "pair": pair,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            
            if result.get("status") == "success":
                return result.get("price", 0.0)
            
            # Fallback to simulation price
            return self._get_simulation_price(pair)
            
        except Exception as e:
            logger.error(f"Error getting price for {pair}: {e}")
            return self._get_simulation_price(pair)
    
    async def get_spread(self, pair: str, terminal_id: str = None) -> float:
        """Get current spread for a pair"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "get_spread",
                "pair": pair,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            
            if result.get("status") == "success":
                return result.get("spread", 0.0)
            
            return 2.0  # Default spread simulation
            
        except Exception as e:
            logger.error(f"Error getting spread for {pair}: {e}")
            return 2.0
    
    async def place_order(self, pair: str, order_type: str, lot_size: float, 
                         entry_price: float, stop_loss: Optional[float] = None,
                         take_profits: List[float] = None, terminal_id: str = None) -> Dict[str, Any]:
        """Place trading order"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            if not terminal_id:
                return {"status": "error", "message": "No active terminal"}
            
            command = {
                "action": "place_order",
                "pair": pair,
                "order_type": order_type,
                "lot_size": lot_size,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profits": take_profits or [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            
            # Handle multi-TP orders
            if result.get("status") == "success" and take_profits and len(take_profits) > 1:
                await self._setup_multi_tp_levels(result.get("ticket"), take_profits, terminal_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"status": "error", "message": str(e)}
    
    async def modify_order(self, ticket: int, stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None, terminal_id: str = None) -> Dict[str, Any]:
        """Modify existing order"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "modify_order",
                "ticket": ticket,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._send_command_to_ea(terminal_id, command)
            
        except Exception as e:
            logger.error(f"Error modifying order {ticket}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def close_partial(self, ticket: int, lot_size: float, terminal_id: str = None) -> Dict[str, Any]:
        """Close partial position"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "close_partial",
                "ticket": ticket,
                "lot_size": lot_size,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._send_command_to_ea(terminal_id, command)
            
        except Exception as e:
            logger.error(f"Error closing partial position {ticket}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def close_order(self, ticket: int, terminal_id: str = None) -> Dict[str, Any]:
        """Close order completely"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "close_order",
                "ticket": ticket,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._send_command_to_ea(terminal_id, command)
            
        except Exception as e:
            logger.error(f"Error closing order {ticket}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def cancel_order(self, ticket: int, terminal_id: str = None) -> Dict[str, Any]:
        """Cancel pending order"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "cancel_order",
                "ticket": ticket,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._send_command_to_ea(terminal_id, command)
            
        except Exception as e:
            logger.error(f"Error canceling order {ticket}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_account_info(self, terminal_id: str = None) -> Dict[str, Any]:
        """Get account information"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "get_account_info",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            
            if result.get("status") == "success":
                return result.get("account_info", {})
            
            # Fallback to simulation
            return {
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "free_margin": 10000.0,
                "margin_level": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    async def get_open_positions(self, terminal_id: str = None) -> List[Dict[str, Any]]:
        """Get all open positions"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "get_positions",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            
            if result.get("status") == "success":
                return result.get("positions", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def _send_command_to_ea(self, terminal_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to MT5 EA via JSON file communication"""
        try:
            # Create command file
            command_file = f"{self.json_path}/command_{terminal_id}_{datetime.utcnow().timestamp()}.json"
            response_file = f"{self.json_path}/response_{terminal_id}_{datetime.utcnow().timestamp()}.json"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(command_file), exist_ok=True)
            
            # Add response file to command
            command["response_file"] = response_file
            
            # Write command file
            with open(command_file, 'w') as f:
                json.dump(command, f, indent=2)
            
            # Wait for response (with timeout)
            response = await self._wait_for_response(response_file, timeout=10)
            
            # Cleanup files
            self._cleanup_files([command_file, response_file])
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending command to EA: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _wait_for_response(self, response_file: str, timeout: int = 10) -> Dict[str, Any]:
        """Wait for EA response file"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            if os.path.exists(response_file):
                try:
                    with open(response_file, 'r') as f:
                        response = json.load(f)
                    return response
                except (json.JSONDecodeError, IOError):
                    # File might be being written, wait a bit more
                    await asyncio.sleep(0.1)
                    continue
            
            await asyncio.sleep(0.1)
        
        return {"status": "timeout", "message": "EA response timeout"}
    
    def _cleanup_files(self, files: List[str]):
        """Clean up temporary files"""
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup file {file_path}: {e}")
    
    def _get_active_terminal(self) -> Optional[str]:
        """Get first active terminal ID"""
        for terminal_id, config in self.terminals.items():
            if config.get("status") == "connected":
                return terminal_id
        return None
    
    def _get_simulation_price(self, pair: str) -> float:
        """Get simulation price for demo mode"""
        # Simple price simulation
        base_prices = {
            "EURUSD": 1.0500,
            "GBPUSD": 1.2500,
            "USDJPY": 150.00,
            "USDCHF": 0.9000,
            "AUDUSD": 0.6500,
            "USDCAD": 1.3500
        }
        
        return base_prices.get(pair, 1.0000)
    
    async def _setup_multi_tp_levels(self, ticket: int, take_profits: List[float], terminal_id: str):
        """Setup multiple TP levels (MT5 limitation workaround)"""
        try:
            # Get original order info
            positions = await self.get_open_positions(terminal_id)
            original_order = None
            
            for pos in positions:
                if pos.get("ticket") == ticket:
                    original_order = pos
                    break
            
            if not original_order:
                return
            
            # Close original order and create multiple orders with different TPs
            lot_per_tp = original_order.get("lot_size", 0.01) / len(take_profits)
            
            for i, tp in enumerate(take_profits):
                if i == 0:
                    # Modify original order with first TP
                    await self.modify_order(ticket, take_profit=tp, terminal_id=terminal_id)
                else:
                    # Create additional orders for other TPs
                    command = {
                        "action": "place_order",
                        "pair": original_order.get("pair"),
                        "order_type": original_order.get("order_type"),
                        "lot_size": lot_per_tp,
                        "entry_price": original_order.get("entry_price"),
                        "stop_loss": original_order.get("stop_loss"),
                        "take_profits": [tp],
                        "comment": f"TP{i+1}_from_{ticket}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await self._send_command_to_ea(terminal_id, command)
                    
        except Exception as e:
            logger.error(f"Error setting up multi-TP levels: {e}")
    
    def get_terminal_status(self, terminal_id: str = None) -> Dict[str, Any]:
        """Get terminal connection status"""
        if terminal_id:
            return self.terminals.get(terminal_id, {"status": "not_found"})
        
        return {
            "terminals": self.terminals,
            "active_count": len([t for t in self.terminals.values() if t.get("status") == "connected"])
        }
    
    async def ping_terminal(self, terminal_id: str) -> bool:
        """Ping terminal to check connectivity"""
        try:
            command = {
                "action": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            
            if result.get("status") == "success":
                if terminal_id in self.terminals:
                    self.terminals[terminal_id]["last_ping"] = datetime.utcnow()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error pinging terminal {terminal_id}: {e}")
            return False
    
    async def emergency_close_all(self, terminal_id: str = None) -> Dict[str, Any]:
        """Emergency close all positions"""
        try:
            if not terminal_id:
                terminal_id = self._get_active_terminal()
            
            command = {
                "action": "emergency_close_all",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_command_to_ea(terminal_id, command)
            logger.warning(f"Emergency close all executed on terminal {terminal_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in emergency close all: {e}")
            return {"status": "error", "message": str(e)}