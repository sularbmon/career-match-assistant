const viewCopy={
  today:['Your next move, made manageable.','See what needs attention, then take one small step.'],
  search:['Explore what comes next.','Choose a direction, browse postings, and save roles worth considering.'],
  compare:['Bring your experience into focus.','Use your CV to identify relevant evidence and gaps for one role at a time.'],
  tracker:['Every opportunity, in one place.','Keep the posting, your next action, and follow-up date together.'],
  accounts:['Your experience, connected.','Review public projects, profile links, and your Gmail authorization.']
};
function setView(view){
  if(!viewCopy[view])view='today';
  for(const panel of document.querySelectorAll('[data-view]'))panel.hidden=panel.dataset.view!==view;
  for(const link of document.querySelectorAll('[data-nav]')){
    if(link.dataset.nav===view)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
  }
  $('view-title').textContent=viewCopy[view][0];$('view-description').textContent=viewCopy[view][1];
  if(location.hash!==`#${view}`)history.replaceState(null,'',`#${view}`);
}
window.addEventListener('hashchange',()=>setView(location.hash.slice(1)));
setView(location.hash.slice(1));

async function openTrackedRole(id){
  const item=trackedApplications.find(row=>row.id===id)|| (await api('/api/v1/career/applications')).find(row=>row.id===id);
  if(item)await openApplication(item);
}
function taskCards(containerId,tasks,emptyText){
  const container=$(containerId);container.replaceChildren();
  if(!tasks.length){const p=document.createElement('p');p.className='empty-note';p.textContent=emptyText;container.append(p);return;}
  for(const task of tasks){
    const article=document.createElement('article');const title=document.createElement('h4');title.textContent=task.title;
    const company=document.createElement('small');company.textContent=`${task.company||'Company not added'}${task.follow_up?` · ${task.follow_up}`:''}`;
    const action=document.createElement('p');action.textContent=task.next_action;
    if(task.scheduled_for){const date=document.createElement('p');date.textContent=new Date(task.scheduled_for).toLocaleString();article.append(date);}
    const button=document.createElement('button');button.type='button';button.className='text-button';button.textContent='Open role / update next step ↗';button.addEventListener('click',async()=>{try{await openTrackedRole(task.id);}catch{$('today-status').textContent='Could not open this role. Refresh and try again.';}});
    article.append(title,company,action,button);container.append(article);
  }
}
async function loadToday(){
  try{
    const now=new Date();const date=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
    const data=await api(`/api/v1/career/today?today=${date}`);$('today-date').textContent=data.date;
    $('pipeline-counts').replaceChildren();
    for(const [stage,count]of Object.entries(data.counts)){const card=document.createElement('a');card.href='#tracker';card.className='pipeline-card';const number=document.createElement('strong');number.textContent=count;const label=document.createElement('span');label.textContent=stage;card.append(number,label);card.addEventListener('click',()=>{$('tracker-filter').value=stage;loadTracker();});$('pipeline-counts').append(card);}
    taskCards('today-due',data.due,'No follow-ups due. Set a date on a saved role when you know the next step.');
    taskCards('today-upcoming',data.upcoming,'No upcoming dates. Start by saving one opportunity.');
    taskCards('today-unplanned',data.needs_next_action,'Your active roles all have a next action.');
    taskCards('today-scheduled',data.scheduled||[],'No scheduled tasks or interviews. Add them from a saved role’s history.');
    $('today-status').textContent='Dates use your browser’s local calendar. Reminders appear here; email notifications are not enabled.';
  }catch{$('today-status').textContent='Today could not load. Check the database connection and refresh.';}
}
async function loadDirection(){
  try{const data=await api('/api/v1/career/direction');
    if(data.role||data.location||data.priorities){$('target-role').value=data.role;$('target-location').value=data.location;$('priorities').value=data.priorities;updateSearchLinks();}
  }catch{$('direction-status').textContent='Saved direction could not load. Existing browser notes remain available; save to store them on this server.';}
}
$('tracker-query').addEventListener('input',()=>loadTracker(false));
$('tracker-filter').addEventListener('change',()=>loadTracker(false));
$('save-comparison').addEventListener('click',()=>{setView('tracker');$('save-form').scrollIntoView({block:'start'});});
$('compare-saved').addEventListener('click',()=>{
  if($('saved-description').value.trim().length<20){$('save-status').textContent='Paste at least 20 characters of the job description first.';return;}
  $('job').value=$('saved-description').value;setView('compare');$('status').textContent='Saved job description ready. Choose your CV and compare; save afterward to attach the result to this role.';
});
loadToday();loadDirection();
