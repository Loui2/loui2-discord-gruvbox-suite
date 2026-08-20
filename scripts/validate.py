#!/usr/bin/env python3
"""Validate the published Discord customization artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USERSCRIPT = ROOT / "tampermonkey/loui2-discord-web-suite.user.js"
BETTERDISCORD = ROOT / "betterdiscord/Loui2GruvboxSharp.theme.css"
REVENGE = ROOT / "revenge/theme.json"
REVENGE_PLUGIN = ROOT / "revenge/channel-labels/index.js"
REVENGE_PLUGIN_MANIFEST = ROOT / "revenge/channel-labels/manifest.json"
REVENGE_PLUGIN_README = ROOT / "revenge/channel-labels/README.md"
REVENGE_PLUGIN_SOURCE = ROOT / "revenge/channel-labels/src/index.cjs"
REVENGE_README = ROOT / "revenge/README.md"
README = ROOT / "README.md"
LICENSE = ROOT / "LICENSE"
NOTICE = ROOT / "NOTICE.md"
REPO = "Loui2/loui2-discord-gruvbox-suite"
OLD_REPO = "Loui2/loui2-gruvbox-sharp-revenge"
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_userscript(text: str) -> None:
    metadata_version = re.search(r"^// @version\s+(\S+)$", text, re.MULTILINE)
    runtime_version = re.search(r'^\s*const VERSION = "([^"]+)";$', text, re.MULTILINE)
    if metadata_version is None:
        raise AssertionError("userscript @version is missing")
    if runtime_version is None:
        raise AssertionError("userscript runtime VERSION is missing")
    require(metadata_version.group(1) == runtime_version.group(1), "userscript versions disagree")
    require(f"https://github.com/{REPO}" in text, "userscript homepage points elsewhere")
    raw_url = f"https://raw.githubusercontent.com/{REPO}/main/tampermonkey/{USERSCRIPT.name}"
    require(text.count(raw_url) == 2, "userscript update/download URLs are missing or duplicated")
    require("// @license      MIT" in text, "userscript MIT metadata is missing")
    require("Original Gruvbox Sharp: Copyright (c) 2026 Liang Zhang." in text, "userscript original copyright is missing")
    require("Permission is hereby granted, free of charge" in text, "userscript MIT permission notice is missing")
    require("THE SOFTWARE IS PROVIDED \"AS IS\"" in text, "userscript MIT warranty disclaimer is missing")

    node = shutil.which("node")
    if node is None:
        raise AssertionError("node is required for userscript syntax validation")
    result = subprocess.run([node, "--check", str(USERSCRIPT)], capture_output=True, text=True)
    require(result.returncode == 0, f"userscript syntax failed:\n{result.stderr}")


def validate_css(text: str) -> None:
    require("@name Loui2 Gruvbox Sharp" in text, "BetterDiscord name is missing")
    require("@author round-panda (original), Loui2 (modifications)" in text, "CSS attribution is missing")
    require("@originalSource https://github.com/round-panda/gruvbox-sharp" in text, "CSS original source is missing")
    require("@originalVersion 3.2" in text, "CSS original base version is missing")
    require(f"@source https://github.com/{REPO}/tree/main/betterdiscord" in text, "CSS source points elsewhere")
    require("Copyright (c) 2026 Liang Zhang" in text, "CSS original copyright is missing")
    require(text.count("{") == text.count("}"), "CSS braces are unbalanced")


def validate_revenge(text: str) -> None:
    data = json.loads(text)
    require(data.get("spec") == 2, "Revenge theme must use spec 2")
    require([author.get("name") for author in data.get("authors", [])] == ["round-panda", "Loui2"], "Revenge attribution is wrong")
    require("adaptation of Gruvbox Sharp by round-panda" in data.get("description", ""), "Revenge description is missing attribution")
    require(data.get("source") == f"https://github.com/{REPO}", "Revenge source points elsewhere")
    require(data.get("originalSource") == "https://github.com/round-panda/gruvbox-sharp", "Revenge original source is missing")
    license_data = data.get("license")
    require(isinstance(license_data, dict), "Revenge standalone license notice is missing")
    require(license_data.get("name") == "MIT", "Revenge license name is wrong")
    require(license_data.get("originalCopyright") == "Copyright (c) 2026 Liang Zhang", "Revenge original copyright is missing")
    require("Permission is hereby granted" in license_data.get("permissionNotice", ""), "Revenge MIT permission notice is missing")
    require("THE SOFTWARE IS PROVIDED AS IS" in license_data.get("warrantyDisclaimer", ""), "Revenge MIT disclaimer is missing")

    semantic = data.get("semanticColors")
    raw = data.get("rawColors")
    require(isinstance(semantic, dict) and bool(semantic), "semanticColors is missing")
    require(semantic.get("CHANNELS_DEFAULT") == ["#a89984"], "Revenge shared channel/thread labels must remain neutral")
    require("REDESIGN_CHANNEL_NAME_TEXT" not in semantic, "Revenge theme must not globally recolor channel and thread names")
    require(semantic.get("REDESIGN_CHANNEL_CATEGORY_NAME_TEXT") == ["#a89984"], "Revenge category labels must remain muted")
    require(isinstance(raw, dict) and bool(raw), "rawColors is missing")
    for key, values in semantic.items():
        require(isinstance(values, list) and bool(values), f"semantic color {key} has no values")
        require(all(isinstance(value, str) and HEX_COLOR.fullmatch(value) for value in values), f"semantic color {key} is invalid")
    for key, value in raw.items():
        require(isinstance(value, str) and HEX_COLOR.fullmatch(value) is not None, f"raw color {key} is invalid")


def validate_revenge_plugin(manifest_text: str, bundle: bytes, source: str) -> None:
    manifest = json.loads(manifest_text)
    require(manifest.get("name") == "Loui2 Gruvbox Channel Labels", "Revenge plugin name is wrong")
    require(manifest.get("main") == "index.js", "Revenge plugin main file is wrong")
    require([author.get("name") for author in manifest.get("authors", [])] == ["Loui2"], "Revenge plugin attribution is wrong")
    require(manifest.get("hash") == hashlib.sha256(bundle).hexdigest(), "Revenge plugin hash is stale")
    require(b"?." not in bundle, "Revenge plugin bundle must remain compatible with Hermes ES2015 parsing")
    require(b"Copyright (c) 2026 Loui2" in bundle, "Revenge plugin standalone copyright is missing")
    require(f"https://github.com/{REPO}".encode() in bundle, "Revenge plugin standalone source URL is missing")
    require("new Set([0, 2, 5, 13, 15, 16])" in source, "Revenge plugin ordinary-channel allowlist changed")
    require("{ color: ORANGE }" in source, "Revenge plugin orange label style is missing")
    require("ChannelInfo" in source, "Revenge plugin channel renderer patch is missing")

    node = shutil.which("node")
    if node is None:
        raise AssertionError("node is required for Revenge plugin syntax validation")
    for path in (REVENGE_PLUGIN_SOURCE, REVENGE_PLUGIN):
        result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
        require(result.returncode == 0, f"Revenge plugin syntax failed for {path.relative_to(ROOT)}:\n{result.stderr}")


def main() -> None:
    required = [
        USERSCRIPT,
        BETTERDISCORD,
        REVENGE,
        REVENGE_PLUGIN,
        REVENGE_PLUGIN_MANIFEST,
        REVENGE_PLUGIN_README,
        REVENGE_PLUGIN_SOURCE,
        REVENGE_README,
        README,
        LICENSE,
        NOTICE,
    ]
    for path in required:
        require(path.is_file(), f"required file is missing: {path.relative_to(ROOT)}")

    texts = {path: path.read_text(encoding="utf-8") for path in required}
    for path, text in texts.items():
        require(OLD_REPO not in text, f"old repository name remains in {path.relative_to(ROOT)}")

    validate_userscript(texts[USERSCRIPT])
    validate_css(texts[BETTERDISCORD])
    validate_revenge(texts[REVENGE])
    validate_revenge_plugin(
        texts[REVENGE_PLUGIN_MANIFEST],
        REVENGE_PLUGIN.read_bytes(),
        texts[REVENGE_PLUGIN_SOURCE],
    )

    root_readme = texts[README]
    for relative in (
        "tampermonkey/loui2-discord-web-suite.user.js",
        "betterdiscord/Loui2GruvboxSharp.theme.css",
        "revenge/theme.json",
        "revenge/channel-labels/",
    ):
        require(f"https://raw.githubusercontent.com/{REPO}/main/{relative}" in root_readme, f"README URL is missing: {relative}")

    require("Copyright (c) 2026 Liang Zhang" in texts[LICENSE], "LICENSE lost the original copyright")
    require("originally created by [round-panda]" in texts[NOTICE], "NOTICE lost original creator attribution")
    print("Validated Tampermonkey, BetterDiscord, Revenge theme/plugin, URLs, license, and attribution.")


if __name__ == "__main__":
    main()
