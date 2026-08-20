"use strict";

// SPDX-License-Identifier: MIT

const ORANGE = "#d79921";
// New Discord channel types stay neutral until they are proven not to be thread-like.
const ORDINARY_GUILD_CHANNEL_TYPES = new Set([0, 2, 5, 13, 15, 16]);

function isOrdinaryGuildChannel(channel) {
  return ORDINARY_GUILD_CHANNEL_TYPES.has(channel && channel.type);
}

function colorOrdinaryChannelLabel(React, args, rendered) {
  const channel = args && args[0] && args[0].channel;
  if (!isOrdinaryGuildChannel(channel) || !React.isValidElement(rendered)) {
    return rendered;
  }

  return React.cloneElement(rendered, {
    style: [rendered.props && rendered.props.style, { color: ORANGE }],
  });
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
