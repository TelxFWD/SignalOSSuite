"""
SignalOS Advanced Execution Engine
Complete order type support and smart execution logic
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .execution_engine import ExecutionEngine, TradingOrder, OrderType, OrderStatus

logger = logging.getLogger(__name__)

class SmartEntryMode(Enum):
    IMMEDIATE = "IMMEDIATE"
    RANGE_BASED = "RANGE_BASED"
    SPREAD_OPTIMIZED = "SPREAD_OPTIMIZED"
    DUAL_ENTRY = "DUAL_ENTRY"

class OrderExecution(Enum):
    MARKET = "MARKET"
    PENDING = "PENDING"
    CONDITIONAL = "CONDITIONAL"

@dataclass
class AdvancedOrderConfig:
    smart_entry_mode: SmartEntryMode = SmartEntryMode.IMMEDIATE
    max_entry_deviation_pips: float = 5.0
    max_spread_pips: float = 3.0
    dual_entry_enabled: bool = False
    dual_entry_distance_pips: float = 10.0
    pending_order_expiry_hours: int = 24
    retry_failed_orders: bool = True
    max_retry_attempts: int = 3

@dataclass
class TakeProfitLevel:
    level: int
    price: float
    lot_percentage: float  # Percentage of total position
    sl_move_on_hit: Optional[float] = None  # Move SL to this price when TP hits
    
@dataclass
class AdvancedTradingOrder(TradingOrder):
    tp_levels: List[TakeProfitLevel] = None
    trailing_sl_enabled: bool = False
    trailing_sl_distance_pips: float = 20.0
    break_even_pips: float = 10.0
    smart_entry_config: AdvancedOrderConfig = None
    original_signal_text: str = ""
    provider_commands: List[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.tp_levels is None:
            self.tp_levels = []
        if self.smart_entry_config is None:
            self.smart_entry_config = AdvancedOrderConfig()
        if self.provider_commands is None:
            self.provider_commands = []

class AdvancedExecutionEngine(ExecutionEngine):
    """Advanced execution engine with complete order management"""
    
    def __init__(self, mt5_bridge=None, risk_manager=None):
        super().__init__(mt5_bridge, risk_manager)
        self.pending_orders: Dict[str, AdvancedTradingOrder] = {}
        self.order_tracking: Dict[int, str] = {}  # MT5 ticket -> order_id mapping
        self.provider_commands_queue: List[Dict[str, Any]] = []
        
    async def process_advanced_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process signal with advanced order management"""
        try:
            logger.info(f"Processing advanced signal: {signal_data.get('id')}")
            
            # Validate and enhance signal
            enhanced_signal = await self._enhance_signal_data(signal_data)
            
            # Create advanced trading order
            order = self._create_advanced_order(enhanced_signal)
            
            # Determine execution strategy
            execution_strategy = self._determine_execution_strategy(order)
            
            if execution_strategy == OrderExecution.MARKET:
                result = await self._execute_market_order(order)
            elif execution_strategy == OrderExecution.PENDING:
                result = await self._place_pending_order(order)
            else:
                result = await self._setup_conditional_order(order)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing advanced signal: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _enhance_signal_data(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance signal data with advanced parsing"""
        enhanced = signal_data.copy()
        
        # Parse multiple TP levels
        tp_levels = self._parse_multiple_tp_levels(signal_data)
        enhanced['tp_levels'] = tp_levels
        
        # Determine order type from signal
        order_type = self._determine_order_type(signal_data)
        enhanced['order_type'] = order_type
        
        # Parse lot size with risk calculation
        lot_size = await self._calculate_advanced_lot_size(signal_data)
        enhanced['lot_size'] = lot_size
        
        # Extract provider commands from signal text
        commands = self._extract_provider_commands(signal_data.get('raw_text', ''))
        enhanced['provider_commands'] = commands
        
        return enhanced
    
    def _parse_multiple_tp_levels(self, signal_data: Dict[str, Any]) -> List[TakeProfitLevel]:
        """Parse up to 100 TP levels from signal"""
        tp_levels = []
        
        # Check for explicit TP levels (TP1, TP2, etc.)
        for i in range(1, 101):  # Support up to 100 TP levels
            tp_key = f"tp{i}"
            if tp_key in signal_data:
                tp_levels.append(TakeProfitLevel(
                    level=i,
                    price=signal_data[tp_key],
                    lot_percentage=100.0 / len([k for k in signal_data.keys() if k.startswith('tp')])
                ))
        
        # If no explicit levels, check for single TP or TP array
        if not tp_levels:
            if 'tp' in signal_data:
                tp_value = signal_data['tp']
                if isinstance(tp_value, list):
                    for i, tp in enumerate(tp_value):
                        tp_levels.append(TakeProfitLevel(
                            level=i+1,
                            price=tp,
                            lot_percentage=100.0 / len(tp_value)
                        ))
                else:
                    tp_levels.append(TakeProfitLevel(
                        level=1,
                        price=tp_value,
                        lot_percentage=100.0
                    ))
        
        # Set SL movement logic for multi-TP
        if len(tp_levels) > 1:
            for i, tp_level in enumerate(tp_levels):
                if i > 0:  # Starting from TP2
                    # Move SL to previous TP level when this TP hits
                    tp_level.sl_move_on_hit = tp_levels[i-1].price
        
        return tp_levels
    
    def _determine_order_type(self, signal_data: Dict[str, Any]) -> OrderType:
        """Determine order type from signal data"""
        action = signal_data.get('action', '').upper()
        order_type_str = signal_data.get('order_type', '').upper()
        
        if 'LIMIT' in order_type_str:
            return OrderType.BUY_LIMIT if action == 'BUY' else OrderType.SELL_LIMIT
        elif 'STOP' in order_type_str:
            return OrderType.BUY_STOP if action == 'BUY' else OrderType.SELL_STOP
        else:
            return OrderType.BUY if action == 'BUY' else OrderType.SELL
    
    async def _calculate_advanced_lot_size(self, signal_data: Dict[str, Any]) -> float:
        """Advanced lot size calculation with proper pip value"""
        if self.risk_manager:
            return self.risk_manager.calculate_lot_size(signal_data)
        
        # Extract lot from signal text if specified
        raw_text = signal_data.get('raw_text', '').upper()
        
        # Look for lot size in text
        import re
        lot_patterns = [
            r'LOT[S]?\s*[:\-]?\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*LOT[S]?',
            r'SIZE\s*[:\-]?\s*(\d+\.?\d*)'
        ]
        
        for pattern in lot_patterns:
            match = re.search(pattern, raw_text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        # Extract risk percentage and calculate
        risk_patterns = [
            r'RISK\s*[:\-]?\s*(\d+\.?\d*)%',
            r'(\d+\.?\d*)%\s*RISK'
        ]
        
        for pattern in risk_patterns:
            match = re.search(pattern, raw_text)
            if match:
                try:
                    risk_percent = float(match.group(1))
                    return await self._calculate_risk_based_lot(signal_data, risk_percent)
                except ValueError:
                    continue
        
        return 0.01  # Default minimum lot
    
    async def _calculate_risk_based_lot(self, signal_data: Dict[str, Any], risk_percent: float) -> float:
        """Calculate lot size based on risk percentage"""
        try:
            entry = signal_data.get('entry', 0)
            sl = signal_data.get('sl', 0)
            pair = signal_data.get('pair', 'EURUSD')
            
            if not entry or not sl:
                return 0.01
            
            # Get account balance
            account_balance = 10000.0  # Default, should get from MT5
            if self.mt5_bridge:
                account_info = await self.mt5_bridge.get_account_info()
                account_balance = account_info.get('balance', 10000.0)
            
            # Calculate risk amount
            risk_amount = account_balance * (risk_percent / 100)
            
            # Calculate pip distance
            pip_distance = abs(entry - sl)
            if pair.endswith('JPY'):
                pip_distance *= 100
            else:
                pip_distance *= 10000
            
            # Calculate pip value (simplified)
            if pair.endswith('JPY'):
                pip_value = 1000  # For 1 lot
            else:
                pip_value = 10  # For 1 lot
            
            # Calculate lot size
            lot_size = risk_amount / (pip_distance * pip_value)
            
            # Validate and round
            lot_size = max(0.01, min(100.0, lot_size))
            return round(lot_size, 2)
            
        except Exception as e:
            logger.error(f"Error calculating risk-based lot: {e}")
            return 0.01
    
    def _extract_provider_commands(self, signal_text: str) -> List[str]:
        """Extract provider commands from signal text"""
        commands = []
        text = signal_text.upper()
        
        # Common command patterns
        command_patterns = [
            r'CLOSE\s+(\d+)%',
            r'CLOSE\s+ALL',
            r'CANCEL\s+ALL',
            r'TP\s+TO\s+(\d+\.?\d*)',
            r'SL\s+TO\s+(\d+\.?\d*)',
            r'BREAK\s*EVEN',
            r'MOVE\s+SL\s+TO\s+(\d+\.?\d*)',
            r'TRAILING\s+STOP'
        ]
        
        for pattern in command_patterns:
            import re
            matches = re.findall(pattern, text)
            if matches:
                commands.append(pattern.replace(r'\s+', ' ').replace(r'(\d+\.?\d*)', matches[0] if matches[0] else ''))
        
        return commands
    
    def _create_advanced_order(self, signal_data: Dict[str, Any]) -> AdvancedTradingOrder:
        """Create advanced trading order from signal data"""
        order = AdvancedTradingOrder(
            id=f"adv_order_{signal_data['id']}_{datetime.utcnow().timestamp()}",
            signal_id=signal_data["id"],
            pair=signal_data["pair"],
            order_type=OrderType(signal_data.get("order_type", "BUY")),
            lot_size=signal_data.get("lot_size", 0.01),
            entry_price=signal_data["entry"],
            stop_loss=signal_data.get("sl"),
            provider_id=signal_data.get("provider_id"),
            strategy_id=signal_data.get("strategy_id"),
            tp_levels=signal_data.get("tp_levels", []),
            original_signal_text=signal_data.get("raw_text", ""),
            provider_commands=signal_data.get("provider_commands", [])
        )
        
        return order
    
    def _determine_execution_strategy(self, order: AdvancedTradingOrder) -> OrderExecution:
        """Determine how to execute the order"""
        # Check if it's a pending order type
        if order.order_type in [OrderType.BUY_LIMIT, OrderType.SELL_LIMIT, 
                               OrderType.BUY_STOP, OrderType.SELL_STOP]:
            return OrderExecution.PENDING
        
        # Check for conditional execution (entry range, spread conditions)
        if order.smart_entry_config.smart_entry_mode != SmartEntryMode.IMMEDIATE:
            return OrderExecution.CONDITIONAL
        
        return OrderExecution.MARKET
    
    async def _execute_market_order(self, order: AdvancedTradingOrder) -> Dict[str, Any]:
        """Execute market order with advanced features"""
        try:
            # Check entry conditions for smart execution
            if not await self._check_smart_entry_conditions(order):
                return await self._queue_for_smart_execution(order)
            
            # Execute primary order
            result = await self._place_primary_order(order)
            
            if result["status"] == "success":
                # Setup multiple TP levels
                await self._setup_multiple_tp_levels(order, result["ticket"])
                
                # Setup trailing SL if enabled
                if order.trailing_sl_enabled:
                    await self._setup_trailing_stop(order, result["ticket"])
                
                # Store order
                self.active_orders[order.id] = order
                self.order_tracking[result["ticket"]] = order.id
                
                # Process any immediate commands
                await self._process_immediate_commands(order)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing market order: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _place_pending_order(self, order: AdvancedTradingOrder) -> Dict[str, Any]:
        """Place pending order (LIMIT/STOP)"""
        try:
            if not self.mt5_bridge:
                # Simulation mode
                order.status = OrderStatus.PENDING
                self.pending_orders[order.id] = order
                return {"status": "success", "message": "Pending order placed (simulation)"}
            
            # Place pending order via MT5
            result = await self.mt5_bridge.place_order(
                pair=order.pair,
                order_type=order.order_type.value,
                lot_size=order.lot_size,
                entry_price=order.entry_price,
                stop_loss=order.stop_loss,
                take_profits=[tp.price for tp in order.tp_levels[:1]]  # Only first TP for pending
            )
            
            if result["status"] == "success":
                order.status = OrderStatus.PENDING
                order.mt5_ticket = result["ticket"]
                self.pending_orders[order.id] = order
                self.order_tracking[result["ticket"]] = order.id
                
                # Set expiry
                expiry_time = datetime.utcnow() + timedelta(hours=order.smart_entry_config.pending_order_expiry_hours)
                asyncio.create_task(self._handle_pending_order_expiry(order.id, expiry_time))
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing pending order: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _setup_conditional_order(self, order: AdvancedTradingOrder) -> Dict[str, Any]:
        """Setup conditional order execution"""
        try:
            # Add to monitoring queue
            self.pending_orders[order.id] = order
            
            # Start monitoring task
            asyncio.create_task(self._monitor_conditional_order(order))
            
            return {
                "status": "conditional",
                "message": "Order setup for conditional execution",
                "order_id": order.id
            }
            
        except Exception as e:
            logger.error(f"Error setting up conditional order: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _check_smart_entry_conditions(self, order: AdvancedTradingOrder) -> bool:
        """Check if smart entry conditions are met"""
        if not self.mt5_bridge:
            return True  # Always allow in simulation
        
        try:
            current_price = await self.mt5_bridge.get_current_price(order.pair)
            spread = await self.mt5_bridge.get_spread(order.pair)
            
            config = order.smart_entry_config
            
            # Check spread condition
            if spread > config.max_spread_pips:
                logger.info(f"Spread too wide: {spread} > {config.max_spread_pips}")
                return False
            
            # Check entry price deviation
            price_diff_pips = abs(current_price - order.entry_price)
            if order.pair.endswith('JPY'):
                price_diff_pips *= 100
            else:
                price_diff_pips *= 10000
            
            if price_diff_pips > config.max_entry_deviation_pips:
                logger.info(f"Price deviation too large: {price_diff_pips} > {config.max_entry_deviation_pips}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking smart entry conditions: {e}")
            return False
    
    async def _setup_multiple_tp_levels(self, order: AdvancedTradingOrder, primary_ticket: int):
        """Setup multiple TP levels for order"""
        try:
            if not order.tp_levels or len(order.tp_levels) <= 1:
                return  # Single or no TP, already handled
            
            # Calculate lot sizes for each TP level
            total_lots = order.lot_size
            
            for i, tp_level in enumerate(order.tp_levels):
                if i == 0:
                    # Modify primary order with first TP
                    await self.mt5_bridge.modify_order(
                        primary_ticket,
                        take_profit=tp_level.price
                    )
                else:
                    # Create additional orders for other TP levels
                    tp_lot_size = total_lots * (tp_level.lot_percentage / 100)
                    
                    if self.mt5_bridge:
                        await self.mt5_bridge.place_order(
                            pair=order.pair,
                            order_type=order.order_type.value,
                            lot_size=tp_lot_size,
                            entry_price=order.entry_price,
                            stop_loss=order.stop_loss,
                            take_profits=[tp_level.price],
                            comment=f"TP{tp_level.level}_from_{primary_ticket}"
                        )
            
            logger.info(f"Setup {len(order.tp_levels)} TP levels for order {order.id}")
            
        except Exception as e:
            logger.error(f"Error setting up multiple TP levels: {e}")
    
    async def _setup_trailing_stop(self, order: AdvancedTradingOrder, ticket: int):
        """Setup trailing stop loss"""
        try:
            # Start trailing stop monitoring task
            asyncio.create_task(self._monitor_trailing_stop(order, ticket))
            
            logger.info(f"Trailing stop setup for order {order.id}, distance: {order.trailing_sl_distance_pips} pips")
            
        except Exception as e:
            logger.error(f"Error setting up trailing stop: {e}")
    
    async def _monitor_trailing_stop(self, order: AdvancedTradingOrder, ticket: int):
        """Monitor and update trailing stop loss"""
        try:
            best_price = order.entry_price
            
            while order.id in self.active_orders:
                if not self.mt5_bridge:
                    await asyncio.sleep(5)
                    continue
                
                current_price = await self.mt5_bridge.get_current_price(order.pair)
                
                # Determine if we should trail
                should_trail = False
                
                if order.order_type == OrderType.BUY:
                    if current_price > best_price:
                        best_price = current_price
                        should_trail = True
                elif order.order_type == OrderType.SELL:
                    if current_price < best_price:
                        best_price = current_price
                        should_trail = True
                
                if should_trail:
                    # Calculate new SL
                    pip_distance = order.trailing_sl_distance_pips
                    if order.pair.endswith('JPY'):
                        pip_value = 0.01
                    else:
                        pip_value = 0.0001
                    
                    if order.order_type == OrderType.BUY:
                        new_sl = best_price - (pip_distance * pip_value)
                    else:
                        new_sl = best_price + (pip_distance * pip_value)
                    
                    # Update SL if it's better than current
                    if ((order.order_type == OrderType.BUY and new_sl > order.stop_loss) or
                        (order.order_type == OrderType.SELL and new_sl < order.stop_loss)):
                        
                        await self.mt5_bridge.modify_order(ticket, stop_loss=new_sl)
                        order.stop_loss = new_sl
                        
                        logger.info(f"Trailing stop updated for {order.id}: new SL {new_sl}")
                
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logger.error(f"Error in trailing stop monitoring: {e}")
    
    async def process_provider_command_advanced(self, command: str, provider_id: str, 
                                              signal_id: str = None) -> Dict[str, Any]:
        """Process advanced provider commands"""
        try:
            command = command.lower().strip()
            
            # Find relevant orders
            relevant_orders = []
            for order in self.active_orders.values():
                if order.provider_id == provider_id:
                    if signal_id is None or order.signal_id == signal_id:
                        relevant_orders.append(order)
            
            if not relevant_orders:
                return {"status": "error", "message": "No relevant orders found"}
            
            # Process command
            if "close" in command and "%" in command:
                percentage = self._extract_percentage(command)
                return await self._close_orders_percentage(relevant_orders, percentage)
            
            elif "close all" in command:
                return await self._close_all_orders(relevant_orders)
            
            elif "tp to" in command:
                new_tp = self._extract_price(command)
                return await self._modify_all_tp(relevant_orders, new_tp)
            
            elif "sl to" in command:
                new_sl = self._extract_price(command)
                return await self._modify_all_sl(relevant_orders, new_sl)
            
            elif "break even" in command or "be" in command:
                return await self._move_all_to_break_even(relevant_orders)
            
            elif "trailing" in command:
                return await self._enable_trailing_stops(relevant_orders)
            
            elif "cancel" in command:
                return await self._cancel_pending_orders(relevant_orders)
            
            return {"status": "error", "message": "Unknown command"}
            
        except Exception as e:
            logger.error(f"Error processing advanced provider command: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _close_orders_percentage(self, orders: List[AdvancedTradingOrder], percentage: float) -> Dict[str, Any]:
        """Close percentage of multiple orders"""
        results = []
        
        for order in orders:
            if order.status == OrderStatus.EXECUTED:
                close_lots = order.lot_size * (percentage / 100)
                result = await self._close_partial(order, percentage)
                results.append(result)
        
        return {"status": "success", "results": results, "orders_affected": len(results)}
    
    async def _place_primary_order(self, order: AdvancedTradingOrder) -> Dict[str, Any]:
        """Place the primary order"""
        if not self.mt5_bridge:
            # Simulation mode
            order.status = OrderStatus.EXECUTED
            order.executed_at = datetime.utcnow()
            order.mt5_ticket = 999999
            return {"status": "success", "ticket": order.mt5_ticket}
        
        # Real MT5 execution
        first_tp = order.tp_levels[0].price if order.tp_levels else None
        
        return await self.mt5_bridge.place_order(
            pair=order.pair,
            order_type=order.order_type.value,
            lot_size=order.lot_size,
            entry_price=order.entry_price,
            stop_loss=order.stop_loss,
            take_profits=[first_tp] if first_tp else []
        )
    
    async def _queue_for_smart_execution(self, order: AdvancedTradingOrder) -> Dict[str, Any]:
        """Queue order for smart execution when conditions are met"""
        self.pending_orders[order.id] = order
        
        # Start monitoring task
        asyncio.create_task(self._monitor_smart_execution(order))
        
        return {
            "status": "queued",
            "message": "Order queued for smart execution",
            "order_id": order.id
        }
    
    async def _monitor_smart_execution(self, order: AdvancedTradingOrder):
        """Monitor order for smart execution conditions"""
        try:
            max_wait_time = 300  # 5 minutes timeout
            start_time = datetime.utcnow()
            
            while (datetime.utcnow() - start_time).total_seconds() < max_wait_time:
                if await self._check_smart_entry_conditions(order):
                    # Conditions met, execute order
                    result = await self._execute_market_order(order)
                    
                    if result["status"] == "success":
                        # Remove from pending
                        self.pending_orders.pop(order.id, None)
                        logger.info(f"Smart execution completed for order {order.id}")
                        return
                
                await asyncio.sleep(1)  # Check every second
            
            # Timeout reached
            logger.warning(f"Smart execution timeout for order {order.id}")
            self.pending_orders.pop(order.id, None)
            
        except Exception as e:
            logger.error(f"Error in smart execution monitoring: {e}")
    
    def get_advanced_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get detailed order status"""
        order = self.active_orders.get(order_id) or self.pending_orders.get(order_id)
        if not order:
            return {"status": "not_found"}
        
        return {
            "status": "found",
            "order": {
                "id": order.id,
                "signal_id": order.signal_id,
                "pair": order.pair,
                "type": order.order_type.value,
                "lot_size": order.lot_size,
                "entry_price": order.entry_price,
                "stop_loss": order.stop_loss,
                "tp_levels": [
                    {
                        "level": tp.level,
                        "price": tp.price,
                        "lot_percentage": tp.lot_percentage,
                        "sl_move_on_hit": tp.sl_move_on_hit
                    }
                    for tp in order.tp_levels
                ],
                "trailing_sl_enabled": order.trailing_sl_enabled,
                "trailing_sl_distance": order.trailing_sl_distance_pips,
                "mt5_ticket": order.mt5_ticket,
                "status": order.status.value,
                "provider_id": order.provider_id,
                "created_at": order.created_at.isoformat(),
                "executed_at": order.executed_at.isoformat() if order.executed_at else None,
                "provider_commands": order.provider_commands
            }
        }