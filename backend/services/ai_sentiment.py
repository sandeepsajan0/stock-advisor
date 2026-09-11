from transformers import pipeline
import yfinance as yf

# Load the FinBERT model pipeline for sentiment analysis
print("Loading FinBERT AI Model... This may take a moment.")
try:
    sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    print("FinBERT loaded successfully.")
except Exception as e:
    print(f"Error loading FinBERT: {e}")
    sentiment_pipeline = None

def get_stock_sentiment(ticker: str) -> dict:
    """
    Fetches recent news for the ticker and uses FinBERT to determine the sentiment.
    Returns a dictionary with the overall sentiment (Bullish, Bearish, Neutral)
    """
    if sentiment_pipeline is None:
        return {"score": 0, "label": "Neutral", "reason": "AI model not loaded"}

    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news
        
        if not news_items:
            return {"score": 0, "label": "Neutral", "reason": "No recent news found."}

        # Extract headlines
        headlines = [item['title'] for item in news_items[:5] if 'title' in item]
        
        if not headlines:
             return {"score": 0, "label": "Neutral", "reason": "No recent news headlines found."}

        # Analyze sentiment for each headline
        results = sentiment_pipeline(headlines)
        
        # Calculate overall score
        score = 0
        for res in results:
            if res['label'] == 'positive':
                score += 1
            elif res['label'] == 'negative':
                score -= 1
                
        # Determine overall label
        if score > 0:
            label = "Bullish"
        elif score < 0:
            label = "Bearish"
        else:
            label = "Neutral"
            
        return {
            "score": score,
            "label": label,
            "reason": f"Analyzed {len(headlines)} headlines."
        }
    except Exception as e:
        print(f"Error analyzing sentiment for {ticker}: {e}")
        return {"score": 0, "label": "Neutral", "reason": "Error fetching news."}
