import json
import re
from pathlib import Path

SKILLS_LIFE = Path(__file__).resolve().parents[2] / "data" / "skills.json"

def load_skills() -> dict:
    with SKILLS_LIFE.open("r", encoding="utf-8") as f:
        data = json.load(f)
        return data["skills"]

def extract_skills(text: str) -> list[str]:
    # Exclude explicit absence statements only up to a sentence/clause boundary.
    # This is a narrow heuristic, not general natural-language negation handling.
    text = re.sub(
        r"\b(?:no experience (?:with|in)|never used|not familiar with)\b[^.;!?]*",
        " ", text, flags=re.IGNORECASE,
    )
    skills = load_skills()
    found_skills = []
    for canonical_skill, aliases in skills.items():
        for alias in aliases:
            pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
            if re.search(pattern, text.lower()):
                found_skills.append(canonical_skill)
                break
    return found_skills
