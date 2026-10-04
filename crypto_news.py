import os
import re
import json
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from pathlib import Path

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = Path("seen.json")
MAX_AGE_MIN = 20
SUMMARY_WORDS = 100

FEEDS = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
    "The Block": "https://www.theblock.co/rss.xml",
    "Bitcoin Magazine": "https://bitcoinmagazine.com/feed",
}

TOKEN_RE = re.compile(r"\$([A-Z]{2,10})\b|\b(BTC|ETH|SOL|BNB|XRP|DOGE|ADA|AVAX|LINK|TON|SUI|APT|NEAR|HYPE|PEPE|PUMP)\b")

def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()

def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen)[-500:]))

def recent(entry):
    if not getattr(entry, "published_parsed", None):
        return True
    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - published < timedelta(minutes=MAX_AGE_MIN)

def tokens(text):
    found = []
    for a, b in TOKEN_RE.findall(text or ""):
        t = a or b
        if t not in found:
            found.append(t)
    return found

def short(text):
    words = re.sub(r"<[^>]+>", " ", text or "").split()
    cut = " ".join(words[:SUMMARY_WORDS])
    return cut if len(words) <= SUMMARY_WORDS else cut + "..."

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text[:4000], "disable_web_page_preview": True},
        timeout=20,
    )

def from_tree():
    html = requests.get("https://tree.news/", timeout=20).text
    items = []
    for title, link in re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', html)[:15]:
        if "x.com" in link:
            continue
        items.append(("Tree News", title, title, link))
    return items

def main():
    seen = load_seen()
    fresh = []
    for source, url in FEEDS.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
            link = e.get("link", "")
            if not link or link in seen or not recent(e):
                continue
            title = e.get("title", "")
            summary = short(e.get("summary", title))
            fresh.append((source, title, summary, link))
            seen.add(link)
    for source, title, summary, link in from_tree():
        if link not in seen:
            fresh.append((source, title, short(summary), link))
            seen.add(link)
    save_seen(seen)
    for source, title, summary, link in fresh[:8]:
        tickers = tokens(title + " " + summary)
        tag = ("Token: " + ", ".join(tickers)) if tickers else "Token: không nêu rõ"
        send(f"{source}\n{title}\n{tag}\n\n{summary}\n\n{link}")

if __name__ == "__main__":
    main()
