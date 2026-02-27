# Project Information: ha-gemini-cli

## Overview
This project is a fork of `hass-claude-code` and aims to integrate Gemini CLI with Home Assistant. It provides a web terminal, full API access, and structured tools for interacting with a smart home.

## Key Files and Structure

### Root Directory
- **README.md**: Main documentation with installation and configuration details.
- **addon/**: Contains the Home Assistant add-on configuration and source code.
- **docs/**: Documentation files for Home Assistant.
- **.claude/**: Legacy Claude-specific configurations and scripts.

### Add-on Structure (`addon/`)
- **config.yaml**: Home Assistant add-on manifest with configuration options.
- **Dockerfile**: Multi-stage build for the add-on Docker image.
- **build.yaml**: Base images per architecture.
- **rootfs/**: Container filesystem overlay.
  - **usr/bin/claude-entrypoint.sh**: Entry point script for the add-on.
- **mcp-server/**: Node.js MCP server for interacting with Home Assistant.
  - **src/**: TypeScript source files for the MCP server.
    - `index.ts`: Main entry point for the MCP server.
    - `ha-api.ts`: Home Assistant REST API tools.
    - `ha-websocket.ts`: Home Assistant WebSocket API tools.
    - `docs-search.ts`: Documentation search tools.
    - `db.ts`, `search.ts`, `embeddings.ts`, `indexer.ts`: Search engine components.
    - `build-index.ts`: Script to build the documentation search index.
  - **package.json**: Node.js dependencies and scripts.

### Configuration
- **api_key**: Required Gemini API key.
- **model**: Gemini model to use (default, flash, or pro).
- **yolo_mode**: Skip permission prompts (default: false).
- **enable_embeddings**: Enable semantic document search (default: false).
- **additional_packages**: Extra Alpine packages to install.

### MCP Tools
The MCP server provides the following tools:
1. `search_entities`: Search entities by name, domain, or area.
2. `get_entity_state`: Get state and attributes of a specific entity.
3. `call_service`: Call any HA service.
4. `search_automations`: Search automation entities.
5. `get_ha_config`: Get Home Assistant core configuration.
6. `list_areas`: List all defined areas.
7. `search_devices`: Search the device registry.
8. `get_config_entries`: List integration config entries.
9. `search_docs`: Search HA developer and user documentation.
10. `read_doc`: Read a specific documentation file.
11. `get_doc_stats`: Get documentation index statistics.

### File Access
The add-on has access to:
- `/homeassistant/`: HA configuration directory (Read/Write).
- `/config/`: Add-on configuration (Read/Write).
- `/share/`: Shared storage between add-ons (Read/Write).
- `/ssl/`: SSL certificates (Read-only).
- `/media/`: Media files (Read-only).

### Build Process
1. Installs Node.js dependencies for the MCP server.
2. Clones the HA documentation from the repository.
3. Builds a keyword search index from the docs.
4. Installs Gemini CLI, ttyd, tmux, and other tools.
5. Sets up s6-overlay services for process management.

### Supported Architectures
- `amd64` (x86_64)
- `aarch64` (ARM64, e.g., Raspberry Pi 4/5)

## Notes
- The project is a work in progress and not fully tested.
- The Docker image is built locally on the device during installation.
- The first install may take several minutes depending on hardware.
