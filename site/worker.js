// Runs the same Python engine as the local app, using WebAssembly.
importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');

async function start() {
  postMessage({progress: 'Loading the real simulator into your browser. The first time takes about 15 seconds.'});
  const pyodide = await loadPyodide();
  postMessage({progress:'Loading numerical libraries…'});
  await pyodide.loadPackage(['numpy', 'scipy', 'pandas']);
  postMessage({progress:'Loading the battery models…'});
  const archive = await fetch('./engine.zip').then((r) => r.arrayBuffer());
  pyodide.unpackArchive(archive, 'zip', {extractDir: '/home/pyodide/volt'});
  pyodide.runPython("import sys; sys.path[:0] = ['/home/pyodide/volt', '/home/pyodide/volt/src']");
  postMessage({progress: 'Starting your private workspace…'});
  const bridge = pyodide.pyimport('bridge');
  // Configuration lookup only. No provider inference, prompt, or key is sent.
  const {readAIStatus} = await import('./ai-status.mjs');
  const status = await readAIStatus();
  bridge.configure_ai(status.available===true, status.provider||'Groq');
  return {pyodide, bridge};
}

async function ask(prompt) {
  try {
    const response = await fetch('/api/ai', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({prompt})});
    const value = await response.json();
    return response.ok ? {text: value.text} : {error: value.error || 'The AI could not answer. Please try again.'};
  } catch {
    return {error: 'The AI could not be reached. Check your connection and try again.'};
  }
}

const ready = start();
let queue=Promise.resolve();
onmessage = ({data}) => { queue=queue.then(async()=>{
try{
  const {pyodide, bridge} = await ready;
  if (data.path.startsWith('/api/studio/export/')) {
    await pyodide.loadPackage('matplotlib');
    bridge.real_plots();
  }
  const call = (reply) => JSON.parse(bridge.handle(data.path, data.method, data.body, reply ? JSON.stringify(reply) : null));
  let answer = call(null);
  if (answer.ai_prompt) answer = call(await ask(answer.ai_prompt));
  postMessage({id: data.id, ...answer});
}catch{postMessage({id:data.id,status:500,type:'application/json',body:JSON.stringify({status:'error',error:{code:'runtime_error',message:'This action could not finish. Download a design backup before retrying.'}}),binary:false});}
});};
