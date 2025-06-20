"""
SignalOS Execution Engine
Handles order placement, modification, and trade management
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_LIMIT = "SELL_LIMIT"
    SELL_STOP = "SELL_STOP"

class OrderStatus(Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    MODIFIED = "MODIFIED"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED = "CLOSED"

@dataclass
class TradingOrder:
    id: str
    signal_id: str
    pair: str
    order_type: OrderType
    lot_size: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profits: List[float] = None
    mt5_ticket: Optional[int] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = None
    executed_at: Optional[datetime] = None
    provider_id: str = None
    strategy_id: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.take_profits is None:
            self.take_profits = []

class ExecutionEngine:
    """Core execution engine for processing trading signals"""
    
    def __init__(self, mt5_bridge=None, risk_manager=None):
        self.mt5_bridge = mt5_bridge
        self.risk_manager = risk_manager
        self.active_orders: Dict[str, TradingOrder] = {}
        self.order_history: List[TradingOrder] = []
        
    async def process_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming trading signal"""
        try:
            logger.info(f"Processing signal: {signal_data.get('id')}")
            
            # Validate signal
            if not self._validate_signal(signal_data):
                return {"status": "error", "message": "Invalid signal data"}
            
            # Apply risk management
            if self.risk_manager and not await self.risk_manager.check_signal(signal_data):
                return {"status": "blocked", "message": "Signal blocked by risk management"}
            
            # Create trading order
            order = self._create_order_from_signal(signal_data)
            
            # Check entry conditions
            if not await self._check_entry_conditions(order):
                return {"status": "delayed", "message": "Entry conditions not met, order queued"}
            
            # Execute order
            result = await self._execute_order(order)
            
            if result["status"] == "success":
                self.active_orders[order.id] = order
                logger.info(f"Order executed successfully: {order.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return {"status": "error", "message": str(e)}
    
    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify existing order (TP, SL, partial close, etc.)"""
        try:
            order = self.active_orders.get(order_id)
            if not order:
                return {"status": "error", "message": "Order not found"}
            
            # Handle different modification types
            if "close_percentage" in modifications:
                return await self._close_partial(order, modifications["close_percentage"])
            
            if "new_stop_loss" in modifications:
                return await self._modify_stop_loss(order, modifications["new_stop_loss"])
            
            if "new_take_profit" in modifications:
                return await self._modify_take_profit(order, modifications["new_take_profit"])
            
            if "break_even" in modifications and modifications["break_even"]:
                return await self._move_to_break_even(order)
            
            return {"status": "error", "message": "Invalid modification type"}
            
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_provider_command(self, command: str, provider_id: str) -> Dict[str, Any]:
        """Process commands from signal providers (Close 50%, TP to X, etc.)"""
        try:
            command = command.lower().strip()
            
            # Parse command
            if "close" in command and "%" in command:
                percentage = self._extract_percentage(command)
                return await self._close_provider_positions(provider_id, percentage)
            
            elif "tp to" in command or "take profit to" in command:
                new_tp = self._extract_price(command)
                return await self._modify_provider_tp(provider_id, new_tp)
            
            elif "sl to" in command or "stop loss to" in command:
                new_sl = self._extract_price(command)
                return await self._modify_provider_sl(provider_id, new_sl)
            
            elif "break even" in command or "be" in command:
                return await self._break_even_provider_positions(provider_id)
            
            elif "cancel" in command or "delete" in command:
                return await self._cancel_provider_pending(provider_id)
            
            return {"status": "error", "message": "Unknown command"}
            
        except Exception as e:
            logger.error(f"Error processing provider command: {e}")
            return {"status": "error", "message": str(e)}
    
    def _validate_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Validate signal data structure"""
        required_fields = ["pair", "action", "entry"]
        return all(field in signal_data for field in required_fields)
    
    def _create_order_from_signal(self, signal_data: Dict[str, Any]) -> TradingOrder:
        """Create TradingOrder from signal data"""
        order_type = OrderType(signal_data["action"].upper())
        
        # Handle multiple TP levels
        take_profits = []
        if "tp" in signal_data:
            if isinstance(signal_data["tp"], list):
                take_profits = signal_data["tp"]
            else:
                take_profits = [signal_data["tp"]]
        
        # Extract TP1, TP2, TP3 if present
        for i in range(1, 6):  # Support up to TP5
            tp_key = f"tp{i}"
            if tp_key in signal_data:
                take_profits.append(signal_data[tp_key])
        
        return TradingOrder(
            id=f"order_{signal_data['id']}_{datetime.utcnow().timestamp()}",
            signal_id=signal_data["id"],
            pair=signal_data["pair"],
            order_type=order_type,
            lot_size=signal_data.get("lot_size", 0.01),
            entry_price=signal_data["entry"],
            stop_loss=signal_data.get("sl"),
            take_profits=take_profits,
            provider_id=signal_data.get("provider_id"),
            strategy_id=signal_data.get("strategy_id")
        )
    
    async def _check_entry_conditions(self, order: TradingOrder) -> bool:
        """Check if entry conditions are met (Smart Entry Mode)"""
        if not self.mt5_bridge:
            return True  # Skip check if no MT5 bridge
        
        try:
            current_price = await self.mt5_bridge.get_current_price(order.pair)
            spread = await self.mt5_bridge.get_spread(order.pair)
            
            # Smart Entry Logic
            price_diff = abs(current_price - order.entry_price)
            max_deviation = 5  # pips - make configurable
            
            # Check if price is within acceptable range
            if price_diff > max_deviation:
                return False
            
            # Check spread conditions
            max_spread = 3  # pips - make configurable
            if spread > max_spread:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking entry conditions: {e}")
            return False
    
    async def _execute_order(self, order: TradingOrder) -> Dict[str, Any]:
        """Execute order via MT5 bridge"""
        if not self.mt5_bridge:
            # Simulation mode
            order.status = OrderStatus.EXECUTED
            order.executed_at = datetime.utcnow()
            order.mt5_ticket = 999999  # Fake ticket for demo
            return {"status": "success", "ticket": order.mt5_ticket}
        
        try:
            result = await self.mt5_bridge.place_order(
                pair=order.pair,
                order_type=order.order_type.value,
                lot_size=order.lot_size,
                entry_price=order.entry_price,
                stop_loss=order.stop_loss,
                take_profits=order.take_profits
            )
            
            if result["status"] == "success":
                order.status = OrderStatus.EXECUTED
                order.executed_at = datetime.utcnow()
                order.mt5_ticket = result["ticket"]
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _close_partial(self, order: TradingOrder, percentage: float) -> Dict[str, Any]:
        """Close partial position"""
        try:
            close_lots = order.lot_size * (percentage / 100)
            
            if self.mt5_bridge:
                result = await self.mt5_bridge.close_partial(order.mt5_ticket, close_lots)
            else:
                result = {"status": "success"}  # Simulation
            
            if result["status"] == "success":
                order.lot_size -= close_lots
                order.status = OrderStatus.PARTIALLY_CLOSED
                logger.info(f"Closed {percentage}% of order {order.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error closing partial position: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _modify_stop_loss(self, order: TradingOrder, new_sl: float) -> Dict[str, Any]:
        """Modify stop loss"""
        try:
            if self.mt5_bridge:
                result = await self.mt5_bridge.modify_order(order.mt5_ticket, stop_loss=new_sl)
            else:
                result = {"status": "success"}  # Simulation
            
            if result["status"] == "success":
                order.stop_loss = new_sl
                order.status = OrderStatus.MODIFIED
                logger.info(f"Modified SL for order {order.id} to {new_sl}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error modifying stop loss: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _move_to_break_even(self, order: TradingOrder) -> Dict[str, Any]:
        """Move stop loss to break even"""
        return await self._modify_stop_loss(order, order.entry_price)
    
    def _extract_percentage(self, text: str) -> float:
        """Extract percentage from text"""
        import re
        match = re.search(r'(\d+(?:\.\d+)?)%', text)
        return float(match.group(1)) if match else 0
    
    def _extract_price(self, text: str) -> float:
        """Extract price from text"""
        import re
        match = re.search(r'to\s+(\d+(?:\.\d+)?)', text)
        return float(match.group(1)) if match else 0
    
    async def _close_provider_positions(self, provider_id: str, percentage: float) -> Dict[str, Any]:
        """Close percentage of all positions from a provider"""
        results = []
        for order in self.active_orders.values():
            if order.provider_id == provider_id and order.status == OrderStatus.EXECUTED:
                result = await self._close_partial(order, percentage)
                results.append(result)
        
        return {"status": "success", "results": results}
    
    async def _modify_provider_tp(self, provider_id: str, new_tp: float) -> Dict[str, Any]:
        """Modify take profit for all provider positions"""
        results = []
        for order in self.active_orders.values():
            if order.provider_id == provider_id and order.status == OrderStatus.EXECUTED:
                result = await self._modify_take_profit(order, new_tp)
                results.append(result)
        
        return {"status": "success", "results": results}
    
    async def _modify_provider_sl(self, provider_id: str, new_sl: float) -> Dict[str, Any]:
        """Modify stop loss for all provider positions"""
        results = []
        for order in self.active_orders.values():
            if order.provider_id == provider_id and order.status == OrderStatus.EXECUTED:
                result = await self._modify_stop_loss(order, new_sl)
                results.append(result)
        
        return {"status": "success", "results": results}
    
    async def _break_even_provider_positions(self, provider_id: str) -> Dict[str, Any]:
        """Move all provider positions to break even"""
        results = []
        for order in self.active_orders.values():
            if order.provider_id == provider_id and order.status == OrderStatus.EXECUTED:
                result = await self._move_to_break_even(order)
                results.append(result)
        
        return {"status": "success", "results": results}
    
    async def _cancel_provider_pending(self, provider_id: str) -> Dict[str, Any]:
        """Cancel all pending orders from provider"""
        results = []
        for order in self.active_orders.values():
            if order.provider_id == provider_id and order.status == OrderStatus.PENDING:
                if self.mt5_bridge:
                    result = await self.mt5_bridge.cancel_order(order.mt5_ticket)
                else:
                    result = {"status": "success"}
                
                if result["status"] == "success":
                    order.status = OrderStatus.CANCELLED
                    results.append(result)
        
        return {"status": "success", "results": results}
    
    async def _modify_take_profit(self, order: TradingOrder, new_tp: float) -> Dict[str, Any]:
        """Modify take profit"""
        try:
            if self.mt5_bridge:
                result = await self.mt5_bridge.modify_order(order.mt5_ticket, take_profit=new_tp)
            else:
                result = {"status": "success"}  # Simulation
            
            if result["status"] == "success":
                # Replace first TP or add new one
                if order.take_profits:
                    order.take_profits[0] = new_tp
                else:
                    order.take_profits = [new_tp]
                order.status = OrderStatus.MODIFIED
                logger.info(f"Modified TP for order {order.id} to {new_tp}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error modifying take profit: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status and details"""
        order = self.active_orders.get(order_id)
        if not order:
            return {"status": "not_found"}
        
        return {
            "status": "found",
            "order": {
                "id": order.id,
                "pair": order.pair,
                "type": order.order_type.value,
                "lot_size": order.lot_size,
                "entry_price": order.entry_price,
                "stop_loss": order.stop_loss,
                "take_profits": order.take_profits,
                "mt5_ticket": order.mt5_ticket,
                "status": order.status.value,
                "created_at": order.created_at.isoformat(),
                "executed_at": order.executed_at.isoformat() if order.executed_at else None
            }
        }
    
    def get_active_orders(self, provider_id: str = None) -> List[Dict[str, Any]]:
        """Get all active orders, optionally filtered by provider"""
        orders = []
        for order in self.active_orders.values():
            if provider_id and order.provider_id != provider_id:
                continue
            
            orders.append({
                "id": order.id,
                "signal_id": order.signal_id,
                "pair": order.pair,
                "type": order.order_type.value,
                "lot_size": order.lot_size,
                "entry_price": order.entry_price,
                "stop_loss": order.stop_loss,
                "take_profits": order.take_profits,
                "mt5_ticket": order.mt5_ticket,
                "status": order.status.value,
                "provider_id": order.provider_id,
                "created_at": order.created_at.isoformat()
            })
        
        return orders