import feedparser, pandas as pd, urllib.parse as up

STATES = ["Karnataka","Telangana","Tamil Nadu","Maharashtra","Gujarat","Uttar Pradesh"]
TOPICS = ["AI policy","AI mission","AI MoU","AI task force","AI centre of excellence","artificial intelligence government"]

rows = []
for s in STATES:
    for t in TOPICS:
        q = up.quote(f'"{s}" {t}')
        url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
        for e in feedparser.parse(url).entries:
            rows.append(dict(state_raw=s, title=e.title, link=e.link,
                             published=e.get("published",""),
                             source_name=e.get("source",{}).get("title","")))
pd.DataFrame(rows).to_csv("data/raw.csv", index=False)
print(len(rows))