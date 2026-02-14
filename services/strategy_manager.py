# strategy_manager.py
# Manages trading strategy selection and configuration
# Handles strategy switching, model loading, and parameters

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *


class StrategyManager:
    """
    Manages multiple trading strategies and handles switching between them.
    Each strategy has its own trained model, parameters, and configuration.
    """
    
    def __init__(self):
        self.active_strategy = ACTIVE_STRATEGY
        self.strategies = STRATEGIES
        self.current_params = self.get_strategy_params(self.active_strategy)
    
    def get_available_strategies(self):
        """Get all available strategies"""
        return {
            name: config for name, config in self.strategies.items()
            if config.get('enabled', True)
        }
    
    def get_all_strategies(self):
        """Get all strategies including disabled ones"""
        return self.strategies
    
    def get_strategy_params(self, strategy_name):
        """Get parameters for a specific strategy"""
        if strategy_name not in self.strategies:
            logger.warning(f"Strategy {strategy_name} not found, using default")
            return self.strategies[ACTIVE_STRATEGY]
        
        return self.strategies[strategy_name]
    
    def switch_strategy(self, strategy_name):
        """Switch to a different strategy"""
        if strategy_name not in self.strategies:
            logger.error(f"Strategy {strategy_name} does not exist")
            return False
        
        if not self.strategies[strategy_name].get('enabled', True):
            logger.error(f"Strategy {strategy_name} is disabled")
            return False
        
        self.active_strategy = strategy_name
        self.current_params = self.get_strategy_params(strategy_name)
        logger.info(f"Switched to strategy: {strategy_name} ({self.current_params['name']})")
        return True
    
    def get_active_strategy(self):
        """Get the currently active strategy name"""
        return self.active_strategy
    
    def get_active_strategy_config(self):
        """Get the currently active strategy configuration"""
        return self.current_params
    
    def get_model_path(self, strategy=None, model_type='random_forest'):
        """Get the model file path for a strategy"""
        if strategy is None:
            strategy = self.active_strategy
        
        # Pattern: model_{strategy}_{model_type}_*.pkl
        model_pattern = f"model_{strategy}_{model_type}_*.pkl"
        model_files = sorted(MODELS_DIR.glob(model_pattern), reverse=True)
        
        if model_files:
            return model_files[0]
        return None
    
    def get_scaler_path(self, strategy=None):
        """Get the scaler file path for a strategy"""
        if strategy is None:
            strategy = self.active_strategy
        
        model_path = self.get_model_path(strategy)
        if not model_path:
            return None
        
        # Extract timestamp from model filename
        timestamp = model_path.stem.split('_')[-1]
        scaler_path = MODELS_DIR / f"scaler_{strategy}_{timestamp}.pkl"
        
        if scaler_path.exists():
            return scaler_path
        return None
    
    def get_features_path(self, strategy=None):
        """Get the features file path for a strategy"""
        if strategy is None:
            strategy = self.active_strategy
        
        model_path = self.get_model_path(strategy)
        if not model_path:
            return None
        
        timestamp = model_path.stem.split('_')[-1]
        features_path = MODELS_DIR / f"features_{strategy}_{timestamp}.pkl"
        
        if features_path.exists():
            return features_path
        return None
    
    def get_strategy_description(self, strategy=None):
        """Get detailed description of a strategy"""
        if strategy is None:
            strategy = self.active_strategy
        
        params = self.get_strategy_params(strategy)
        
        return f"""
Strategy: {params['name']}
Description: {params['description']}

Configuration:
- Lookback Bars: {params['lookback_bars']}
- Minimum Confidence: {params['min_confidence']}
- Risk Per Trade: {params['risk_per_trade'] * 100}%
- Status: {'Enabled' if params.get('enabled', True) else 'Disabled'}
        """
    
    def validate_strategy_models(self):
        """Check if all strategies have trained models"""
        status = {}
        
        for strategy_name in self.strategies:
            model_path = self.get_model_path(strategy_name)
            scaler_path = self.get_scaler_path(strategy_name)
            features_path = self.get_features_path(strategy_name)
            
            status[strategy_name] = {
                'model': model_path is not None,
                'scaler': scaler_path is not None,
                'features': features_path is not None,
                'ready': all([model_path, scaler_path, features_path])
            }
        
        return status


# Global instance
strategy_manager = StrategyManager()
