# services/twitter_sentiment_agent.py - IMPROVED VERSION
from config import *
import requests
from textblob import TextBlob
import json
from datetime import datetime

class TwitterSentimentAgent:
    def __init__(self):
        self.name = "twitter_sentiment"

    def _search_tweets(self, query, count=25):
        try:
            url = f"https://nitter.poast.org/search?f=tweets&q={query}&since=&until=&near="
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                return []
            titles = []
            for line in r.text.splitlines():
                if "<title>" in line and "</title>" in line:
                    title = line.split("<title>")[1].split("</title>")[0].strip()
                    if len(title) > 15:
                        titles.append(title)
            return titles[:count]
        except:
            return []

    def predict(self, symbols=None):
        if not symbols:
            symbols = ["SPY", "NVDA", "TSLA"]
        total_bias = 0.0
        catalyst_score = 0.0
        stock_signals = {}

        for sym in symbols[:5]:
            tweets = self._search_tweets(sym, count=25)
            if not tweets:
                stock_signals[sym] = 0.0
                continue
            sentiments = [TextBlob(t).sentiment.polarity for t in tweets]
            bias = sum(sentiments) / len(sentiments) if sentiments else 0
            cat = sum(1 for t in tweets if any(k in t.lower() for k in ["earnings", "fda", "beat", "guidance", "squeeze", "merger", "short"])) / len(tweets)
            stock_signals[sym] = bias + cat * 0.6
            total_bias += bias
            catalyst_score += cat

        overall_bias = total_bias / len(symbols[:5]) if symbols else 0
        catalyst_score /= len(symbols[:5]) if symbols else 1
        final_signal = 1 if overall_bias > 0.18 or catalyst_score > 0.45 else 0
        confidence = min(0.95, 0.5 + abs(overall_bias) * 1.3 + catalyst_score * 1.8)

        entry = {
            "date": datetime.now(TIMEZONE).isoformat(),
            "specialist": "twitter_sentiment",
            "bias": overall_bias,
            "catalyst_score": catalyst_score
        }
        kb = json.load(open(KNOWLEDGE_BASE)) if KNOWLEDGE_BASE.exists() else []
        kb.append(entry)
        with open(KNOWLEDGE_BASE, 'w') as f:
            json.dump(kb[-1000:], f, indent=2)

        logger.info(f"🐦 Twitter Agent → Bias: {overall_bias:.2f} | Catalysts: {catalyst_score:.2f} | Confidence: {confidence:.1%}")
        return {
            "specialist": "twitter_sentiment",
            "signal": final_signal,
            "confidence": float(confidence),
            "rationale": f"Twitter bias {overall_bias:.2f} | Hot catalysts {catalyst_score:.2f}"
        }