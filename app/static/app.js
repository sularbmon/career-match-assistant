const $ = id => document.getElementById(id);
let currentMatch = null;
let currentApplicationId = null;
let currentApplicationVersion = null;
let trackedApplications = [];
let roleSelectionVersion = 0;
let comparisonRequest = 0;
let learningRequest = 0;
let reviewRequest = 0;
let trackerRequest = 0;
let resumeRequest = 0;
async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try { const body = await response.json(); if (typeof body.detail === 'string') detail = body.detail; } catch {}
    throw new Error(detail);
  }
  return response.json();
}
function chips(id, skills, emptyMessage) {
  $(id).replaceChildren();
  for (const skill of skills.length ? skills : [emptyMessage]) {
    const chip = document.createElement('span'); chip.textContent = skill; $(id).append(chip);
  }
}
function renderMatch(match) {
  $('empty').hidden = true; $('results').hidden = false;
  $('score').textContent = `${match.final_match_score.toFixed(1)}%`;
  $('match-id').textContent = `COMPARISON #${match.match_result_id}`;
  $('skills-score').textContent = `${match.skill_match_percentage.toFixed(1)}%`;
  $('text-score').textContent = `${match.text_similarity_percentage.toFixed(1)}%`;
  $('skill-bar').value = match.skill_match_percentage; $('text-bar').value = match.text_similarity_percentage;
  chips('matched', match.matched_skills, 'No recognized overlap');
  chips('missing', match.missing_skills, 'No missing skills in the recognized taxonomy');
}
async function learningPlan(id) {
  const request=++learningRequest;
  $('retry').hidden = true; $('learning').textContent = 'Retrieving learning material… First use may download the embedding model.';
  try {
    const data = await api(`/api/v1/rag/recommendations/${id}`);
    if(request!==learningRequest||currentMatch!==id)return;
    $('learning').replaceChildren();
    if (!data.recommendations.length) $('learning').textContent = 'No missing skills were identified in the recognized taxonomy.';
    for (const item of data.recommendations) {
      const article = document.createElement('article');
      const heading = document.createElement('h4'); heading.textContent = item.missing_skills;
      article.append(heading);
      // Older seed runs may have stored identical material more than once.
      const seen = new Set();
      for (const chunk of item.retrieved_knowledge) {
        const key = `${chunk.title}:${chunk.content}`; if (seen.has(key)) continue; seen.add(key);
        const title = document.createElement('strong'); title.textContent = chunk.title;
        const content = document.createElement('p'); content.textContent = chunk.content;
        const source = document.createElement('small'); source.textContent = `Curated knowledge #${chunk.knowledge_id} · ${chunk.level || 'General'}`;
        article.append(title, content, source);
      }
      if (!item.retrieved_knowledge.length) { const note = document.createElement('p'); note.textContent = item.recommendations; article.append(note); }
      $('learning').append(article);
    }
  } catch (error) {
    if(request!==learningRequest||currentMatch!==id)return;
    $('learning').textContent = `Your match is saved, but the learning plan could not load: ${error.message}`;
    $('retry').hidden = false;
  }
}
$('sample').addEventListener('click', async () => {
  $('sample').disabled = true;
  try {
    const response = await fetch('/demo/resume.pdf'); if (!response.ok) throw new Error('Sample PDF could not load.');
    const transfer = new DataTransfer(); transfer.items.add(new File([await response.blob()], 'synthetic-resume.pdf', {type:'application/pdf'}));
    $('resume').files = transfer.files;
    $('saved-resume').value = ''; $('resume').required = true;
    $('job').value = 'Seeking a Python FastAPI PostgreSQL developer with Docker, REST API and AWS experience.';
    $('status').textContent = 'Synthetic sample ready. Select “Compare with this role” to run the full workflow.';
  } catch (error) { $('status').textContent = error.message; }
  finally { $('sample').disabled = false; }
});
$('compare-form').addEventListener('submit', async event => {
  event.preventDefault();
  const file = $('resume').files[0];
  const existingResume = $('saved-resume').value;
  if (!existingResume && (!file || file.size > 10 * 1024 * 1024)) { $('status').textContent = 'Choose a saved resume or a PDF of 10 MB or smaller.'; return; }
  if ($('job').value.trim().length < 20) { $('status').textContent = 'Enter at least 20 characters for the job description.'; return; }
  const selection=roleSelectionVersion,request=++comparisonRequest,jobText=$('job').value;
  const stillCurrent=()=>selection===roleSelectionVersion&&request===comparisonRequest;
  learningRequest++;reviewRequest++;
  $('submit').disabled = true; $('sample').disabled = true; $('retry').hidden = true;
  $('results').hidden = true; $('empty').hidden = false;
  try {
    $('status').textContent = 'Step 1 of 3 · Reading your resume…';
    const form = new FormData(); form.append('file', file);
    const resume = existingResume ? {resume_id:Number(existingResume)} : await api('/api/v1/resume/upload', {method:'POST', body:form});
    if(!stillCurrent())return;
    $('status').textContent = 'Step 2 of 3 · Analyzing the role…';
    const job = await api('/api/v1/jobs/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({job_description:jobText})});
    if(!stillCurrent())return;
    $('status').textContent = 'Step 3 of 3 · Calculating your comparison…';
    const match = await api('/api/v1/matching/match', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({resume_id:resume.resume_id, job_id:job.job_id})});
    if(!stillCurrent())return;
    currentMatch = match.match_result_id; renderMatch(match);
    $('saved-description').value=jobText;
    $('save-status').textContent = 'Saving this role will include the comparison above.';
    $('status').textContent = 'Comparison saved. Your score breakdown is ready.';
    void learningPlan(currentMatch);void loadReview(currentMatch);void loadResumes();
  } catch (error) { if(stillCurrent())$('status').textContent = `Comparison could not finish: ${error.message}. Earlier successful steps may remain saved; retry creates a new comparison.`; }
  finally { $('submit').disabled = false; $('sample').disabled = false; }
});
$('retry').addEventListener('click', async () => { if (currentMatch) await learningPlan(currentMatch); });

async function loadResumes() {
  const request=++resumeRequest;
  try {
    const resumes = await api('/api/v1/career/resumes');
    if(request!==resumeRequest)return;
    const selected = $('saved-resume').value;
    $('saved-resume').replaceChildren();
    const first = document.createElement('option'); first.value=''; first.textContent='Upload a new resume'; $('saved-resume').append(first);
    for (const resume of resumes) {
      const option = document.createElement('option'); option.value=resume.id;
      option.textContent=`${resume.filename} · version #${resume.id}`; $('saved-resume').append(option);
    }
    $('saved-resume').value=selected;
    $('resume').required=!$('saved-resume').value;
  } catch { if(request===resumeRequest)$('status').textContent='Saved resumes could not load. You can still upload a new PDF.'; }
}
$('saved-resume').addEventListener('change', () => { $('resume').required = !$('saved-resume').value; });

async function loadReview(id) {
  const request=++reviewRequest;
  $('review').textContent='Finding experience you can highlight…';
  try {
    const data = await api(`/api/v1/career/review/${id}`);
    if(request!==reviewRequest||currentMatch!==id)return;
    $('review').replaceChildren();
    for (const item of data.evidence) {
      const article=document.createElement('article'); const heading=document.createElement('h4'); heading.textContent=`Highlight your ${item.skill} experience`;
      article.append(heading);
      for (const snippet of item.snippets) { const quote=document.createElement('blockquote'); quote.textContent=snippet; article.append(quote); }
      const action=document.createElement('p'); action.textContent='Explain what you did with this skill, your contribution, and a result you can verify.'; article.append(action); $('review').append(article);
    }
    for (const gap of data.gaps) { const p=document.createElement('p'); p.textContent=gap.action; $('review').append(p); }
    const list=document.createElement('ul'); for(const step of data.checklist){const li=document.createElement('li');li.textContent=step;list.append(li);} $('review').append(list);
    const template=document.createElement('p'); template.textContent=`Bullet structure to fill with facts: ${data.bullet_template}`; $('review').append(template);
  } catch(error) { if(request===reviewRequest&&currentMatch===id)$('review').textContent=`Resume suggestions could not load: ${error.message}. Reload this saved comparison to retry.`; }
}

async function loadTracker(refresh=true) {
  const request=refresh?++trackerRequest:trackerRequest;
  try {
    if(refresh){const rows=await api('/api/v1/career/applications');if(request!==trackerRequest)return;trackedApplications=rows;} $('tracker').replaceChildren();
    if(!trackedApplications.length) $('tracker').textContent='No saved roles yet. Compare a job, then save it here with your next action.';
    const today=new Date(); const localDate=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
    const filter=$('tracker-filter').value,query=$('tracker-query').value.toLowerCase().trim();
    const visible=trackedApplications.filter(item=>(filter==='all'||item.status===filter)&&`${item.title} ${item.company} ${item.notes}`.toLowerCase().includes(query));
    if(trackedApplications.length&&!visible.length)$('tracker').textContent='No roles match these filters.';
    for(const item of visible){
      const article=document.createElement('article'); const heading=document.createElement('h3'); heading.textContent=item.title;
      const detail=document.createElement('p'); detail.textContent=`${item.company || 'Company not added'} · ${item.status}${item.score == null ? ' · Not compared yet' : ` · ${item.score.toFixed(1)}% resume overlap`}`;
      article.append(heading,detail);
      if(item.next_action){const action=document.createElement('p');action.textContent=`Next: ${item.next_action}`;article.append(action);}
      if(item.follow_up){const follow=document.createElement('p'); const active=!['closed','offer'].includes(item.status); follow.textContent=`${active && item.follow_up <= localDate ? 'Follow-up due: ' : 'Follow-up: '}${item.follow_up}`; if(active && item.follow_up <= localDate) follow.className='due'; article.append(follow);}
      if(item.notes){const notes=document.createElement('p'); notes.textContent=item.notes; article.append(notes);}
      if(item.url){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Open job posting ↗';article.append(link);}
      const button=document.createElement('button');button.type='button';button.className='text-button';button.textContent='Review / update this role ↗';button.addEventListener('click',()=>openApplication(item));article.append(button);$('tracker').append(article);
    }
  } catch(error) {if(request===trackerRequest)$('tracker').textContent=`Job tracker could not load: ${error.message}. Check the database setup and refresh.`;}
}
async function openApplication(item){
  const selection=++roleSelectionVersion;
  try{
    $('status').textContent='Opening saved comparison…';
    currentApplicationId=item.id; currentMatch=item.match_result_id;
    currentApplicationVersion=item.version||null;
    learningRequest++;reviewRequest++;
    setView('tracker');
    $('results').hidden=true;$('empty').hidden=false;clearDossier();
    $('job-title').value=item.title;$('company').value=item.company;$('job-url').value=item.url;$('application-status').value=item.status;$('notes').value=item.notes;$('follow-up').value=item.follow_up || '';
    $('saved-description').value=item.job_description||'';$('next-action').value=item.next_action||'';
    $('save-status').textContent='Editing this saved role.';$('status').textContent='Saved comparison opened. Update the application below.';
    await loadDossier(item.id,item.title);
    if(selection!==roleSelectionVersion)return;
    $('save-form').scrollIntoView({behavior:'smooth',block:'start'});
    if(item.match_result_id){
      const match=await api(`/api/v1/matching/${item.match_result_id}`);
      if(selection!==roleSelectionVersion)return;
      renderMatch(match);void loadReview(item.match_result_id);void learningPlan(item.match_result_id);
    }
  }catch(error){if(selection===roleSelectionVersion)$('status').textContent=error.message;}
}
$('save-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const selection=roleSelectionVersion,title=$('job-title').value;
  $('save-job').disabled=true;
  try{
    const saved=await api('/api/v1/career/applications',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({application_id:currentApplicationId,version:currentApplicationVersion,match_result_id:currentMatch,title:$('job-title').value,company:$('company').value,url:$('job-url').value,status:$('application-status').value,follow_up:$('follow-up').value||null,notes:$('notes').value,job_description:$('saved-description').value,next_action:$('next-action').value})});
    await Promise.all([loadTracker(),loadToday()]);
    if(selection!==roleSelectionVersion)return;
    currentApplicationId=saved.id;
    currentApplicationVersion=saved.version||null;
    $('save-status').textContent='Saved. Your role is in My job tracker below.';await loadDossier(saved.id,title);
  }catch(error){if(selection===roleSelectionVersion)$('save-status').textContent=`Could not save: ${error.message}`;}
  finally{$('save-job').disabled=false;}
});
loadResumes().then(loadPersonalProfile);loadTracker();
async function loadPersonalProfile(){
  try{
    const profile=await api('/api/v1/career/profile');if(!profile.configured)return;
    $('personal-profile').hidden=false;$('profile-headline').textContent=profile.headline;
    $('profile-summary').textContent=profile.summary;chips('profile-skills',profile.strengths, 'Review your experience');
    for(const role of profile.suggested_roles){const button=document.createElement('button');button.type='button';button.className='text-button';button.textContent=role;button.addEventListener('click',()=>{$('target-role').value=role;updateSearchLinks();$('direction-status').textContent='Search direction selected. Add your preferred location and save when ready.';});$('profile-roles').append(button);}
    $('profile-languages').textContent=`Languages in your CV: ${profile.languages}. Job language requirements still need checking.`;
    if(profile.resume_id && !$('saved-resume').value){$('saved-resume').value=String(profile.resume_id);$('resume').required=!$('saved-resume').value;}
  }catch{$('direction-status').textContent='Your personal profile could not load; you can still enter a search direction below.';}
}
$('new-role').addEventListener('click',()=>{roleSelectionVersion++;learningRequest++;reviewRequest++;currentApplicationId=null;currentApplicationVersion=null;currentMatch=null;$('save-form').reset();$('save-status').textContent='New role. Add a title to save it without a comparison.';$('results').hidden=true;$('empty').hidden=false;clearDossier();});

function updateSearchLinks(){
  const role=$('target-role').value.trim(),location=$('target-location').value.trim();
  $('linkedin-search').href=`https://www.linkedin.com/jobs/search/?${new URLSearchParams({keywords:role,location})}`;
  $('indeed-search').href=`https://www.indeed.com/jobs?${new URLSearchParams({q:role,l:location})}`;
}
try{const direction=JSON.parse(localStorage.getItem('career-match-direction')||'{}');$('target-role').value=direction.role||'';$('target-location').value=direction.location||'';$('priorities').value=direction.priorities||'';}catch{}
updateSearchLinks();
$('target-role').addEventListener('input',updateSearchLinks);$('target-location').addEventListener('input',updateSearchLinks);
$('direction-form').addEventListener('submit',async event=>{event.preventDefault();try{await api('/api/v1/career/direction',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:$('target-role').value,location:$('target-location').value,priorities:$('priorities').value})});$('direction-status').textContent='Saved on this local server. You can change your direction as you explore.';}catch(error){$('direction-status').textContent=`Could not save your direction: ${error.message}`;}});
