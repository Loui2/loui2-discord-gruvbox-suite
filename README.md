# Loui2 Discord Gruvbox Suite

A multi-client Discord customization suite derived from [Gruvbox Sharp](https://github.com/round-panda/gruvbox-sharp), originally created by [round-panda](https://github.com/round-panda). This repository contains Loui2's maintained adaptations for Tampermonkey, BetterDiscord, and Revenge Android.

This is a modified work, not the original Gruvbox Sharp release. See [NOTICE.md](NOTICE.md) for attribution and [LICENSE](LICENSE) for the retained MIT license.

## Available versions

| Client | Artifact | Scope |
| --- | --- | --- |
| Tampermonkey on Discord Web | [`tampermonkey/loui2-discord-web-suite.user.js`](tampermonkey/loui2-discord-web-suite.user.js) | Gruvbox styling plus browser workspace controls, typography controls, message tools, mobile layout, tab titles, and invisible typing |
| BetterDiscord | [`betterdiscord/Loui2GruvboxSharp.theme.css`](betterdiscord/Loui2GruvboxSharp.theme.css) | Visual theme only |
| Revenge on Android | [`revenge/theme.json`](revenge/theme.json) | Native Android color-theme adaptation |

## Tampermonkey installation

Install from the direct userscript URL:

```text
https://raw.githubusercontent.com/Loui2/loui2-discord-gruvbox-suite/main/tampermonkey/loui2-discord-web-suite.user.js
```

The userscript includes matching `@downloadURL` and `@updateURL` metadata so Tampermonkey can retrieve later published versions.

The message-deletion control depends on a separate local companion service bound to `127.0.0.1`. That service is not distributed by this repository. Without it, deletion requests fail locally and safely; the userscript does not send deletion requests to a third-party service.

The Tampermonkey and BetterDiscord desktop versions import IBM Plex from Google Fonts. Loading either desktop theme therefore sends ordinary font-request metadata, such as IP address and user agent, to Google.

## BetterDiscord installation

Download:

```text
https://raw.githubusercontent.com/Loui2/loui2-discord-gruvbox-suite/main/betterdiscord/Loui2GruvboxSharp.theme.css
```

Place `Loui2GruvboxSharp.theme.css` in the BetterDiscord themes directory, enable Discord Dark Mode, and enable the theme under **User Settings → Themes**.

The editable Loui2 typography and channel-color variables are near the top of the CSS file.

## Revenge installation

Paste this URL into **Discord Settings → Revenge → Themes → +**:

```text
https://raw.githubusercontent.com/Loui2/loui2-discord-gruvbox-suite/main/revenge/theme.json
```

The Revenge version reproduces the Gruvbox palette using Android semantic and raw color mappings. React Native does not support the desktop theme's CSS selectors, exact typography, or sharp-corner rules.

## Maintenance model

This Git working tree is the canonical source for all three published artifacts. Platform-specific implementations intentionally differ, but no separate publication copies are maintained.

Run the repository validator before publishing:

```bash
python3 scripts/validate.py
```

## Attribution

- **Original theme:** [Gruvbox Sharp](https://github.com/round-panda/gruvbox-sharp) by [round-panda](https://github.com/round-panda)
- **Original copyright:** Copyright (c) 2026 Liang Zhang
- **Adaptations and modifications:** Loui2
- **Color palette:** [Gruvbox](https://github.com/morhetz/gruvbox) by morhetz

## License

MIT. The original copyright and permission notice are preserved in [LICENSE](LICENSE).
