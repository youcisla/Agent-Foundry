---
name: chrome-devtools-mcp-bridge
description: Google's official Chrome DevTools MCP — 26+ tools for browser automation,
  network inspection, console capture, screenshot diffing, performance tracing. From
  ChromeDevTools/chrome-devtools-mcp (Apache-2.0). Use for web app debugging, screenshots,
  network traces, performance analysis.
version: 0.1.0
license: Apache-2.0
author: Agent Foundry Contributors
---

# Chrome DevTools MCP Bridge

Google's official Chrome DevTools MCP server (Apache-2.0). Exposes 26+ tools for browser automation through the DevTools Protocol — real DOM inspection, network traces, console capture, screenshot diffing, and performance tracing.

## When to Use

- Web app debugging: "why isn't this click working?", "what's the network request?"
- Visual regression: screenshot a page, compare to a baseline
- Console errors: grab console logs, find JS exceptions
- Performance: Lighthouse audit, Core Web Vitals
- Screenshots: full-page, element-specific

## Available Tools (26+)

| Category | Tools |
|----------|-------|
| Navigation | `navigate_page`, `new_page`, `close_page`, `select_page`, `list_pages` |
| Inspection | `take_snapshot` (a11y tree), `take_screenshot`, `click`, `hover`, `fill`, `drag` |
| Console | `list_console_messages`, `get_console_message` |
| Network | `list_network_requests`, `get_network_request` |
| Script | `evaluate_script`, `type_text`, `fill_form`, `press_key`, `upload_file` |
| Performance | `performance_start_trace`, `performance_stop_trace`, `performance_analyze_insight` |
| Audit | `lighthouse_audit`, `emulate` (device/network/user-agent) |
| Memory | `take_heapsnapshot` |

## How It Works

The MCP server connects to a running Chrome instance via the DevTools Protocol. It requires Chrome to be running with `--remote-debugging-port`. The typical workflow:

1. Launch Chrome with remote debugging enabled
2. Connect the MCP server to the debugging port
3. Use any of the 26+ tools via MCP to drive the browser

## Pairing with Desktop Automation

- This = browser-native (web pages, DevTools, network, console)
- Desktop automation = cua-driver (system-level: click, type, scroll on any window)

Use chrome-devtools-mcp when the task is on a web page. Use desktop automation when the target is a native app.

## Installation

Refer to the upstream repo's README for the latest install instructions. The MCP server can be run as a standalone process and connected via any MCP-compatible client.

## Anti-patterns

- Using this for desktop automation (use cua-driver instead)
- Using desktop automation for web-page DOM tasks (use this instead)
- Relying on screenshots when you could read the DOM tree
