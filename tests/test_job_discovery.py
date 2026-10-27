import httpx
from tests.test_portfolio_workflow import db,client
from app.services import job_discovery


SOURCE={'provider':'lever','board':'example','name':'Example Company'}
JOB={'id':'job-1','title':'Computer Vision Engineer','location':'Tokyo','workplace':'hybrid',
     'url':'https://jobs.lever.co/example/job-1','description':'Build Python and OpenCV tools.',
     **SOURCE,'company':SOURCE['name']}


def test_public_html_is_decoded_to_plain_text():
    text=job_discovery.plain_text('&amp;lt;p&amp;gt;Python &amp;amp; OpenCV&amp;lt;/p&amp;gt;<script>bad()</script>')
    assert 'Python & OpenCV' in text
    assert 'bad()' not in text
    assert '<p>' not in text


def test_search_filters_keywords_and_exposes_source_failure(monkeypatch):
    def fetch(source):
        if source['board']=='unavailable':
            response=httpx.Response(404,request=httpx.Request('GET','https://api.lever.co'))
            response.raise_for_status()
        return [JOB,{**JOB,'id':'job-2','title':'Retail associate','description':'Handle customer email','location':'Osaka'}],False
    monkeypatch.setattr(job_discovery,'fetch_board',fetch)
    result=job_discovery.search_sources([SOURCE,{**SOURCE,'board':'unavailable'}],'computer vision, machine learning','tokyo')
    assert len(result['jobs'])==1
    assert result['sources'][1]['error'].startswith('Board not found')
    assert job_discovery.search_sources([SOURCE],'AI','')['jobs']==[]


def test_live_posting_save_is_deduplicated_and_preserves_status(client,monkeypatch):
    monkeypatch.setattr(job_discovery,'fetch_board',lambda source:([JOB],False))
    data={'source':SOURCE,'posting_id':'job-1'}
    first=client.post('/api/v1/discovery/save',json=data)
    assert first.status_code==200
    role_id=first.json()['id']
    assert first.json()['already_saved'] is False
    role=next(item for item in client.get('/api/v1/career/applications').json() if item['id']==role_id)
    assert 'Build Python' in role['job_description']
    role.update(application_id=role_id,status='applied',notes='My application notes')
    assert client.put('/api/v1/career/applications',json=role).status_code==200
    again=client.post('/api/v1/discovery/save',json=data).json()
    assert again=={'id':role_id,'already_saved':True}
    role=next(item for item in client.get('/api/v1/career/applications').json() if item['id']==role_id)
    assert role['status']=='applied'
    assert role['notes']=='My application notes'


def test_existing_manual_posting_is_linked_without_overwriting_notes(client,monkeypatch):
    manual=client.put('/api/v1/career/applications',json={'title':'Manually captured','url':JOB['url'],
        'notes':'Important research','status':'interview'}).json()['id']
    monkeypatch.setattr(job_discovery,'fetch_board',lambda source:([JOB],False))
    saved=client.post('/api/v1/discovery/save',json={'source':SOURCE,'posting_id':'job-1'}).json()
    assert saved=={'id':manual,'already_saved':True}
    role=next(item for item in client.get('/api/v1/career/applications').json() if item['id']==manual)
    assert role['notes']=='Important research'
    assert role['status']=='interview'


def test_source_validation_and_closed_posting(client,monkeypatch):
    assert client.put('/api/v1/discovery/sources',json={'sources':[{**SOURCE,'board':'../../private'}]}).status_code==422
    assert client.put('/api/v1/discovery/sources',json={'sources':[SOURCE,SOURCE]}).status_code==422
    assert client.put('/api/v1/discovery/sources',json={'sources':[]}).status_code==200
    assert client.post('/api/v1/discovery/search',json={}).status_code==409
    monkeypatch.setattr(job_discovery,'fetch_board',lambda source:([],False))
    assert client.post('/api/v1/discovery/save',json={'source':SOURCE,'posting_id':'closed'}).status_code==404


def test_lever_reads_pages_and_normalizes_html(client,monkeypatch):
    calls=[]
    class FakeClient:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def get(self,url,params):
            calls.append((url,params))
            count=100 if params['skip']==0 else 1
            payload=[{'id':str(params['skip']+i),'text':'Vision role','hostedUrl':'https://jobs.lever.co/example/id',
                      'description':'<p>Use Python</p>','categories':{'location':'Tokyo'}} for i in range(count)]
            return httpx.Response(200,json=payload,request=httpx.Request('GET',url))
    monkeypatch.setattr(job_discovery.httpx,'Client',FakeClient)
    jobs,truncated=job_discovery.fetch_board(SOURCE)
    assert len(jobs)==101 and not truncated
    assert [params['skip'] for _,params in calls]==[0,100]
    assert all(url.startswith('https://api.lever.co/') for url,_ in calls)
    assert jobs[0]['description']=='Use Python'


def test_greenhouse_connector_preserves_location_and_decodes_description(monkeypatch):
    class FakeClient:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def get(self,url,params):
            assert url=='https://boards-api.greenhouse.io/v1/boards/example/jobs'
            assert params=={'content':'true'}
            return httpx.Response(200,json={'jobs':[{'id':42,'title':'ML Engineer',
                'absolute_url':'https://job-boards.greenhouse.io/example/jobs/42',
                'location':{'name':'Tokyo, Japan'},'content':'&lt;p&gt;Use PyTorch&lt;/p&gt;'}]},
                request=httpx.Request('GET',url))
    monkeypatch.setattr(job_discovery.httpx,'Client',FakeClient)
    jobs,truncated=job_discovery.fetch_board({'provider':'greenhouse','board':'example','name':'Example'})
    assert not truncated
    assert jobs[0]['description']=='Use PyTorch'
    assert jobs[0]['location']=='Tokyo, Japan'
    assert jobs[0]['id']=='42'
