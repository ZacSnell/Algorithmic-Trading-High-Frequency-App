# services/ml_ensemble.py - DYNAMIC WITH LOWER THRESHOLD
from config import *
from ml_specialist import Specialist
from news_agent import NewsCatalystAgent
from twitter_sentiment_agent import TwitterSentimentAgent

class EnsembleCoordinator:
    def __init__(self):
        self.specialists = {}
        self.news_agent = NewsCatalystAgent()
        self.twitter_agent = TwitterSentimentAgent()
        self.load_all()

    def load_all(self):
        for name, cfg in SPECIALISTS.items():
            if cfg['type'] == 'ml':
                self.specialists[name] = Specialist(name, cfg)
            elif cfg['type'] == 'news':
                self.specialists[name] = self.news_agent
            elif cfg['type'] == 'twitter':
                self.specialists[name] = self.twitter_agent

    def predict(self, features_df, symbol=None):
        votes = []
        print("\n--- INDIVIDUAL VOTES ---")  # Show live votes in console
        for name, agent in self.specialists.items():
            if isinstance(agent, Specialist):
                pred = agent.predict(features_df)
            elif name == 'news_catalyst':
                pred = self.news_agent.predict([symbol])
            else:
                pred = self.twitter_agent.predict([symbol])
            votes.append((pred['signal'], pred['confidence'], pred['rationale']))
            print(f"  {name:15} → Signal: {pred['signal']} | Conf: {pred['confidence']:.1%} | {pred['rationale']}")

        buy_conf = sum(w for s, w, r in votes if s == 1)
        total = sum(w for _, w, _ in votes)
        final_signal = 1 if buy_conf > total * 0.25 else 0   # LOWERED for dynamic testing
        final_conf = buy_conf / total if total > 0 else 0

        logger.info(f"🤖 ENSEMBLE → {'BUY' if final_signal else 'HOLD'} ({final_conf:.1%}) | {len([v for v,_,_ in votes if v==1])}/7 specialists agree")
        return {"signal": final_signal, "confidence": final_conf, "recommendation": "BUY" if final_signal and final_conf >= MIN_CONFIDENCE else "HOLD"}