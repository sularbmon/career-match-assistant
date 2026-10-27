let dossierApplicationId=null;
let dossierRequest=0;
function clearDossier(){
  resetAssistant();
  dossierApplicationId=null;dossierRequest++;
  $('dossier-content').hidden=true;$('dossier-empty').hidden=false;
  $('dossier-empty').textContent='Save or open a role to keep its correspondence, interview preparation, and application documents together.';
  $('dossier-title').textContent='Opportunity history';$('dossier-status').textContent='';
}
async function loadDossier(id,title){
  const request=++dossierRequest;
  if(dossierApplicationId!==id){for(const form of ['event-form','contact-form','document-form'])$(form).reset();resetAssistant();loadAssistantChoices();}
  dossierApplicationId=id;$('dossier-title').textContent=`History · ${title}`;
  $('dossier-content').hidden=true;$('dossier-empty').hidden=false;$('dossier-empty').textContent='Loading opportunity history…';
  try{
    const data=await api(`/api/v1/career/applications/${id}/dossier`);
    if(request!==dossierRequest||currentApplicationId!==id)return;
    $('dossier-content').hidden=false;$('dossier-empty').hidden=true;
    $('role-timeline').replaceChildren();
    if(!data.events.length)$('role-timeline').textContent='No history yet. Add a note or your next interview.';
    for(const event of data.events){
      const article=document.createElement('article'),heading=document.createElement('h4'),meta=document.createElement('small'),body=document.createElement('p');
      heading.textContent=event.title;meta.textContent=`${event.kind} · ${new Date(event.created_at).toLocaleString()}${event.done?' · Completed':''}`;body.textContent=event.body;
      article.append(heading,meta,body);
      if(event.scheduled_for){const time=document.createElement('p');time.textContent=`Scheduled: ${new Date(event.scheduled_for).toLocaleString()}`;article.append(time);}
      if(['task','interview'].includes(event.kind)){
        const button=document.createElement('button');button.type='button';button.className='text-button';button.textContent=event.done?'Reopen item':'Mark completed';
        button.addEventListener('click',async()=>{button.disabled=true;try{await api(`/api/v1/career/applications/${id}/events/${event.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:event.kind,title:event.title,body:event.body,scheduled_for:event.scheduled_for,done:!event.done})});if(currentApplicationId===id)await loadDossier(id,$('job-title').value);await loadToday();}catch(error){$('dossier-status').textContent=error.message;button.disabled=false;}});article.append(button);
      }
      $('role-timeline').append(article);
    }
    $('role-contacts').replaceChildren();
    for(const contact of data.contacts){const article=document.createElement('article'),name=document.createElement('h4'),detail=document.createElement('p'),notes=document.createElement('p');name.textContent=contact.name;detail.textContent=[contact.role,contact.email].filter(Boolean).join(' · ');notes.textContent=contact.notes;article.append(name,detail,notes);$('role-contacts').append(article);}
    $('role-documents').replaceChildren();
    for(const documentInfo of data.documents){const article=document.createElement('article'),link=document.createElement('a'),meta=document.createElement('small');link.href=`/api/v1/career/applications/${id}/documents/${documentInfo.id}`;link.textContent=`Download ${documentInfo.label}`;meta.textContent=`${documentInfo.filename} · ${new Date(documentInfo.created_at).toLocaleDateString()}`;article.append(link,meta);$('role-documents').append(article);}
  }catch(error){if(request===dossierRequest){$('dossier-empty').textContent=`History could not load: ${error.message}. Open the role again to retry.`;}}
}
function handleDossierForm(formId,save){
  $(formId).addEventListener('submit',async event=>{
    event.preventDefault();const id=dossierApplicationId;
    if(!id||id!==currentApplicationId){$('dossier-status').textContent='Save or open a role first.';return;}
    const button=$(formId).querySelector('button[type=submit]');button.disabled=true;
    try{await save(id);if(currentApplicationId===id){$(formId).reset();$('dossier-status').textContent='Saved to this opportunity.';await loadDossier(id,$('job-title').value);}await loadToday();}
    catch(error){$('dossier-status').textContent=`Could not save: ${error.message}`;}
    finally{button.disabled=false;}
  });
}
handleDossierForm('event-form',id=>api(`/api/v1/career/applications/${id}/events`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:$('event-kind').value,title:$('event-title').value,body:$('event-body').value,scheduled_for:$('event-date').value?new Date($('event-date').value).toISOString():null})}));
handleDossierForm('contact-form',id=>api(`/api/v1/career/applications/${id}/contacts`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('contact-name').value,email:$('contact-email').value,role:$('contact-role').value,notes:$('contact-notes').value})}));
handleDossierForm('document-form',id=>{const file=$('document-file').files[0];if(!file||file.size>10*1024*1024)throw new Error('Choose a file of 10 MB or smaller.');const body=new FormData();body.append('file',file);body.append('label',$('document-label').value);return api(`/api/v1/career/applications/${id}/documents`,{method:'POST',body});});
