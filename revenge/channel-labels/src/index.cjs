"use strict";

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Loui2
// Source: https://github.com/Loui2/loui2-discord-gruvbox-suite

const ORANGE = "#d79921";
// New Discord channel types stay neutral until they are proven not to be thread-like.
const ORDINARY_GUILD_CHANNEL_TYPES = new Set([0, 2, 5, 13, 15, 16]);

function isOrdinaryGuildChannel(channel) {
  return ORDINARY_GUILD_CHANNEL_TYPES.has(channel && channel.type);
}

function directlyContainsChannelName(children, channelName) {
  if (children === channelName) return true;
  return Array.isArray(children) && children.some((child) => child === channelName);
}

function colorChannelNameInTree(React, node, channelName) {
  if (Array.isArray(node)) {
    let changed = false;
    const next = node.map((child) => {
      const colored = colorChannelNameInTree(React, child, channelName);
      if (colored !== child) changed = true;
      return colored;
    });
    return changed ? next : node;
  }

  if (!React.isValidElement(node)) return node;

  const props = node.props || {};
  if (directlyContainsChannelName(props.children, channelName)) {
    return React.cloneElement(node, {
      style: [props.style, { color: ORANGE }],
    });
  }

  const children = colorChannelNameInTree(React, props.children, channelName);
  if (children === props.children) return node;
  return React.cloneElement(node, { children });
}

function colorOrdinaryChannelLabel(React, args, rendered) {
  const channel = args && args[0] && args[0].channel;
  if (
    !isOrdinaryGuildChannel(channel)
    || typeof channel.name !== "string"
    || !React.isValidElement(rendered)
  ) {
    return rendered;
  }

  return colorChannelNameInTree(React, rendered, channel.name);
}

function createPlugin(vendetta) {
  let unpatch;

  return {
    onLoad() {
      const ChannelInfo = vendetta.metro.findByName("ChannelInfo", false);
      if (!ChannelInfo || !ChannelInfo.default) {
        throw new Error("ChannelInfo renderer unavailable");
      }

      unpatch = vendetta.patcher.after(
        "default",
        ChannelInfo,
        (args, rendered) => colorOrdinaryChannelLabel(
          vendetta.metro.common.React,
          args,
          rendered,
        ),
      );
    },

    onUnload() {
      if (!unpatch) return;
      const removePatch = unpatch;
      unpatch = undefined;
      removePatch();
    },
  };
}

module.exports = {
  ORANGE,
  colorOrdinaryChannelLabel,
  createPlugin,
  isOrdinaryGuildChannel,
};
