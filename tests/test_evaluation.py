from scripts.evaluate import evaluate
from app.services.skill_extractor import extract_skills
from app.services.text_similarity import calculate_text_similarity


def test_synthetic_development_suite():
    result = evaluate()
    assert result['case_count'] == 30
    assert result['false_positives'] == 0
    assert result['false_negatives'] == 0
    assert result['ranking_groups_passed'] == result['ranking_groups']


def test_negation_stops_at_clause_boundary():
    assert extract_skills('No experience with AWS; Python and Docker.') == ['python', 'docker']


def test_empty_vocabulary_is_zero_similarity():
    assert calculate_text_similarity('! a', '? b')['similarity_score'] == 0
