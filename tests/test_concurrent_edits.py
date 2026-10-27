from tests.test_portfolio_workflow import db,client


def test_old_role_version_cannot_overwrite_newer_notes(client):
    saved=client.put('/api/v1/career/applications',json={'title':'Vision role','notes':'Original'}).json()
    first={'application_id':saved['id'],'version':saved['version'],'title':'Vision role','notes':'New notes from first tab'}
    updated=client.put('/api/v1/career/applications',json=first)
    assert updated.status_code==200
    assert updated.json()['version']>saved['version']
    stale={**first,'notes':'Old form from another tab'}
    response=client.put('/api/v1/career/applications',json=stale)
    assert response.status_code==409
    actual=next(item for item in client.get('/api/v1/career/applications').json() if item['id']==saved['id'])
    assert actual['notes']=='New notes from first tab'


def test_current_version_can_update_role(client):
    saved=client.put('/api/v1/career/applications',json={'title':'CV role'}).json()
    response=client.put('/api/v1/career/applications',json={
        'application_id':saved['id'],'version':saved['version'],'title':'CV role','status':'applied'})
    assert response.status_code==200
    assert response.json()['version']==saved['version']+1
