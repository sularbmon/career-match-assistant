from app.services.skill_extractor import extract_skills
from app.services.text_cleaner import clean_text
from tests.test_portfolio_workflow import client, db
from app.api import career


def test_edge_vision_skills_are_recognized():
    skills = set(extract_skills(clean_text(
        'Computer vision using OpenCV and YOLO on NVIDIA Jetson Orin NX with CUDA and TensorRT.'
    )))
    assert {'computer vision','opencv','yolo','nvidia jetson','cuda','tensorrt'} <= skills


def test_multimodal_and_training_aliases():
    skills = set(extract_skills(clean_text(
        'Vision-language models, multi-object tracking, PyTorch DDP, Weights & Biases.'
    )))
    assert {'vision-language models','multi-object tracking','distributed training','weights & biases'} <= skills


def test_similar_words_are_not_skill_matches():
    assert 'cuda' not in extract_skills('barracuda')
    assert 'sam' not in extract_skills('sample')


def test_profile_is_optional_and_local(client, monkeypatch, tmp_path):
    monkeypatch.setattr(career, 'PROFILE_PATH', tmp_path / 'profile.json')
    assert client.get('/api/v1/career/profile').json() == {'configured':False}
    (tmp_path / 'profile.json').write_text('{"headline":"Example","resume_id":1}')
    data=client.get('/api/v1/career/profile').json()
    assert data['configured'] is True
    assert data['headline']=='Example'
