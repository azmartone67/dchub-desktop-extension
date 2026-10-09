> **Note:** This is the Claude Desktop (MCPB) packaging of the canonical **DC Hub MCP server** — for the main listing see [glama.ai/mcp/servers/qa3uoznre7](https://glama.ai/mcp/servers/qa3uoznre7) · [github.com/azmartone67/dchub-mcp-server](https://github.com/azmartone67/dchub-mcp-server).

# DC Hub — Claude Desktop Extension

A Claude Desktop extension (MCPB) that connects Claude to **DC Hub** — the live
data-center, power & grid intelligence layer for AI agents.

- **MCP server:** `https://dchub.cloud/mcp` (Streamable HTTP)
- **Tools:** 94 (query *and* cite; data is CC-BY-4.0)
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
risk, tax incentives, and 1,700+ tracked M&A deals.

## Capacity Source

The extension bridges to the full `https://dchub.cloud/mcp` endpoint, so it
carries the whole **Capacity Source** flow: data-center capacity to buy or
lease (powered land, powered shells, turnkey capacity and colocation), listed
free by operators and brokers at <https://dchub.cloud/listings>.

- **`source_capacity`** searches the listings by size (`min_kw` in kW or
  `min_mw` in MW) and location (a region such as North America or Europe, a
  country, a US state or a metro). Listing cards work with no signup; pass a
  listing's `slug` to open it.
- **`accept_capacity_terms`** records your acceptance of DC Hub's introduction
  terms (<https://dchub.cloud/listings#terms>) the first time you open a
  listing. Claude should call it only after you have agreed to them.
- **`request_capacity_intro`** registers a deal on a listing. DC Hub sends the
  provider only your company name and requirement; contacts are shared only if
  the provider accepts, and nothing is shared on a decline.
- **`/dchub:find_capacity`** is the ready-made prompt that runs the whole flow
  from a plain-language requirement (for example "powered shell in Dallas,
  energized next year"): search, explain which listings fit, then register.

To list capacity, use <https://dchub.cloud/listings#list-capacity> (listing is free).

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
