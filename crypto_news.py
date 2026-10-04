import feedparser
import requests
from datetime import datetime, timezone, timedelta
import os

FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.theblock.co/rss.xml",
    "https://bitcoinmagazine.com/feed",
]

KEYWORDS = ["bitcoin", "ethereum", "crypto", "etf", "sec", "regulation", "stablecoin"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def is_recent(entry, hours=24):
    if not hasattr(entry, "published_parsed") or not entry.published_parsed:
        return True
    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - published < timedelta(hours=hours)

def relevant(text):
    t = (text or "").lower()
    return any(k in t for k in KEYWORDS)

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": text[:4000], "disable_web_page_preview": True},
        timeout=20,
    )

def main():
    items = []
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        source = feed.feed.get("title", feed_url)
        for e in feed.entries[:15]:
            title = e.get("title", "")
            summary = e.get("summary", "")
            link = e.get("link", "")
            if is_recent(e) and relevant(title + " " + summary):
                items.append(f"• {title}\n{source}\n{link}")
    if not items:
        send("Không có tin crypto mới phù hợp trong 24h.")
        return
    chunk = "Crypto news hôm nay:\n\n" + "\n\n".join(items[:12])
    send(chunk)

if __name__ == "__main__":
    main()
