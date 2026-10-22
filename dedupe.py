import pandas as pd
from rapidfuzz import fuzz

THRESH = 80
df = pd.read_csv("data/classified.csv").fillna("")
df = df.sort_values(["state", "date"]).reset_index(drop=True)

clusters = []
for i, r in df.iterrows():
    for c in clusters:
        k = df.loc[c["canon"]]
        if k.state != r.state:
            continue
        close = (not r.date or not k.date) or abs((pd.Timestamp(r.date) - pd.Timestamp(k.date)).days) <= 7
        if close and fuzz.token_set_ratio(r.title, k.title) >= THRESH:
            c["members"].append(i)
            break
    else:
        clusters.append({"canon": i, "members": [i]})

out = []
for c in clusters:
    row = df.loc[c["canon"]].to_dict()
    row["duplicate_count"] = len(c["members"])
    others = {df.loc[m].source_name for m in c["members"]} - {row["source_name"]}
    row["also_reported_by"] = "; ".join(sorted(others))
    out.append(row)
pd.DataFrame(out).to_csv("data/final.csv", index=False)
print(len(df), "->", len(out), "after dedupe")