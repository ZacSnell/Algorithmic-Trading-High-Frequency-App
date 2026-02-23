# ml_trainer.py
from config import *
import glob
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.utils.parallel")

class MLTrainer:
    def __init__(self):
        self.scaler = StandardScaler()

    def get_training_data(self):
        csv_files = glob.glob("*_labeled.csv")
        if not csv_files:
            logger.warning("No training data found.")
            return None
        all_data = [pd.read_csv(f, index_col=0) for f in csv_files if not pd.read_csv(f, index_col=0).empty]
        if not all_data:
            return None
        combined = pd.concat(all_data, ignore_index=True).dropna()
        logger.info(f"Combined training data: {len(combined)} samples")
        return combined

    def train_random_forest(self, X_train, y_train):
        model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=1, class_weight='balanced')
        model.fit(X_train, y_train)
        return model

    def train_gradient_boosting(self, X_train, y_train):
        model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        return model

    def train_all_specialists(self):
        logger.info("🚀 Training ALL 7 specialist agents...")
        df = self.get_training_data()
        if df is None or len(df) < 100:
            logger.error("Not enough training data")
            return False
        from ml_specialist import Specialist
        from ml_ensemble import EnsembleCoordinator
        ensemble = EnsembleCoordinator()
        for name, spec in ensemble.specialists.items():
            if hasattr(spec, 'train'):
                spec.train(df)
        logger.info("✅ All specialists trained. Knowledge base updated.")
        return True

if __name__ == "__main__":
    trainer = MLTrainer()
    trainer.train_all_specialists()