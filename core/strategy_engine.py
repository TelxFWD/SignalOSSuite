"""
SignalOS Strategy Engine
Advanced strategy management with rules and automation
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    CONSERVATIVE = "CONSERVATIVE"
    AGGRESSIVE = "AGGRESSIVE"
    SCALPING = "SCALPING"
    SWING = "SWING"
    GRID = "GRID"
    MARTINGALE = "MARTINGALE"
    CUSTOM = "CUSTOM"

class ActionType(Enum):
    MODIFY_LOT_SIZE = "MODIFY_LOT_SIZE"
    MODIFY_SL = "MODIFY_SL"
    MODIFY_TP = "MODIFY_TP"
    ADD_TP_LEVEL = "ADD_TP_LEVEL"
    BREAK_EVEN = "BREAK_EVEN"
    TRAIL_SL = "TRAIL_SL"
    REVERSE_SIGNAL = "REVERSE_SIGNAL"
    BLOCK_PAIR = "BLOCK_PAIR"
    BLOCK_PROVIDER = "BLOCK_PROVIDER"

@dataclass
class StrategyRule:
    rule_id: str
    name: str
    condition: str  # JSON condition
    action: ActionType
    parameters: Dict[str, Any]
    priority: int = 100
    active: bool = True

@dataclass
class TradingStrategy:
    strategy_id: str
    name: str
    strategy_type: StrategyType
    description: str
    active: bool = True
    rules: List[StrategyRule] = None
    provider_assignments: List[str] = None  # Provider IDs
    pair_assignments: List[str] = None  # Currency pairs
    risk_settings: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.rules is None:
            self.rules = []
        if self.provider_assignments is None:
            self.provider_assignments = []
        if self.pair_assignments is None:
            self.pair_assignments = []
        if self.risk_settings is None:
            self.risk_settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class StrategyEngine:
    """Strategy management and rule execution engine"""
    
    def __init__(self):
        self.strategies: Dict[str, TradingStrategy] = {}
        self.strategy_templates = self._initialize_templates()
        self.execution_history: List[Dict[str, Any]] = []
        
    def create_strategy(self, strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new trading strategy"""
        try:
            strategy = TradingStrategy(
                strategy_id=strategy_config['strategy_id'],
                name=strategy_config['name'],
                strategy_type=StrategyType(strategy_config['strategy_type']),
                description=strategy_config.get('description', ''),
                active=strategy_config.get('active', True),
                provider_assignments=strategy_config.get('provider_assignments', []),
                pair_assignments=strategy_config.get('pair_assignments', []),
                risk_settings=strategy_config.get('risk_settings', {})
            )
            
            # Add default rules based on strategy type
            default_rules = self._get_default_rules(strategy.strategy_type)
            strategy.rules = default_rules
            
            self.strategies[strategy.strategy_id] = strategy
            
            logger.info(f"Strategy created: {strategy.name} ({strategy.strategy_type.value})")
            
            return {
                "status": "success",
                "message": "Strategy created successfully",
                "strategy_id": strategy.strategy_id
            }
            
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return {"status": "error", "message": str(e)}
    
    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing strategy"""
        try:
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                return {"status": "error", "message": "Strategy not found"}
            
            # Update fields
            for field, value in updates.items():
                if hasattr(strategy, field):
                    setattr(strategy, field, value)
            
            strategy.updated_at = datetime.utcnow()
            
            return {
                "status": "success",
                "message": "Strategy updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating strategy: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Delete strategy"""
        try:
            if strategy_id in self.strategies:
                del self.strategies[strategy_id]
                return {
                    "status": "success",
                    "message": "Strategy deleted successfully"
                }
            else:
                return {"status": "error", "message": "Strategy not found"}
                
        except Exception as e:
            logger.error(f"Error deleting strategy: {e}")
            return {"status": "error", "message": str(e)}
    
    def apply_strategy_to_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply strategy rules to incoming signal"""
        try:
            provider_id = signal_data.get('provider_id')
            pair = signal_data.get('pair')
            
            # Find applicable strategies
            applicable_strategies = self._find_applicable_strategies(provider_id, pair)
            
            # Apply rules from all applicable strategies
            modified_signal = signal_data.copy()
            applied_rules = []
            
            for strategy in applicable_strategies:
                for rule in strategy.rules:
                    if rule.active and self._evaluate_rule_condition(rule, signal_data):
                        modified_signal = self._apply_rule_action(rule, modified_signal)
                        applied_rules.append({
                            'strategy_id': strategy.strategy_id,
                            'rule_id': rule.rule_id,
                            'action': rule.action.value
                        })
            
            # Log execution
            self._log_strategy_execution(signal_data, applied_rules, modified_signal)
            
            return {
                "status": "success",
                "original_signal": signal_data,
                "modified_signal": modified_signal,
                "applied_rules": applied_rules
            }
            
        except Exception as e:
            logger.error(f"Error applying strategy: {e}")
            return {"status": "error", "message": str(e)}
    
    def _find_applicable_strategies(self, provider_id: str, pair: str) -> List[TradingStrategy]:
        """Find strategies applicable to provider/pair combination"""
        applicable = []
        
        for strategy in self.strategies.values():
            if not strategy.active:
                continue
            
            # Check provider assignment
            provider_match = (not strategy.provider_assignments or 
                            provider_id in strategy.provider_assignments)
            
            # Check pair assignment
            pair_match = (not strategy.pair_assignments or 
                         pair in strategy.pair_assignments)
            
            if provider_match and pair_match:
                applicable.append(strategy)
        
        # Sort by priority (if implemented)
        return applicable
    
    def _evaluate_rule_condition(self, rule: StrategyRule, signal_data: Dict[str, Any]) -> bool:
        """Evaluate if rule condition is met"""
        try:
            condition = json.loads(rule.condition)
            
            # Simple condition evaluation
            if condition.get('type') == 'always':
                return True
            
            elif condition.get('type') == 'pair_equals':
                return signal_data.get('pair') == condition.get('value')
            
            elif condition.get('type') == 'action_equals':
                return signal_data.get('action') == condition.get('value')
            
            elif condition.get('type') == 'sl_distance_greater':
                entry = signal_data.get('entry', 0)
                sl = signal_data.get('sl', 0)
                if entry and sl:
                    distance = abs(entry - sl)
                    return distance > condition.get('value', 0)
            
            elif condition.get('type') == 'time_range':
                current_hour = datetime.utcnow().hour
                start_hour = condition.get('start_hour', 0)
                end_hour = condition.get('end_hour', 23)
                return start_hour <= current_hour <= end_hour
            
            elif condition.get('type') == 'risk_percent_less':
                risk = signal_data.get('risk_percent', 0)
                return risk < condition.get('value', 100)
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule condition: {e}")
            return False
    
    def _apply_rule_action(self, rule: StrategyRule, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rule action to signal data"""
        try:
            modified_signal = signal_data.copy()
            
            if rule.action == ActionType.MODIFY_LOT_SIZE:
                multiplier = rule.parameters.get('multiplier', 1.0)
                original_lot = modified_signal.get('lot_size', 0.01)
                modified_signal['lot_size'] = original_lot * multiplier
            
            elif rule.action == ActionType.MODIFY_SL:
                sl_adjustment = rule.parameters.get('adjustment_pips', 0)
                original_sl = modified_signal.get('sl', 0)
                if original_sl:
                    pair = modified_signal.get('pair', 'EURUSD')
                    pip_value = 0.0001 if not pair.endswith('JPY') else 0.01
                    modified_signal['sl'] = original_sl + (sl_adjustment * pip_value)
            
            elif rule.action == ActionType.MODIFY_TP:
                tp_adjustment = rule.parameters.get('adjustment_pips', 0)
                original_tp = modified_signal.get('tp')
                if original_tp:
                    pair = modified_signal.get('pair', 'EURUSD')
                    pip_value = 0.0001 if not pair.endswith('JPY') else 0.01
                    modified_signal['tp'] = original_tp + (tp_adjustment * pip_value)
            
            elif rule.action == ActionType.ADD_TP_LEVEL:
                additional_tp = rule.parameters.get('tp_price')
                if additional_tp:
                    tps = modified_signal.get('take_profits', [])
                    if isinstance(tps, list):
                        tps.append(additional_tp)
                    else:
                        tps = [tps, additional_tp] if tps else [additional_tp]
                    modified_signal['take_profits'] = tps
            
            elif rule.action == ActionType.REVERSE_SIGNAL:
                if modified_signal.get('action') == 'BUY':
                    modified_signal['action'] = 'SELL'
                elif modified_signal.get('action') == 'SELL':
                    modified_signal['action'] = 'BUY'
            
            elif rule.action == ActionType.BLOCK_PAIR:
                blocked_pairs = rule.parameters.get('pairs', [])
                if modified_signal.get('pair') in blocked_pairs:
                    modified_signal['blocked'] = True
                    modified_signal['block_reason'] = 'Pair blocked by strategy'
            
            elif rule.action == ActionType.BLOCK_PROVIDER:
                blocked_providers = rule.parameters.get('providers', [])
                if modified_signal.get('provider_id') in blocked_providers:
                    modified_signal['blocked'] = True
                    modified_signal['block_reason'] = 'Provider blocked by strategy'
            
            return modified_signal
            
        except Exception as e:
            logger.error(f"Error applying rule action: {e}")
            return signal_data
    
    def _get_default_rules(self, strategy_type: StrategyType) -> List[StrategyRule]:
        """Get default rules for strategy type"""
        rules = []
        
        if strategy_type == StrategyType.CONSERVATIVE:
            rules = [
                StrategyRule(
                    rule_id="conservative_lot_limit",
                    name="Limit Lot Size",
                    condition='{"type": "always"}',
                    action=ActionType.MODIFY_LOT_SIZE,
                    parameters={"multiplier": 0.5}
                ),
                StrategyRule(
                    rule_id="conservative_tight_sl",
                    name="Tighter Stop Loss",
                    condition='{"type": "sl_distance_greater", "value": 0.005}',
                    action=ActionType.MODIFY_SL,
                    parameters={"adjustment_pips": -10}
                )
            ]
        
        elif strategy_type == StrategyType.AGGRESSIVE:
            rules = [
                StrategyRule(
                    rule_id="aggressive_lot_boost",
                    name="Increase Lot Size",
                    condition='{"type": "always"}',
                    action=ActionType.MODIFY_LOT_SIZE,
                    parameters={"multiplier": 2.0}
                ),
                StrategyRule(
                    rule_id="aggressive_wider_sl",
                    name="Wider Stop Loss",
                    condition='{"type": "always"}',
                    action=ActionType.MODIFY_SL,
                    parameters={"adjustment_pips": 15}
                )
            ]
        
        elif strategy_type == StrategyType.SCALPING:
            rules = [
                StrategyRule(
                    rule_id="scalping_quick_tp",
                    name="Quick Take Profit",
                    condition='{"type": "always"}',
                    action=ActionType.MODIFY_TP,
                    parameters={"adjustment_pips": -5}
                ),
                StrategyRule(
                    rule_id="scalping_time_limit",
                    name="Time Restriction",
                    condition='{"type": "time_range", "start_hour": 8, "end_hour": 18}',
                    action=ActionType.MODIFY_LOT_SIZE,
                    parameters={"multiplier": 1.0}
                )
            ]
        
        elif strategy_type == StrategyType.GRID:
            rules = [
                StrategyRule(
                    rule_id="grid_multiple_entries",
                    name="Multiple Entry Levels",
                    condition='{"type": "always"}',
                    action=ActionType.ADD_TP_LEVEL,
                    parameters={"tp_price": 0}  # Would be calculated dynamically
                )
            ]
        
        return rules
    
    def add_rule_to_strategy(self, strategy_id: str, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add rule to existing strategy"""
        try:
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                return {"status": "error", "message": "Strategy not found"}
            
            rule = StrategyRule(
                rule_id=rule_config['rule_id'],
                name=rule_config['name'],
                condition=rule_config['condition'],
                action=ActionType(rule_config['action']),
                parameters=rule_config.get('parameters', {}),
                priority=rule_config.get('priority', 100),
                active=rule_config.get('active', True)
            )
            
            strategy.rules.append(rule)
            strategy.updated_at = datetime.utcnow()
            
            return {
                "status": "success",
                "message": "Rule added successfully",
                "rule_id": rule.rule_id
            }
            
        except Exception as e:
            logger.error(f"Error adding rule: {e}")
            return {"status": "error", "message": str(e)}
    
    def remove_rule_from_strategy(self, strategy_id: str, rule_id: str) -> Dict[str, Any]:
        """Remove rule from strategy"""
        try:
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                return {"status": "error", "message": "Strategy not found"}
            
            strategy.rules = [r for r in strategy.rules if r.rule_id != rule_id]
            strategy.updated_at = datetime.utcnow()
            
            return {
                "status": "success",
                "message": "Rule removed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error removing rule: {e}")
            return {"status": "error", "message": str(e)}
    
    def _log_strategy_execution(self, original_signal: Dict[str, Any], 
                               applied_rules: List[Dict[str, Any]], 
                               modified_signal: Dict[str, Any]):
        """Log strategy execution for analysis"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'signal_id': original_signal.get('id'),
            'provider_id': original_signal.get('provider_id'),
            'pair': original_signal.get('pair'),
            'applied_rules_count': len(applied_rules),
            'applied_rules': applied_rules,
            'modifications': self._calculate_modifications(original_signal, modified_signal)
        }
        
        self.execution_history.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def _calculate_modifications(self, original: Dict[str, Any], modified: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate what was modified in the signal"""
        modifications = {}
        
        for key in ['lot_size', 'sl', 'tp', 'action', 'entry']:
            if key in original and key in modified:
                if original[key] != modified[key]:
                    modifications[key] = {
                        'from': original[key],
                        'to': modified[key]
                    }
        
        return modifications
    
    def get_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        try:
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                return {"status": "error", "message": "Strategy not found"}
            
            # Calculate performance from execution history
            executions = [e for e in self.execution_history 
                         if any(r['strategy_id'] == strategy_id for r in e['applied_rules'])]
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "total_executions": len(executions),
                "last_execution": executions[-1]['timestamp'] if executions else None,
                "rules_triggered": len(strategy.rules),
                "active_rules": len([r for r in strategy.rules if r.active]),
                "performance_period": "last_30_days"  # Would implement actual calculation
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get all strategies"""
        return [
            {
                "strategy_id": s.strategy_id,
                "name": s.name,
                "strategy_type": s.strategy_type.value,
                "description": s.description,
                "active": s.active,
                "rules_count": len(s.rules),
                "provider_assignments": s.provider_assignments,
                "pair_assignments": s.pair_assignments,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat()
            }
            for s in self.strategies.values()
        ]
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategy templates"""
        return {
            "conservative_forex": {
                "name": "Conservative Forex",
                "strategy_type": "CONSERVATIVE",
                "description": "Low-risk strategy with tight risk management",
                "default_rules": ["conservative_lot_limit", "conservative_tight_sl"]
            },
            "aggressive_scalper": {
                "name": "Aggressive Scalper",
                "strategy_type": "SCALPING",
                "description": "High-frequency trading with quick profits",
                "default_rules": ["scalping_quick_tp", "scalping_time_limit"]
            },
            "swing_trader": {
                "name": "Swing Trader",
                "strategy_type": "SWING",
                "description": "Medium-term positions with wider targets",
                "default_rules": []
            }
        }