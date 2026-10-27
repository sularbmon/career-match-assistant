from tests.test_portfolio_workflow import db, client
from app.models.resume import Resume
from app.models.job import Job
from app.services.matching_services import create_match_result


def make_comparison(db):
    resume = Resume(original_filename='career-test.pdf', extracted_text='Built Python APIs for a reporting tool.',
                    cleaned_text='built python apis', extracted_skills=['python'])
    job = Job(job_description='Python and AWS developer', cleaned_text='python aws developer',
              extracted_skills=['python', 'aws'])
    db.add_all([resume, job]); db.flush()
    return create_match_result(db, resume.id, job.id)['match_result_id']


def test_review_quotes_existing_experience(client, db):
    match_id = make_comparison(db)
    response = client.get(f'/api/v1/career/review/{match_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['evidence'][0]['snippets'] == ['Built Python APIs for a reporting tool']
    assert data['gaps'][0]['skill'] == 'aws'
    assert 'real aws experience' in data['gaps'][0]['action']


def test_tracker_saves_and_updates_one_record(client, db):
    match_id = make_comparison(db)
    data = {'match_result_id':match_id, 'title':'Backend engineer', 'company':'Demo',
            'url':'https://example.com/job', 'follow_up':'2026-11-01'}
    first = client.put('/api/v1/career/applications', json=data)
    assert first.status_code == 200
    data.update(status='applied', notes='Submitted tailored resume')
    updated = client.put('/api/v1/career/applications', json=data)
    assert updated.json()['id'] == first.json()['id']
    saved = [row for row in client.get('/api/v1/career/applications').json()
             if row['match_result_id'] == match_id]
    assert len(saved) == 1
    assert saved[0]['status'] == 'applied'
    assert saved[0]['notes'] == 'Submitted tailored resume'
    assert saved[0]['follow_up'] == '2026-11-01'


def test_tracker_rejects_unsafe_url_and_blank_title(client, db):
    match_id = make_comparison(db)
    for title, url in [('Developer','javascript:alert(1)'), ('  ','')]:
        response = client.put('/api/v1/career/applications', json={
            'match_result_id':match_id,'title':title,'url':url})
        assert response.status_code == 422


def test_unknown_review_is_404(client):
    assert client.get('/api/v1/career/review/2147483647').status_code == 404


def test_save_opportunity_before_having_a_resume(client):
    first = client.put('/api/v1/career/applications', json={'title':'Exploratory role'})
    assert first.status_code == 200
    assert first.json()['match_result_id'] is None
    changed = client.put('/api/v1/career/applications', json={
        'application_id':first.json()['id'], 'title':'Exploratory role',
        'status':'applied', 'notes':'Applied on employer site'})
    assert changed.json()['id'] == first.json()['id']
    saved = next(row for row in client.get('/api/v1/career/applications').json()
                 if row['id'] == first.json()['id'])
    assert saved['score'] is None
    assert saved['status'] == 'applied'
