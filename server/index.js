#!/usr/bin/env node
"use strict";
// DC Hub — remote MCP proxy for Claude Desktop.
// Runs the BUNDLED mcp-remote (node_modules) with Claude Desktop's own Node
// via process.execPath — so it needs NO npx, NO PATH lookup, and NO network
// download at launch. It bridges Claude's local stdio transport to the hosted
// Streamable-HTTP MCP server at https://dchub.cloud/mcp. Free tier works with
// no signup; optional OAuth (WorkOS AuthKit) unlocks the full data tier.
const { spawn } = require("node:child_process");
const path = require("node:path");

const TARGET = "https://dchub.cloud/mcp";
const proxy = path.join(__dirname, "..", "node_modules", "mcp-remote", "dist", "proxy.js");

const child = spawn(process.execPath, [proxy, TARGET], {
  stdio: "inherit",
  env: process.env,
});
child.on("error", (e) => { console.error("[dchub] failed to start mcp-remote:", e.message); process.exit(1); });
child.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
process.on("SIGINT", () => child.kill("SIGINT"));
process.on("SIGTERM", () => child.kill("SIGTERM"));
