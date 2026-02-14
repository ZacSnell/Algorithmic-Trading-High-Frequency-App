# ml_trainer.py
# Trains machine learning models on historical data
# Runs when market is closed

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
import glob
from datetime import datetime
import pickle

class MLTrainer:
    """
    Trains and evaluates machine learning models.
    Stores trained models for real-time predictions.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None
        self.feature_columns = None
        self.train_date = None
        
    def get_training_data(self, strategy='macd_crossover'):
        """Load and combine all available CSV files for a specific strategy"""
        # Look for strategy-specific CSV files
        csv_files = glob.glob(f"*_{strategy}_labeled.csv")
        
        if not csv_files:
            # Fall back to general labeled files
            csv_files = glob.glob("*_labeled.csv")
            csv_files = [f for f in csv_files if "combined" not in f]
        
        if not csv_files:
            logger.warning(f"No training data found for strategy: {strategy}. Run build_dataset.py first!")
            return None
        
        logger.info(f"Loading {len(csv_files)} training files for {strategy}")
        all_data = []
        
        for file in csv_files:
            try:
                df = pd.read_csv(file, index_col=0)
                if df.empty or 'Target' not in df.columns:
                    logger.warning(f"Skipping {file} - no Target column")
                    continue
                all_data.append(df)
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")
        
        if not all_data:
            logger.error("No valid training data loaded")
            return None
        
        combined = pd.concat(all_data, ignore_index=True)
        combined = combined.dropna()
        
        logger.info(f"Combined training data: {len(combined)} samples")
        return combined
    
    def prepare_features(self, df):
        """Select and prepare features for model"""
        # Features we engineered in build_dataset.py
        feature_cols = [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'VWAP', 'MACD', 'MACD_Signal', 'MACD_Hist',
            'VWAP_Deviation', 'Typical_Price'
        ]
        
        # Keep only features that exist
        available_features = [col for col in feature_cols if col in df.columns]
        self.feature_columns = available_features
        
        logger.info(f"Using {len(available_features)} features")
        return df[available_features], df['Target']
    
    def train_random_forest(self, X_train, y_train):
        """Train RandomForest model"""
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        logger.info("Training RandomForest...")
        model.fit(X_train, y_train)
        
        # Print feature importances
        importances = pd.Series(
            model.feature_importances_,
            index=self.feature_columns
        ).sort_values(ascending=False)
        
        logger.info("Feature Importances:")
        for feat, importance in importances.items():
            logger.info(f"  {feat}: {importance:.4f}")
        
        return model
    
    def train_gradient_boosting(self, X_train, y_train):
        """Train GradientBoosting model"""
        model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=5,
            subsample=0.8,
            random_state=42,
            verbose=1
        )
        
        logger.info("Training GradientBoosting...")
        model.fit(X_train, y_train)
        
        importances = pd.Series(
            model.feature_importances_,
            index=self.feature_columns
        ).sort_values(ascending=False)
        
        logger.info("Feature Importances:")
        for feat, importance in importances.items():
            logger.info(f"  {feat}: {importance:.4f}")
        
        return model
    
    def evaluate_model(self, model, X_train, X_test, y_train, y_test):
        """Evaluate model performance"""
        logger.info("\n" + "="*60)
        logger.info("MODEL EVALUATION")
        logger.info("="*60)
        
        # Training score
        train_pred = model.predict(X_train)
        train_acc = (train_pred == y_train).mean()
        logger.info(f"Training Accuracy: {train_acc:.4f}")
        
        # Test score
        test_pred = model.predict(X_test)
        test_acc = (test_pred == y_test).mean()
        logger.info(f"Test Accuracy: {test_acc:.4f}")
        
        # Detailed metrics
        logger.info("\nClassification Report (Test Set):")
        logger.info(classification_report(y_test, test_pred))
        
        # Probability predictions for ROC AUC
        try:
            test_proba = model.predict_proba(X_test)[:, 1]
            auc_score = roc_auc_score(y_test, test_proba)
            logger.info(f"ROC AUC Score: {auc_score:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate ROC AUC: {e}")
        
        # Precision and Recall
        precision = precision_score(y_test, test_pred, zero_division=0)
        recall = recall_score(y_test, test_pred, zero_division=0)
        logger.info(f"Precision: {precision:.4f} | Recall: {recall:.4f}")
        
        # Class distribution
        logger.info(f"\nClass Distribution (Test):")
        logger.info(f"  Buy signals (1): {(y_test == 1).sum()}")
        logger.info(f"  No signal (0): {(y_test == 0).sum()}")
        
        return {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'precision': precision,
            'recall': recall
        }
    
    def save_model(self, model, model_type, strategy='macd_crossover'):
        """Save trained model and scaler to disk with strategy name"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_path = MODELS_DIR / f"model_{strategy}_{model_type}_{timestamp}.pkl"
        scaler_path = MODELS_DIR / f"scaler_{strategy}_{timestamp}.pkl"
        features_path = MODELS_DIR / f"features_{strategy}_{timestamp}.pkl"
        
        try:
            joblib.dump(model, model_path)
            joblib.dump(self.scaler, scaler_path)
            joblib.dump(self.feature_columns, features_path)
            
            logger.info(f"\nModel saved to {model_path}")
            logger.info(f"Scaler saved to {scaler_path}")
            logger.info(f"Features saved to {features_path}")
            
            return model_path
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return None
    
    def load_latest_model(self, model_type):
        """Load the most recent trained model"""
        model_files = sorted(MODELS_DIR.glob(f"model_{model_type}_*.pkl"), reverse=True)
        
        if not model_files:
            logger.warning(f"No saved models found for {model_type}")
            return None, None, None
        
        try:
            latest_model = model_files[0]
            model = joblib.load(latest_model)
            
            # Load corresponding scaler and features
            timestamp = latest_model.stem.split('_')[-1]
            scaler = joblib.load(MODELS_DIR / f"scaler_{timestamp}.pkl")
            features = joblib.load(MODELS_DIR / f"features_{timestamp}.pkl")
            
            logger.info(f"Loaded model: {latest_model}")
            return model, scaler, features
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None, None, None
    
    def train(self, strategy='macd_crossover'):
        """Main training pipeline for a specific strategy"""
        logger.info("\n" + "="*60)
        logger.info(f"STARTING MODEL TRAINING: {strategy}")
        logger.info("="*60)
        
        # Load strategy-specific data
        df = self.get_training_data(strategy=strategy)
        if df is None or len(df) < MIN_TRAINING_SAMPLES:
            logger.error(f"Insufficient training data (need {MIN_TRAINING_SAMPLES}, got {len(df) if df is not None else 0})")
            return False
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        logger.info(f"Data shape: {X.shape}")
        logger.info(f"Buy signals: {(y == 1).sum()} | No signal: {(y == 0).sum()}")
        logger.info(f"Buy signal ratio: {(y == 1).sum() / len(y) * 100:.2f}%")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=TRAIN_TEST_SPLIT,
            random_state=42,
            stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if ML_MODEL_TYPE == "gradient_boosting":
            model = self.train_gradient_boosting(X_train_scaled, y_train)
        else:
            model = self.train_random_forest(X_train_scaled, y_train)
        
        self.model = model
        self.train_date = datetime.now()
        
        # Evaluate
        self.evaluate_model(model, X_train_scaled, X_test_scaled, y_train, y_test)
        
        # Save with strategy name
        self.save_model(model, model_type=ML_MODEL_TYPE, strategy=strategy)
        
        logger.info("\n" + "="*60)
        logger.info(f"TRAINING COMPLETE FOR {strategy}")
        logger.info("="*60)
        
        return True


if __name__ == "__main__":
    trainer = MLTrainer()
    
    # Train models for all strategies
    strategies = ['macd_crossover', 'scalping']  # Add more as implemented
    
    logger.info("\n" + "="*60)
    logger.info("STARTING MULTI-STRATEGY MODEL TRAINING")
    logger.info("="*60 + "\n")
    
    results = {}
    for strategy in strategies:
        logger.info(f"Training model for: {strategy}")
        success = trainer.train(strategy=strategy)
        results[strategy] = 'SUCCESS' if success else 'FAILED'
    
    logger.info("\n" + "="*60)
    logger.info("TRAINING SUMMARY")
    logger.info("="*60)
    for strategy, status in results.items():
        logger.info(f"  {strategy}: {status}")
    logger.info("="*60)
    
    if success:
        logger.info("\n✓ Model training succeeded!")
    else:
        logger.error("\n✗ Model training failed!")
        sys.exit(1)
