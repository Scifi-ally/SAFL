import re
import pandas as pd

DATE_FROM = "2024-01-01"
BAD_SOURCES = {"instagram", "facebook", "youtube", "linkedin", "x", "twitter", "reddit", "quora"}

STATES = {
    "Karnataka": ["karnataka", "bengaluru", "bangalore"],
    "Telangana": ["telangana", r"t\W?gana", "hyderabad"],
    "Tamil Nadu": ["tamil nadu", "tamilnadu", "chennai"],
    "Maharashtra": ["maharashtra", "mumbai", "pune", "nagpur"],
    "Gujarat": ["gujarat", "gandhinagar", "ahmedabad", "gift city"],
    "Uttar Pradesh": ["uttar pradesh", "lucknow", "noida", "yogi"],
}

OTHER = [
    "madhya pradesh", "mp chief minister", "mohan yadav", "indore", "bhopal", "kerala",
    "punjab", "haryana", "rajasthan", "andhra", "odisha", "west bengal", "bihar", "assam",
    "jharkhand", "chhattisgarh", "uttarakhand", "himachal",
]

AI_TERM = re.compile(r"\bai\b|artificial intelligence|genai", re.I)
GOV = re.compile(r"govt|government|minister|cabinet|\bcm\b", re.I)

ACTION = re.compile(
    r"approv|clears?\b|cabinet|\bsign(?:s|ed|ing)?\b|\bink(?:s|ed)?\b|\bmou\b|memorandum|\bpact\b|"
    r"agreement|launch|unveil|announc|introduc|roll(?:s|ed)? out|sets? up|establish|allocat|outlay|"
    r"notif|select|roadmap|\bplans?\b|policy|mission|task\s?force|centre of excellence|"
    r"center of excellence|\bcoe\b|guidelines|framework|vocational|curriculum|cancel",
    re.I,
)
NOISE = re.compile(r"\bopinion\b|\banalysis\b|\bexplained\b|\beditorial\b|\bsurvey\b|per\s?cent|\bpercent\b", re.I)

RULES = [
    ("MoU/Partnership", r"\bmou\b|memorandum|\bpact\b|agreement|letter of intent|\bsigns?\b|\binks?\b"),
    ("Task force/CoE", r"task\s?force|centre of excellence|center of excellence|\bcoe\b|expert committee"),
    ("Budget", r"budget|allocat|outlay|earmark"),
    ("Regulation/Ethics", r"ethic|regulat|guidelines|safeguard|framework"),
    ("Policy/Mission", r"policy|mission|action plan|roadmap|strategy"),
    ("Governance deployment", r"health|agricultur|polic(?:e|ing)|educat|school|student|hospital|farmer|vocational"),
]


def find_state(title, query_state):
    t = title.lower()
    hits = [
        (m.start(), st)
        for st, pats in STATES.items()
        for p in pats
        if (m := re.search(rf"\b{p}\b", t))
    ]
    if hits:
        return min(hits)[1], "title"
    if any(re.search(rf"\b{o}", t) for o in OTHER):
        return None, "other-state"
    return query_state, "query"


def relevant(title):
    return bool(AI_TERM.search(title) and GOV.search(title) and ACTION.search(title) and not NOISE.search(title))


def categorize(title):
    for cat, pattern in RULES:
        if re.search(pattern, title, re.I):
            return cat
    return "Other"


def status(title):
    t = title.lower()
    if re.search(r"cancel|scrap|withdraw|revok", t):
        return "cancelled"
    if re.search(r"\bplans? to\b|\bset to\b|\bproposed\b|\blikely\b|\bexpected\b|\bwill\b", t):
        return "planned"
    if re.search(r"approv|clears?\b|\bnod\b", t):
        return "approved"
    if re.search(r"\bsign(?:s|ed|ing)?\b|\bink(?:s|ed)?\b|\bmou\b|exchange|\bpact\b|agreement", t):
        return "signed"
    return "announced"


def drop(df, keep_mask, why):
    print(f"  dropped {int((~keep_mask).sum()):>4}  {why}")
    return df[keep_mask]


if __name__ == "__main__":
    df = pd.read_csv("data/normalized.csv").fillna("")
    print(f"{len(df)} rows in")
    df = drop(df, ~df.source_name.str.lower().isin(BAD_SOURCES), "social / non-news source")
    df = drop(df, (df.date == "") | (df.date >= DATE_FROM), f"dated before {DATE_FROM}")

    found = [find_state(t, s) for t, s in zip(df.title, df.state)]
    df = df.assign(state=[f[0] for f in found], state_basis=[f[1] for f in found])
    df = drop(df, df.state.notna(), "headline is about another state")

    df = drop(df, df.title.map(relevant), "not a government AI action")
    df = df.assign(category=df.title.map(categorize), status=df.title.map(status))
    df.to_csv("data/classified.csv", index=False)

    print(f"{len(df)} rows kept")
    print("state taken from:", df.state_basis.value_counts().to_dict())