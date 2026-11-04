'use strict';
const support=location.pathname!='/meetings';
let state={documents:[],tickets:[],meetings:[],tasks:[]};
const $=id=>document.getElementById(id);
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function notice(message,error=false){$('notice').textContent=message;$('notice').className=error?'error':'';}
function field(form,label,name,type='text',value=''){const id='f-'+name+'-'+Math.random().toString(36).slice(2);const l=el('label',label);l.htmlFor=id;const n=el(type==='textarea'?'textarea':'input');n.id=id;n.name=name;if(type!=='textarea')n.type=type;n.value=value;form.append(l,n);return n;}
async function request(route,data){const response=await fetch('/api/'+route,{method:'POST',headers:{'Content-Type':'application/json','X-Workspace-Token':state.token},body:JSON.stringify(data)});const result=await response.json();if(!response.ok)throw Error(result.error||'Request failed');return result;}
async function load(){const r=await fetch('/api/state');if(!r.ok)throw Error('Could not load workspace');state=await r.json();render();}
function bind(form,handler){form.addEventListener('submit',async e=>{e.preventDefault();const b=form.querySelector('button[type=submit]');b.disabled=true;notice('Working…');try{await handler(Object.fromEntries(new FormData(form)));await load();notice('Saved to your workspace.');}catch(err){notice(err.message,true);}finally{b.disabled=false;}});}
function submit(form,text){const b=el('button',text);b.type='submit';form.append(b);return b;}
function removeButton(table,id){const b=el('button','Delete','danger');b.type='button';b.onclick=async()=>{if(!confirm('Delete this item? Meeting deletion also removes its tasks.'))return;try{await request('delete',{table,id});await load();notice('Item deleted.');}catch(e){notice(e.message,true);}};return b;}
function details(title,text){const d=el('details');d.append(el('summary',title),el('pre',text));return d;}
$('heading').textContent=support?'Less inbox. More focus.':'Meetings end. Work begins.';
$('subtitle').textContent=support?'Turn your business policies into source-backed reply drafts. Review, refine, and resolve client requests in one place.':'Turn meeting notes into a practical task board. Keep every commitment connected to its original context.';
$(support?'support-link':'meetings-link').classList.add('active');
$('list-title').textContent=support?'Client requests':'Meeting workspace';
const composer=$('composer');
if(support){
 const card=el('section',undefined,'card');card.append(el('h2','New client request'),el('p','Replies quote matching policy excerpts. Nothing is sent automatically.'));
 const form=el('form');field(form,'Client / subject','title').required=true;field(form,'What does the client need?','body','textarea').required=true;submit(form,'Find policy & draft reply');bind(form,async data=>{await request('tickets',data);form.reset();});card.append(form);composer.append(card);
 const knowledge=el('section',undefined,'card');knowledge.append(el('h2','Your knowledge base'),el('p','Add refund rules, service descriptions, or FAQs. Separate topics with blank lines for clearer matches.'));
 const doc=el('form');field(doc,'Policy title','title').required=true;field(doc,'Policy text','body','textarea').required=true;submit(doc,'Add policy');bind(doc,async data=>{await request('documents',data);doc.reset();});knowledge.append(doc,el('div',undefined));knowledge.lastChild.id='documents';composer.append(knowledge);
}else{
 const card=el('section',undefined,'card');card.append(el('h2','Capture a meeting'),el('p','Paste notes or a transcript. Offline mode recognizes “Maya will send proposal” and “Action: Maya: send proposal by 2026-12-15”.'));
 const form=el('form');field(form,'Meeting title','title').required=true;field(form,'Notes / transcript','body','textarea').required=true;
 const label=el('label','Extraction mode');const select=el('select');select.name='ai';select.id='mode';label.htmlFor='mode';for(const [value,text] of [['false','Offline patterns — no setup'],['true','Local AI — requires Ollama model']]){const o=el('option',text);o.value=value;select.append(o);}form.append(label,select);submit(form,'Extract action items');bind(form,async data=>{await request('meetings',{...data,ai:data.ai==='true'});form.reset();});card.append(form);composer.append(card);
 const guide=el('section',undefined,'card');guide.append(el('h2','Take your work with you'),el('p','Export all tasks to a spreadsheet. Review extracted owners and dates before starting work.'));const a=el('a','Download tasks CSV','button secondary');a.href='/api/export';a.download='actionboard-tasks.csv';guide.append(a);composer.append(guide);
}
$('demo').onclick=()=>{const forms=composer.querySelectorAll('form');if(support){forms[0].elements.title.value='Avery / refund request';forms[0].elements.body.value='Can I receive a refund for my unused design package?';forms[1].elements.title.value='Studio refund policy (sample)';forms[1].elements.body.value='Unused design packages qualify for a refund within 14 days of purchase. Include the invoice number when requesting a refund.\n\nCustom work that has already started is not refundable. Contact the studio to discuss remaining deliverables.';notice('Demo filled. Add the sample policy first, then create the client request.');}else{forms[0].elements.title.value='Website launch / planning';forms[0].elements.body.value='Decision: Launch after client approval.\nAction: Maya: Send revised homepage mockups by 2026-12-15.\nArjun will review mobile navigation by 2026-12-16.\nAction: Jordan: Confirm final copy with client.\nNote: The launch date is still tentative.';notice('Demo filled. Choose Extract action items to save this meeting.');}};
$('filter').oninput=render;
function render(){
 const metrics=support?[[state.tickets.filter(t=>t.status==='open').length,'Open requests'],[state.documents.length,'Saved policies'],[state.tickets.filter(t=>t.status==='resolved').length,'Resolved']]:[[state.meetings.length,'Saved meetings'],[state.tasks.filter(t=>t.status!=='done').length,'Active tasks'],[state.tasks.filter(t=>t.status==='done').length,'Completed']];
 $('metrics').replaceChildren(...metrics.map(([number,label])=>{const c=el('div',undefined,'metric');c.append(el('strong',String(number)),el('span',label));return c;}));
 if(support){$('documents').replaceChildren(...state.documents.map(d=>{const item=details(d.title,d.body);item.append(removeButton('documents',d.id));return item;}));}
 const query=$('filter').value.toLowerCase();const items=(support?state.tickets:state.meetings).filter(i=>(i.title+' '+i.body).toLowerCase().includes(query));
 $('list').replaceChildren();if(!items.length){$('list').append(el('div',query?'No items match your search.':support?'Your first client request starts here. Add a policy, then ask a question.':'A clear action plan starts with your first meeting. Paste notes or try the demo.','empty'));return;}
 for(const item of items){const card=el('article',undefined,'card');card.append(el('span',support?item.status:item.mode,'badge'),el('h3',item.title));
 if(support){card.append(el('p',item.body));const form=el('form');field(form,'Reply draft — edit before using','draft','textarea',item.draft).required=true;
 const label=el('label','Request status');const status=el('select');status.name='status';status.id='ticket-'+item.id;label.htmlFor=status.id;for(const s of ['open','resolved']){const o=el('option',s);o.value=s;o.selected=item.status===s;status.append(o);}form.append(label,status);submit(form,'Save reply & status');bind(form,d=>request('ticket',{...d,id:item.id}));card.append(form);
 const sources=JSON.parse(item.sources);if(!sources.length)card.append(el('p','No matching evidence. Review manually.','muted'));for(const s of sources){card.append(el('div',s.title+' · similarity '+s.score+'\n'+s.excerpt,'source'));}card.append(removeButton('tickets',item.id));
 }else{
 const tasks=state.tasks.filter(t=>t.meeting_id===item.id);if(!tasks.length)card.append(el('p','No explicit actions found. Try lines like “Maya will send proposal”, or use local AI extraction.'));
 for(const task of tasks){const form=el('form',undefined,'task');field(form,'Action','title','text',task.title).required=true;const row=el('div',undefined,'row');const owner=el('div'),due=el('div');field(owner,'Owner','owner','text',task.owner);field(due,'Due date','due','date',task.due);row.append(owner,due);form.append(row);const label=el('label','Progress');const status=el('select');status.name='status';status.id='task-'+task.id;label.htmlFor=status.id;for(const s of ['todo','doing','done']){const o=el('option',s);o.value=s;o.selected=task.status===s;status.append(o);}form.append(label,status,el('div',task.evidence,'source'));submit(form,'Save task');bind(form,d=>request('task',{...d,id:task.id}));form.append(removeButton('tasks',task.id));card.append(form);}
 card.append(details('Original meeting notes',item.body),removeButton('meetings',item.id));
 }$('list').append(card);}
}
load().catch(e=>notice(e.message,true));
