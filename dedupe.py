import re
import pandas as pd
from rapidfuzz import fuzz

THRESH = 80
WINDOW = 7
FLAG_WINDOW = 2

NAMES = re.compile(
    r"karnataka|telangana|tamil nadu|maharashtra|gujarat|uttar pradesh|bengaluru|bangalore|hyderabad|"
    r"chennai|mumbai|pune|nagpur|lucknow|noida|gandhinagar|ahmedabad|gift city|t\W?gana|yogi"
)

GENERIC = set("""
govt government gov minister chief cabinet state states india indian indias new first key major largest
global world country sign signs signed signing inks ink inked pact mou mous agreement memorandum
partnership approves approved approve clears nod launches launch launched unveils announces
introduces introduce plan plans set sets establish establishes establishing create creates boost
drive push policy policies mission centre center excellence task force committee with for from into
over amid after more also says will have been that this about their its
tech technology digital data startup startups skilling skill skills jobs job investment crore lakh
education schools school students student classes class university universities institute hospital
hospitals farmers agriculture health industry sector sectors labs lab hub park city cluster
""".split())


def anchors(title):
    t = NAMES.sub(" ", title.lower())
    return {w for w in re.findall(r"[a-z]{4,}", t) if w not in GENERIC}


def days(a, b):
    return abs((pd.Timestamp(a) - pd.Timestamp(b)).days)


def same_event(a, b):
    if a["state"] != b["state"]:
        return False
    if (a["status"] == "cancelled") != (b["status"] == "cancelled"):
        return False
    if a["date"] and b["date"] and days(a["date"], b["date"]) > WINDOW:
        return False
    if a["anchors"] & b["anchors"]:
        return True
    return fuzz.token_set_ratio(a["title"], b["title"]) >= THRESH


df = pd.read_csv("data/classified.csv").fillna("")
df = df.sort_values(["state", "date"]).reset_index(drop=True)
rows = df.to_dict("records")
for r in rows:
    r["anchors"] = anchors(r["title"])

clusters = []
for i, r in enumerate(rows):
    for c in clusters:
        if same_event(rows[c[0]], r):
            c.append(i)
            break
    else:
        clusters.append([i])

out = []
for c in clusters:
    keep = dict(rows[c[0]])
    others = {rows[i]["source_name"] for i in c} - {keep["source_name"]}
    keep["duplicate_count"] = len(c)
    keep["also_reported_by"] = "; ".join(sorted(others))
    keep["possible_dup_of"] = ""
    out.append(keep)

for j, b in enumerate(out):
    for a in out[:j]:
        if (
            a["state"] == b["state"] and a["category"] == b["category"] and a["status"] == b["status"]
            and a["date"] and b["date"] and days(a["date"], b["date"]) <= FLAG_WINDOW
        ):
            b["possible_dup_of"] = a["title"][:70]
            break

final = pd.DataFrame(out).drop(columns=["anchors", "published", "state_raw"], errors="ignore")
final = final.rename(columns={"link": "source_url"})
final["summary"] = final["title"]
cols = [
    "state", "title", "date", "date_precision", "source_name", "source_url", "summary",
    "category", "status", "duplicate_count", "also_reported_by", "possible_dup_of", "state_basis",
]
final[cols].sort_values("date", ascending=False).to_csv("data/final.csv", index=False)

flagged = sum(1 for o in out if o["possible_dup_of"])
print(f"{len(df)} -> {len(out)} after dedupe, {flagged} flagged as possible duplicates")