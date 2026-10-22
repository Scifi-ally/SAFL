import pandas as pd, re
from dateutil import parser as dp

ALIASES = {
 "Uttar Pradesh": ["up","uttar pradesh","uttar-pradesh","u.p."],
 "Tamil Nadu": ["tn","tamil nadu","tamilnadu","tamil-nadu"],
 "Karnataka": ["karnataka","ka"], "Telangana": ["telangana","ts"],
 "Maharashtra": ["maharashtra","mh"], "Gujarat": ["gujarat","gj"],
}
LOOKUP = {a: k for k, v in ALIASES.items() for a in v}
def norm_state(x):
    return LOOKUP.get(re.sub(r"\s+"," ",str(x).strip().lower().replace("-"," ")), "UNMAPPED")

def norm_date(x):
    try: return dp.parse(str(x)).date().isoformat(), "day"
    except Exception: return "", "unknown"

df = pd.read_csv("data/raw.csv")
df["state"] = df.state_raw.map(norm_state)
df[["date","date_precision"]] = df.published.apply(lambda x: pd.Series(norm_date(x)))
df["title"] = df.title.str.replace(r"\s+-\s+[^-]+$","",regex=True)  # strip " - Publisher"
df.to_csv("data/normalized.csv", index=False)
print(df.state.value_counts(), (df.date=="").sum())