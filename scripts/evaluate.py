"""Deterministic synthetic evaluation; no database or model download required."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.skill_extractor import extract_skills
from app.services.text_cleaner import clean_text
from app.services.skill_matcher import match_skills
from app.services.text_similarity import calculate_text_similarity
from app.services.match_score import calculate_final_match_score


def evaluate():
    cases = json.loads((ROOT / 'data/evaluation/cases.json').read_text())['cases']
    rows, tp, fp, fn = [], 0, 0, 0
    for case in cases:
        resume, job = clean_text(case['resume']), clean_text(case['job'])
        extracted_resume, extracted_job = extract_skills(resume), extract_skills(job)
        for actual, expected in [(extracted_resume, case['expected_resume_skills']),
                                 (extracted_job, case['expected_job_skills'])]:
            actual, expected = set(actual), set(expected)
            tp += len(actual & expected)
            fp += len(actual - expected)
            fn += len(expected - actual)
        coverage = match_skills(extracted_resume, extracted_job)['match_percentage']
        similarity = calculate_text_similarity(resume, job)['similarity_percentage']
        score = calculate_final_match_score(coverage, similarity)['final_match_score']
        rows.append(dict(id=case['id'], group=case['group'], relevance=case['relevance'],
                         score=score, resume_skills=extracted_resume, job_skills=extracted_job))
    groups = sorted({row['group'] for row in rows})
    rankings = {}
    for group in groups:
        scores = {row['relevance']: row['score'] for row in rows if row['group']==group}
        rankings[group] = scores['strong'] > scores['partial'] > scores['unrelated']
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return dict(case_count=len(rows), extraction_precision=round(precision,4),
                extraction_recall=round(recall,4), false_positives=fp, false_negatives=fn,
                ranking_groups_passed=sum(rankings.values()), ranking_groups=len(groups),
                rankings=rankings, cases=rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='docs/evaluation-current.json')
    args = parser.parse_args()
    result = evaluate()
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'cases'}, indent=2))
