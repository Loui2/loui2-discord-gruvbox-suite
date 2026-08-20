# Loui2 Gruvbox Channel Labels

Optional Revenge companion plugin for [Loui2 Gruvbox Sharp](../theme.json). It colors ordinary guild channel names Gruvbox orange `#d79921` without applying that color to threads or category labels.

## Installation

First install and enable the Revenge theme from:

```text
https://raw.githubusercontent.com/Loui2/loui2-discord-gruvbox-suite/main/revenge/theme.json
```

Then open **Discord Settings → Revenge → Plugins → +** and install:

```text
https://raw.githubusercontent.com/Loui2/loui2-discord-gruvbox-suite/main/revenge/channel-labels/
```

Enable **Loui2 Gruvbox Channel Labels** and reload Discord.

For plugin updates, leave automatic updates enabled and fully restart Discord. Revenge compares the manifest hash and fetches the changed bundle during startup. If automatic updates were disabled for this plugin, remove it and add the same URL again.

Paste the directory URL exactly as shown. Revenge appends `manifest.json`; the base URL is not intended to open as a standalone browser page.

## Scope

The plugin colors these guild channel types:

- Text
- Voice
- Announcement
- Stage
- Forum
- Media

It leaves categories, direct messages, announcement threads, public threads, private threads, and unknown future channel types unchanged. Disabling the plugin removes its renderer patch.

The plugin is intentionally separate because Revenge theme JSON replaces shared color tokens globally and cannot distinguish an ordinary channel row from a thread row.

## License

MIT. See the repository-level [LICENSE](../../LICENSE) and [NOTICE.md](../../NOTICE.md).
