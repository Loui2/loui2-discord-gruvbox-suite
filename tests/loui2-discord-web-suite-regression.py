#!/usr/bin/env python3
import hashlib
from html import unescape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE = REPO_ROOT / "tampermonkey/loui2-discord-web-suite.user.js"
ROLLBACK_DIR = Path(os.environ["LOUI2_DISCORD_ROLLBACK_DIR"]) if "LOUI2_DISCORD_ROLLBACK_DIR" in os.environ else None
ROLLBACK_HASHES = {
    "gruvbox-sharp-discord-web.user.js": "fa8ca3fd9c4bd3461db44b85daa2f10279c231f9928f10d3201e99b7dab7cbc5",
    "discord-tab-title.user.js": "b7f1872eb8dab55651fc11b0148a24dcd53aa63299f10c8377aa58969eef79c5",
    "discord-web-invisible-typing.user.js": "b806ce18a585fb370bb96babb05d853a676dba97acf3fd786f6f20672db5aed2",
}


def run_browser_fixture(
    body_script,
    *,
    tab_mode="thread",
    virtual_time_ms=1000,
    gm_add_style_throws=False,
    separate_unsafe_window=False,
    source_override=None,
    process_timeout=40,
    defer_gm_get_tab=False,
):
    source = source_override if source_override is not None else SUITE.read_text()
    if "</script>" in source.lower():
        raise AssertionError("suite source cannot be embedded in the browser fixture")

    fixture = r'''<!doctype html><html><head><meta charset="utf-8"><title>Discord | #channel-alpha | Server Alpha</title>
<style>
  body { margin: 0; }
  .children_fixture { align-items:center; display:flex; height:40px; position:absolute; left:0; top:30px; width:600px; }
  .channelIcon_fixture { height:24px; width:24px; }
  .toolbar_fixture { align-items:center; display:flex; height:40px; position:absolute; right:0; top:30px; width:500px; }
  .native { height:32px; width:32px; }
  .sidebar_fixture { height:500px; width:300px; }
  nav[aria-label="Servers sidebar"] { height:500px; width:64px; }
  .heading_fixture { height:24px; margin:0; position:absolute; top:40px; }
  .server_heading_fixture { left:100px; }
  .parentChannelName_fixture { left:300px; }
  .thread_heading_fixture { left:460px; }
  ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"],
  ul[aria-label="Channels"] [aria-label$="(thread)"] [class*="name_"],
  ul[aria-label="Channels"] [class*="name_"][class*="header_"] { color: rgb(168, 153, 132); }
</style>
<script>
document.documentElement.dataset.loui2GruvboxSharp = '1.6.0';
document.documentElement.dataset.loui2DiscordTabTitle = 'thread:Existing standalone title';
window.__gmValues = new Map();
window.__gmListeners = new Map();
window.__gmMenus = new Map();
window.__gmNextId = 1;
window.__tabObject = {tabTitleMode: __TAB_MODE__};
window.__suiteSource = __SUITE_JSON__;
window.__xhrNetworkSends = 0;
window.__fetchNetworkSends = 0;
window.__gmHttpNetworkSends = 0;
class TestXHR extends EventTarget {
  constructor() { super(); this.readyState=0; this.status=0; }
  open(method,url) { this.method=method; this.url=url; this.readyState=1; this.dispatchEvent(new Event('readystatechange')); }
  send(body) { this.body=body; window.__xhrNetworkSends++; }
  abort() { this.aborted=true; this.dispatchEvent(new Event('abort')); this.dispatchEvent(new Event('loadend')); }
}
window.XMLHttpRequest = TestXHR;
window.fetch = async (...args) => { window.__fetchNetworkSends++; return new Response(JSON.stringify(args), {status:200}); };
window.__nativeOpen = TestXHR.prototype.open;
window.__nativeSend = TestXHR.prototype.send;
window.__nativeAbort = TestXHR.prototype.abort;
window.__nativeFetch = window.fetch;
window.__nativePushState = history.pushState;
window.__nativeReplaceState = history.replaceState;
__UNSAFE_WINDOW_SETUP__
window.GM_addStyle = __GM_ADD_STYLE__;
window.GM_getValue = (key,fallback) => window.__gmValues.has(key) ? window.__gmValues.get(key) : fallback;
window.GM_setValue = (key,value) => { const old=window.__gmValues.get(key); window.__gmValues.set(key,value); for(const entry of window.__gmListeners.values()) if(entry.key===key) entry.callback(key,old,value,false); };
window.GM_addValueChangeListener = (key,callback) => { const id=window.__gmNextId++; window.__gmListeners.set(id,{key,callback}); return id; };
window.GM_removeValueChangeListener = (id) => window.__gmListeners.delete(id);
window.GM_registerMenuCommand = (label,callback) => { const id=window.__gmNextId++; window.__gmMenus.set(id,{label,callback}); return id; };
window.GM_unregisterMenuCommand = (id) => window.__gmMenus.delete(id);
window.GM_getTab = __GM_GET_TAB__;
window.GM_saveTab = (tab,callback) => { window.__tabObject=tab; callback?.(); };
window.GM_xmlhttpRequest = (options) => { window.__gmHttpNetworkSends++; throw new Error('unexpected GM_xmlhttpRequest: '+String(options?.url||'')); };
</script><script>__SUITE__</script></head><body>
<div class="upperContainer_fixture"><div class="children_fixture"><div class="channelIcon_fixture"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M3 3h18v18H3z"></path></svg></div><h2 class="heading_fixture parentChannelName_fixture">#channel-alpha</h2></div><div class="toolbar_fixture"><div class="native" role="button" aria-label="Threads"></div></div></div>
<div class="sidebar_fixture"><nav aria-label="Servers sidebar"><div data-list-id="guildsnav"></div></nav><nav aria-label="Fixture server"><ul aria-label="Channels"><li><div class="name_fixture header_fixture">Fixture category</div></li><li><a aria-label="fixture-channel (text channel)"><div class="name_fixture">fixture-channel</div></a></li><li><div class="typeThread_fixture" role="button" aria-label="fixture-thread (thread)"><div class="name_fixture">fixture-thread</div></div></li></ul></nav><div>channels</div></div>
<h1 class="heading_fixture server_heading_fixture">Server Alpha: channel-alpha</h1>
<h2 class="heading_fixture thread_heading_fixture">Thread: Thread Beta chat</h2>
<main><ol data-list-id="chat-messages"><li class="message_fixture"><span class="username_fixture">Fixture user</span><time class="timestamp_fixture">Today</time><div class="messageContent_fixture"><div class="markup_fixture">Fixture message</div></div></li></ol><div class="channelTextArea_fixture"><div role="textbox" data-slate-editor="true">Fixture composer</div></div></main>
<div class="popout_fixture"><div class="messageContent_fixture externalMessage_fixture">External message</div><div role="textbox" data-slate-editor="true" class="externalEditor_fixture">External editor</div></div>
<div class="membersWrap_fixture"><div class="membersGroup_fixture">ONLINE</div><div class="name_fixture">Fixture member</div><div class="activity_fixture">Fixture status</div></div>
<output id="result"></output>
<script>
window.addEventListener('DOMContentLoaded', () => setTimeout(async () => {
  try { __BODY_SCRIPT__ }
  catch (error) { document.getElementById('result').textContent=JSON.stringify({error:String(error.stack||error)}); }
}, 300));
</script></body></html>'''
    fixture = fixture.replace("__TAB_MODE__", json.dumps(tab_mode))
    fixture = fixture.replace("__SUITE_JSON__", json.dumps(source))
    unsafe_window_setup = (
        """
window.__unsafeFetchCalls = 0;
window.unsafeWindow = {
  XMLHttpRequest: window.XMLHttpRequest,
  Request: window.Request,
  Response: window.Response,
  fetch: async (...args) => {
    window.__unsafeFetchCalls++;
    return new Response(JSON.stringify(args), {status:200});
  },
};
"""
        if separate_unsafe_window
        else ""
    )
    fixture = fixture.replace("__UNSAFE_WINDOW_SETUP__", unsafe_window_setup)
    style_stub = (
        "() => { throw new Error('synthetic GM_addStyle failure'); }"
        if gm_add_style_throws
        else "(css) => { const style=document.createElement('style'); style.textContent=css; document.documentElement.append(style); return style; }"
    )
    fixture = fixture.replace("__GM_ADD_STYLE__", style_stub)
    gm_get_tab_stub = (
        "(callback) => { window.__deferredGetTab = callback; }"
        if defer_gm_get_tab
        else "(callback) => callback(window.__tabObject)"
    )
    fixture = fixture.replace("__GM_GET_TAB__", gm_get_tab_stub)
    fixture = fixture.replace("__SUITE__", source)
    fixture = fixture.replace("__BODY_SCRIPT__", body_script)

    dom_path = Path("/tmp/loui2-discord-web-suite-fixture.dom")
    profile = Path(tempfile.mkdtemp(prefix="loui2-suite-profile-", dir="/tmp"))
    payload = fixture.encode()

    class FixtureHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    fixture_url = (
        f"http://127.0.0.1:{server.server_port}"
        "/channels/111111111111111111/222222222222222222"
    )
    try:
        chromium_args = [
            os.environ.get("CHROMIUM_BIN", "chromium"),
            "--headless", "--no-sandbox", "--disable-gpu",
            "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
            f"--user-data-dir={profile}",
        ]
        if virtual_time_ms is None:
            chromium_args.append("--timeout=2000")
        else:
            chromium_args.append(f"--virtual-time-budget={virtual_time_ms}")
        chromium_args.extend(["--dump-dom", fixture_url])
        completed = subprocess.run(
            chromium_args,
            check=True,
            capture_output=True,
            text=True,
            timeout=process_timeout,
        )
        dom_path.write_text(completed.stdout)
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)
        shutil.rmtree(profile, ignore_errors=True)

    match = re.search(r'<output id="result">(.*?)</output>', completed.stdout, re.S)
    if not match:
        raise AssertionError("browser fixture did not produce a result")
    state = json.loads(unescape(match.group(1)))
    if state.get("error"):
        raise AssertionError(state["error"])
    return state


class SuiteMetadataTests(unittest.TestCase):
    def test_all_userscripts_declare_mandatory_version_bump_policy(self):
        userscripts = [SUITE]
        self.assertTrue(userscripts)
        policy = re.compile(
            r"^// @version\s+\d+\.\d+\.\d+\n"
            r"// IMPORTANT: Always bump @version whenever ANY change is made\. No exceptions\.$",
            re.MULTILINE,
        )
        for path in userscripts:
            self.assertRegex(path.read_text(), policy, str(path))

    def test_suite_has_unified_metadata_and_embedded_theme(self):
        self.assertTrue(SUITE.exists(), f"missing suite artifact: {SUITE}")
        source = SUITE.read_text()

        required_metadata = [
            "// @name         Loui2 Discord Web suite",
            "// @version      2.7.33",
            "// @match        https://discord.com/*",
            "// @run-at       document-start",
            "// @sandbox      raw",
            "// @grant        GM_addStyle",
            "// @grant        unsafeWindow",
            "// @grant        GM_getTab",
            "// @grant        GM_saveTab",
            "// @grant        GM_getValue",
            "// @grant        GM_setValue",
            "// @grant        GM_registerMenuCommand",
            "// @grant        GM_xmlhttpRequest",
            "// @connect      127.0.0.1",
        ]
        for line in required_metadata:
            self.assertIn(line, source)

        self.assertIn("Gruvbox Dark Soft palette", source)
        self.assertIn("--background-primary: #32302f", source)
        self.assertIn('font-family: "IBM Plex Mono"', source)
        self.assertIn("--message-background-hover: rgba(80, 73, 69, 0.45)", source)
        self.assertIn('#app-mount img[class*="avatar_"]', source)
        self.assertIn("function runRenderedExtraction()", source)
        self.assertIn("Export Discord: currently rendered messages", source)
        for unsupported in [
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
        ]:
            self.assertNotIn(unsupported, source)
        for unsupported in (
            r"discord(?:app)?\.com/api",
            r"\buser[\s_-]*token\b",
            r"\bcredentials?\b",
        ):
            self.assertNotRegex(source, re.compile(unsupported, re.IGNORECASE))
        self.assertEqual(
            re.findall(r"^// @connect\s+(.+)$", source, re.MULTILINE),
            ["127.0.0.1"],
        )
        self.assertEqual(
            re.findall(r'''http://[^\s"'`]+''', source),
            ["http://127.0.0.1:18766"],
        )
        self.assertNotIn('typeof pageWindow.fetch === "function" ? pageWindow.fetch : originalFetch', source)
        self.assertIn('function startTitleFeature(savedTabState) {\n    if (suiteCleanedUp) return;', source)
        self.assertIn('const DELETE_COMPANION_BASE_URL = "http://127.0.0.1:18766";', source)
        self.assertIn('const DELETE_COMPANION_CLIENT_HEADER = "X-Loui2-Discord-Suite";', source)
        self.assertIn("function requestDeleteCompanion(method, path, body, expectedStatus, owner)", source)
        companion = source.split("function requestDeleteCompanion(method, path, body, expectedStatus, owner)", 1)[1].split("function installFullWidthMobileMode()", 1)[0]
        self.assertIn("GM_xmlhttpRequest", companion)
        self.assertIn("url: DELETE_COMPANION_BASE_URL + path", companion)
        self.assertNotRegex(companion, r"https?://")
        self.assertNotIn("console.", companion)
        self.assertNotIn("Authorization", companion)
        self.assertNotIn("discord.com/api", source)
        self.assertNotIn("Authorization", source)
        subprocess.run(["node", "--check", str(SUITE)], check=True)

    def test_delete_ui_is_local_channel_scoped_and_trusted_two_step(self):
        source = SUITE.read_text()
        self.assertIn('const VERSION = "2.7.33";', source)
        self.assertIn('function createMessageDeletionControl()', source)
        self.assertIn('function readNormalizedDeleteCount(input)', source)
        self.assertIn('createSuiteMenuOption("delete-mine", "Delete my recent messages...", "menuitem"', source)
        self.assertIn('location.pathname.match(/^\\/channels\\/(\\d{1,20})\\/(\\d{1,20})$/)', source)
        self.assertIn('event instanceof MouseEvent', source)
        self.assertGreaterEqual(source.count('!event.isTrusted'), 2)
        self.assertIn('"/v1/deletions/preview"', source)
        self.assertIn('`/v1/deletions/${state.operationId}/confirm`', source)
        self.assertIn('`/v1/deletions/${state.operationId}`', source)
        self.assertNotIn('/v1/delete-my-messages', source)
        self.assertNotIn('/v1/operations', source)
        self.assertIn('anonymous: true', source)
        self.assertNotIn("discord.com/api", source)
        self.assertNotIn("Authorization", source)
        delete_ui = source.split('const DELETE_DIALOG_ID = ', 1)[1].split('function buildTabTitle()', 1)[0]
        self.assertNotIn("GM_getValue", delete_ui)
        self.assertNotIn("GM_setValue", delete_ui)
        self.assertNotRegex(delete_ui, r"(?:targetUser|userToken|messageIds)\s*:")
        self.assertIn('channelId: route.channelId, count', delete_ui)
        self.assertIn('`/v1/deletions/${state.operationId}/confirm`, {}', delete_ui)
        self.assertIn('/^[0-9a-f-]{36}$/i', source)
        self.assertIn('MAX_DELETE_TIMESTAMP_LENGTH = 64', delete_ui)
        self.assertIn('DELETE_TIMESTAMP_PATTERN = /^\\d{4}-\\d{2}-\\d{2}T', delete_ui)
        self.assertIn('Permanently deleting these messages cannot be undone.', delete_ui)
        self.assertIn('messages permanently`', delete_ui)
        self.assertIn('document.addEventListener("focusin", state.onFocusin, true)', delete_ui)
        self.assertIn('DELETE_POLL_LIFETIME_MS = 180_000', delete_ui)
        self.assertIn('value.total === expectedTotal', delete_ui)
        self.assertIn('value.completed === 0', delete_ui)
        self.assertIn('(value.status === "running" || value.completed === value.total)', delete_ui)
        self.assertIn('value.errors.length === value.failed', delete_ui)
        self.assertNotIn('GM_registerMenuCommand', delete_ui)
        self.assertNotIn('"Delete my recent messages…"', source)

    def test_rollback_sources_remain_byte_identical(self):
        if ROLLBACK_DIR is None:
            self.skipTest("set LOUI2_DISCORD_ROLLBACK_DIR to verify standalone rollback artifacts")
        for name, expected in ROLLBACK_HASHES.items():
            path = ROLLBACK_DIR / name
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(actual, expected, str(path))


class SuiteMobileModeTests(unittest.TestCase):
    def test_stale_tab_mobile_value_cannot_override_the_global_setting(self):
        source = "window.__tabObject.mobileEnabled=true;\n" + SUITE.read_text()
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="menu"]').click();
document.getElementById('result').textContent=JSON.stringify({
  active:document.documentElement.hasAttribute('data-loui2-discord-full-width-mobile'),
  checked:document.querySelector('[data-loui2-option="mobile"]').getAttribute('aria-checked'),
  reloadRequired:document.documentElement.hasAttribute('data-loui2-mobile-reload-required'),
  tabHasMobile:Object.prototype.hasOwnProperty.call(window.__tabObject,'mobileEnabled'),
});
''', source_override=source)
        self.assertEqual(
            state,
            {"active": False, "checked": "false", "reloadRequired": False, "tabHasMobile": False},
        )

    def test_enabled_mobile_mode_keeps_real_geometry_and_spoofs_mobile_signals(self):
        source = (
            'window.__preMobile={userAgent:navigator.userAgent,innerWidth,'
            'screenWidth:screen.width,dpr:devicePixelRatio};'
            'GM_setValue("forceFullWidthMobileLayout",true);\n'
            + SUITE.read_text()
        )
        state = run_browser_fixture(r'''
const trigger=document.querySelector('[data-loui2-control="menu"]');
trigger.click();
const mobileOption=document.querySelector('[data-loui2-option="mobile"]');
document.getElementById('result').textContent=JSON.stringify({
  active:document.documentElement.hasAttribute('data-loui2-discord-full-width-mobile'),
  reloadRequired:document.documentElement.hasAttribute('data-loui2-mobile-reload-required'),
  uaMobile:/Mobile/.test(navigator.userAgent),
  uaDataMobile:navigator.userAgentData?.mobile??null,
  touch:navigator.maxTouchPoints,
  max500:matchMedia('(max-width: 500px)').matches,
  fine:matchMedia('(pointer: fine)').matches,
  innerWidth:window.innerWidth,
  screenWidth:screen.width,
  dpr:window.devicePixelRatio,
  bodyWidth:Math.round(document.body.getBoundingClientRect().width),
  documentWidth:document.documentElement.clientWidth,
  checked:mobileOption?.getAttribute('aria-checked')||null,
  label:mobileOption?.innerText.trim()||null,
  pre:window.__preMobile,
});
''', source_override=source)
        self.assertTrue(state["active"])
        self.assertFalse(state["reloadRequired"])
        self.assertTrue(state["uaMobile"])
        self.assertTrue(state["uaDataMobile"])
        self.assertEqual(state["touch"], 5)
        self.assertTrue(state["max500"])
        self.assertFalse(state["fine"])
        self.assertEqual(state["innerWidth"], state["pre"]["innerWidth"])
        self.assertEqual(state["screenWidth"], state["pre"]["screenWidth"])
        self.assertEqual(state["dpr"], state["pre"]["dpr"])
        self.assertEqual(state["bodyWidth"], state["documentWidth"])
        self.assertEqual(state["checked"], "true")
        self.assertEqual(state["label"], "Use full-width mobile layout")

    def test_mobile_menu_toggle_persists_and_marks_reload_required(self):
        state = run_browser_fixture(r'''
const native={
  userAgent:navigator.userAgent,
  innerWidth:window.innerWidth,
  screenWidth:screen.width,
  dpr:window.devicePixelRatio,
};
const trigger=document.querySelector('[data-loui2-control="menu"]');
trigger.click();
const mobileOption=document.querySelector('[data-loui2-option="mobile"]');
const before=mobileOption?.getAttribute('aria-checked')||null;
mobileOption?.click();
document.getElementById('result').textContent=JSON.stringify({
  before,
  stored:window.__gmValues.get('forceFullWidthMobileLayout'),
  checked:mobileOption?.getAttribute('aria-checked')||null,
  label:mobileOption?.innerText.trim()||null,
  reloadRequired:document.documentElement.hasAttribute('data-loui2-mobile-reload-required'),
  active:document.documentElement.hasAttribute('data-loui2-discord-full-width-mobile'),
  geometryUnchanged:native.innerWidth===window.innerWidth&&native.screenWidth===screen.width&&native.dpr===window.devicePixelRatio,
  identityUnchanged:native.userAgent===navigator.userAgent,
});
''')
        self.assertEqual(state["before"], "false")
        self.assertTrue(state["stored"])
        self.assertEqual(state["checked"], "true")
        self.assertIn("reload required", state["label"])
        self.assertTrue(state["reloadRequired"])
        self.assertFalse(state["active"])
        self.assertTrue(state["geometryUnchanged"])
        self.assertTrue(state["identityUnchanged"])

    def test_mobile_installer_does_not_override_rendered_geometry(self):
        source = SUITE.read_text()
        installer = source.split("function installFullWidthMobileMode()", 1)[1].split(
            "const mobileModeRequestedAtStartup", 1
        )[0]
        for property_name in (
            "innerWidth", "innerHeight", "outerWidth", "outerHeight",
            "devicePixelRatio", "availWidth", "availHeight",
        ):
            self.assertNotIn(f'"{property_name}"', installer, property_name)
        self.assertNotIn("--loui2-discord-mobile-width", installer)
        self.assertNotRegex(installer, r"(?:width|max-width)\s*:\s*393px")
        self.assertIn("393 <= value", installer)
        self.assertIn('define(w, "matchMedia"', installer)

    def test_open_dropdown_repositions_inside_visual_viewport(self):
        prelude = r'''
const __fixtureVisualViewport=new EventTarget();
Object.assign(__fixtureVisualViewport,{offsetLeft:0,offsetTop:0,width:360,height:640});
Object.defineProperty(window,'visualViewport',{configurable:true,value:__fixtureVisualViewport});
'''
        state = run_browser_fixture(r'''
const trigger=document.querySelector('[data-loui2-control="menu"]');
trigger.click();
const menu=document.getElementById('loui2-discord-suite-menu');
window.visualViewport.height=220;
window.visualViewport.dispatchEvent(new Event('resize'));
const rect=menu.getBoundingClientRect();
document.getElementById('result').textContent=JSON.stringify({
  maxHeight:menu.style.maxHeight,
  top:rect.top,
  bottom:rect.bottom,
  viewportBottom:window.visualViewport.height,
});
''', source_override=prelude + SUITE.read_text())
        self.assertEqual(state["maxHeight"], "204px")
        self.assertGreaterEqual(state["top"], 7)
        self.assertLessEqual(state["bottom"], state["viewportBottom"] - 7)


class SuiteTypographyTests(unittest.TestCase):
    def test_channel_color_input_participates_in_menu_arrow_navigation(self):
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="menu"]').click();
const mobile=document.querySelector('[data-loui2-option="mobile"]');
const color=document.querySelector('[data-loui2-color-control="channel"] input');
mobile.focus();
const enterColor=new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true});
mobile.dispatchEvent(enterColor);
const reachedColor=document.activeElement===color;
const nativeArrow=new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true});
color.dispatchEvent(nativeArrow);
document.getElementById('result').textContent=JSON.stringify({
  reachedColor,
  traversalPrevented:enterColor.defaultPrevented,
  colorKeptFocus:document.activeElement===color,
  nativePrevented:nativeArrow.defaultPrevented,
});
''')
        self.assertEqual(
            state,
            {
                "reachedColor": True,
                "traversalPrevented": True,
                "colorKeptFocus": True,
                "nativePrevented": False,
            },
        )

    def test_channel_color_distinguishes_channels_from_threads_and_saves_globally(self):
        state = run_browser_fixture(r'''
const channel=document.querySelector('ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"]');
const thread=document.querySelector('ul[aria-label="Channels"] [aria-label$="(thread)"] [class*="name_"]');
const category=document.querySelector('ul[aria-label="Channels"] [class*="name_"][class*="header_"]');
document.querySelector('[data-loui2-control="menu"]').click();
const input=document.querySelector('[data-loui2-color-control="channel"] input[type="color"]');
const initial={
  input:input?.value||null,
  channel:getComputedStyle(channel).color,
  thread:getComputedStyle(thread).color,
  category:getComputedStyle(category).color,
};
if(input){
  input.value='#fabd2f';
  input.dispatchEvent(new Event('input',{bubbles:true}));
}
document.getElementById('result').textContent=JSON.stringify({
  initial,
  changed:{
    channel:getComputedStyle(channel).color,
    thread:getComputedStyle(thread).color,
    category:getComputedStyle(category).color,
    root:document.documentElement.style.getPropertyValue('--loui2-channel-name-color'),
    tabHasColor:Object.prototype.hasOwnProperty.call(window.__tabObject,'channelNameColor'),
    global:window.__gmValues.get('channelNameColor')??null,
    scope:document.querySelector('[data-loui2-color-control="channel"] .loui2-suite-font-unit').textContent,
  },
});
''')
        self.assertEqual(
            state["initial"],
            {
                "input": "#b8bb26",
                "channel": "rgb(184, 187, 38)",
                "thread": "rgb(168, 153, 132)",
                "category": "rgb(168, 153, 132)",
            },
        )
        self.assertEqual(
            state["changed"],
            {
                "channel": "rgb(250, 189, 47)",
                "thread": "rgb(168, 153, 132)",
                "category": "rgb(168, 153, 132)",
                "root": "#fabd2f",
                "tabHasColor": False,
                "global": "#fabd2f",
                "scope": "global",
            },
        )

    def test_channel_and_thread_sidebar_labels_use_compact_scoped_sizes(self):
        state = run_browser_fixture(r'''
const outside=document.createElement('div');
outside.className='name_fixture';
outside.textContent='outside';
document.body.append(outside);
const root=document.querySelector('ul[aria-label="Channels"]');
const channel=root.querySelector('a [class*="name_"]');
const thread=root.querySelector('[class*="typeThread_"] [class*="name_"]');
document.getElementById('result').textContent=JSON.stringify({
  channel:getComputedStyle(channel).fontSize,
  thread:getComputedStyle(thread).fontSize,
  outside:getComputedStyle(outside).fontSize,
});
''')
        self.assertEqual(state, {"channel": "15px", "thread": "13px", "outside": "16px"})

    def test_persisted_font_sizes_survive_refresh_hydration_without_menu_interaction(self):
        prelude = r'''
window.__gmValues.set('sidebarFontSize', 18);
window.__gmValues.set('mainChatFontSize', 17);
window.__gmValues.set('memberListFontSize', 15);
'''
        state = run_browser_fixture(r'''
const size=(selector)=>getComputedStyle(document.querySelector(selector)).fontSize;
const readSizes=()=>({
  channel:size('ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"]'),
  message:size('[class*="messageContent_"]'),
  member:size('[class*="membersWrap_"] [class*="name_"]'),
});
const initial=readSizes();
for(const property of [
  '--loui2-sidebar-font-size',
  '--loui2-main-chat-font-size',
  '--loui2-member-font-size',
]) document.documentElement.style.removeProperty(property);
await new Promise((resolve)=>setTimeout(resolve,50));
document.getElementById('result').textContent=JSON.stringify({
  initial,
  afterHydration:readSizes(),
  menuOpened:Boolean(document.getElementById('loui2-discord-suite-menu')),
});
''', source_override=prelude + SUITE.read_text())
        expected = {"channel": "18px", "message": "17px", "member": "15px"}
        self.assertEqual(state["initial"], expected)
        self.assertEqual(state["afterHydration"], expected)
        self.assertFalse(state["menuOpened"])

    def test_dropdown_text_weight_control_applies_persists_and_survives_hydration(self):
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="menu"]').click();
let menu=document.getElementById('loui2-discord-suite-menu');
let input=menu?.querySelector('[data-loui2-font-control="weight"] input')||null;
const weight=(selector)=>getComputedStyle(document.querySelector(selector)).fontWeight;
const initial=input?{
  value:input.value,
  min:input.min,
  max:input.max,
  step:input.step,
  message:weight('[class*="messageContent_"]'),
  username:weight('[class*="username_"]'),
}:null;
if(input){
  input.value='100';
  input.dispatchEvent(new Event('input',{bubbles:true}));
  input.dispatchEvent(new Event('change',{bubbles:true}));
}
const changed=input?{
  message:weight('[class*="messageContent_"]'),
  composer:weight('[role="textbox"][data-slate-editor="true"]'),
  channel:weight('ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"]'),
  member:weight('[class*="membersWrap_"] [class*="name_"]'),
  username:weight('[class*="username_"]'),
  stored:window.__gmValues.get('textFontWeight')??null,
  root:document.documentElement.style.getPropertyValue('--loui2-text-font-weight'),
}:null;
document.documentElement.style.removeProperty('--loui2-text-font-weight');
await new Promise((resolve)=>setTimeout(resolve,50));
const afterHydration=input?{
  message:weight('[class*="messageContent_"]'),
  root:document.documentElement.style.getPropertyValue('--loui2-text-font-weight'),
}:null;
document.querySelector('[data-loui2-control="menu"]').click();
document.querySelector('[data-loui2-control="menu"]').click();
menu=document.getElementById('loui2-discord-suite-menu');
input=menu?.querySelector('[data-loui2-font-control="weight"] input')||null;
document.getElementById('result').textContent=JSON.stringify({
  present:Boolean(input),
  initial,
  changed,
  afterHydration,
  reopenedValue:input?.value||null,
});
''')
        self.assertTrue(state["present"])
        self.assertEqual(
            state["initial"],
            {"value": "300", "min": "100", "max": "500", "step": "100", "message": "300", "username": "400"},
        )
        self.assertEqual(
            state["changed"],
            {
                "message": "100",
                "composer": "100",
                "channel": "100",
                "member": "100",
                "username": "200",
                "stored": 100,
                "root": "100",
            },
        )
        self.assertEqual(state["afterHydration"], {"message": "100", "root": "100"})
        self.assertEqual(state["reopenedValue"], "100")

    def test_dropdown_font_controls_apply_and_persist_scoped_sizes(self):
        state = run_browser_fixture(r'''
const outside=document.createElement('div');
outside.className='name_fixture';
outside.textContent='outside';
document.body.append(outside);
document.querySelector('[data-loui2-control="menu"]').click();
const menu=document.getElementById('loui2-discord-suite-menu');
const controls=Object.fromEntries(['sidebar','main-chat','members'].map(name=>[
  name,
  menu?.querySelector(`[data-loui2-font-control="${name}"] input`)||null,
]));
const present=Object.fromEntries(Object.entries(controls).map(([name,input])=>[name,Boolean(input)]));
const defaults=Object.fromEntries(Object.entries(controls).map(([name,input])=>[name,input?.value||null]));
for(const [name,value] of Object.entries({'sidebar':18,'main-chat':17,'members':15})){
  const input=controls[name];
  if(!input) continue;
  input.value=String(value);
  input.dispatchEvent(new Event('input',{bubbles:true}));
  input.dispatchEvent(new Event('change',{bubbles:true}));
}
const size=(selector)=>getComputedStyle(document.querySelector(selector)).fontSize;
document.getElementById('result').textContent=JSON.stringify({
  present,
  defaults,
  bounds:controls.sidebar?{min:controls.sidebar.min,max:controls.sidebar.max,step:controls.sidebar.step}:null,
  sizes:{
    channel:size('ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"]'),
    category:size('ul[aria-label="Channels"] [class*="name_"][class*="header_"]'),
    thread:size('ul[aria-label="Channels"] [aria-label$="(thread)"] [class*="name_"]'),
    message:size('[class*="messageContent_"]'),
    username:size('[class*="message_"] [class*="username_"]'),
    timestamp:size('[class*="message_"] [class*="timestamp_"]'),
    composer:size('[role="textbox"][data-slate-editor="true"]'),
    member:size('[class*="membersWrap_"] [class*="name_"]'),
    memberGroup:size('[class*="membersWrap_"] [class*="membersGroup_"]'),
    activity:size('[class*="membersWrap_"] [class*="activity_"]'),
    outside:getComputedStyle(outside).fontSize,
    externalMessage:size('.externalMessage_fixture'),
    externalEditor:size('.externalEditor_fixture'),
  },
  stored:{
    sidebar:window.__gmValues.get('sidebarFontSize')??null,
    mainChat:window.__gmValues.get('mainChatFontSize')??null,
    members:window.__gmValues.get('memberListFontSize')??null,
  },
});
''')
        self.assertEqual(state["present"], {"sidebar": True, "main-chat": True, "members": True})
        self.assertEqual(state["defaults"], {"sidebar": "15", "main-chat": "16", "members": "16"})
        self.assertEqual(state["bounds"], {"min": "10", "max": "24", "step": "1"})
        self.assertEqual(
            state["sizes"],
            {
                "channel": "18px",
                "category": "17px",
                "thread": "16px",
                "message": "17px",
                "username": "17px",
                "timestamp": "13px",
                "composer": "17px",
                "member": "15px",
                "memberGroup": "11px",
                "activity": "13px",
                "outside": "16px",
                "externalMessage": "16px",
                "externalEditor": "16px",
            },
        )
        self.assertEqual(state["stored"], {"sidebar": 18, "mainChat": 17, "members": 15})

    def test_font_control_bounds_normalize_manual_values(self):
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="menu"]').click();
const menu=document.getElementById('loui2-discord-suite-menu');
const input=(name)=>menu.querySelector(`[data-loui2-font-control="${name}"] input`);
for(const [name,value] of Object.entries({'sidebar':'30','main-chat':'9','members':''})){
  input(name).value=value;
  input(name).dispatchEvent(new Event('change',{bubbles:true}));
}
const size=(selector)=>getComputedStyle(document.querySelector(selector)).fontSize;
document.getElementById('result').textContent=JSON.stringify({
  values:{sidebar:input('sidebar').value,mainChat:input('main-chat').value,members:input('members').value},
  stored:{
    sidebar:window.__gmValues.get('sidebarFontSize'),
    mainChat:window.__gmValues.get('mainChatFontSize'),
    members:window.__gmValues.get('memberListFontSize'),
  },
  sizes:{
    channel:size('ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"]'),
    thread:size('ul[aria-label="Channels"] [aria-label$="(thread)"] [class*="name_"]'),
    message:size('[class*="messageContent_"]'),
    timestamp:size('[class*="message_"] [class*="timestamp_"]'),
    member:size('[class*="membersWrap_"] [class*="name_"]'),
  },
});
''')
        self.assertEqual(state["values"], {"sidebar": "24", "mainChat": "10", "members": "16"})
        self.assertEqual(state["stored"], {"sidebar": 24, "mainChat": 10, "members": 16})
        self.assertEqual(
            state["sizes"],
            {"channel": "24px", "thread": "22px", "message": "10px", "timestamp": "10px", "member": "16px"},
        )

    def test_font_control_reset_restores_defaults(self):
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="menu"]').click();
const menu=document.getElementById('loui2-discord-suite-menu');
const input=(name)=>menu.querySelector(`[data-loui2-font-control="${name}"] input`);
for(const [name,value] of Object.entries({'sidebar':19,'main-chat':18,'members':17})){
  input(name).value=String(value);
  input(name).dispatchEvent(new Event('input',{bubbles:true}));
}
menu.querySelector('[data-loui2-option="font-reset"]').click();
const size=(selector)=>getComputedStyle(document.querySelector(selector)).fontSize;
document.getElementById('result').textContent=JSON.stringify({
  values:{sidebar:input('sidebar').value,mainChat:input('main-chat').value,members:input('members').value},
  stored:{
    sidebar:window.__gmValues.get('sidebarFontSize'),
    mainChat:window.__gmValues.get('mainChatFontSize'),
    members:window.__gmValues.get('memberListFontSize'),
  },
  sizes:{
    channel:size('ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"]'),
    thread:size('ul[aria-label="Channels"] [aria-label$="(thread)"] [class*="name_"]'),
    message:size('[class*="messageContent_"]'),
    member:size('[class*="membersWrap_"] [class*="name_"]'),
  },
  menuOpen:Boolean(document.getElementById('loui2-discord-suite-menu')),
});
''')
        self.assertEqual(state["values"], {"sidebar": "15", "mainChat": "16", "members": "16"})
        self.assertEqual(state["stored"], {"sidebar": 15, "mainChat": 16, "members": 16})
        self.assertEqual(
            state["sizes"],
            {"channel": "15px", "thread": "13px", "message": "16px", "member": "16px"},
        )
        self.assertTrue(state["menuOpen"])


class SuiteControlTests(unittest.TestCase):
    def test_header_sidebar_buttons_and_suite_dropdown_are_accessible(self):
        state = run_browser_fixture(r'''
const menuGroup=document.getElementById('loui2-discord-suite-controls');
const trigger=menuGroup?.querySelector('[data-loui2-control="menu"]');
const sidebarGroup=document.getElementById('loui2-discord-sidebar-controls');
const titleHost=document.querySelector('.children_fixture');
const leftButton=sidebarGroup?.querySelector('[data-loui2-control="left"]');
const serverButton=sidebarGroup?.querySelector('[data-loui2-control="server"]');
const nativeIcon=titleHost?.querySelector('.channelIcon_fixture');
const result={
  menuGroupCount:document.querySelectorAll('#loui2-discord-suite-controls').length,
  menuButtonCount:menuGroup?.querySelectorAll(':scope > button').length||0,
  menuGroupRole:menuGroup?.getAttribute('role')||null,
  hasTrigger:!!trigger,
  hasPopup:trigger?.getAttribute('aria-haspopup')||null,
  expandedBefore:trigger?.getAttribute('aria-expanded')||null,
  sidebarGroupCount:document.querySelectorAll('#loui2-discord-sidebar-controls').length,
  sidebarButtonCount:sidebarGroup?.querySelectorAll(':scope > button').length||0,
  sidebarGroupRole:sidebarGroup?.getAttribute('role')||null,
  sidebarOrder:[...(sidebarGroup?.querySelectorAll(':scope > button')||[])].map(button=>button.dataset.loui2Control),
  sidebarIsFirst:titleHost?.firstElementChild===sidebarGroup,
  nativeIconFollows:sidebarGroup?.nextElementSibling===nativeIcon,
  leftBefore:{pressed:leftButton?.getAttribute('aria-pressed')||null,label:leftButton?.getAttribute('aria-label')||null},
  serverBefore:{pressed:serverButton?.getAttribute('aria-pressed')||null,label:serverButton?.getAttribute('aria-label')||null},
};
leftButton?.click();
serverButton?.click();
if(trigger){
  trigger.click();
  const menu=document.getElementById('loui2-discord-suite-menu');
  const option=(name)=>menu?.querySelector(`[data-loui2-option="${name}"]`);
  result.menuRole=menu?.getAttribute('role')||null;
  result.expandedOpen=trigger.getAttribute('aria-expanded');
  result.options=[...(menu?.querySelectorAll('[data-loui2-option]')||[])].map((item)=>({
    option:item.dataset.loui2Option,
    role:item.getAttribute('role'),
    checked:item.getAttribute('aria-checked'),
  }));
  const sidebarInput=menu.querySelector('[data-loui2-font-control="sidebar"] input');
  const colorInput=menu.querySelector('[data-loui2-color-control="channel"] input');
  option('mobile').focus();
  const firstNavigationEvent=new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true});
  option('mobile').dispatchEvent(firstNavigationEvent);
  const focusedColorAfterFirst=document.activeElement===colorInput;
  result.arrowNavigation={
    focusedColorAfterFirst,
    firstPrevented:firstNavigationEvent.defaultPrevented,
  };
  sidebarInput.focus();
  const numberEvent=new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true});
  sidebarInput.dispatchEvent(numberEvent);
  result.numberArrow={keptFocus:document.activeElement===sidebarInput,prevented:numberEvent.defaultPrevented};
  option('typing')?.click();
  option('title-channel')?.click();
  await new Promise((resolve)=>setTimeout(resolve,220));
  result.after={
    serverHidden:document.documentElement.hasAttribute('data-loui2-hide-server-rail'),
    leftHidden:document.documentElement.hasAttribute('data-loui2-hide-left-sidebar'),
    typingBlocked:document.documentElement.dataset.loui2TypingBroadcastBlocked,
    title:document.title,
    serverPressed:serverButton?.getAttribute('aria-pressed')||null,
    leftPressed:leftButton?.getAttribute('aria-pressed')||null,
    serverLabel:serverButton?.getAttribute('aria-label')||null,
    leftLabel:leftButton?.getAttribute('aria-label')||null,
    typingChecked:option('typing')?.getAttribute('aria-checked')||null,
    channelChecked:option('title-channel')?.getAttribute('aria-checked')||null,
    menuStillOpen:!!document.getElementById('loui2-discord-suite-menu'),
  };
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  result.closed={
    menuRemoved:!document.getElementById('loui2-discord-suite-menu'),
    expanded:trigger.getAttribute('aria-expanded'),
    triggerFocused:document.activeElement===trigger,
  };
}
document.getElementById('result').textContent=JSON.stringify(result);
''')
        self.assertEqual(state["menuGroupCount"], 1)
        self.assertEqual(state["menuButtonCount"], 1)
        self.assertEqual(state["menuGroupRole"], "group")
        self.assertTrue(state["hasTrigger"])
        self.assertEqual(state["hasPopup"], "menu")
        self.assertEqual(state["expandedBefore"], "false")
        self.assertEqual(state["sidebarGroupCount"], 1)
        self.assertEqual(state["sidebarButtonCount"], 2)
        self.assertEqual(state["sidebarGroupRole"], "group")
        self.assertEqual(state["sidebarOrder"], ["left", "server"])
        self.assertTrue(state["sidebarIsFirst"])
        self.assertTrue(state["nativeIconFollows"])
        self.assertEqual(
            state["leftBefore"],
            {"pressed": "false", "label": "Hide complete left sidebar"},
        )
        self.assertEqual(
            state["serverBefore"],
            {"pressed": "false", "label": "Hide server rail"},
        )
        self.assertEqual(state["menuRole"], "menu")
        self.assertEqual(state["expandedOpen"], "true")
        self.assertEqual(
            state["arrowNavigation"],
            {
                "focusedColorAfterFirst": True,
                "firstPrevented": True,
            },
        )
        self.assertEqual(state["numberArrow"], {"keptFocus": True, "prevented": False})
        self.assertEqual(
            state["options"],
            [
                {"option": "typing", "role": "menuitemcheckbox", "checked": "true"},
                {"option": "browser-shortcuts", "role": "menuitemcheckbox", "checked": "false"},
                {"option": "mobile", "role": "menuitemcheckbox", "checked": "false"},
                {"option": "font-reset", "role": "menuitem", "checked": None},
                {"option": "export", "role": "menuitem", "checked": None},
                {"option": "delete-mine", "role": "menuitem", "checked": None},
                {"option": "title-thread", "role": "menuitemradio", "checked": "true"},
                {"option": "title-channel", "role": "menuitemradio", "checked": "false"},
                {"option": "title-server", "role": "menuitemradio", "checked": "false"},
            ],
        )
        self.assertEqual(
            state["after"],
            {
                "serverHidden": True,
                "leftHidden": True,
                "typingBlocked": "false",
                "title": "#channel-alpha",
                "serverPressed": "true",
                "leftPressed": "true",
                "serverLabel": "Show server rail",
                "leftLabel": "Show complete left sidebar",
                "typingChecked": "false",
                "channelChecked": "true",
                "menuStillOpen": True,
            },
        )
        self.assertEqual(
            state["closed"],
            {"menuRemoved": True, "expanded": "false", "triggerFocused": True},
        )

class SuiteBrowserShortcutTests(unittest.TestCase):
    def test_ctrl_shift_a_is_released_only_when_enabled_and_cleanup_restores_propagation(self):
        state = run_browser_fixture(r'''
const observed=[];
const observe=(event)=>observed.push({
  type:event.type,
  key:event.key,ctrl:event.ctrlKey,shift:event.shiftKey,alt:event.altKey,meta:event.metaKey,
});
window.addEventListener('keydown',observe);
window.addEventListener('keyup',observe);
const eventTarget=document.querySelector('[role="textbox"]');
const fire=(init,type='keydown')=>{
  const event=new KeyboardEvent(type,{bubbles:true,cancelable:true,...init});
  const dispatched=eventTarget.dispatchEvent(event);
  return {dispatched,defaultPrevented:event.defaultPrevented};
};
const exact={key:'A',code:'KeyA',ctrlKey:true,shiftKey:true};
const disabledResult=fire(exact);
const disabledObserved=observed.length;
document.querySelector('[data-loui2-control="menu"]').click();
const option=document.querySelector('[data-loui2-option="browser-shortcuts"]');
const before=option?.getAttribute('aria-checked');
option?.click();
observed.length=0;
const enabledResult=fire(exact);
const enabledKeyupResult=fire(exact,'keyup');
const enabledObserved=observed.length;
for(const near of [
  {key:'A',code:'KeyA',ctrlKey:true,shiftKey:true,altKey:true},
  {key:'A',code:'KeyA',ctrlKey:true,shiftKey:true,metaKey:true},
  {key:'a',code:'KeyA',ctrlKey:true},
  {key:'A',code:'KeyA',shiftKey:true},
  {key:'B',code:'KeyB',ctrlKey:true,shiftKey:true},
  {key:'A',code:'KeyA',ctrlKey:true,shiftKey:true,isComposing:true},
]) fire(near);
const afterNear=observed.length;
option?.click();
fire(exact);
const afterTabDisable=observed.length;
option?.click();
fire(exact);
const afterTabEnable=observed.length;
window.__loui2DiscordWebSuiteRuntime.cleanup();
fire(exact);
document.getElementById('result').textContent=JSON.stringify({
  disabledResult,disabledObserved,before,
  afterClick:'true',
  stored:window.__gmValues.get('releaseCtrlShiftAToBrowser'),
  enabledResult,enabledKeyupResult,enabledObserved,afterNear,afterTabDisable,afterTabEnable,
  afterCleanup:observed.length,
});
''')
        self.assertEqual(state["disabledResult"], {"dispatched": True, "defaultPrevented": False})
        self.assertEqual(state["disabledObserved"], 1)
        self.assertEqual(state["before"], "false")
        self.assertEqual(state["afterClick"], "true")
        self.assertTrue(state["stored"])
        self.assertEqual(state["enabledResult"], {"dispatched": True, "defaultPrevented": False})
        self.assertEqual(state["enabledKeyupResult"], {"dispatched": True, "defaultPrevented": False})
        self.assertEqual(state["enabledObserved"], 0)
        self.assertEqual(state["afterNear"], 6)
        self.assertEqual(state["afterTabDisable"], 7)
        self.assertEqual(state["afterTabEnable"], 7)
        self.assertEqual(state["afterCleanup"], 8)

    def test_reinjection_preserves_document_start_priority_over_later_page_capture_listener(self):
        source = 'GM_setValue("releaseCtrlShiftAToBrowser",true);\n' + SUITE.read_text()
        state = run_browser_fixture(r'''
let discordCalls=0;
const discordCapture=(event)=>{
  if(event.ctrlKey&&event.shiftKey&&(event.key==='a'||event.key==='A')){
    discordCalls++;
    event.preventDefault();
  }
};
window.addEventListener('keydown',discordCapture,true);
(0,eval)(window.__suiteSource);
const target=document.querySelector('[role="textbox"]');
const fire=()=>{
  const event=new KeyboardEvent('keydown',{
    key:'A',code:'KeyA',ctrlKey:true,shiftKey:true,bubbles:true,cancelable:true,
  });
  const dispatched=target.dispatchEvent(event);
  return {dispatched,defaultPrevented:event.defaultPrevented};
};
const afterReinject=fire();
const callsAfterReinject=discordCalls;
window.__loui2DiscordWebSuiteRuntime.cleanup();
const afterCleanup=fire();
window.removeEventListener('keydown',discordCapture,true);
document.getElementById('result').textContent=JSON.stringify({
  afterReinject,callsAfterReinject,afterCleanup,discordCalls,
});
''', source_override=source)
        self.assertEqual(state, {
            "afterReinject": {"dispatched": True, "defaultPrevented": False},
            "callsAfterReinject": 0,
            "afterCleanup": {"dispatched": False, "defaultPrevented": True},
            "discordCalls": 1,
        })

    def test_persisted_shortcut_release_is_active_at_startup(self):
        source = 'GM_setValue("releaseCtrlShiftAToBrowser",true);\n' + SUITE.read_text()
        state = run_browser_fixture(r'''
let observed=0;
window.addEventListener('keydown',()=>{ observed++; });
const event=new KeyboardEvent('keydown',{
  key:'A',code:'KeyA',ctrlKey:true,shiftKey:true,bubbles:true,cancelable:true,
});
const dispatched=window.dispatchEvent(event);
document.querySelector('[data-loui2-control="menu"]').click();
document.getElementById('result').textContent=JSON.stringify({
  observed,dispatched,defaultPrevented:event.defaultPrevented,
  checked:document.querySelector('[data-loui2-option="browser-shortcuts"]')?.getAttribute('aria-checked'),
});
''', source_override=source)
        self.assertEqual(state, {
            "observed": 0,
            "dispatched": True,
            "defaultPrevented": False,
            "checked": "true",
        })


class SuitePersistenceTests(unittest.TestCase):
    def test_user_changes_before_delayed_tab_hydration_override_stale_saved_state(self):
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="left"]').click();
document.querySelector('[data-loui2-control="menu"]').click();
document.querySelector('[data-loui2-option="typing"]').click();
document.querySelector('[data-loui2-option="title-channel"]').click();
window.__deferredGetTab({
  tabTitleMode:'server',
  leftHidden:false,
  channelNameColor:'#83a598',
});
await new Promise((resolve)=>setTimeout(resolve,220));
document.getElementById('result').textContent=JSON.stringify({
  tab:window.__tabObject,
  left:document.documentElement.hasAttribute('data-loui2-hide-left-sidebar'),
  typing:document.documentElement.dataset.loui2TypingBroadcastBlocked,
  globalTyping:window.__gmValues.get('blockTypingBroadcasts'),
  tabHasTyping:Object.prototype.hasOwnProperty.call(window.__tabObject,'typingBlocked'),
  channelColor:document.documentElement.style.getPropertyValue('--loui2-channel-name-color'),
  tabHasColor:Object.prototype.hasOwnProperty.call(window.__tabObject,'channelNameColor'),
  title:document.title,
});
''', defer_gm_get_tab=True)
        self.assertEqual(state["left"], True)
        self.assertEqual(state["typing"], "false")
        self.assertEqual(state["globalTyping"], False)
        self.assertEqual(state["tabHasTyping"], False)
        self.assertEqual(state["channelColor"], "#b8bb26")
        self.assertEqual(state["tabHasColor"], False)
        self.assertEqual(state["title"], "#channel-alpha")
        self.assertEqual(state["tab"]["leftHidden"], True)
        self.assertEqual(state["tab"]["tabTitleMode"], "channel")

    def test_global_workspace_values_apply_without_globalizing_sidebar_state(self):
        source = r'''
GM_setValue('hideServerRail',true);
GM_setValue('hideLeftSidebar',true);
GM_setValue('blockTypingBroadcasts',false);
GM_setValue('releaseCtrlShiftAToBrowser',true);
GM_setValue('forceFullWidthMobileLayout',true);
''' + SUITE.read_text()
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="menu"]').click();
document.getElementById('result').textContent=JSON.stringify({
  server:document.documentElement.hasAttribute('data-loui2-hide-server-rail'),
  left:document.documentElement.hasAttribute('data-loui2-hide-left-sidebar'),
  typing:document.querySelector('[data-loui2-option="typing"]').getAttribute('aria-checked'),
  shortcuts:document.querySelector('[data-loui2-option="browser-shortcuts"]').getAttribute('aria-checked'),
  mobile:document.querySelector('[data-loui2-option="mobile"]').getAttribute('aria-checked'),
  mobileActive:document.documentElement.hasAttribute('data-loui2-discord-full-width-mobile'),
});
''', source_override=source)
        self.assertEqual(
            state,
            {
                "server": False,
                "left": False,
                "typing": "false",
                "shortcuts": "true",
                "mobile": "true",
                "mobileActive": True,
            },
        )

    def test_workspace_appearance_and_typography_are_global_while_sidebar_and_title_are_per_tab(self):
        state = run_browser_fixture(r'''
document.querySelector('[data-loui2-control="left"]').click();
document.querySelector('[data-loui2-control="server"]').click();
document.querySelector('[data-loui2-control="menu"]').click();
const option=(name)=>document.querySelector(`[data-loui2-option="${name}"]`);
option('typing').click();
option('browser-shortcuts').click();
option('mobile').click();
option('title-channel').click();
const channelColor=document.querySelector('[data-loui2-color-control="channel"] input');
channelColor.value='#fabd2f';
channelColor.dispatchEvent(new Event('input',{bubbles:true}));
const sidebar=document.querySelector('[data-loui2-font-control="sidebar"] input');
sidebar.value='18';
sidebar.dispatchEvent(new Event('input',{bubbles:true}));
await new Promise((resolve)=>setTimeout(resolve,220));
const localKeys=['hideServerRail','hideLeftSidebar','blockTypingBroadcasts','releaseCtrlShiftAToBrowser','forceFullWidthMobileLayout','channelNameColor'];
document.getElementById('result').textContent=JSON.stringify({
  tab:window.__tabObject,
  globalLocalKeys:localKeys.filter((key)=>window.__gmValues.has(key)),
  globalSidebar:window.__gmValues.get('sidebarFontSize')??null,
  listenerKeys:[...window.__gmListeners.values()].map((entry)=>entry.key).sort(),
});
''')
        self.assertEqual(
            state["tab"],
            {
                "tabTitleMode": "channel",
                "serverHidden": True,
                "leftHidden": True,
            },
        )
        self.assertEqual(
            state["globalLocalKeys"],
            [
                "blockTypingBroadcasts",
                "releaseCtrlShiftAToBrowser",
                "forceFullWidthMobileLayout",
                "channelNameColor",
            ],
        )
        self.assertEqual(state["globalSidebar"], 18)
        self.assertEqual(
            state["listenerKeys"],
            [
                "blockTypingBroadcasts",
                "channelNameColor",
                "forceFullWidthMobileLayout",
                "mainChatFontSize",
                "memberListFontSize",
                "releaseCtrlShiftAToBrowser",
                "sidebarFontSize",
                "textFontWeight",
            ],
        )

    def test_remote_workspace_and_typography_sync_leave_sidebar_state_isolated(self):
        state = run_browser_fixture(r'''
const sendRemote=(key,value)=>{
  const entry=[...window.__gmListeners.values()].find((candidate)=>candidate.key===key);
  entry.callback(key,undefined,value,true);
};
sendRemote('blockTypingBroadcasts',false);
sendRemote('releaseCtrlShiftAToBrowser',true);
sendRemote('forceFullWidthMobileLayout',true);
sendRemote('channelNameColor','#fabd2f');
sendRemote('sidebarFontSize',19);
sendRemote('mainChatFontSize',18);
sendRemote('memberListFontSize',14);
sendRemote('textFontWeight',200);
document.querySelector('[data-loui2-control="menu"]').click();
const suiteMenu=document.getElementById('loui2-discord-suite-menu');
const typingOption=suiteMenu.querySelector('[data-loui2-option="typing"]');
const remote={
  server:document.documentElement.hasAttribute('data-loui2-hide-server-rail'),
  left:document.documentElement.hasAttribute('data-loui2-hide-left-sidebar'),
  typing:typingOption.getAttribute('aria-checked'),
  shortcuts:suiteMenu.querySelector('[data-loui2-option="browser-shortcuts"]').getAttribute('aria-checked'),
  mobile:suiteMenu.querySelector('[data-loui2-option="mobile"]').getAttribute('aria-checked'),
  channelColor:suiteMenu.querySelector('[data-loui2-color-control="channel"] input').value,
  workspaceListeners:['blockTypingBroadcasts','releaseCtrlShiftAToBrowser','forceFullWidthMobileLayout']
    .filter(key=>[...window.__gmListeners.values()].some(entry=>entry.key===key)),
  fontValues:Object.fromEntries(['sidebar','main-chat','members','weight'].map(name=>[
    name,
    suiteMenu.querySelector(`[data-loui2-font-control="${name}"] input`).value,
  ])),
  computed:{
    channel:getComputedStyle(document.querySelector('ul[aria-label="Channels"] [aria-label$=" channel)"] [class*="name_"]')).fontSize,
    message:getComputedStyle(document.querySelector('[class*="messageContent_"]')).fontSize,
    member:getComputedStyle(document.querySelector('[class*="membersWrap_"] [class*="name_"]')).fontSize,
    messageWeight:getComputedStyle(document.querySelector('[class*="messageContent_"]')).fontWeight,
    memberWeight:getComputedStyle(document.querySelector('[class*="membersWrap_"] [class*="name_"]')).fontWeight,
  },
};
const typingMenu=[...window.__gmMenus.values()].find((entry)=>entry.label==='Toggle Discord typing broadcast');
typingMenu.callback();
const afterMenu={
  typing:typingOption.getAttribute('aria-checked'),
  tabHasTyping:Object.prototype.hasOwnProperty.call(window.__tabObject,'typingBlocked'),
  global:window.__gmValues.get('blockTypingBroadcasts'),
};
document.getElementById('result').textContent=JSON.stringify({remote,afterMenu,listenerCount:window.__gmListeners.size});
''')
        self.assertEqual(
            state["remote"],
            {
                "server": False,
                "left": False,
                "typing": "false",
                "shortcuts": "true",
                "mobile": "true",
                "channelColor": "#fabd2f",
                "workspaceListeners": [
                    "blockTypingBroadcasts",
                    "releaseCtrlShiftAToBrowser",
                    "forceFullWidthMobileLayout",
                ],
                "fontValues": {"sidebar": "19", "main-chat": "18", "members": "14", "weight": "200"},
                "computed": {
                    "channel": "19px",
                    "message": "18px",
                    "member": "14px",
                    "messageWeight": "200",
                    "memberWeight": "200",
                },
            },
        )
        self.assertEqual(
            state["afterMenu"],
            {"typing": "true", "tabHasTyping": False, "global": True},
        )
        self.assertEqual(state["listenerCount"], 8)


class SuiteTypingTests(unittest.TestCase):
    def test_typing_requests_resolve_locally_and_unrelated_requests_pass_through(self):
        state = run_browser_fixture(r'''
const events=[];
const typing=new XMLHttpRequest();
for(const name of ['readystatechange','load','loadend']) typing.addEventListener(name,()=>events.push(name));
typing.open('POST','/api/v9/channels/123456789012345678/typing');
typing.send();
await new Promise((resolve)=>setTimeout(resolve,20));
const blockedXHR={status:typing.status,readyState:typing.readyState,network:window.__xhrNetworkSends,events};

const normal=new XMLHttpRequest();
normal.open('POST','/api/v9/channels/123456789012345678/messages');
normal.send('{}');
const afterNormalXHR=window.__xhrNetworkSends;

const blockedFetch=await fetch('/api/v9/channels/123456789012345678/typing',{method:'POST'});
const afterBlockedFetch={status:blockedFetch.status,network:window.__fetchNetworkSends};
await fetch('/api/v9/channels/123456789012345678/messages',{method:'POST'});
const afterNormalFetch=window.__fetchNetworkSends;

document.querySelector('[data-loui2-control="menu"]').click();
const typingOption=document.querySelector('#loui2-discord-suite-menu [data-loui2-option="typing"]');
typingOption.click();
const allowed=new XMLHttpRequest();
allowed.open('POST','/api/v9/channels/123456789012345678/typing');
allowed.send();

document.getElementById('result').textContent=JSON.stringify({
  blockedXHR,
  afterNormalXHR,
  afterBlockedFetch,
  afterNormalFetch,
  afterAllowedTypingXHR:window.__xhrNetworkSends,
  typingPressed:typingOption.getAttribute('aria-checked'),
  blockedCount:document.documentElement.dataset.loui2TypingRequestsBlocked||'0',
});
''')
        self.assertEqual(state["blockedXHR"]["status"], 204)
        self.assertEqual(state["blockedXHR"]["readyState"], 4)
        self.assertEqual(state["blockedXHR"]["network"], 0)
        self.assertIn("load", state["blockedXHR"]["events"])
        self.assertIn("loadend", state["blockedXHR"]["events"])
        self.assertEqual(state["afterNormalXHR"], 1)
        self.assertEqual(state["afterBlockedFetch"], {"status": 204, "network": 0})
        self.assertEqual(state["afterNormalFetch"], 1)
        self.assertEqual(state["afterAllowedTypingXHR"], 2)
        self.assertEqual(state["typingPressed"], "false")
        self.assertEqual(state["blockedCount"], "2")

    def test_transport_patches_tampermonkey_unsafe_window_realm(self):
        state = run_browser_fixture(
            r'''
const typingResponse=await unsafeWindow.fetch(
  '/api/v9/channels/123456789012345678/typing',
  {method:'POST'}
);
const normalResponse=await unsafeWindow.fetch('/favicon.ico');
document.getElementById('result').textContent=JSON.stringify({
  typingStatus:typingResponse.status,
  typingBody:await typingResponse.text(),
  normalStatus:normalResponse.status,
  unsafeFetchCalls:window.__unsafeFetchCalls,
  blockedCount:document.documentElement.dataset.loui2TypingRequestsBlocked||'0',
});
''',
            separate_unsafe_window=True,
        )
        self.assertEqual(
            state,
            {
                "typingStatus": 204,
                "typingBody": "",
                "normalStatus": 200,
                "unsafeFetchCalls": 1,
                "blockedCount": "1",
            },
        )

    def test_later_fetch_replacement_is_not_forcibly_overwritten(self):
        state = run_browser_fixture(r'''
window.__replacementFetchCalls=0;
window.fetch=async (...args)=>{
  window.__replacementFetchCalls++;
  return new Response(JSON.stringify(args), {status:200});
};
const typingResponse=await fetch(
  '/api/v9/channels/123456789012345678/typing',
  {method:'POST'}
);
const normalResponse=await fetch('/favicon.ico');
document.getElementById('result').textContent=JSON.stringify({
  typingStatus:typingResponse.status,
  typingBody:await typingResponse.text(),
  normalStatus:normalResponse.status,
  replacementCalls:window.__replacementFetchCalls,
  baseFetchCalls:window.__fetchNetworkSends,
  blockedCount:document.documentElement.dataset.loui2TypingRequestsBlocked||'0',
});
''')
        self.assertEqual(state["typingStatus"], 200)
        self.assertIn("/typing", state["typingBody"])
        self.assertEqual(state["normalStatus"], 200)
        self.assertEqual(state["replacementCalls"], 2)
        self.assertEqual(state["baseFetchCalls"], 0)
        self.assertEqual(state["blockedCount"], "0")

    def test_noncooperative_later_fetch_wrapper_is_not_forcibly_replaced(self):
        state = run_browser_fixture(r'''
window.__discordWrapperCalls=0;
window.fetch=(...args)=>{
  window.__discordWrapperCalls++;
  return window.fetch(...args);
};
await new Promise(resolve=>setTimeout(resolve,300));
let outcome;
try {
  const response=await fetch('/favicon.ico');
  outcome={status:response.status,fetchError:null};
} catch(error) {
  outcome={status:null,fetchError:error.name};
}
document.getElementById('result').textContent=JSON.stringify({
  ...outcome,
  discordWrapperCalls:window.__discordWrapperCalls,
  baseFetchCalls:window.__fetchNetworkSends,
});
''')
        self.assertIsNone(state["status"])
        self.assertEqual(state["fetchError"], "RangeError")
        self.assertGreater(state["discordWrapperCalls"], 1)
        self.assertEqual(state["baseFetchCalls"], 0)

    def test_typing_privacy_survives_theme_style_injection_failure(self):
        state = run_browser_fixture(
            r'''
const typing=new XMLHttpRequest();
typing.open('POST','/api/v9/channels/123456789012345678/typing');
typing.send();
await new Promise((resolve)=>setTimeout(resolve,20));
document.getElementById('result').textContent=JSON.stringify({
  status:typing.status,
  readyState:typing.readyState,
  network:window.__xhrNetworkSends,
  marker:document.documentElement.dataset.loui2DiscordInvisibleTyping||null,
});
''',
            gm_add_style_throws=True,
        )
        self.assertEqual(
            state,
            {"status": 204, "readyState": 4, "network": 0, "marker": "2.7.33"},
        )


class SuiteRenderedExtractionTests(unittest.TestCase):
    def test_extraction_route_ids_are_validated_and_escaped(self):
        source = SUITE.read_text()
        self.assertIn("function isDiscordSnowflake", source)
        context_block = source[source.index("  function getExtractionContext"):source.index("  function escapeExtractionHtml")]
        self.assertIn("isDiscordSnowflake(guildId)", context_block)
        self.assertIn("isDiscordSnowflake(channelId)", context_block)
        header_block = source[source.index("  function buildExtractionHeader"):source.index("  function openExtractionOutput")]
        self.assertIn("escapeExtractionMarkdown(context.channelId)", header_block)
        self.assertIn("escapeExtractionMarkdown(context.guildId)", header_block)



class SuiteCleanupTests(unittest.TestCase):
    def test_deferred_tab_callback_cannot_restart_title_feature_after_cleanup(self):
        state = run_browser_fixture(r'''
const runtime=window.__loui2DiscordWebSuiteRuntime;
runtime.cleanup();
window.__deferredGetTab(window.__tabObject);
await Promise.resolve();
document.getElementById('result').textContent=JSON.stringify({
  runtime:Boolean(window.__loui2DiscordWebSuiteRuntime),
  menus:window.__gmMenus.size,
  listeners:window.__gmListeners.size,
  marker:document.documentElement.dataset.loui2DiscordTabTitle||null,
});
''', defer_gm_get_tab=True)
        self.assertEqual(
            state,
            {"runtime": False, "menus": 0, "listeners": 0, "marker": "thread:Existing standalone title"},
        )

    def test_runtime_cleanup_restores_browser_primitives_and_removes_suite_artifacts(self):
        state = run_browser_fixture(r'''
const runtimeBefore=!!window.__loui2DiscordWebSuiteRuntime;
const sidebarControlBefore=!!document.getElementById('loui2-discord-sidebar-controls');
const typographyBefore={
  sidebar:document.documentElement.style.getPropertyValue('--loui2-sidebar-font-size'),
  mainChat:document.documentElement.style.getPropertyValue('--loui2-main-chat-font-size'),
  members:document.documentElement.style.getPropertyValue('--loui2-member-font-size'),
};
window.__loui2DiscordWebSuiteRuntime.cleanup();
document.getElementById('result').textContent=JSON.stringify({
  runtimeBefore,
  sidebarControlBefore,
  typographyBefore,
  typographyAfter:{
    sidebar:document.documentElement.style.getPropertyValue('--loui2-sidebar-font-size'),
    mainChat:document.documentElement.style.getPropertyValue('--loui2-main-chat-font-size'),
    members:document.documentElement.style.getPropertyValue('--loui2-member-font-size'),
  },
  runtimeAfter:!!window.__loui2DiscordWebSuiteRuntime,
  control:!!document.getElementById('loui2-discord-suite-controls'),
  sidebarControl:!!document.getElementById('loui2-discord-sidebar-controls'),
  style:!!document.querySelector('style[data-loui2-suite]'),
  openRestored:XMLHttpRequest.prototype.open===window.__nativeOpen,
  sendRestored:XMLHttpRequest.prototype.send===window.__nativeSend,
  abortRestored:XMLHttpRequest.prototype.abort===window.__nativeAbort,
  fetchRestored:window.fetch===window.__nativeFetch,
  pushRestored:history.pushState===window.__nativePushState,
  replaceRestored:history.replaceState===window.__nativeReplaceState,
  listenerCount:window.__gmListeners.size,
  menuCount:window.__gmMenus.size,
  suiteMarker:document.documentElement.dataset.loui2DiscordWebSuite||null,
  typingMarker:document.documentElement.dataset.loui2DiscordInvisibleTyping||null,
  restoredThemeMarker:document.documentElement.dataset.loui2GruvboxSharp||null,
  restoredTitleMarker:document.documentElement.dataset.loui2DiscordTabTitle||null,
});
''')
        self.assertTrue(state["runtimeBefore"])
        self.assertTrue(state["sidebarControlBefore"])
        self.assertEqual(state["typographyBefore"], {"sidebar": "15px", "mainChat": "16px", "members": "16px"})
        self.assertEqual(state["typographyAfter"], {"sidebar": "", "mainChat": "", "members": ""})
        self.assertFalse(state["runtimeAfter"])
        self.assertFalse(state["control"])
        self.assertFalse(state["sidebarControl"])
        self.assertFalse(state["style"])
        self.assertTrue(state["openRestored"])
        self.assertTrue(state["sendRestored"])
        self.assertTrue(state["abortRestored"])
        self.assertTrue(state["fetchRestored"])
        self.assertTrue(state["pushRestored"])
        self.assertTrue(state["replaceRestored"])
        self.assertEqual(state["listenerCount"], 0)
        self.assertEqual(state["menuCount"], 0)
        self.assertIsNone(state["suiteMarker"])
        self.assertIsNone(state["typingMarker"])
        self.assertEqual(state["restoredThemeMarker"], "1.6.0")
        self.assertEqual(state["restoredTitleMarker"], "thread:Existing standalone title")

    def test_cleanup_restores_prior_typography_priority_and_preserves_later_owner(self):
        prelude = r'''
document.documentElement.style.setProperty('--loui2-sidebar-font-size','13px','important');
'''
        state = run_browser_fixture(r'''
document.documentElement.style.setProperty('--loui2-member-font-size','22px','important');
window.__loui2DiscordWebSuiteRuntime.cleanup();
const read=(property)=>({
  value:document.documentElement.style.getPropertyValue(property),
  priority:document.documentElement.style.getPropertyPriority(property),
});
document.getElementById('result').textContent=JSON.stringify({
  sidebar:read('--loui2-sidebar-font-size'),
  mainChat:read('--loui2-main-chat-font-size'),
  members:read('--loui2-member-font-size'),
});
''', source_override=prelude + SUITE.read_text())
        self.assertEqual(state["sidebar"], {"value": "13px", "priority": "important"})
        self.assertEqual(state["mainChat"], {"value": "", "priority": ""})
        self.assertEqual(state["members"], {"value": "22px", "priority": "important"})


class SuiteSpaTests(unittest.TestCase):
    def test_spa_rerender_restores_controls_and_refreshes_the_title(self):
        state = run_browser_fixture(r'''
const replacement=document.createElement('div');
replacement.className='toolbar_fixture';
replacement.innerHTML='<div class="native" role="button" aria-label="Threads"></div>';
document.querySelector('.toolbar_fixture').replaceWith(replacement);
const replacementTitle=document.createElement('div');
replacementTitle.className='children_fixture';
replacementTitle.innerHTML='<div class="channelIcon_fixture"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M3 3h18v18H3z"></path></svg></div><h2 class="heading_fixture parentChannelName_fixture">#channel-alpha</h2>';
document.querySelector('.children_fixture').replaceWith(replacementTitle);
document.querySelector('.thread_heading_fixture').textContent='Thread: New Thread chat';
await new Promise((resolve)=>setTimeout(resolve,260));
const sidebarControls=replacementTitle.querySelector('#loui2-discord-sidebar-controls');
document.getElementById('result').textContent=JSON.stringify({
  controls:replacement.querySelectorAll('#loui2-discord-suite-controls').length,
  totalControls:document.querySelectorAll('#loui2-discord-suite-controls').length,
  sidebarControls:sidebarControls?.querySelectorAll(':scope > button').length||0,
  totalSidebarControls:document.querySelectorAll('#loui2-discord-sidebar-controls').length,
  sidebarFirst:replacementTitle.firstElementChild===sidebarControls,
  sidebarOrder:[...(sidebarControls?.querySelectorAll(':scope > button')||[])].map(button=>button.dataset.loui2Control),
  title:document.title,
  marker:document.documentElement.dataset.loui2DiscordTabTitle,
});
''')
        self.assertEqual(state["controls"], 1)
        self.assertEqual(state["totalControls"], 1)
        self.assertEqual(state["sidebarControls"], 2)
        self.assertEqual(state["totalSidebarControls"], 1)
        self.assertTrue(state["sidebarFirst"])
        self.assertEqual(state["sidebarOrder"], ["left", "server"])
        self.assertEqual(state["title"], "New Thread")
        self.assertEqual(state["marker"], "thread:New Thread")


class SuiteTitleTests(unittest.TestCase):
    def test_per_tab_title_modes_drive_thread_channel_and_server_titles(self):
        state = run_browser_fixture(r'''
const menu=(fragment)=>[...window.__gmMenus.values()].find((entry)=>entry.label.includes(fragment));
const initial={title:document.title,mode:window.__tabObject.tabTitleMode};
menu('use channel name').callback();
await new Promise((resolve)=>setTimeout(resolve,220));
const channel={title:document.title,mode:window.__tabObject.tabTitleMode};
menu('use server name').callback();
await new Promise((resolve)=>setTimeout(resolve,220));
const server={
  title:document.title,
  mode:window.__tabObject.tabTitleMode,
  marker:document.documentElement.dataset.loui2DiscordTabTitle,
};
document.getElementById('result').textContent=JSON.stringify({initial,channel,server,menus:[...window.__gmMenus.values()].map((entry)=>entry.label)});
''')
        self.assertEqual(state["initial"], {"title": "Thread Beta", "mode": "thread"})
        self.assertEqual(state["channel"], {"title": "#channel-alpha", "mode": "channel"})
        self.assertEqual(
            state["server"],
            {"title": "Server Alpha", "mode": "server", "marker": "server:Server Alpha"},
        )
        self.assertIn("This Discord tab: use thread name", state["menus"])
        self.assertIn("This Discord tab: use channel name", state["menus"])
        self.assertIn("This Discord tab: use server name", state["menus"])


class SuiteIsolationTests(unittest.TestCase):
    def test_tab_title_modes_are_isolated_between_independent_tabs(self):
        body = r'''
document.getElementById('result').textContent=JSON.stringify({
  title:document.title,
  mode:window.__tabObject.tabTitleMode,
});
'''
        server_tab = run_browser_fixture(body, tab_mode="server")
        channel_tab = run_browser_fixture(body, tab_mode="channel")
        self.assertEqual(server_tab, {"title": "Server Alpha", "mode": "server"})
        self.assertEqual(channel_tab, {"title": "#channel-alpha", "mode": "channel"})

    def test_reinjecting_the_suite_does_not_stack_controls_or_transport_hooks(self):
        state = run_browser_fixture(r'''
(0,eval)(window.__suiteSource);
await new Promise((resolve)=>setTimeout(resolve,340));
const typing=new XMLHttpRequest();
typing.open('POST','/api/v9/channels/123456789012345678/typing');
typing.send();
await new Promise((resolve)=>setTimeout(resolve,20));
document.getElementById('result').textContent=JSON.stringify({
  controls:document.querySelectorAll('#loui2-discord-suite-controls').length,
  styles:document.querySelectorAll('style[data-loui2-suite]').length,
  listeners:window.__gmListeners.size,
  menus:window.__gmMenus.size,
  typingStatus:typing.status,
  typingNetwork:window.__xhrNetworkSends,
  blockedCount:document.documentElement.dataset.loui2TypingRequestsBlocked||'0',
  runtimeVersion:window.__loui2DiscordWebSuiteRuntime?.version||null,
});
''', virtual_time_ms=1400)
        self.assertEqual(
            state,
            {
                "controls": 1,
                "styles": 1,
                "listeners": 8,
                "menus": 6,
                "typingStatus": 204,
                "typingNetwork": 0,
                "blockedCount": "1",
                "runtimeVersion": "2.7.33",
            },
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
