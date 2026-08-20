const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const {
  ORANGE,
  colorOrdinaryChannelLabel,
  createPlugin,
  isOrdinaryGuildChannel,
} = require("../revenge/channel-labels/src/index.cjs");

test("ordinary guild channel types are eligible for orange labels", () => {
  for (const type of [0, 2, 5, 13, 15, 16]) {
    assert.equal(isOrdinaryGuildChannel({ type }), true, `type ${type}`);
  }
});

test("threads, categories, DMs, and unknown types are excluded", () => {
  for (const type of [1, 3, 4, 10, 11, 12, 14, 99]) {
    assert.equal(isOrdinaryGuildChannel({ type }), false, `type ${type}`);
  }

  assert.equal(isOrdinaryGuildChannel(null), false);
  assert.equal(isOrdinaryGuildChannel({}), false);
});

test("eligible channel labels preserve existing style and append orange", () => {
  const rendered = { props: { style: { fontWeight: "500" }, children: "general" } };
  const React = {
    isValidElement: (element) => element === rendered,
    cloneElement: (element, props) => ({ ...element, props: { ...element.props, ...props } }),
  };

  const result = colorOrdinaryChannelLabel(React, [{ channel: { type: 0, name: "general" } }], rendered);

  assert.notEqual(result, rendered);
  assert.deepEqual(result.props.style, [rendered.props.style, { color: ORANGE }]);
  assert.equal(result.props.children, "general");
});

test("eligible channel labels are colored inside the ChannelInfo wrapper", () => {
  const icon = { type: "Icon", props: {} };
  const label = { type: "Text", props: { style: { opacity: 0.8 }, children: "general" } };
  const rendered = { type: "View", props: { style: { flex: 1 }, children: [icon, label] } };
  const React = {
    isValidElement: (element) => Boolean(element && element.type),
    cloneElement: (element, props) => ({ ...element, props: { ...element.props, ...props } }),
  };

  const result = colorOrdinaryChannelLabel(React, [{ channel: { type: 0, name: "general" } }], rendered);

  assert.notEqual(result, rendered);
  assert.equal(result.props.style, rendered.props.style);
  assert.equal(result.props.children[0], icon);
  assert.notEqual(result.props.children[1], label);
  assert.deepEqual(result.props.children[1].props.style, [label.props.style, { color: ORANGE }]);
});

test("thread, category, and invalid rendered rows are returned untouched", () => {
  const thread = { props: { style: { color: "original" } } };
  const category = { props: {} };
  const React = {
    isValidElement: (element) => element === thread || element === category,
    cloneElement: () => assert.fail("excluded rows must not be cloned"),
  };

  assert.equal(colorOrdinaryChannelLabel(React, [{ channel: { type: 11 } }], thread), thread);
  assert.equal(colorOrdinaryChannelLabel(React, [{ channel: { type: 4 } }], category), category);
  assert.equal(colorOrdinaryChannelLabel(React, [{ channel: { type: 0 } }], null), null);
});

test("plugin patches ChannelInfo on load and unpatches on unload", () => {
  const channelInfo = { default() {} };
  const rendered = { props: { style: { opacity: 0.8 }, children: "voice" } };
  const React = {
    isValidElement: (element) => element === rendered,
    cloneElement: (element, props) => ({ ...element, props: { ...element.props, ...props } }),
  };
  let patch;
  let unpatchCalls = 0;
  const vendetta = {
    metro: {
      findByName: (name, all) => {
        assert.equal(name, "ChannelInfo");
        assert.equal(all, false);
        return channelInfo;
      },
      common: { React },
    },
    patcher: {
      after: (method, target, callback) => {
        assert.equal(method, "default");
        assert.equal(target, channelInfo);
        patch = callback;
        return () => { unpatchCalls += 1; };
      },
    },
  };

  const plugin = createPlugin(vendetta);
  plugin.onLoad();
  const colored = patch([{ channel: { type: 2, name: "voice" } }], rendered);
  assert.deepEqual(colored.props.style, [rendered.props.style, { color: ORANGE }]);

  plugin.onUnload();
  plugin.onUnload();
  assert.equal(unpatchCalls, 1);
});

test("plugin fails closed when Discord's ChannelInfo renderer is unavailable", () => {
  const plugin = createPlugin({
    metro: { findByName: () => undefined, common: { React: {} } },
    patcher: { after: () => assert.fail("must not patch an unknown renderer") },
  });

  assert.throws(() => plugin.onLoad(), /ChannelInfo renderer unavailable/);
});

test("published bundle and manifest are installable and preserve channel scoping", () => {
  const pluginDir = path.join(__dirname, "..", "revenge", "channel-labels");
  const bundle = fs.readFileSync(path.join(pluginDir, "index.js"), "utf8");
  const manifest = JSON.parse(fs.readFileSync(path.join(pluginDir, "manifest.json"), "utf8"));
  const hash = crypto.createHash("sha256").update(bundle).digest("hex");

  assert.equal(manifest.main, "index.js");
  assert.equal(manifest.hash, hash);

  const channelInfo = { default() {} };
  const label = { type: "Text", props: { style: { opacity: 1 }, children: "general" } };
  const rendered = { type: "View", props: { children: [{ type: "Icon", props: {} }, label] } };
  let patch;
  const vendetta = {
    metro: {
      findByName: () => channelInfo,
      common: {
        React: {
          isValidElement: (element) => Boolean(element && element.type),
          cloneElement: (element, props) => ({ ...element, props: { ...element.props, ...props } }),
        },
      },
    },
    patcher: {
      after: (_method, _target, callback) => {
        patch = callback;
        return () => {};
      },
    },
  };

  const plugin = Function("vendetta", `return ${bundle}`)(vendetta);
  plugin.onLoad();

  const channel = patch([{ channel: { type: 0, name: "general" } }], rendered);
  const thread = patch([{ channel: { type: 11, name: "thread" } }], rendered);
  assert.deepEqual(channel.props.children[1].props.style, [label.props.style, { color: ORANGE }]);
  assert.equal(thread, rendered);
});
