#!/usr/bin/env node
"use strict";
// DC Hub — remote MCP proxy for Claude Desktop.
//
// Claude Desktop launches extensions with a locked-down HOME, so mcp-remote's
// default config dir (~/.mcp-auth) can't be created → EPERM → the server dies
// ("Server disconnected"). Fix: point mcp-remote's config dir at the OS temp
// dir (always writable in the sandbox), then run mcp-remote IN THIS PROCESS
// (single process — stdio wired straight to Claude Desktop, matching the native
// remote connector). Free tier works with no signup; optional OAuth (WorkOS
// AuthKit) unlocks the full data tier. No data stored locally.
const path = require("node:path");
const os = require("node:os");
const fs = require("node:fs");

const cfgDir = path.join(os.tmpdir(), "dchub-mcp-auth");
try { fs.mkdirSync(cfgDir, { recursive: true }); } catch (_) { /* best effort */ }
if (!process.env.MCP_REMOTE_CONFIG_DIR) process.env.MCP_REMOTE_CONFIG_DIR = cfgDir;

const proxy = path.join(__dirname, "..", "node_modules", "mcp-remote", "dist", "proxy.js");
process.argv = [process.argv[0], proxy, "https://dchub.cloud/mcp", "--transport", "http-first"];

import(proxy).catch((e) => {
  console.error("[dchub] failed to start mcp-remote:", e && e.message);
  process.exit(1);
});
