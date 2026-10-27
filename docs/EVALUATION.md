# Matching evaluation

## Method

The development dataset contains 30 synthetic resume/job pairs across 10 role groups. Each group has a strong, partial, and unrelated resume. Expected skills are annotated against the existing taxonomy. The ranking check requires strong > partial > unrelated within each group. Extraction precision and recall are micro-averaged over both resume and job skill sets (60 documents, including repeated job descriptions).

These short examples were authored during development. They are useful regression checks, not an independent test set, human-reviewed ground truth, a hiring-quality benchmark, or evidence of fairness. Repeated job text and simple templates make these metrics easier than realistic resumes. No production data or personal resumes are included.

## Results

| Metric | Before this evaluation revision | After |
| --- | ---: | ---: |
| Cases | 30 | 30 |
| Skill extraction precision | 98.48% | 100% |
| Skill extraction recall | 100% | 100% |
| False-positive skill mentions | 2 | 0 |
| False-negative skill mentions | 0 | 0 |
| Correct within-role ranking groups | 10 / 10 | 10 / 10 |

The baseline was the backend portfolio revision before negation handling, not the original downloaded repository. Full scores and extracted skills are saved in `evaluation-baseline.json` and `evaluation-current.json`.

## Finding and change

The resume “Delivered Python projects. No experience with FastAPI or Docker.” incorrectly counted all three skills. The extractor now suppresses text following explicit phrases such as “no experience with,” “no experience in,” “never used,” and “not familiar with,” stopping at a sentence or semicolon boundary. Python remains recognized. This reduced the partial candidate's skill coverage from 100% to 33.33% for that role. It is deliberately a narrow heuristic: mixed positive/negative clauses, optional job requirements, ambiguous wording, and general negation remain unresolved.

Separately, TF-IDF now returns zero for input pairs with no valid tokens instead of throwing an empty-vocabulary error. This edge case has its own regression test and is not included in the metrics above.

## Reproduce

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe -m pytest -q
```

Evaluation itself needs no database or downloaded embedding model. The complete pytest suite requires an initialized PostgreSQL database. Keep the baseline file unchanged when rerunning the evaluator. The baseline is retained evidence, not a second implementation maintained in the application.

## Next evaluation milestone

Collect a separate, more varied set of synthetic or consented/anonymized resumes. Have another reviewer label skills and relative fit before running the system. Include multi-page documents, negation, unfamiliar skills, synonymous experience, optional requirements, and noisy PDF extraction. Compare against the frozen baseline and report errors as well as aggregate metrics. Do not tune on that held-out set. Assess proficiency and fairness separately; the current score does neither.
