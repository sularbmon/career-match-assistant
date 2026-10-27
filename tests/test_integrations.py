import httpx
import pytest
from tests.test_portfolio_workflow import db, client
from app.api import integrations


def test_profiles_are_saved_and_validated(client):
    assert client.put('/api/v1/integrations/profiles', json={
        'github':'octocat', 'linkedin':'https://www.linkedin.com/in/example'}).status_code == 200
    assert client.get('/api/v1/integrations/status').json()['github'] == 'octocat'
    for data in [{'github':'../bad'}, {'linkedin':'https://evil.com/in/user'}]:
        assert client.put('/api/v1/integrations/profiles', json=data).status_code == 422


def test_gmail_missing_authorization_is_actionable(client, monkeypatch, tmp_path):
    monkeypatch.setattr(integrations, 'LOCAL_DIR', tmp_path)
    assert client.get('/api/v1/integrations/status').json()['gmail'] == 'setup-required'
    assert client.get('/api/v1/integrations/gmail/messages').status_code == 409


def test_github_preview_and_rate_limit(client, monkeypatch):
    responses = [httpx.Response(200,json={'login':'octocat','name':'Example'}, request=httpx.Request('GET','https://api.github.com')),
                 httpx.Response(200,json=[{'name':'demo','html_url':'https://github.com/octocat/demo','fork':True},
                                         {'name':'old','html_url':'https://github.com/octocat/old','fork':False,'archived':True}],
                                request=httpx.Request('GET','https://api.github.com'))]
    class FakeClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, *args, **kwargs): return responses.pop(0)
    monkeypatch.setattr(integrations.httpx, 'Client', FakeClient)
    result = client.get('/api/v1/integrations/github/octocat')
    assert result.status_code == 200
    assert len(result.json()['projects']) == 1
    assert result.json()['projects'][0]['fork'] is True
    responses.extend([httpx.Response(403), httpx.Response(403)])
    assert client.get('/api/v1/integrations/github/octocat').status_code == 429


def test_gmail_returns_headers_without_bodies(client, monkeypatch, tmp_path):
    pytest.importorskip('google.auth')
    from google.oauth2.credentials import Credentials
    from google.auth.transport import requests
    monkeypatch.setattr(integrations,'LOCAL_DIR',tmp_path)
    (tmp_path/'gmail-token.json').write_text('{}')
    class FakeCredentials:
        def to_json(self): return '{}'
    monkeypatch.setattr(Credentials,'from_authorized_user_file',lambda *args,**kwargs:FakeCredentials())
    class FakeResponse:
        def __init__(self,data): self.data=data
        def raise_for_status(self): pass
        def json(self): return self.data
    class FakeSession:
        def __init__(self,*args): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def get(self,url,params,timeout):
            if url.endswith('/messages'):
                assert params['maxResults']==20
                return FakeResponse({'messages':[{'id':'abc123'}]})
            assert params['format']=='metadata'
            return FakeResponse({'id':'abc123','payload':{'headers':[{'name':'Subject','value':'Interview'}]},'body':'PRIVATE BODY'})
    monkeypatch.setattr(requests,'AuthorizedSession',FakeSession)
    result=client.get('/api/v1/integrations/gmail/messages')
    assert result.status_code==200
    assert result.json()['messages'][0]['subject']=='Interview'
    assert 'PRIVATE BODY' not in result.text
