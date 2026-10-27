"""Evidence-based preparation prompts, without generated experience claims."""
import re
from app.services.text_cleaner import clean_text
from app.services.skill_extractor import extract_skills
from app.services.skill_matcher import match_skills


REQUIREMENT_PATTERNS={
    'Language':r'\b(?:japanese|english|jlpt|toeic|bilingual|native|fluent)\b|日本語|英語',
    'Location and work style':r'\b(?:remote|hybrid|onsite|on-site|relocat\w*|tokyo|japan|office)\b|勤務地|リモート',
    'Work authorization':r'\b(?:visa|sponsor\w*|work authorization|right to work)\b|ビザ|在留資格',
    'Experience and qualifications':r'\b(?:years?|degree|master|phd|bachelor|experience|required|must)\b|必須|経験',
    'Compensation':r'\b(?:salary|compensation|jpy|usd|yen|bonus|equity)\b|年収|給与|万円',
}


def build_review(application,resume,description,preferences):
    resume_text=(resume.extracted_text or '') if resume else ''
    resume_skills=extract_skills(clean_text(resume_text))
    job_skills=extract_skills(clean_text(description))
    overlap=match_skills(resume_skills,job_skills)
    snippets=[line.strip() for line in re.split(r'[\n.!?]+',resume_text) if line.strip()]
    evidence=[]
    for skill in overlap['matched_skills']:
        matches=[line[:500] for line in snippets if skill in extract_skills(clean_text(line))][:2]
        evidence.append({'skill':skill,'snippets':matches})
    requirement_lines=[line.strip() for line in re.split(r'[\n;]+|(?<=[.!?])\s+',description) if line.strip()]
    requirements=[]
    for label,pattern in REQUIREMENT_PATTERNS.items():
        excerpts=[line[:500] for line in requirement_lines if re.search(pattern,line,re.I)][:3]
        requirements.append({'topic':label,'excerpts':excerpts,
                             'action':'Read these excerpts and confirm what is mandatory versus preferred.' if excerpts
                             else 'Not identified automatically. Check the posting or ask the recruiter.'})
    stage_actions={
        'saved':['Check the full posting against your priorities before deciding to apply.',
                 'Prepare a tailored CV using the evidence below; add only experience you actually have.'],
        'applied':['Record the exact CV and cover letter submitted in this role’s documents.',
                   'Review any employer response and set a specific follow-up date.'],
        'interview':['Prepare examples for the interview questions below.',
                     'Record the interview time, participants, and questions you want to ask.'],
        'offer':['Record the written offer and clarify unresolved conditions before making a decision.'],
        'closed':['Record the outcome and what you learned, then keep useful preparation for future roles.'],
    }
    actions=stage_actions.get(application.status,stage_actions['saved']).copy()
    if not description:actions.insert(0,'Save the full job description so this review can use the actual requirements.')
    if not resume:actions.append('Choose or upload a CV to identify evidence for this opportunity.')
    if overlap['missing_skills']:
        actions.append('Review skills not found in this CV. Separate experience omitted from the document from genuine learning gaps.')
    questions=[f'Describe a real project where you used {skill}. What did you personally contribute, how did you evaluate it, and what trade-offs did you make?'
               for skill in overlap['matched_skills'][:4]]
    questions.extend(['Which responsibilities would you own in the first three months?',
                      'How does the team evaluate successful work, and what support is available for learning?'])
    company=application.company or '[Company]'
    if application.status=='saved':
        subject=f'Question about {application.title}'
        body=f'Dear [Recruiter name],\n\nI am considering the {application.title} opportunity at {company}. Could you clarify [specific question about the role or requirements]?\n\nThank you for your time.\n[Your name]'
    else:
        subject=f'Follow-up: {application.title}'
        body=f'Dear [Recruiter name],\n\nI am following up regarding the {application.title} opportunity at {company}. I would appreciate any update on the next steps. Please let me know if there is additional information I can provide.\n\nThank you for your time.\n[Your name]'
    return {'application_id':application.id,'resume':{'id':resume.id,'filename':resume.original_filename} if resume else None,
            'job_skills':job_skills,'evidence':evidence,'missing_in_cv':overlap['missing_skills'],
            'requirements':requirements,'preferences':preferences,'next_actions':actions,
            'interview_questions':questions,'email_draft':{'subject':subject,'body':body},
            'method':'Dictionary skill evidence and deterministic templates. No external LLM is used. '
                     'No fit prediction or factual verification of CV claims is performed.'}
