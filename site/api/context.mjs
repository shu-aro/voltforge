// Retrieve a few source-labelled passages and compact the actual experiment without inventing values.
const tokens = text => new Set(String(text).toLowerCase().match(/[a-z0-9]+/g) || []);
export function retrieve(question, knowledge, limit=3) {
  const query=tokens(question);
  return knowledge.map((doc,index)=>({doc,index,score:[...tokens(doc.title+' '+doc.tags)].filter(t=>query.has(t)).length*3+[...tokens(doc.text)].filter(t=>query.has(t)).length}))
    .filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.index-b.index).slice(0,limit).map(x=>({id:x.doc.id,title:x.doc.title,text:x.doc.text,source:x.doc.source}));
}
const round = value => typeof value==='number'? Math.round(value*1e5)/1e5:value;
function clean(value) {
  if(Array.isArray(value)) return value.map(clean);
  if(value && typeof value==='object') return Object.fromEntries(Object.entries(value).filter(([k])=>!['trace','samples','rows','model_cards','thermal_provenance','thermal_assumptions','source','listings'].includes(k)).map(([k,v])=>[k,clean(v)]));
  return round(value);
}
function graph(value){
  if(!value) return null;
  return {name:value.name,cells:value.cells,connections:value.connections,output:value.output,thermal:value.thermal};
}
function saved(test){
  if(!test) return null;
  const summary=test.summary||{};
  return clean({id:test.id,name:test.name,status:test.status,current:test.current,model_hash:test.model_hash,software_hash:test.software_hash,
    settings:test.settings,summary:{metrics:summary.metrics,checks:summary.checks,assessment:summary.assessment,verification:summary.verification,
    thermal_available:summary.thermal_available,operating_limit_coverage:summary.operating_limit_coverage,design_warnings:summary.design_warnings},stop:test.stop});
}
export function prepare(prompt, knowledge) {
  const input=JSON.parse(prompt),c=input.context||{},conversation=input.conversation||[];
  if(!Array.isArray(conversation)||conversation.length<1||conversation.length>16||conversation.at(-1).role!=='user'||conversation.some(m=>!['user','assistant'].includes(m.role)||typeof m.content!=='string'||m.content.length>4000)) throw Error('Invalid conversation');
  const context=clean({editable_design:graph(c.editable_design),editable_settings:c.editable_settings,edit_revision:c.edit_revision,selected_component:c.selected_component,
    available_models:(c.available_models||[]).map(m=>({key:m.key,name:m.name,family:m.family,capacity_Ah:m.capacity_Ah,temperature_range_C:m.temperature_range_C,soc_range_pct:m.soc_range_pct,operating_limits:m.operating_limits,status:m.status})),
    test:saved(c.test),comparison:c.comparison?{...c.comparison,tests:c.comparison.tests?.map(saved)}:null,
    investigation:c.investigation?{scope:c.investigation.scope,condition:c.investigation.condition,complete:c.investigation.complete,cases:c.investigation.cases?.map(x=>({name:x.name,cell_count:x.cell_count,outcome:x.outcome,sizing:x.sizing,metrics:x.metrics}))}:null});
  const passages=retrieve(conversation.at(-1).content,knowledge);
  // Old turns are lower priority than the current engineering context.
  const recent=conversation.slice(-6);
  const payload={context,conversation:recent,retrieved_sources:passages,context_note:'Some detailed arrays and older turns are omitted. Ask for a saved experiment if the required number is absent. Never infer a missing result.'};
  if(JSON.stringify(payload).length>18000) {
    if(context.comparison) context.comparison={tests:context.comparison.tests,differences:context.comparison.differences};
    if(context.investigation?.cases?.length>8) context.investigation.cases=context.investigation.cases.slice(0,8);
    payload.conversation=conversation.slice(-2);
  }
  if(JSON.stringify(payload).length>18000) throw Error('Context too large');
  return payload;
}
