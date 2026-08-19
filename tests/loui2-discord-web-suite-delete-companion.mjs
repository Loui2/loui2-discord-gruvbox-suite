#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const SUITE_PATH = new URL("../tampermonkey/loui2-discord-web-suite.user.js", import.meta.url);
const originalSuite = fs.readFileSync(SUITE_PATH, "utf8");
const close = "})();";
const closeAt = originalSuite.lastIndexOf(close);
assert.notEqual(closeAt, -1, "suite IIFE close missing");
const suite = `${originalSuite.slice(0, closeAt)}
  pageWindow.__loui2DeleteCompanionFixture = {requestDeleteCompanion, cleanupSuite};
${originalSuite.slice(closeAt)}`;
const encodedSuite = Buffer.from(suite).toString("base64");
const html = `<!doctype html><html><head><meta charset="utf-8"><title>companion fixture</title>
<script>
window.__gmValues=new Map([['forceFullWidthMobileLayout',false]]);window.__gmMenus=new Map();window.__gmNextId=1;
window.__gmRequests=[];window.__gmAbortCallback=true;window.__gmMode='normal';
window.GM_addStyle=()=>({remove(){}});
window.GM_getValue=(key,fallback)=>window.__gmValues.has(key)?window.__gmValues.get(key):fallback;
window.GM_setValue=(key,value)=>window.__gmValues.set(key,value);
window.GM_addValueChangeListener=()=>window.__gmNextId++;
window.GM_removeValueChangeListener=()=>{};
window.GM_registerMenuCommand=(label,callback)=>{const id=window.__gmNextId++;window.__gmMenus.set(id,{label,callback});return id};
window.GM_unregisterMenuCommand=(id)=>window.__gmMenus.delete(id);
window.GM_getTab=(callback)=>callback({tabTitleMode:'thread'});
window.GM_saveTab=(_tab,callback)=>callback?.();
window.GM_openInTab=()=>({close(){}});
window.GM_xmlhttpRequest=(options)=>{
  const entry={options,abortCount:0,mode:window.__gmMode};
  const handle={abort(){entry.abortCount+=1;if(window.__gmAbortCallback)options.onabort?.();}};
  entry.handle=handle;window.__gmRequests.push(entry);
  if(entry.mode==='undefined')return undefined;
  if(entry.mode==='nonabortable')return {};
  return handle;
};
window.alert=()=>{};window.confirm=()=>false;window.prompt=()=>null;
</script></head><body><script>{const bytes=Uint8Array.from(atob('${encodedSuite}'),c=>c.charCodeAt(0));(0,eval)(new TextDecoder().decode(bytes));}</script></body></html>`;

const server = http.createServer((_request, response) => {
  const body = Buffer.from(html);
  response.writeHead(200, {"content-type":"text/html; charset=utf-8","content-length":body.length});
  response.end(body);
});
await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
const fixtureUrl = `http://127.0.0.1:${server.address().port}/channels/1/2`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "loui2-delete-companion-"));
const chromium = spawn(process.env.CHROMIUM_BIN || "chromium", [
  "--headless", "--no-sandbox", "--disable-gpu", "--no-first-run", "--remote-debugging-port=0",
  "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
  `--user-data-dir=${profile}`, fixtureUrl,
], {stdio:["ignore","ignore","pipe"]});
let stderr="";chromium.stderr.on("data",chunk=>{stderr+=String(chunk)});
const portFile=path.join(profile,"DevToolsActivePort");
for(let i=0;i<120&&!fs.existsSync(portFile);i+=1)await new Promise(resolve=>setTimeout(resolve,50));
if(!fs.existsSync(portFile))throw new Error(`DevToolsActivePort unavailable: ${stderr}`);
const [port]=fs.readFileSync(portFile,"utf8").trim().split(/\r?\n/);
let target;
for(let i=0;i<120;i+=1){
  const targets=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  target=targets.find(item=>item.type==="page"&&item.url.startsWith(fixtureUrl));
  if(target)break;
  await new Promise(resolve=>setTimeout(resolve,50));
}
if(!target)throw new Error("fixture target unavailable");
const socket=new WebSocket(target.webSocketDebuggerUrl);let nextId=0;const pending=new Map();
socket.addEventListener("message",event=>{const message=JSON.parse(String(event.data));if(!message.id)return;const entry=pending.get(message.id);if(!entry)return;pending.delete(message.id);message.error?entry.reject(new Error(message.error.message)):entry.resolve(message.result)});
await new Promise((resolve,reject)=>{socket.addEventListener("open",resolve,{once:true});socket.addEventListener("error",reject,{once:true})});
const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++nextId;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}))});

try {
  let evaluated;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      evaluated=await call("Runtime.evaluate",{awaitPromise:true,returnByValue:true,expression:`(async()=>{
    const delay=()=>new Promise(resolve=>setTimeout(resolve,0));
    for(let i=0;i<100&&!window.__loui2DeleteCompanionFixture;i+=1)await delay();
    const api=window.__loui2DeleteCompanionFixture;
    if(!api)return {missing:true};
    const requests=window.__gmRequests;
    const snapshot=(entry)=>({method:entry.options.method,url:entry.options.url,headers:entry.options.headers,data:Object.prototype.hasOwnProperty.call(entry.options,'data')?entry.options.data:'__absent__',timeout:entry.options.timeout,anonymous:entry.options.anonymous,optionKeys:Object.keys(entry.options)});
    const safeError=(error)=>({name:error?.name,message:error?.message,code:error?.code,status:error?.status,keys:Object.keys(error||{}),text:String(error)});
    const settleLoad=async(method,path,body,response)=>{const promise=api.requestDeleteCompanion(method,path,body);const entry=requests.at(-1);entry.options.onload(response);return {request:snapshot(entry),value:await promise,abortCount:entry.abortCount};};

    const health=await settleLoad('GET','/healthz',undefined,{status:200,responseText:'{"ok":true}'});
    const preview=await settleLoad('POST','/v1/deletions/preview',{channelId:'123',count:7},{status:201,responseText:'{"preview":7}'});
    const confirm=await settleLoad('POST','/v1/deletions/11111111-1111-4111-8111-111111111111/confirm',{}, {status:200,responseText:'{}'});
    const operation=await settleLoad('GET','/v1/deletions/11111111-1111-4111-8111-111111111111',undefined,{status:204,responseText:''});

    const rejected=[];
    for(const [method,path,body] of [['DELETE','/healthz'],['POST','/healthz'],['GET','/v1/deletions/preview'],['GET','http://127.0.0.1:18766/healthz'],['GET','/v1/deletions/'],['GET','/v1/deletions/bad.id'],['GET','/v1/deletions/op_pending'],['GET','/v1/deletions/'+('g'.repeat(36))],['GET','/v1/deletions/'+('a'.repeat(129))],['GET','/v1/deletions/good/extra'],['GET','/healthz?x=1'],['POST','/v1/delete-my-messages/preview',{channelId:'123',count:1}],['POST','/v1/delete-my-messages/confirm',{}],['GET','/v1/operations/11111111-1111-4111-8111-111111111111'],['POST','/v1/deletions/11111111-1111-4111-8111-111111111111/confirm',{operationId:'11111111-1111-4111-8111-111111111111'}],['POST','/v1/deletions/preview',{channelId:'123'}]]){
      const before=requests.length;
      try{await api.requestDeleteCompanion(method,path,body);}catch(error){rejected.push({method,path,before,after:requests.length,error:safeError(error)});}
    }

    const failure=async(kind,response)=>{const promise=api.requestDeleteCompanion('GET','/healthz');const entry=requests.at(-1);entry.options[kind](response);try{await promise;return {resolved:true};}catch(error){return {error:safeError(error),abortCount:entry.abortCount};}};
    const httpError=await failure('onload',{status:500,responseText:'SECRET_TOKEN https://discord.com/channels/current'});
    const malformed=await failure('onload',{status:200,responseText:'{SECRET_TOKEN'});
    const oversized=await failure('onload',{status:200,responseText:'x'.repeat(1000001)});
    const networkError=await failure('onerror',{status:0,responseText:'SECRET_TOKEN'});
    const timeoutError=await failure('ontimeout',{status:0,responseText:'SECRET_TOKEN'});
    const abortError=await failure('onabort',{status:0,responseText:'SECRET_TOKEN'});

    const hostileLoad=async(property,secret)=>{
      const promise=api.requestDeleteCompanion('GET','/healthz');
      const entry=requests.at(-1);
      const response=property==='status'
        ? Object.defineProperty({},'status',{get(){throw new Error(secret)}})
        : Object.defineProperties({}, {status:{value:200},responseText:{get(){throw new Error(secret)}}});
      let callbackThrew=false;
      try{entry.options.onload(response);}catch{callbackThrew=true;}
      let outcome;
      try{await Promise.race([promise,new Promise((_,reject)=>setTimeout(()=>reject(new Error('hostile response promise stayed pending')),50))]);outcome={resolved:true};}
      catch(error){outcome={error:safeError(error)};}
      return {callbackThrew,outcome,serialized:JSON.stringify(outcome)};
    };
    const hostileStatus=await hostileLoad('status','HOSTILE_STATUS_SECRET_91a7');
    const hostileText=await hostileLoad('responseText','HOSTILE_TEXT_SECRET_42bc');

    window.__gmMode='normal';
    const normalPromise=api.requestDeleteCompanion('POST','/v1/deletions/preview',{channelId:'123',count:1});
    const normalEntry=requests.at(-1);
    window.__gmMode='undefined';
    const undefinedPromise=api.requestDeleteCompanion('GET','/healthz');
    const undefinedEntry=requests.at(-1);
    window.__gmMode='nonabortable';
    const nonabortablePromise=api.requestDeleteCompanion('GET','/v1/deletions/22222222-2222-4222-8222-222222222222');
    const nonabortableEntry=requests.at(-1);
    const settlementCounts=[0,0,0];
    const pendingPromises=[normalPromise,undefinedPromise,nonabortablePromise].map((promise,index)=>promise.then(
      value=>{settlementCounts[index]+=1;return {resolved:true,value}},
      error=>{settlementCounts[index]+=1;return {error:safeError(error)}},
    ));
    const abortsBefore=requests.reduce((sum,entry)=>sum+entry.abortCount,0);
    window.__gmAbortCallback=false;
    api.cleanupSuite();
    const postCleanupRequestCountBefore=requests.length;
    let postCleanupError;try{await api.requestDeleteCompanion('GET','/healthz');}catch(error){postCleanupError=safeError(error);}
    const postCleanupRequestCountAfter=requests.length;
    const cleanupResults=await Promise.race([Promise.all(pendingPromises),new Promise((_,reject)=>setTimeout(()=>reject(new Error('cleanup promises stayed pending')),50))]);
    for(const entry of [normalEntry,undefinedEntry,nonabortableEntry])entry.options.onload({status:200,responseText:'{"late":true,"SECRET_TOKEN":true}'});
    await delay();
    return {missing:false,health,preview,confirm,operation,rejected,httpError,malformed,oversized,networkError,timeoutError,abortError,hostileStatus,hostileText,cleanupResults,settlementCounts,postCleanupError,postCleanupRequestCountBefore,postCleanupRequestCountAfter,pendingAbortCounts:[normalEntry.abortCount,undefinedEntry.abortCount,nonabortableEntry.abortCount],abortsBefore,abortsAfter:requests.reduce((sum,entry)=>sum+entry.abortCount,0),runtimePresent:Boolean(window.__loui2DiscordWebSuiteRuntime),requestCount:requests.length,requests:requests.map(snapshot)};
  })()`});
      break;
    } catch (error) {
      if (attempt === 2 || !/Execution context was destroyed/i.test(String(error))) throw error;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }
  if(evaluated.exceptionDetails)throw new Error(evaluated.exceptionDetails.exception?.description||evaluated.exceptionDetails.text);
  const result=evaluated.result.value;
  assert.equal(result.missing,false,"private helper was not injected into fixture");
  assert.deepEqual(result.health.value,{ok:true});
  assert.deepEqual(result.preview.value,{preview:7});
  assert.deepEqual(result.operation.value,null);
  assert.deepEqual(result.health.request,{method:"GET",url:"http://127.0.0.1:18766/healthz",headers:{"Content-Type":"application/json","X-Loui2-Discord-Suite":"1"},data:"__absent__",timeout:15000,anonymous:true,optionKeys:["method","url","headers","timeout","anonymous","onload","onerror","ontimeout","onabort"]});
  assert.deepEqual(result.preview.request,{method:"POST",url:"http://127.0.0.1:18766/v1/deletions/preview",headers:{"Content-Type":"application/json","X-Loui2-Discord-Suite":"1"},data:'{"channelId":"123","count":7}',timeout:15000,anonymous:true,optionKeys:["method","url","headers","timeout","anonymous","onload","onerror","ontimeout","onabort","data"]});
  assert.equal(result.confirm.request.url,"http://127.0.0.1:18766/v1/deletions/11111111-1111-4111-8111-111111111111/confirm");
  assert.equal(result.confirm.request.data,"{}");
  for(const item of result.rejected){assert.equal(item.before,item.after,`${item.method} ${item.path} reached GM_xmlhttpRequest`);assert.equal(item.error.code,"INVALID_REQUEST");}
  assert.equal(result.rejected.length,16);
  for(const [name,item,code,status] of [["http",result.httpError,"HTTP_ERROR",500],["malformed",result.malformed,"INVALID_RESPONSE",undefined],["oversized",result.oversized,"RESPONSE_TOO_LARGE",undefined],["network",result.networkError,"NETWORK_ERROR",undefined],["timeout",result.timeoutError,"TIMEOUT",undefined],["abort",result.abortError,"ABORTED",undefined]]){
    assert.equal(item.error.code,code,name);if(status!==undefined)assert.equal(item.error.status,status,name);
    const serialized=JSON.stringify(item.error);assert.ok(!/SECRET_TOKEN|discord\.com|channels\/current|body-is-not-an-error|127\.0\.0\.1/.test(serialized),`${name} leaked sensitive detail: ${serialized}`);
    assert.deepEqual(item.error.keys,status===undefined?["code"]:["code","status"],`${name} unsafe error properties`);
  }
  for(const [name,item] of [["hostile status",result.hostileStatus],["hostile responseText",result.hostileText]]){
    assert.equal(item.callbackThrew,false,`${name} escaped onload`);
    assert.equal(item.outcome.error.code,"INVALID_RESPONSE",`${name} used wrong generic error`);
    assert.deepEqual(item.outcome.error.keys,["code"],`${name} exposed unsafe error properties`);
    assert.ok(!/HOSTILE_(?:STATUS|TEXT)_SECRET/.test(item.serialized),`${name} leaked thrown secret`);
  }
  assert.deepEqual(result.cleanupResults.map(item=>item.error?.code),["ABORTED","ABORTED","ABORTED"],"cleanup did not reject every handle type");
  for(const item of result.cleanupResults)assert.deepEqual(item.error.keys,["code"],"cleanup exposed unsafe error properties");
  assert.deepEqual(result.settlementCounts,[1,1,1],"cleanup or late callbacks settled a request more than once");
  assert.deepEqual(result.pendingAbortCounts,[1,0,0],"cleanup abort ownership depended on returned handle shape");
  assert.equal(result.abortsBefore,0,"terminal callbacks left completed handles tracked");
  assert.equal(result.abortsAfter,1,"cleanup aborted a completed handle");
  assert.equal(result.runtimePresent,false,"cleanup left suite runtime installed");
  assert.equal(result.postCleanupError.code,"CLEANED_UP","post-cleanup request used wrong generic error");
  assert.deepEqual(result.postCleanupError.keys,["code"],"post-cleanup error exposed unsafe properties");
  assert.equal(result.postCleanupRequestCountBefore,result.postCleanupRequestCountAfter,"post-cleanup request reached GM_xmlhttpRequest");
  for(const request of result.requests){
    assert.equal(request.anonymous,true,`request was not anonymous: ${request.method} ${request.url}`);
    for(const forbidden of ["withCredentials","Authorization","Cookie","user","password","credentials"]){
      assert.ok(!request.optionKeys.includes(forbidden),`forbidden option ${forbidden} present: ${JSON.stringify(request)}`);
    }
    assert.ok(!Object.keys(request.headers||{}).some((name)=>/^(?:Authorization|Cookie)$/i.test(name)),`credential-bearing header present: ${JSON.stringify(request)}`);
    assert.equal(request.headers?.["Content-Type"],"application/json",`missing JSON content type: ${request.method} ${request.url}`);
  }
  console.log(JSON.stringify({passed:true,test:"private loopback-only delete companion boundary"}));
} finally {
  socket.close();chromium.kill("SIGTERM");
  await Promise.race([new Promise(resolve=>chromium.once("exit",resolve)),new Promise(resolve=>setTimeout(resolve,2500))]);
  if(chromium.exitCode===null){chromium.kill("SIGKILL");await new Promise(resolve=>chromium.once("exit",resolve));}
  await new Promise(resolve=>server.close(resolve));
  try{fs.rmSync(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100})}catch{}
}
