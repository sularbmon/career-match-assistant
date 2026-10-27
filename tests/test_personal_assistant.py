from types import SimpleNamespace
from tests.test_portfolio_workflow import db, client
from app.models.resume import Resume
from app.services.career_assistant import build_review
from app.api import assistant


def test_review_uses_cv_evidence_and_preserves_requirements():
    application=SimpleNamespace(id=1,title='Vision Engineer',company='Example',status='saved')
    resume=SimpleNamespace(id=2,original_filename='cv.pdf',extracted_text='Built Python and OpenCV tools. No experience with AWS.')
    review=build_review(application,resume,
        'Python OpenCV and AWS. Japanese JLPT N2 required. Hybrid in Tokyo. Visa sponsorship unavailable.',
        {'role':'Vision Engineer','location':'Japan','priorities':'Learning'})
    assert {item['skill'] for item in review['evidence']}=={'python','opencv'}
    assert review['missing_in_cv']==['aws']
    assert review['resume']['id']==2
    language=next(item for item in review['requirements'] if item['topic']=='Language')
    assert any('JLPT N2' in line for line in language['excerpts'])
    assert '[specific question' in review['email_draft']['body']
    assert 'my application' not in review['email_draft']['body']
    assert 'Learning'==review['preferences']['priorities']


def test_review_without_cv_or_posting_is_explicit():
    application=SimpleNamespace(id=1,title='Exploratory role',company='',status='saved')
    review=build_review(application,None,'',{})
    assert review['resume'] is None
    assert review['evidence']==[]
    assert any('full job description' in action for action in review['next_actions'])
    assert any('upload a CV' in action for action in review['next_actions'])


def test_opportunity_review_does_not_write_application_or_draft(client,db,monkeypatch,tmp_path):
    monkeypatch.setattr(assistant,'PROFILE_PATH',tmp_path/'absent.json')
    resume=Resume(original_filename='test-cv.pdf',extracted_text='Built Python tools.',cleaned_text='built python tools',extracted_skills=['python'])
    db.add(resume);db.flush()
    role=client.put('/api/v1/career/applications',json={'title':'Python Engineer','job_description':'Python and Docker engineer','status':'applied'}).json()['id']
    before=client.get(f'/api/v1/career/applications/{role}/dossier').json()
    response=client.get(f'/api/v1/career/applications/{role}/assistant?resume_id={resume.id}')
    assert response.status_code==200
    assert response.json()['missing_in_cv']==['docker']
    assert 'following up' in response.json()['email_draft']['body']
    after=client.get(f'/api/v1/career/applications/{role}/dossier').json()
    assert after==before
    assert client.get('/api/v1/career/applications/2147483647/assistant').status_code==404


def test_gmail_message_reference_is_deduplicated_per_role(client):
    role=client.put('/api/v1/career/applications',json={'title':'Vision Engineer','status':'applied'}).json()['id']
    message={'application_id':role,'message_id':'abc123','subject':'Interview invitation','sender':'recruiter@example.com','date':'2026-10-27'}
    first=client.post('/api/v1/integrations/gmail/save-to-role',json=message)
    assert first.status_code==200
    assert first.json()['already_saved'] is False
    second=client.post('/api/v1/integrations/gmail/save-to-role',json=message)
    assert second.json()['already_saved'] is True
    assert second.json()['id']==first.json()['id']
    history=client.get(f'/api/v1/career/applications/{role}/dossier').json()
    emails=[event for event in history['events'] if event['kind']=='email']
    assert len(emails)==1
    assert 'https://mail.google.com/' in emails[0]['body']
    stored=next(item for item in client.get('/api/v1/career/applications').json() if item['id']==role)
    assert stored['status']=='applied'
    message['message_id']='bad/../../id'
    assert client.post('/api/v1/integrations/gmail/save-to-role',json=message).status_code==422
