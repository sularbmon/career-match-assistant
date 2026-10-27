const ce=id=>document.getElementById(id);
async function connectionApi(path,options={}){const response=await fetch(`/api/v1/integrations${path}`,options);const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Request failed. Check your input and setup.');return data;}
async function loadConnections(){try{const data=await connectionApi('/status');ce('github-user').value=data.github;ce('linkedin-url').value=data.linkedin;ce('linkedin-open').href=data.linkedin||'https://www.linkedin.com/';ce('gmail-state').textContent=data.gmail==='setup-required'?'Not authorized in this app. Follow the setup guide.':'Local authorization file found. Search to verify access.';}catch{ce('profiles-status').textContent='Account settings could not load. Initialize the database and refresh.';}}
ce('profiles-form').addEventListener('submit',async event=>{event.preventDefault();try{await connectionApi('/profiles',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({github:ce('github-user').value.trim(),linkedin:ce('linkedin-url').value.trim()})});ce('linkedin-open').href=ce('linkedin-url').value.trim()||'https://www.linkedin.com/';ce('profiles-status').textContent='Profile links saved. This does not sign in to either account.';}catch(error){ce('profiles-status').textContent=error.message;}});
ce('github-preview').addEventListener('click',async()=>{ce('github-preview').disabled=true;ce('github-projects').textContent='Loading public projects…';try{const user=ce('github-user').value.trim();if(!user)throw new Error('Enter your GitHub username first.');const data=await connectionApi(`/github/${encodeURIComponent(user)}`);ce('github-projects').replaceChildren();const summary=document.createElement('p');summary.textContent=`${data.name||data.username} · ${data.limit_note}`;ce('github-projects').append(summary);if(!data.projects.length)summary.textContent+=' No public projects found.';for(const project of data.projects){const article=document.createElement('article');const link=document.createElement('a');link.href=project.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=project.name;const text=document.createElement('p');text.textContent=project.description||'No description supplied.';const meta=document.createElement('small');meta.textContent=`${project.language||'Language not listed'}${project.fork?' · Fork: describe your own changes':''}`;article.append(link,text,meta);ce('github-projects').append(article);}}catch(error){ce('github-projects').textContent=error.message;}finally{ce('github-preview').disabled=false;}});
ce('gmail-form').addEventListener('submit',async event=>{
  event.preventDefault();ce('gmail-search').disabled=true;ce('gmail-messages').textContent='Reading matching headers?';
  try{
    const data=await connectionApi(`/gmail/messages?${new URLSearchParams({query:ce('gmail-query').value})}`);
    const roles=await api('/api/v1/career/applications');ce('gmail-messages').replaceChildren();
    if(!data.messages.length)ce('gmail-messages').textContent='No matching emails. Check your label or query.';
    for(const message of data.messages){
      const article=document.createElement('article'),link=document.createElement('a'),sender=document.createElement('p');
      link.href=message.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=message.subject;
      sender.textContent=`${message.sender} ? ${message.date}`;article.append(link,sender);
      if(roles.length){
        const select=document.createElement('select');select.setAttribute('aria-label','Choose the role for this email');
        for(const role of roles){const option=document.createElement('option');option.value=role.id;option.textContent=`${role.title} ? ${role.company||'Company not added'}`;select.append(option);}
        const button=document.createElement('button'),status=document.createElement('p');button.type='button';button.className='text-button';button.textContent='Save this message reference to the selected role';
        button.addEventListener('click',async()=>{button.disabled=true;try{const saved=await connectionApi('/gmail/save-to-role',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({application_id:Number(select.value),message_id:message.id,subject:message.subject.slice(0,2000),sender:message.sender.slice(0,1000),date:message.date.slice(0,1000)})});status.textContent=saved.already_saved?'Already saved to this role.':'Saved to the role?s timeline. Application status was not changed.';}catch(error){status.textContent=error.message;}finally{button.disabled=false;}});
        article.append(select,button,status);
      }else{const note=document.createElement('p');note.textContent='Save an opportunity in Tracker first to attach this correspondence.';article.append(note);}
      ce('gmail-messages').append(article);
    }
    ce('gmail-state').textContent=`Gmail access verified. Up to ${data.limit} results. Review each message and choose a role before saving its reference.`;
  }catch(error){ce('gmail-messages').textContent=error.message;}finally{ce('gmail-search').disabled=false;}
});
loadConnections();
ce('backup-download').addEventListener('click',async()=>{
  ce('backup-download').disabled=true;ce('backup-status').textContent='Creating a private backup. This may take a moment…';
  try{
    const response=await fetch('/api/v1/career/backup',{method:'POST'});
    if(!response.ok)throw new Error('Backup failed. Check PostgreSQL tools and local disk access.');
    const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');
    link.href=url;link.download='career-workspace-backup.zip';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
    ce('backup-status').textContent='Backup created and download requested. Check your downloads folder and keep the archive private.';
  }catch(error){ce('backup-status').textContent=error.message;}finally{ce('backup-download').disabled=false;}
});
