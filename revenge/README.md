# Loui2 Gruvbox Sharp for Revenge

A Revenge Android adaptation of [Gruvbox Sharp](https://github.com/round-panda/gruvbox-sharp), originally created by [round-panda](https://github.com/round-panda). This edition preserves the original Gruvbox Dark Soft direction while adding Loui2's palette mappings and readability modifications for Discord's Android client.

This is a modified work, not the original Gruvbox Sharp release. For the original BetterDiscord/Vencord theme, documentation, and previews, visit [round-panda/gruvbox-sharp](https://github.com/round-panda/gruvbox-sharp).

## Installation

Revenge installs themes from a public direct URL. Use:

```text
https://raw.githubusercontent.com/Loui2/loui2-discord-gruvbox-suite/main/revenge/theme.json
```

In Discord Android, open **Settings → Revenge → Themes**, tap **+**, paste the URL, install the theme, and select it.

### Optional channel-label companion plugin

Revenge theme tokens are shared between ordinary channel rows and thread rows. To color ordinary guild channels orange without also recoloring threads or category names, install the companion plugin under **Settings → Revenge → Plugins → +**:

```text
https://raw.githubusercontent.com/Loui2/loui2-discord-gruvbox-suite/main/revenge/channel-labels/
```

Enable **Loui2 Gruvbox Channel Labels** and reload Discord. The plugin targets guild text, voice, announcement, stage, forum, and media channels. It deliberately excludes categories, direct messages, public threads, private threads, announcement threads, and unknown future channel types.

## Scope

The Android client uses React Native rather than desktop Discord's HTML/CSS interface. This port reproduces the Gruvbox palette for backgrounds, text, controls, status colors, cards, chat input, and overlays. Desktop-only CSS behavior such as exact font sizing, sharp corners, hover selectors, and channel-only selectors cannot be represented by Revenge's standard color-theme format; the optional companion plugin supplies the channel-only behavior.

## Credits

- **Original theme:** [Gruvbox Sharp](https://github.com/round-panda/gruvbox-sharp) by [round-panda](https://github.com/round-panda)
- **Original copyright:** Copyright (c) 2026 Liang Zhang
- **Android adaptation and modifications:** Loui2
- **Color palette:** [Gruvbox](https://github.com/morhetz/gruvbox) by morhetz

## License

Distributed under the MIT License used by the original Gruvbox Sharp project. The original copyright and permission notice are retained in [LICENSE](../LICENSE), and the relationship between the original work and this adaptation is documented in [NOTICE.md](../NOTICE.md).
