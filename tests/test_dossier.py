from tests.test_portfolio_workflow import db, client
from app.api import dossier


def save_role(client,title='Vision role'):
    return client.put('/api/v1/career/applications',json={'title':title}).json()['id']


def test_status_changes_are_preserved_once(client):
    role=save_role(client)
    for _ in range(2):
        assert client.put('/api/v1/career/applications',json={
            'application_id':role,'title':'Vision role','status':'applied'}).status_code==200
    history=client.get(f'/api/v1/career/applications/{role}/dossier').json()
    statuses=[event for event in history['events'] if event['kind']=='status']
    assert len(statuses)==2
    assert statuses[0]['title']=='Status changed: saved → applied'
    assert statuses[1]['title']=='Role saved'


def test_interview_task_is_scheduled_and_can_be_completed(client):
    role=save_role(client)
    data={'kind':'interview','title':'Technical conversation','body':'Discuss deployed vision systems',
          'scheduled_for':'2026-10-28T10:00:00+09:00'}
    response=client.post(f'/api/v1/career/applications/{role}/events',json=data)
    assert response.status_code==201
    event=response.json()
    today=client.get('/api/v1/career/today?today=2026-10-27').json()
    assert any(item['event_id']==event['id'] for item in today['scheduled'])
    data['done']=True
    assert client.put(f"/api/v1/career/applications/{role}/events/{event['id']}",json=data).status_code==200
    today=client.get('/api/v1/career/today?today=2026-10-27').json()
    assert not any(item['event_id']==event['id'] for item in today['scheduled'])
    data['scheduled_for']='2026-10-28T10:00:00'
    assert client.post(f'/api/v1/career/applications/{role}/events',json=data).status_code==422


def test_contacts_and_file_roundtrip(client,monkeypatch,tmp_path):
    monkeypatch.setattr(dossier,'DOCUMENT_DIR',tmp_path)
    role=save_role(client)
    assert client.post(f'/api/v1/career/applications/{role}/contacts',json={
        'name':'Demo recruiter','email':'recruiter@example.com','role':'Recruiter','notes':'Talked about role scope'}).status_code==201
    response=client.post(f'/api/v1/career/applications/{role}/documents',
        files={'file':('submitted-cv.txt',b'Exact submitted version','text/plain')},data={'label':'CV submitted'})
    assert response.status_code==201
    document=response.json()
    assert 'storage_name' not in document
    downloaded=client.get(f"/api/v1/career/applications/{role}/documents/{document['id']}")
    assert downloaded.content==b'Exact submitted version'
    assert 'attachment' in downloaded.headers['content-disposition']
    history=client.get(f'/api/v1/career/applications/{role}/dossier').json()
    assert history['contacts'][0]['name']=='Demo recruiter'
    assert history['documents'][0]['label']=='CV submitted'
    other=save_role(client,'Another role')
    assert client.get(f"/api/v1/career/applications/{other}/documents/{document['id']}").status_code==404


def test_document_validation_and_unknown_roles(client,monkeypatch,tmp_path):
    monkeypatch.setattr(dossier,'DOCUMENT_DIR',tmp_path)
    role=save_role(client)
    for filename,content,code in [('run.exe',b'not supported',400),('empty.txt',b'',400),
                                 ('large.txt',b'x'*(10*1024*1024+1),413)]:
        response=client.post(f'/api/v1/career/applications/{role}/documents',files={'file':(filename,content)})
        assert response.status_code==code
    assert list(tmp_path.iterdir())==[]
    assert client.get('/api/v1/career/applications/2147483647/dossier').status_code==404
