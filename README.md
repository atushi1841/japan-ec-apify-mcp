# japan-ec-apify-mcp

An x402-enabled Model Context Protocol (MCP) server wrapping Apify Actors for Japanese e-commerce marketplaces (Mercari Japan, Yahoo! Auctions, Rakuten, SUUMO, Kakaku.com).

Enables AI agents (Claude Desktop, Cursor, AutoGPT) to execute paid API searches on-demand using the x402 protocol ($0.001 USDC / call).

## Features

- **x402 Micropayments Protocol Support**: HTTP 402 / EIP-712 payment authorization for AI agents
- **Apify Actor Integration**: Directly connects with `fruitful_quintessence/mercari-japan-search-scraper`
- **Multi-Transport**: Runs over stdio, HTTP / SSE
- **Official MCP Registry Compatible**: Registered on modelcontextprotocol.io registry

## Installation & Usage

### 1. FastMCP stdio / Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "japan-ec-apify-mcp": {
      "command": "python3",
      "args": ["/path/to/scripts/mcp_x402_server.py"]
    }
  }
}
```

### 2. x402 Payment Flow Example

When calling `search_mercari_japan(keyword="CBR250RR")`:

1. Server returns `isError: true` with x402 `PaymentRequired` payload ($0.001 USDC required).
2. Agent signs EIP-712 payment authorization and re-sends request with `_meta["x402/payment"]`.
3. Server validates payment signature, retrieves Mercari listings, and returns data with `_meta["x402/payment-response"]`.

## Verification

```bash
python3 -m py_compile scripts/mcp_x402_server.py
```

## Related Links

- [Apify Store Actor](https://apify.com/fruitful_quintessence/mercari-japan-search-scraper)
- [MCP Registry Entry](https://registry.modelcontextprotocol.io)
- [x402 Specification v2](https://github.com/coinbase/x402)
