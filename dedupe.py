from rapidfuzz import fuzz
import pandas as pd
df = df.sort_values(["state","date"]).reset_index(drop=True)
clusters = []   
for i, r in df.iterrows():
    placed = False
    for c in clusters:
        k = df.loc[c["canon"]]
        if k.state != r.state: continue
        close = (not r.date or not k.date) or abs((pd.Timestamp(r.date)-pd.Timestamp(k.date)).days) <= 7
        if close and fuzz.token_set_ratio(r.title, k.title) >= 80:
            c["members"].append(i); placed = True; break
    if not placed: clusters.append(dict(canon=i, members=[i]))