> **Note:** This is the Claude Desktop (MCPB) packaging of the canonical **DC Hub MCP server** — for the main listing see [glama.ai/mcp/servers/qa3uoznre7](https://glama.ai/mcp/servers/qa3uoznre7) · [github.com/azmartone67/dchub-mcp-server](https://github.com/azmartone67/dchub-mcp-server).

# DC Hub — Claude Desktop Extension

A Claude Desktop extension (MCPB) that connects Claude to **DC Hub** — the live
data-center, power & grid intelligence layer for AI agents.

- **MCP server:** `https://dchub.cloud/mcp` (Streamable HTTP)
- **Tools:** 92 — query *and* cite (data is CC-BY-4.0)
- **Auth:** free tier works with no signup; optional OAuth 2.0 (WorkOS AuthKit,
  Dynamic Client Registration + PKCE) unlocks the full data tier
- **Privacy:** https://dchub.cloud/privacy · **Terms:** https://dchub.cloud/terms
- **Docs / full tool list:** https://dchub.cloud/llms.txt

## What it does

DC Hub gives Claude live, cited ground truth on the physical infrastructure
behind AI: a global data-center facility map across 170+ countries
(corroborated count pending), 300+ power
markets (the DCPI power index with BUILD/CAUTION/AVOID verdicts), real-time ISO
grid telemetry and interconnection-queue depth, natural gas, fiber routes, water
risk, tax incentives, and 1,600+ tracked M&A deals.

## How it works

The extension bundles [`mcp-remote`](https://www.npmjs.com/package/mcp-remote),
which bridges Claude Desktop's local **stdio** transport to the hosted DC Hub
**Streamable-HTTP** MCP server. `mcp-remote` is bundled in `node_modules` and run
with Claude Desktop's own Node runtime (`process.execPath`), so the extension
needs no `npx`, no PATH lookup, and no network download at launch. No data is
stored locally — every call goes straight to `dchub.cloud`.

```
Claude Desktop  ──stdio──▶  server/index.js  ──▶  mcp-remote  ──HTTPS──▶  https://dchub.cloud/mcp
```

## Install

Download **[`dchub.mcpb`](./dchub.mcpb)** and open it with Claude Desktop → **Install**.
Then ask, e.g., *"Use DC Hub to rank the top US power markets by capacity."*

## Build from source

```bash
npm install
npx @anthropic-ai/mcpb pack . dchub.mcpb
```

## License

MIT — see [LICENSE](./LICENSE). Underlying DC Hub data is licensed CC-BY-4.0.

Maintained by DC Hub · https://dchub.cloud · jonathan@dchub.cloud
