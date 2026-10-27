from datetime import date
from tests.test_portfolio_workflow import db, client
from app.models.application import Application


def test_today_orders_due_tasks_and_excludes_finished_roles(client, db):
    rows = [
        Application(title='Overdue test',status='applied',follow_up=date(2026,10,25),next_action='Check recruiter reply'),
        Application(title='Due today test',status='interview',follow_up=date(2026,10,27),next_action='Prepare examples'),
        Application(title='Upcoming test',status='saved',follow_up=date(2026,10,29)),
        Application(title='Closed test',status='closed',follow_up=date(2026,10,20)),
        Application(title='Offer test',status='offer',follow_up=date(2026,10,20)),
    ]
    db.add_all(rows);db.flush()
    ids={row.id for row in rows}
    response=client.get('/api/v1/career/today?today=2026-10-27')
    assert response.status_code==200
    data=response.json()
    due=[item for item in data['due'] if item['id'] in ids]
    assert [item['title'] for item in due]==['Overdue test','Due today test']
    assert due[0]['next_action']=='Check recruiter reply'
    assert any(item['id']==rows[2].id for item in data['upcoming'])
    assert not any(item['id'] in {rows[3].id,rows[4].id} for item in data['needs_next_action'])
    assert client.get('/api/v1/career/today?today=not-a-date').status_code==422


def test_direction_is_saved_on_server(client):
    data={'role':'Computer Vision Engineer','location':'Japan','priorities':'Applied research and learning'}
    assert client.put('/api/v1/career/direction',json=data).status_code==200
    assert client.get('/api/v1/career/direction').json()==data


def test_saved_job_keeps_description_and_next_action(client):
    data={'title':'Vision engineer','job_description':'Computer vision role using PyTorch and TensorRT.',
          'next_action':'Check language requirements'}
    saved=client.put('/api/v1/career/applications',json=data).json()
    role=next(row for row in client.get('/api/v1/career/applications').json() if row['id']==saved['id'])
    assert role['job_description']==data['job_description']
    assert role['next_action']==data['next_action']
    assert role['score'] is None


def test_dashboard_has_focused_workspace_views(client):
    page=client.get('/dashboard')
    for view in ('today','search','compare','tracker','accounts'):
        assert f'data-view="{view}"' in page.text
        assert f'data-nav="{view}"' in page.text
    assert client.get('/static/workspace.js').status_code==200
