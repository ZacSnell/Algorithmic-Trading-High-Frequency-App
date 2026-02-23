# services/news_agent.py
from config import *
import feedparser
import yfinance as yf
from textblob import TextBlob
import json
from datetime import datetime

class NewsCatalystAgent:
    def __init__(self):
        pass

    def fetch_market_news(self):
        feeds = ["https://www.cnbc.com/id/100003114/device/rss/rss.html", "https://feeds.reuters.com/reuters/businessNews"]
        news = []
        for url in feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:
                    title = entry.title
                    sentiment = TextBlob(title).sentiment.polarity
                    news.append({"title": title, "sentiment": sentiment})
            except:
                pass
        return news

    def predict(self, symbols=None):
        market_news = self.fetch_market_news()
        overall_bias = sum(n['sentiment'] for n in market_news) / len(market_news) if market_news else 0
        catalyst_score = 0.0
        final_signal = 1 if overall_bias > 0.05 else 0
        confidence = min(0.92, 0.45 + abs(overall_bias))
        return {
            "specialist": "news_catalyst",
            "signal": final_signal,
            "confidence": float(confidence),
            "rationale": f"News bias {overall_bias:.2f} | Catalysts {catalyst_score:.2f}"
        }