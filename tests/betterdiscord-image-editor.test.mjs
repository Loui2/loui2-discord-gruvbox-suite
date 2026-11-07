import assert from 'node:assert/strict';
import {readFileSync, mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import test from 'node:test';

const theme = readFileSync(new URL('../betterdiscord/Loui2GruvboxSharp.theme.css', import.meta.url), 'utf8');

test('theme preserves transparent image-editor overlays and native crop masks', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'gruvbox-image-editor-'));
  try {
    // Component-level fixture, not a capture of the current private Discord DOM.
    // The crop surface must remain transparent so the image beneath stays visible.
    const html = `<!doctype html><html class="theme-dark"><head><style>
      .overlay_cropFixture { background-color: transparent; }
      .overlay_maskFixture { background-color: rgba(0,0,0,.5); }
    </style><style>${theme.replace(/@import[^;]+;/g, '')}</style></head>
    <body><div id="app-mount"><div role="dialog" aria-label="Edit Image">
    <div class="overlay_cropFixture" id="avatar"></div>
    <div class="overlay_cropFixture" id="banner"></div>
    <div class="overlay_maskFixture" id="mask"></div>
    </div></div><pre id="result"></pre><script>
    document.getElementById('result').textContent = JSON.stringify(
      ['avatar','banner','mask'].map(id=>getComputedStyle(document.getElementById(id)).backgroundColor));
    </script></body></html>`;
    const file = path.join(dir, 'fixture.html');
    writeFileSync(file, html);
    const run = spawnSync(process.env.CHROMIUM_BIN || 'chromium', [
      '--headless', '--no-sandbox', '--disable-gpu', '--no-first-run',
      '--host-resolver-rules=MAP * ~NOTFOUND', `--user-data-dir=${path.join(dir, 'profile')}`,
      '--dump-dom', pathToFileURL(file).href,
    ], {encoding:'utf8', timeout:30000});
    assert.equal(run.status, 0, run.stderr);
    const match = run.stdout.match(/<pre id="result">([^<]+)<\/pre>/);
    assert.ok(match, 'browser returned computed colors');
    assert.deepEqual(JSON.parse(match[1]), [
      'rgba(0, 0, 0, 0)', 'rgba(0, 0, 0, 0)', 'rgba(0, 0, 0, 0.5)',
    ], 'theme must not turn image-editor overlays into opaque surfaces');
  } finally {
    rmSync(dir, {recursive:true, force:true});
  }
});
