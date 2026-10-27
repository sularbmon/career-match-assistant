"""Public ATS job-board reads. Never fetch a user-supplied URL."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from html import unescape
from html.parser import HTMLParser
import re
import httpx

MAX_POSTINGS=500


class PlainText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag in ('p','br','li','div','h2','h3'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag in ('p','li','div'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)


def plain_text(value):
    parser=PlainText();parser.feed(unescape(unescape(value or '')))
    return re.sub(r'\n\s*\n+','\n\n',''.join(parser.parts)).strip()


def checked_json(response):
    response.raise_for_status()
    if len(response.content)>12*1024*1024:raise ValueError('Provider response is too large')
    return response.json()


def fetch_board(source):
    provider,board=source['provider'],source['board']
    jobs=[];truncated=False
    with httpx.Client(timeout=20,follow_redirects=False,headers={'User-Agent':'CareerMatch-Personal/1.0'}) as client:
        if provider=='lever':
            for skip in range(0,MAX_POSTINGS,100):
                batch=checked_json(client.get(f'https://api.lever.co/v0/postings/{board}',params={'mode':'json','limit':100,'skip':skip}))
                if not isinstance(batch,list):raise ValueError('Unexpected Lever response')
                jobs.extend(batch)
                if len(batch)<100:break
            else:truncated=True
            normalized=[]
            for job in jobs:
                categories=job.get('categories') or {}
                sections=[job.get('openingPlain') or plain_text(job.get('opening','')),
                          job.get('descriptionPlain') or plain_text(job.get('description','')),
                          job.get('descriptionBodyPlain') or plain_text(job.get('descriptionBody',''))]
                for section in job.get('lists',[]):sections.extend([section.get('text',''),plain_text(section.get('content',''))])
                sections.append(job.get('additionalPlain') or plain_text(job.get('additional','')))
                # Identical plain descriptions can appear in multiple API fields.
                description='\n\n'.join(dict.fromkeys(part for part in sections if part))
                normalized.append({'id':str(job['id']),'title':job['text'],'location':categories.get('location',''),
                    'workplace':job.get('workplaceType',''),'url':job['hostedUrl'],'description':description[:50000],
                    'provider':provider,'board':board,'company':source['name']})
        elif provider=='greenhouse':
            payload=checked_json(client.get(f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs',params={'content':'true'}))
            jobs=payload['jobs'];truncated=len(jobs)>MAX_POSTINGS
            normalized=[{'id':str(job['id']),'title':job['title'],'location':(job.get('location') or {}).get('name',''),
                'workplace':'','url':job['absolute_url'],'description':plain_text(job.get('content',''))[:50000],
                'provider':provider,'board':board,'company':source['name']} for job in jobs[:MAX_POSTINGS]]
        else:raise ValueError('Unsupported provider')
    # External links are for opening in the browser, never server-side fetching.
    normalized=[job for job in normalized if re.match(r'^https://[^\s]+$',job['url'])]
    return normalized,truncated


def search_sources(sources,keywords,location):
    groups=[re.findall(r'[\w+#.-]+',part.casefold()) for part in keywords.split(',') if part.strip()]
    jobs=[];statuses=[]
    def read(source):
        try:
            postings,truncated=fetch_board(source)
            return source,postings,truncated,None
        except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
            status='Source unavailable; check board slug or try later.'
            if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code==404:status='Board not found; check its provider and slug.'
            return source,[],False,status
    with ThreadPoolExecutor(max_workers=4) as pool:
        for source,postings,truncated,error in pool.map(read,sources):
            statuses.append({'provider':source['provider'],'board':source['board'],'name':source['name'],
                             'checked':len(postings),'truncated':truncated,'error':error})
            for job in postings:
                text=f"{job['title']} {job['description']}".casefold()
                def contains(word):
                    return bool(re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)',text)) if len(word)<=2 and word.isascii() else word in text
                if groups and not any(all(contains(word) for word in group) for group in groups):continue
                if location and location.casefold() not in f"{job['location']} {job['workplace']}".casefold():continue
                jobs.append(job)
    jobs.sort(key=lambda job:(job['company'].casefold(),job['title'].casefold(),job['id']))
    unique={f"{job['provider']}:{job['board']}:{job['id']}":job for job in jobs}
    results=list(unique.values())
    return {'jobs':results[:50],'total_matches':len(results),'sources':statuses,
            'checked_at':datetime.now(timezone.utc).isoformat(),
            'limited':len(results)>50,'method':'Keyword filtering over selected public company boards; not a complete job-market search or a fit ranking.'}
