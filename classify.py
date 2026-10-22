import re, pandas as pd

RULES = [
 ("MoU/Partnership", ["mou","memorandum","partnership","letter of intent"]),
 ("Task force/CoE", ["task force","taskforce","centre of excellence","center of excellence","coe"]),
 ("Budget", ["budget","allocat","crore"]),
 ("Regulation/Ethics", ["ethic","regulat","framework","guidelines"]),
 ("Governance deployment", ["health","agricultur","police","policing","education","school"]),
 ("Policy/Mission", ["policy","mission","strategy","action plan"]),
]
GOV = ["govt","government","minister","cabinet","chief minister"]

def categorize(title):
    t = " " + re.sub(r"[^a-z0-9 ]", " ", title.lower()) + " "
    if not any(k in t for k in [" ai ", "artificial intelligence", " genai "]):
        return None
    if not any(g in t for g in GOV):
        return None
    for cat, kws in RULES:
        if any(k in t for k in kws):
            return cat
    return None

if __name__ == "__main__":
    df = pd.read_csv("data/normalized.csv").fillna("")
    df["category"] = df.title.map(categorize)
    df = df[df.category.notna()]
    df.to_csv("data/classified.csv", index=False)
    print(len(df), "kept")