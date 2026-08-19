#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const SUITE_PATH = new URL("../tampermonkey/loui2-discord-web-suite.user.js", import.meta.url);
const suite = fs.readFileSync(SUITE_PATH, "utf8");

for (const forbidden of [
  "Authorization",
  "/api/v10/channels",
  "/api/v9/channels",
  "webpackChunkdiscord_app",
  "requestDiscordApi",
  "startApiExtraction",
  "armExtractionAuthorization",
  "THREAD_CATALOG",
  "threadCatalog",
  "showAllAccessibleThreads",
  "Extract: last N messages (API)",
  "Extract: entire channel (API)",
]) {
  assert.ok(!suite.includes(forbidden), `unsupported captured-session API subsystem remains: ${forbidden}`);
}
for (const forbidden of [
  /discord(?:app)?\.com\/api/i,
  /\buser[\s_-]*token\b/i,
  /\bcredentials?\b/i,
]) {
  assert.doesNotMatch(suite, forbidden, `credential/API boundary remains: ${forbidden}`);
}
assert.deepEqual(
  [...suite.matchAll(/^\/\/ @connect\s+(.+)$/gm)].map((match) => match[1].trim()),
  ["127.0.0.1"],
  "@connect must remain loopback-only"
);
assert.equal(
  [...suite.matchAll(/http:\/\/[^\s"'`]+/g)].map((match) => match[0]).join("\n"),
  "http://127.0.0.1:18766",
  "deletion traffic must have exactly one literal HTTP origin"
);
assert.ok(
  suite.includes('const DELETE_COMPANION_BASE_URL = "http://127.0.0.1:18766";'),
  "local deletion companion origin changed"
);
const deleteCompanionRequest = suite
  .split("function requestDeleteCompanion(method, path, body, expectedStatus, owner)", 2)[1]
  ?.split("function installFullWidthMobileMode()", 1)[0] || "";
assert.ok(
  deleteCompanionRequest.includes("url: DELETE_COMPANION_BASE_URL + path"),
  "deletion traffic no longer uses only the fixed companion base"
);
assert.doesNotMatch(deleteCompanionRequest, /https?:\/\//, "deletion request function contains another literal origin");
assert.ok(suite.includes("function runRenderedExtraction("), "rendered-DOM export was removed");
assert.ok(
  suite.includes("Export Discord: currently rendered messages"),
  "rendered-DOM export command was removed"
);

const encodedSuite = Buffer.from(suite).toString("base64");
const html = `<!doctype html><html><head><meta charset="utf-8"><title>Discord | #general | Server Alpha</title>
<style>.toolbar_fixture{display:flex;height:40px}.children_fixture{display:flex;height:40px}</style>
<script>
window.__gmValues=new Map([['forceFullWidthMobileLayout',false]]);
window.__gmMenus=new Map();window.__gmNextId=1;window.__opened=[];window.__fetchCalls=[];window.__xhrCalls=[];window.__gmHttpCalls=[];
window.GM_addStyle=(css)=>{const style=document.createElement('style');style.textContent=css;document.documentElement.append(style);return style};
window.GM_getValue=(key,fallback)=>window.__gmValues.has(key)?window.__gmValues.get(key):fallback;
window.GM_setValue=(key,value)=>window.__gmValues.set(key,value);
window.GM_addValueChangeListener=()=>window.__gmNextId++;
window.GM_removeValueChangeListener=()=>{};
window.GM_registerMenuCommand=(label,callback)=>{const id=window.__gmNextId++;window.__gmMenus.set(id,{label,callback});return id};
window.GM_unregisterMenuCommand=(id)=>window.__gmMenus.delete(id);
window.GM_getTab=(callback)=>callback({tabTitleMode:'thread'});
window.GM_saveTab=(_tab,callback)=>callback?.();
window.GM_openInTab=(url)=>{window.__opened.push(String(url));return {close(){}}};
window.GM_xmlhttpRequest=(options)=>{window.__gmHttpCalls.push(options);throw new Error('DOM-only export must not use GM_xmlhttpRequest')};
window.alert=()=>{};window.confirm=()=>false;window.prompt=()=>null;
window.fetch=async(...args)=>{window.__fetchCalls.push(args);throw new Error('DOM-only export must not fetch')};
class TestXHR extends EventTarget{open(...args){window.__xhrCalls.push({kind:'open',args})}setRequestHeader(...args){window.__xhrCalls.push({kind:'header',args})}send(...args){window.__xhrCalls.push({kind:'send',args});throw new Error('DOM-only export must not use XHR')}abort(){}}
window.XMLHttpRequest=TestXHR;
</script></head><body>
<div class="toolbar_fixture"><div class="toolbar__abc"></div></div>
<div class="children_fixture"><h2>general</h2></div>
<nav aria-label="Servers sidebar"></nav>
<ol data-list-id="chat-messages">
  <li id="chat-messages-222222222222222222-900000000000000001"><article><span id="message-username-900000000000000001">Alice</span><div id="message-content-900000000000000001">Visible message</div><time datetime="2026-07-15T14:23:30.000Z"></time></article></li>
</ol>
<script>{const bytes=Uint8Array.from(atob('${encodedSuite}'),character=>character.charCodeAt(0));(0,eval)(new TextDecoder().decode(bytes));}</script>
</body></html>`;

const server = http.createServer((_request, response) => {
  const body = Buffer.from(html);
  response.writeHead(200, { "content-type": "text/html; charset=utf-8", "content-length": body.length });
  response.end(body);
});
await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
const fixtureUrl = `http://127.0.0.1:${server.address().port}/channels/111111111111111111/222222222222222222`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "loui2-dom-only-export-"));
const chromium = spawn(process.env.CHROMIUM_BIN || "chromium", [
  "--headless", "--no-sandbox", "--disable-gpu", "--no-first-run", "--remote-debugging-port=0",
  `--user-data-dir=${profile}`, fixtureUrl,
], { stdio: ["ignore", "ignore", "pipe"] });
let stderr = "";
chromium.stderr.on("data", (chunk) => { stderr += String(chunk); });
const portFile = path.join(profile, "DevToolsActivePort");
for (let attempt = 0; attempt < 120 && !fs.existsSync(portFile); attempt += 1) await new Promise((resolve) => setTimeout(resolve, 50));
if (!fs.existsSync(portFile)) throw new Error(`DevToolsActivePort unavailable: ${stderr}`);
const [port] = fs.readFileSync(portFile, "utf8").trim().split(/\r?\n/);
let target;
for (let attempt = 0; attempt < 120; attempt += 1) {
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  target = targets.find((item) => item.type === "page" && item.url.startsWith(fixtureUrl));
  if (target) break;
  await new Promise((resolve) => setTimeout(resolve, 50));
}
if (!target) throw new Error("fixture target unavailable");

const socket = new WebSocket(target.webSocketDebuggerUrl);
let nextId = 1;
const pending = new Map();
socket.addEventListener("message", (event) => {
  const message = JSON.parse(String(event.data));
  if (!message.id) return;
  const entry = pending.get(message.id);
  if (!entry) return;
  pending.delete(message.id);
  message.error ? entry.reject(new Error(message.error.message)) : entry.resolve(message.result);
});
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
const call = (method, params = {}) => new Promise((resolve, reject) => {
  const id = nextId += 1;
  pending.set(id, { resolve, reject });
  socket.send(JSON.stringify({ id, method, params }));
});

try {
  let evaluated;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      evaluated = await call("Runtime.evaluate", {
    awaitPromise: true,
    returnByValue: true,
    expression: `(async()=>{
      const delay=(ms)=>new Promise(resolve=>setTimeout(resolve,ms));
      for(let attempt=0;attempt<100&&!window.__loui2DiscordWebSuiteRuntime;attempt+=1)await delay(20);
      const labels=[...window.__gmMenus.values()].map(entry=>entry.label);
      const rendered= [...window.__gmMenus.values()].find(entry=>entry.label==='Export Discord: currently rendered messages');
      document.querySelector('[data-loui2-control="menu"]')?.click();
      const deleteRegistered=Boolean(document.querySelector('[data-loui2-delete-count] input')&&document.querySelector('[data-loui2-option="delete-mine"]'));
      const startup={gmRequests:window.__gmHttpCalls.length,fetchCalls:window.__fetchCalls.length,xhrCalls:window.__xhrCalls.length};
      if(!rendered)return {labels,missingRendered:true,deleteRegistered,startup};
      await rendered.callback();
      await delay(20);
      const result={
        labels,
        deleteRegistered,
        startup,
        opened:[...window.__opened],
        fetchCalls:window.__fetchCalls.length,
        xhrCalls:window.__xhrCalls.length,
        gmHttpCalls:window.__gmHttpCalls.length,
        runtimeVersion:window.__loui2DiscordWebSuiteRuntime?.version||'',
      };
      window.__loui2DiscordWebSuiteRuntime.cleanup();
      return result;
    })()`,
    });
      break;
    } catch (error) {
      if (attempt === 1 || !/Execution context was destroyed/i.test(String(error))) throw error;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }
  if (evaluated.exceptionDetails) throw new Error(evaluated.exceptionDetails.exception?.description || evaluated.exceptionDetails.text);
  const result = evaluated.result.value;
  assert.equal(result.missingRendered, undefined, `rendered export command missing; registered: ${JSON.stringify(result.labels)}`);
  assert.equal(result.deleteRegistered, true, "deletion companion UI was not registered");
  assert.deepEqual(
    result.startup,
    { gmRequests: 0, fetchCalls: 0, xhrCalls: 0 },
    "deletion companion registration/existence caused startup network activity"
  );
  assert.equal(result.opened.length, 1, "rendered export did not create local output");
  assert.match(result.opened[0], /^blob:/, "rendered export did not use a local Blob output");
  assert.equal(result.fetchCalls, 0, "rendered export made a Fetch request");
  assert.equal(result.xhrCalls, 0, "rendered export made an XHR request");
  assert.equal(result.gmHttpCalls, 0, "rendered export made a GM_xmlhttpRequest request");
  assert.ok(!result.labels.some((label) => /(?:API|last N|entire channel|cancel active)/i.test(label)), `unsupported API command remains: ${JSON.stringify(result.labels)}`);
  assert.ok(result.runtimeVersion, "suite runtime marker missing");
  console.log(JSON.stringify({ passed: true, test: "rendered-DOM-only export has no API subsystem" }));
} finally {
  socket.close();
  chromium.kill("SIGTERM");
  await Promise.race([new Promise((resolve) => chromium.once("exit", resolve)), new Promise((resolve) => setTimeout(resolve, 2500))]);
  if (chromium.exitCode === null) { chromium.kill("SIGKILL"); await new Promise((resolve) => chromium.once("exit", resolve)); }
  await new Promise((resolve) => server.close(resolve));
  try { fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 }); } catch {}
}
