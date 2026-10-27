// Executes the real classic page scripts against a small DOM test double.
// This tests async behavior and script integration, not browser layout or CSS.
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'app/static/index.html'),'utf8');
const scriptPaths=[...html.matchAll(/<script src="([^"]+)"/g)].map(match=>path.join(root,'app',match[1]));
class Element{
  constructor(id=''){this.id=id;this.children=[];this.handlers={};this._value='';this._text='';this.hidden=false;this.disabled=false;this.files=[];this.dataset={};}
  get value(){return this._value;}set value(value){this._value=String(value??'');}
  get textContent(){return this._text;}set textContent(value){this._text=String(value);this.children=[];}
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this._text='';this.children=items;}
  addEventListener(name,callback){(this.handlers[name]??=[]).push(callback);}
  setAttribute(name,value){this[name]=value;}
  removeAttribute(name){delete this[name];}
  querySelector(){return new Element();}
  reset(){} scrollIntoView(){} remove(){} click(){}
}
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return{promise,resolve,reject};}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function createHarness(){
  const elements=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(match=>[match[1],new Element(match[1])]));
  const panels=[...html.matchAll(/data-view="([^"]+)"/g)].map(match=>Object.assign(new Element(),{dataset:{view:match[1]}}));
  const navs=[...html.matchAll(/data-nav="([^"]+)"/g)].map(match=>Object.assign(new Element(),{dataset:{nav:match[1]}}));
  elements.get('tracker-filter').value='all';elements.get('application-status').value='saved';
  const calls=[],routes=new Map();
  function defaultResponse(url){
    if(url.endsWith('/resumes')||url.endsWith('/applications'))return[];
    if(url.endsWith('/profile'))return{configured:false};
    if(url.endsWith('/direction'))return{role:'',location:'',priorities:''};
    if(url.includes('/today?'))return{date:'2026-10-27',counts:{saved:0,applied:0,interview:0,offer:0,closed:0},due:[],upcoming:[],needs_next_action:[],scheduled:[]};
    if(url.endsWith('/integrations/status'))return{github:'',linkedin:'',gmail:'setup-required'};
    if(url.endsWith('/discovery/sources'))return{sources:[],example_default:false};
    if(url.endsWith('/dossier'))return{events:[],contacts:[],documents:[]};
    if(url.includes('/rag/recommendations/'))return{recommendations:[]};
    if(url.includes('/career/review/'))return{evidence:[],gaps:[],checklist:[],bullet_template:''};
    throw Error(`Unmocked request: ${url}`);
  }
  const location={hash:''};
  const context=vm.createContext({console,URL,URLSearchParams,setTimeout,clearTimeout,
    location,history:{replaceState(_a,_b,hash){location.hash=hash;}},window:{addEventListener(){}},
    localStorage:{getItem(){return null;},setItem(){}},FormData:class{append(){}},
    document:{getElementById:id=>elements.get(id)||null,createElement:()=>new Element(),
      querySelectorAll:selector=>selector==='[data-view]'?panels:navs,body:new Element()},
    fetch:async(url,options={})=>{
      const call={url,options};calls.push(call);
      const route=routes.get(`${options.method||'GET'} ${url}`);
      const data=await(route?route(call):defaultResponse(url));
      if(data?.isHttpReply)return{ok:data.status>=200&&data.status<300,status:data.status,json:async()=>data.data};
      return{ok:true,status:200,json:async()=>data};
    }
  });
  for(const file of scriptPaths)new vm.Script(fs.readFileSync(file,'utf8'),{filename:file}).runInContext(context);
  return{context,elements,calls,routes,panels,
    el:id=>elements.get(id),
    evaluate:source=>vm.runInContext(source,context),
    fire:async(id,event='submit')=>{for(const callback of elements.get(id).handlers[event]||[])await callback({preventDefault(){}});},
    delay(url,method='GET'){const wait=deferred();routes.set(`${method} ${url}`,()=>wait.promise);return wait;}
  };
}
function role(id,match=null){return{id,version:1,match_result_id:match,title:`Role ${id}`,company:`Company ${id}`,url:'',status:'saved',notes:`Notes ${id}`,follow_up:null,job_description:`Description for role ${id}`,next_action:''};}
function match(id,score){return{match_result_id:id,final_match_score:score,skill_match_percentage:score,text_similarity_percentage:score,matched_skills:['python'],missing_skills:[]};}
function text(element){return[element.textContent,...element.children.filter(child=>child&&typeof child==='object').map(text)].join(' ');}
module.exports={createHarness,role,match,text,flush};
