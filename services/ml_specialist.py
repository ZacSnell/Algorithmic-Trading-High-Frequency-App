# services/ml_specialist.py
from config import *
import json
from datetime import datetime
import pandas as pd
import glob

class Specialist:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.load_latest_model()

    def load_latest_model(self):
        model_files = sorted(glob.glob(str(MODELS_DIR / f"specialist_{self.name}_*.pkl")), reverse=True)
        if model_files:
            self.model = joblib.load(model_files[0])
            scaler_file = model_files[0].replace("specialist_", "specialist_scaler_")
            features_file = model_files[0].replace("specialist_", "specialist_features_")
            self.scaler = joblib.load(scaler_file)
            self.feature_columns = joblib.load(features_file)
            logger.info(f"✅ Loaded latest model for {self.config['name']}")

    def train(self, df):
        logger.info(f"🔬 Training {self.config['name']}...")
        from ml_trainer import MLTrainer
        trainer = MLTrainer()
        feature_cols = [f for f in self.config['features'] if f in df.columns]
        X = df[feature_cols]
        y = df['Target']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TRAIN_TEST_SPLIT, random_state=42, stratify=y)
        trainer.scaler.fit(X_train)
        X_train_s = trainer.scaler.transform(X_train)
        if self.config['model_type'] == 'gradient_boosting':
            self.model = trainer.train_gradient_boosting(X_train_s, y_train)
        else:
            self.model = trainer.train_random_forest(X_train_s, y_train)
        self.scaler = trainer.scaler
        self.feature_columns = feature_cols
        self._update_knowledge(df, X_test, y_test)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        joblib.dump(self.model, MODELS_DIR / f"specialist_{self.name}_{timestamp}.pkl")
        joblib.dump(self.scaler, MODELS_DIR / f"specialist_scaler_{self.name}_{timestamp}.pkl")
        joblib.dump(self.feature_columns, MODELS_DIR / f"specialist_features_{self.name}_{timestamp}.pkl")

    def _update_knowledge(self, df, X_test, y_test):
        importances = pd.Series(self.model.feature_importances_, index=self.feature_columns).sort_values(ascending=False)
        entry = {
            "date": datetime.now(TIMEZONE).isoformat(),
            "specialist": self.name,
            "top_features": importances.head(5).to_dict(),
            "test_accuracy": (self.model.predict(self.scaler.transform(X_test)) == y_test).mean(),
            "insight": f"Strongest signal: {importances.index[0]}"
        }
        kb = json.load(open(KNOWLEDGE_BASE)) if KNOWLEDGE_BASE.exists() else []
        kb.append(entry)
        with open(KNOWLEDGE_BASE, 'w') as f:
            json.dump(kb[-1000:], f, indent=2)
        logger.info(f"📚 {self.config['name']} added insight")

    def predict(self, features_df):
        if self.model is None:
            return {"specialist": self.name, "signal": 0, "confidence": 0.0, "rationale": "Model not loaded"}
        X_df = features_df[self.feature_columns].iloc[-1:]
        X_s = self.scaler.transform(X_df)
        signal = self.model.predict(X_s)[0]
        proba = self.model.predict_proba(X_s)[0]
        conf = proba[1] if signal == 1 else proba[0]
        return {
            "specialist": self.name,
            "signal": int(signal),
            "confidence": float(conf),
            "rationale": f"{self.config['name']} {conf:.1%}"
        }