import json
import time
import datetime
import pandas as pd
from ntscraper import Nitter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os

class TwitterSentimentAgent:
    def __init__(self, watchlist=None):
        self.watchlist = watchlist or ["AAPL", "TSLA", "NVDA", "AMD", "META"]  # edit in config.py later
        self.scraper = Nitter(log_level=1, skip_instance_check=False)
        self.analyzer = SentimentIntensityAnalyzer()
        self.kb_path = "knowledge_base.json"
        self._load_knowledge_base()
        self.avg_volume = {ticker: 5.0 for ticker in self.watchlist}  # rolling average tweets/hour

    def _load_knowledge_base(self):
        if os.path.exists(self.kb_path):
            with open(self.kb_path, 'r') as f:
                self.kb = json.load(f)
        else:
            self.kb = {"insights": [], "hot_mentions": []}

    def _save_knowledge_base(self):
        with open(self.kb_path, 'w') as f:
            json.dump(self.kb, f, indent=2)

    def _fetch_recent_tweets(self, ticker, minutes=15):
        try:
            since = (datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%d")
            tweets = self.scraper.get_tweets(f"${ticker} OR {ticker}", mode='search', since=since, max_results=50)
            return tweets.get('tweets', []) if tweets else []
        except:
            return []

    def get_vote(self, ticker):
        tweets = self._fetch_recent_tweets(ticker, minutes=15)
        if len(tweets) < 3:
            return "HOLD", 30, "Low tweet volume"

        df = pd.DataFrame([{
            'text': t['text'],
            'likes': t.get('stats', {}).get('likes', 0),
            'retweets': t.get('stats', {}).get('retweets', 0)
        } for t in tweets])

        volume = len(df)
        velocity = volume / (15 / 60.0)  # tweets per hour
        self.avg_volume[ticker] = (self.avg_volume.get(ticker, 5) * 0.7 + velocity * 0.3)

        # Sentiment
        sentiments = [self.analyzer.polarity_scores(t['text'])['compound'] for t in df['text']]
        avg_sent = sum(sentiments) / len(sentiments)

        # Urgency boost
        urgency_kw = ['moon', 'surge', 'pump', 'breakout', 'beat', 'approval', 'fda', 'acquisition', 'partnership', 'exploding']
        urgency = sum(any(kw in text.lower() for kw in urgency_kw) for text in df['text']) / volume

        # Catalyst score (0-1)
        catalyst_score = (
                max(avg_sent, 0) * 0.5 +
                min(velocity / max(self.avg_volume[ticker], 10), 2.0) * 0.3 +
                urgency * 0.2
        )
        catalyst_score = max(0.0, min(1.0, catalyst_score))

        confidence = int(catalyst_score * 100)

        if catalyst_score > 0.65 and volume > 10:
            vote = "BUY"
            reason = f"HOT CATALYST: {volume} tweets, {avg_sent:.2f} sentiment, {urgency:.0%} urgency"
            self.kb["hot_mentions"].append({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "ticker": ticker,
                "score": catalyst_score,
                "reason": reason
            })
            if len(self.kb["hot_mentions"]) > 50:
                self.kb["hot_mentions"] = self.kb["hot_mentions"][-50:]
            self._save_knowledge_base()
            return vote, confidence, reason

        return "HOLD", confidence, f"Neutral ({catalyst_score:.2f} catalyst score)"

# Test it live
if __name__ == "__main__":
    agent = TwitterSentimentAgent()
    for ticker in agent.watchlist:
        vote, conf, reason = agent.get_vote(ticker)
        print(f"{ticker}: {vote} ({conf}%) → {reason}")