# x402 Protocol Implementation & Payment Flow Design Specification

**Author:** Kensho Team  
**Date:** 2026-10-18  
**Protocol Version:** x402 Specification v2 (Model Context Protocol Transport)  
**Target Architecture:** Apify Actor Monetization via Autonomous AI Agent Pay-Per-Call

---

## 1. Executive Summary

This document specifies the x402 micro-payment wrapper architecture for Kensho's Apify Actors (58 scraping actors including `mercari-japan-search-scraper`, `yahoo-auctions-japan-scraper`, `rakuten-market-scraper`, `suumo-japan-real-estate-scraper`, and `japan-kakaku-price-search`).

By wrapping Apify Actors with an x402-enabled Model Context Protocol (MCP) server, AI agents (Claude, Cursor, AutoGPT, LangChain agents) can call Japanese market scrapers on-demand without managing API keys or monthly subscriptions, completing instant micro-settlements over EVM Base / Base Sepolia stablecoins (USDC).

---

## 2. Core Payment Flow Model

The payment cycle follows the Coinbase x402 v2 MCP Transport Specification:

```
+------------------+                    +------------------------+                    +-----------------------+
|  AI Agent Client |                    | x402 MCP Server Wrapper|                    | Apify Scraper Backend |
+------------------+                    +------------------------+                    +-----------------------+
         |                                           |                                            |
         |  1. Tool Call without payment             |                                            |
         |------------------------------------------>|                                            |
         |                                           |                                            |
         |  2. Tool Result: isError=true + 402       |                                            |
         |     (PaymentRequired JSON payload)        |                                            |
         |<------------------------------------------|                                            |
         |                                           |                                            |
         |  3. Parse requirement, sign EIP-712 auth  |                                            |
         |                                           |                                            |
         |  4. Retry Tool Call with _meta["x402/payment"]                                         |
         |------------------------------------------>|                                            |
         |                                           |  5. Verify sig & amount                    |
         |                                           |------------------------+                   |
         |                                           |                        |                   |
         |                                           |<-----------------------+                   |
         |                                           |                                            |
         |                                           |  6. Invoke Scraper Actor                   |
         |                                           |------------------------------------------->|
         |                                           |                                            |
         |                                           |  7. Return Scraped Data                    |
         |                                           |<-------------------------------------------|
         |                                           |                                            |
         |  8. Return Tool Result + Data             |                                            |
         |     _meta["x402/payment-response"]       |                                            |
         |<------------------------------------------|                                            |
```

---

## 3. Pricing Matrix & Unit Pricing ($/call)

| Resource / Tool | Base Asset | Atomic Amount | USD Equivalent | Unit / Quota |
| :--- | :--- | :--- | :--- | :--- |
| `search_mercari_japan` | USDC (6 decimals) | `1000` | **$0.001** | Per 10 search results |
| `search_yahoo_auctions` | USDC (6 decimals) | `1000` | **$0.001** | Per 10 search results |
| `search_rakuten_japan` | USDC (6 decimals) | `1000` | **$0.001** | Per 10 search results |
| `search_suumo_real_estate`| USDC (6 decimals) | `2000` | **$0.002** | Per 10 listings |
| `get_kakaku_price_trend` | USDC (6 decimals) | `1000` | **$0.001** | Per item history |

*Note: Minimum settlement unit is 1,000 micro-USDC ($0.001 USD), keeping friction negligible for AI agents while covering Apify infrastructure execution cost (~$0.0002/item).*

---

## 4. x402 Protocol Message Schemas

### 4.1 PaymentRequired (Server Response when un-paid)

```json
{
  "isError": true,
  "structuredContent": {
    "x402Version": 2,
    "error": "Payment required to call this tool",
    "resource": {
      "url": "mcp://japan-mercari-x402-mcp/search_mercari_japan",
      "description": "Search Mercari Japan for 'CBR250RR' ($0.001 USDC/call)",
      "mimeType": "application/json"
    },
    "accepts": [
      {
        "scheme": "exact",
        "network": "eip155:84532",
        "amount": "1000",
        "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "payTo": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
        "maxTimeoutSeconds": 300,
        "extra": {
          "name": "USDC",
          "version": "2"
        }
      }
    ],
    "extensions": {}
  },
  "content": [
    {
      "type": "text",
      "text": "{\"x402Version\":2,\"error\":\"Payment required...\"}"
    }
  ]
}
```

### 4.2 PaymentPayload (Client Header in _meta)

```json
{
  "_meta": {
    "x402/payment": {
      "x402Version": 2,
      "scheme": "exact",
      "accepted": {
        "scheme": "exact",
        "network": "eip155:84532",
        "amount": "1000",
        "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "payTo": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C"
      },
      "payload": {
        "authorization": {
          "from": "0x1111111111111111111111111111111111111111",
          "nonce": "nonce_12345"
        },
        "signature": "0x..."
      }
    }
  }
}
```

---

## 5. Verification & Audit Trail

1. **Syntax Verification:** `python3 -m py_compile scripts/mcp_x402_server.py`
2. **x402 Signal Test:** Executing un-authenticated tool call returns structured HTTP 402 / x402 PaymentRequired JSON.
3. **Registry Distribution:** Server definitions mirrored in `server.json`, `manifest.json`, and published to MCP Registry and Apify Store ecosystem.
