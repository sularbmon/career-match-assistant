const test=require('node:test');
const assert=require('node:assert/strict');
const {createHarness,role,match,text,flush}=require('./harness.cjs');

test('all real page scripts initialize together against the declared HTML IDs',async()=>{
  const h=createHarness();await flush();
  assert.equal(h.el('view-title').textContent,'Your next move, made manageable.');
  assert.ok(h.el('compare-form').handlers.submit.length);
  assert.ok(h.el('event-form').handlers.submit.length);
  assert.ok(h.el('discovery-form').handlers.submit.length);
});

test('opening roles out of order cannot replace the latest form or comparison',async()=>{
  const h=createHarness();await flush();
  const first=h.delay('/api/v1/matching/101'),second=h.delay('/api/v1/matching/202');
  const openedFirst=h.context.openApplication(role(1,101));await flush();
  const openedSecond=h.context.openApplication(role(2,202));await flush();
  second.resolve(match(202,80));await openedSecond;
  first.resolve(match(101,10));await openedFirst;await flush();
  assert.equal(h.el('job-title').value,'Role 2');
  assert.equal(h.el('notes').value,'Notes 2');
  assert.equal(h.el('score').textContent,'80.0%');
  assert.equal(h.evaluate('currentApplicationId'),2);
});

test('a delayed save cannot select a role the user has left',async()=>{
  const h=createHarness();await flush();await h.context.openApplication(role(1));
  const save=h.delay('/api/v1/career/applications','PUT');
  const saving=h.fire('save-form');await flush();
  const payload=JSON.parse(h.calls.find(call=>call.options.method==='PUT').options.body);
  assert.equal(payload.application_id,1);assert.equal(payload.title,'Role 1');
  await h.context.openApplication(role(2));save.resolve({id:1});await saving;
  assert.equal(h.evaluate('currentApplicationId'),2);
  assert.equal(h.el('job-title').value,'Role 2');
  assert.equal(h.el('notes').value,'Notes 2');
});

test('switching roles cancels presentation of an old comparison pipeline',async()=>{
  const h=createHarness();await flush();await h.context.openApplication(role(1));
  h.el('saved-resume').value='99';h.el('job').value='Python engineer for a detailed role description';
  const analysis=h.delay('/api/v1/jobs/analyze','POST');
  const comparing=h.fire('compare-form');await flush();
  await h.context.openApplication(role(2));analysis.resolve({job_id:17});await comparing;
  assert.equal(h.evaluate('currentApplicationId'),2);
  assert.equal(h.el('saved-description').value,'Description for role 2');
  assert.equal(h.calls.filter(call=>call.url==='/api/v1/matching/match').length,0);
});

test('failed comparison does not detach the previous saved comparison',async()=>{
  const h=createHarness();await flush();
  h.routes.set('GET /api/v1/matching/101',()=>match(101,50));
  await h.context.openApplication(role(1,101));
  h.el('saved-resume').value='99';h.el('job').value='A sufficiently detailed job description';
  h.routes.set('POST /api/v1/jobs/analyze',()=>{throw Error('Temporary failure');});
  await h.fire('compare-form');
  assert.equal(h.evaluate('currentMatch'),101);
  assert.match(h.el('status').textContent,/Temporary failure/);
});

test('late learning responses cannot replace a newer comparison learning plan',async()=>{
  const h=createHarness();await flush();
  const first=h.delay('/api/v1/rag/recommendations/101'),second=h.delay('/api/v1/rag/recommendations/202');
  h.evaluate('currentMatch=101');const a=h.context.learningPlan(101);
  h.evaluate('currentMatch=202');const b=h.context.learningPlan(202);
  second.resolve({recommendations:[{missing_skills:'new-plan',retrieved_knowledge:[],recommendations:'Current guidance'}]});await b;
  first.resolve({recommendations:[{missing_skills:'old-plan',retrieved_knowledge:[],recommendations:'Old guidance'}]});await a;
  assert.match(text(h.el('learning')),/new-plan/);
  assert.doesNotMatch(text(h.el('learning')),/old-plan/);
});

test('a comparison uses the submitted description and releases controls before learning completes',async()=>{
  const h=createHarness();await flush();
  h.el('saved-resume').value='99';h.el('job').value='Submitted Python engineer job description';
  const analysis=h.delay('/api/v1/jobs/analyze','POST');
  const learning=h.delay('/api/v1/rag/recommendations/303');
  h.routes.set('POST /api/v1/matching/match',()=>match(303,75));
  const comparing=h.fire('compare-form');await flush();
  h.el('job').value='A different job typed while the request was pending';
  analysis.resolve({job_id:8});await comparing;
  assert.equal(h.el('saved-description').value,'Submitted Python engineer job description');
  assert.equal(h.el('submit').disabled,false);
  assert.equal(h.el('score').textContent,'75.0%');
  learning.resolve({recommendations:[]});await flush();
});

test('late CV review errors cannot overwrite the latest review',async()=>{
  const h=createHarness();await flush();
  const first=h.delay('/api/v1/career/review/101'),second=h.delay('/api/v1/career/review/202');
  h.evaluate('currentMatch=101');const a=h.context.loadReview(101);
  h.evaluate('currentMatch=202');const b=h.context.loadReview(202);
  second.resolve({evidence:[],gaps:[{action:'Latest guidance'}],checklist:[],bullet_template:''});await b;
  first.reject(Error('Old request failed'));await a;
  assert.match(text(h.el('review')),/Latest guidance/);
  assert.doesNotMatch(text(h.el('review')),/Old request failed/);
});

test('conflicting saves leave local notes intact and show the server conflict',async()=>{
  const h=createHarness();await flush();await h.context.openApplication(role(1));
  h.el('notes').value='Unsaved notes I need to preserve';
  h.routes.set('PUT /api/v1/career/applications',()=>({isHttpReply:true,status:409,data:{detail:'This role changed since you opened it.'}}));
  await h.fire('save-form');
  assert.equal(h.el('notes').value,'Unsaved notes I need to preserve');
  assert.match(h.el('save-status').textContent,/changed since you opened/);
  assert.equal(h.evaluate('currentApplicationVersion'),1);
  const payload=JSON.parse(h.calls.find(call=>call.options.method==='PUT').options.body);
  assert.equal(payload.version,1);
});
