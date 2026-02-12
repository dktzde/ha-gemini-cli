---
name: hass-dev-docs
description: "Home Assistant developer documentation. Use when the user asks about Home Assistant integrations, add-ons, architecture, APIs, entities, config flows, or any HA development topic. Also use when explicitly asked to update or search HA developer docs."
argument-hint: "[update|index|search <query>]"
allowed-tools: Bash(python *), Bash(npx tsx *), Bash(curl *), Bash(cat .hass-docs-port), Bash(kill *), Task(hass-docs-search)
---

# Home Assistant Developer Docs

This skill manages a local mirror of the Home Assistant developer documentation and provides search access via an embedded search service with semantic (vector) and keyword (FTS5) search.

The docs live at: `docs/hass-developer/` (relative to the project root).

## Search Service

The search service runs as a background HTTP process. Before any search or index operation, ensure it's running:

```bash
# Check if service is running
if ! curl -s http://localhost:$(cat .hass-docs-port 2>/dev/null)/health > /dev/null 2>&1; then
  # Start the service in the background
  nohup npx tsx .claude/skills/hass-dev-docs/service/src/server.ts > /tmp/hass-docs-search.log 2>&1 &
  # Wait for port file to appear (up to 30 seconds)
  for i in $(seq 1 30); do
    if [ -f .hass-docs-port ] && curl -s http://localhost:$(cat .hass-docs-port)/health > /dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi
```

The service auto-indexes docs on startup and writes its port to `.hass-docs-port`.

## Commands

### `/hass-dev-docs update`

Update the local docs mirror from the upstream GitHub repository.

Run:
```bash
python .claude/skills/hass-dev-docs/scripts/update-docs.py docs/hass-developer
```

This will:
1. Clone the latest HA developer docs from GitHub
2. Strip YAML frontmatter (extracting only the title)
3. Remove MDX components (`<ApiEndpoint>`, `<RelatedRules>`, etc.)
4. Strip raw HTML tags (keeping inner text content)
5. Remove Docusaurus admonition markers (`:::note`, `:::tip`, etc.) while keeping content
6. Generate a `CLAUDE.md` index in `docs/hass-developer/`
7. Diff against existing docs and update `CHANGELOG.md` with changes
8. Purge old docs and deploy the clean versions

After updating, trigger a re-index:
```bash
curl -X POST "http://localhost:$(cat .hass-docs-port)/index?doc_set=hass-developer"
```

Report the result to the user — summarize what changed based on the script output.

### `/hass-dev-docs index`

Trigger a re-index of the documentation. Ensure the service is running first (see above), then:

```bash
curl -X POST "http://localhost:$(cat .hass-docs-port)/index?doc_set=hass-developer"
```

Check progress with:
```bash
curl -s "http://localhost:$(cat .hass-docs-port)/stats"
```

### `/hass-dev-docs search <query>`

Search the HA developer docs for a specific topic.

Ensure the search service is running (see above), then delegate to the `hass-docs-search` subagent with the search query and the port number from `.hass-docs-port`.

Example: `/hass-dev-docs search config flow` will search for documentation about config flows using semantic search.

### `/hass-dev-docs` (no arguments)

When invoked without arguments, check if `docs/hass-developer/CLAUDE.md` exists:
- If it exists, read it and use it as context for answering HA development questions
- If it doesn't exist, tell the user to run `/hass-dev-docs update` first

## Answering HA Questions

When this skill is loaded to answer a question (not via explicit `/` command):
1. Ensure the search service is running (see above)
2. Delegate to `hass-docs-search` to find relevant documentation
3. Use the search results to provide an accurate answer
4. Reference specific doc files in your answer

## Important

- The docs are plain markdown files — no build step needed
- The `CLAUDE.md` index has a one-line description per file for quick navigation
- Always delegate searches to `hass-docs-search` to avoid bloating main context
- The search service must be installed first: `cd .claude/skills/hass-dev-docs/service && npm install`
- The update script handles everything via a staging directory — safe to re-run
