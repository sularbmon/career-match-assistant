let configuredJobSources=[];
async function discoveryApi(path,options={}){return api(`/api/v1/discovery${path}`,options);}
async function saveJobSources(sources){
  await discoveryApi('/sources',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({sources})});
  configuredJobSources=sources;renderJobSources();
}
function renderJobSources(){
  $('discovery-sources').replaceChildren();
  for(const [index,source]of configuredJobSources.entries()){
    const row=document.createElement('div'),label=document.createElement('span'),button=document.createElement('button');
    label.textContent=`${source.name} · ${source.provider}/${source.board}`;button.type='button';button.className='text-button';button.textContent='Remove source';
    button.addEventListener('click',async()=>{button.disabled=true;try{await saveJobSources(configuredJobSources.filter(item=>!(item.provider===source.provider&&item.board===source.board)));$('source-status').textContent='Company source removed. Saved opportunities are unchanged.';}catch(error){$('source-status').textContent=error.message;button.disabled=false;}});
    row.append(label,button);$('discovery-sources').append(row);
  }
  if(!configuredJobSources.length)$('discovery-sources').textContent='No sources yet. Add a company board below.';
}
async function loadJobSources(){try{const data=await discoveryApi('/sources');configuredJobSources=data.sources;renderJobSources();if(data.example_default)$('source-status').textContent='An example source is available. Replace or expand it with companies you want to explore.';}catch(error){$('source-status').textContent=`Sources could not load: ${error.message}`;}}
$('source-form').addEventListener('submit',async event=>{
  event.preventDefault();const button=$('source-form').querySelector('button[type=submit]');button.disabled=true;
  try{
    let provider=$('source-provider').value,board=$('source-board').value.trim();
    if(board.startsWith('https://')){const url=new URL(board);if(url.hostname==='jobs.lever.co')provider='lever';else if(['boards.greenhouse.io','job-boards.greenhouse.io'].includes(url.hostname))provider='greenhouse';else throw new Error('Use a supported public Lever or Greenhouse board URL.');board=url.pathname.split('/').filter(Boolean)[0]||'';}
    if(!/^[A-Za-z0-9_-]{1,100}$/.test(board))throw new Error('Enter a board slug or supported https board URL.');
    await saveJobSources([...configuredJobSources,{provider,board,name:$('source-name').value.trim()}]);$('source-form').reset();$('source-status').textContent='Company source saved. Run a search to verify its availability.';
  }catch(error){$('source-status').textContent=error.message;}finally{button.disabled=false;}
});
$('discovery-use-direction').addEventListener('click',()=>{$('discovery-keywords').value=$('target-role').value;$('discovery-location').value=$('target-location').value;$('discovery-status').textContent='Direction copied. Location is a literal text filter; simplify it to a city or work-style term if needed.';});
$('discovery-form').addEventListener('submit',async event=>{
  event.preventDefault();$('discovery-search').disabled=true;$('discovery-status').textContent='Checking selected company boards…';$('discovery-results').replaceChildren();$('discovery-source-status').replaceChildren();
  try{
    const data=await discoveryApi('/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keywords:$('discovery-keywords').value,location:$('discovery-location').value})});
    $('discovery-status').textContent=`${data.total_matches} matching postings in checked sources${data.limited?' · showing the first 50':''}. Checked ${new Date(data.checked_at).toLocaleString()}.`;
    for(const source of data.sources){const p=document.createElement('p');p.textContent=`${source.name}: ${source.error||`${source.checked} postings checked${source.truncated?' (source limit reached)':''}`}`;if(source.error)p.className='source-error';$('discovery-source-status').append(p);}
    if(!data.jobs.length){const p=document.createElement('p');p.textContent='No results in the checked sources. Try fewer keywords, clear the location filter, or add another company board. This does not mean no suitable jobs exist.';$('discovery-results').append(p);}
    for(const job of data.jobs){
      const article=document.createElement('article'),title=document.createElement('h3'),meta=document.createElement('p'),link=document.createElement('a');title.textContent=job.title;meta.textContent=`${job.company} · ${job.location||'Location not listed'}${job.workplace?` · ${job.workplace}`:''}`;link.href=job.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Read original posting ↗';
      const details=document.createElement('details'),summary=document.createElement('summary'),description=document.createElement('p');summary.textContent='Preview posting text';description.textContent=job.description;details.append(summary,description);
      const save=document.createElement('button'),status=document.createElement('p');save.type='button';save.className='primary';save.textContent='Save opportunity to my tracker';
      save.addEventListener('click',async()=>{save.disabled=true;status.textContent='Verifying the current posting and saving…';try{const saved=await discoveryApi('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:{provider:job.provider,board:job.board,name:job.company},posting_id:job.id})});status.textContent=saved.already_saved?'Already in your tracker. Your notes and status were preserved.':'Saved with the posting text and source link.';await Promise.all([loadTracker(),loadToday()]);const open=document.createElement('button');open.type='button';open.className='text-button';open.textContent='Open saved opportunity ↗';open.addEventListener('click',async()=>{try{await openTrackedRole(saved.id);}catch(error){status.textContent=error.message;}});status.append(open);}catch(error){status.textContent=error.message;}finally{save.disabled=false;}});
      article.append(title,meta,link,details,save,status);$('discovery-results').append(article);
    }
  }catch(error){$('discovery-status').textContent=`Search could not complete: ${error.message}`;}finally{$('discovery-search').disabled=false;}
});
loadJobSources();
