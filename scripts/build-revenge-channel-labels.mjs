#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pluginDir = path.join(root, "revenge", "channel-labels");
const source = await fs.readFile(path.join(pluginDir, "src", "index.cjs"), "utf8");
const sourceManifest = JSON.parse(
  await fs.readFile(path.join(pluginDir, "manifest.source.json"), "utf8"),
);

const bundle = `(() => {\n  const module = { exports: {} };\n  const exports = module.exports;\n  ((module, exports) => {\n${source}\n  })(module, exports);\n  return module.exports.createPlugin(vendetta);\n})()\n`;
const hash = crypto.createHash("sha256").update(bundle).digest("hex");
const manifest = {
  ...sourceManifest,
  main: "index.js",
  hash,
};

await fs.writeFile(path.join(pluginDir, "index.js"), bundle);
await fs.writeFile(
  path.join(pluginDir, "manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`,
);

console.log(`Built Revenge channel-label plugin ${hash}`);
