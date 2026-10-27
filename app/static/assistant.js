let assistantRoleId=null;
let assistantReview=null;
function resetAssistant(){
  assistantRoleId=null;assistantReview=null;$('assistant-results').hidden=true;
  $('assistant-status').textContent='Choose a CV if needed, then review the saved job description.';
}
async function loadAssistantChoices(){
  try{const resumes=await api('/api/v1/career/resumes');const selected=$('assistant-resume').value;
    $('assistant-resume').replaceChildren();const fallback=document.createElement('option');fallback.value='';fallback.textContent='Use this role’s comparison CV, or my personal CV';$('assistant-resume').append(fallback);
    for(const resume of resumes){const option=document.createElement('option');option.value=resume.id;option.textContent=`${resume.filename} · version #${resume.id}`;$('assistant-resume').append(option);}
    $('assistant-resume').value=selected;
  }catch{$('assistant-status').textContent='CV list could not load. The role’s saved comparison CV can still be used if available.';}
}
$('assistant-review').addEventListener('click',async()=>{
  const roleId=currentApplicationId;if(!roleId)return;
  const savedRole=trackedApplications.find(role=>role.id===roleId);
  if(savedRole&&($('saved-description').value!==(savedRole.job_description||'')||$('job-title').value!==savedRole.title||$('company').value!==savedRole.company)){
    $('assistant-status').textContent='Save your role edits first so the review uses the latest posting, title, and company.';return;
  }
  $('assistant-review').disabled=true;$('assistant-status').textContent='Reviewing saved posting text and CV evidence…';
  $('assistant-results').hidden=true;
  try{
    const resumeId=$('assistant-resume').value;const query=resumeId?`?resume_id=${encodeURIComponent(resumeId)}`:'';
    const data=await api(`/api/v1/career/applications/${roleId}/assistant${query}`);
    if(currentApplicationId!==roleId)return;
    assistantRoleId=roleId;assistantReview=data;$('assistant-results').hidden=false;
    $('assistant-source').textContent=data.resume?`CV used: ${data.resume.filename} · version #${data.resume.id}`:'No CV selected. Add or choose one for evidence-based prompts.';
    $('assistant-actions').replaceChildren();
    for(const action of data.next_actions){const article=document.createElement('article'),text=document.createElement('p'),button=document.createElement('button');text.textContent=action;button.type='button';button.className='text-button';button.textContent='Use as my next action';button.addEventListener('click',()=>{$('next-action').value=action;$('save-status').textContent='Next action filled in. Save the role to keep this change.';$('save-form').scrollIntoView({block:'start'});});article.append(text,button);$('assistant-actions').append(article);}
    $('assistant-evidence').replaceChildren();
    if(!data.evidence.length)$('assistant-evidence').textContent='No shared dictionary skills were identified. Review the CV and posting manually; this is not a rejection recommendation.';
    for(const item of data.evidence){const article=document.createElement('article'),heading=document.createElement('h4');heading.textContent=item.skill;article.append(heading);for(const snippet of item.snippets){const quote=document.createElement('blockquote');quote.textContent=snippet;article.append(quote);}$('assistant-evidence').append(article);}
    $('assistant-gaps').textContent=data.missing_in_cv.length?`Not found in this CV: ${data.missing_in_cv.join(', ')}. Check for omitted experience before treating these as learning gaps.`:'No gaps identified within the recognized skill dictionary.';
    $('assistant-requirements').replaceChildren();
    for(const requirement of data.requirements){const article=document.createElement('article'),heading=document.createElement('h4'),action=document.createElement('p');heading.textContent=requirement.topic;action.textContent=requirement.action;article.append(heading);for(const excerpt of requirement.excerpts){const quote=document.createElement('blockquote');quote.textContent=excerpt;article.append(quote);}article.append(action);$('assistant-requirements').append(article);}
    $('assistant-priorities').textContent=data.preferences.priorities?`Your saved priorities: ${data.preferences.priorities}. Compare these with what the employer actually offers.`:'Save what matters to you in Search so you can consider it alongside each opportunity.';
    $('assistant-questions').replaceChildren();for(const question of data.interview_questions){const li=document.createElement('li');li.textContent=question;$('assistant-questions').append(li);}
    $('assistant-subject').value=data.email_draft.subject;$('assistant-body').value=data.email_draft.body;
    $('assistant-method').textContent=data.method;$('assistant-status').textContent='Review ready. It uses the saved role; save any posting edits before reviewing again.';
  }catch(error){$('assistant-status').textContent=`Could not review this role: ${error.message}`;}
  finally{$('assistant-review').disabled=false;}
});
async function saveAssistantNote(title,body){
  if(!assistantRoleId||assistantRoleId!==currentApplicationId)throw new Error('Review the current role first.');
  const roleId=assistantRoleId;
  await api(`/api/v1/career/applications/${roleId}/events`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'note',title:title.slice(0,200),body})});
  if(currentApplicationId!==roleId)return;
  await loadDossier(roleId,$('job-title').value);
  $('dossier-status').textContent='Saved preparation to this role’s timeline. Nothing was sent.';
}
$('assistant-save-prep').addEventListener('click',async()=>{try{if(!assistantReview)throw new Error('Review this role first.');await saveAssistantNote('Interview preparation prompts',assistantReview.interview_questions.join('\n\n'));}catch(error){$('assistant-status').textContent=error.message;}});
$('assistant-save-draft').addEventListener('click',async()=>{try{if(!$('assistant-subject').value.trim()||!$('assistant-body').value.trim())throw new Error('Add a subject and message first.');await saveAssistantNote(`Draft: ${$('assistant-subject').value}`,$('assistant-body').value);}catch(error){$('assistant-status').textContent=error.message;}});
