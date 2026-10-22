RULES = [
 ("MoU/Partnership", ["mou","memorandum","partnership","letter of intent"]),
 ("Task force/CoE", ["task force","taskforce","centre of excellence","center of excellence","coe"]),
 ("Budget", ["budget","allocat","crore"]),
 ("Regulation/Ethics", ["ethic","regulat","safe and ethical","framework","guidelines"]),
 ("Governance deployment", ["health","agricultur","police","policing","education","school"]),
 ("Policy/Mission", ["policy","mission","strategy","action plan"]),
]
def categorize(t):
    t = t.lower()
    if not any(k in t for k in [" ai ","artificial intelligence","ai-","genai"]): return None
    for cat, kws in RULES:
        if any(k in t for k in kws): return cat
    return None