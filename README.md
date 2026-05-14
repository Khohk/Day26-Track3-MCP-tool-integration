# Lab: Build a Database MCP Server with FastMCP and SQLite

## Goal

Build a Model Context Protocol (MCP) server using FastMCP that exposes a small database through:

- `search`
- `insert`
- `aggregate`

You must also expose the database schema as an MCP resource, test the server with Inspector or equivalent tooling, and show the server working from at least one MCP client.

## Learning Outcomes

By the end of this lab, students should be able to:

- explain what MCP tools and resources are
- build a FastMCP server in Python
- connect FastMCP to a SQLite database
- safely validate database requests before executing SQL
- expose dynamic schema context through `@mcp.resource(...)`
- test tool schemas, normal calls, and error responses
- connect the server to an MCP client such as Claude Code, Codex, or Gemini CLI

## Required Features

### Part 1: MCP Server

Implement a FastMCP server that exposes exactly these tool categories:

1. `search`
2. `insert`
3. `aggregate`

Your server may use SQLite for the main implementation. If you want to support PostgreSQL too, design the code so the database layer can be swapped later.

### Part 2: Resource

Expose database schema information as MCP resources:

- one resource for the full database schema
- one dynamic resource template for a single table schema

Suggested URIs:

- `schema://database`
- `schema://table/{table_name}`

### Part 3: Validation and Error Handling

Your tools must reject unsafe or invalid requests:

- unknown table names
- unknown column names
- unsupported filter operators
- invalid aggregate requests
- empty inserts

Do not build SQL by blindly concatenating raw user input.

### Part 4: Testing and Verification

Verify all of the following:

1. the server starts correctly
2. the three tools are discoverable
3. the schema resource is discoverable
4. valid tool calls return useful results
5. invalid tool calls return clear errors
6. at least one MCP client can connect and use the server

### Part 5: Demo Deliverables

Prepare:

- GitHub repository
- setup instructions
- tool descriptions
- testing steps
- at least one client configuration example
- short demo video, around 2 minutes

Inspector screenshots are recommended if you use MCP Inspector.

## Suggested Project Structure

```text
implementation/
  db.py
  init_db.py
  mcp_server.py
  verify_server.py
  tests/
    test_server.py
```

## Recommended Data Model

Use a small relational dataset so `search`, `insert`, and `aggregate` are easy to demo. Example:

- `students`
- `courses`
- `enrollments`

## Example Tasks to Demonstrate

- search all students in cohort `A1`
- insert a new student
- count rows in a table
- compute average score by cohort
- read the full schema resource
- read `schema://table/students`
- show an invalid request, such as searching a missing table

## FastMCP and Inspector References

- FastMCP quickstart: https://gofastmcp.com/v2/getting-started/quickstart
- FastMCP resources: https://gofastmcp.com/v2/servers/resources
- MCP Inspector: https://modelcontextprotocol.io/docs/tools/inspector

## Client Setup Notes

### Claude Code

Anthropic documents local JSON config and `claude mcp add` flows here:

- https://code.claude.com/docs/en/mcp

Claude Code supports MCP resources via `@server:resource-uri` references and supports environment variable expansion in `.mcp.json`.

### Codex

OpenAI documents Codex MCP setup here:

- https://developers.openai.com/learn/docs-mcp

Codex supports MCP server configuration through the CLI and `~/.codex/config.toml`.

### Gemini CLI

Gemini CLI has a built-in MCP manager. In the verified local workflow, the simplest path is:

```bash
gemini mcp add sqlite-lab /ABSOLUTE/PATH/TO/python /ABSOLUTE/PATH/TO/implementation/mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
```

Gemini CLI also documents configuration details here:

- https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md

Expected outcome:

- the server appears as `Connected`
- Gemini can discover `search`, `insert`, and `aggregate`
- a headless smoke test works with `gemini --allowed-mcp-server-names sqlite-lab --yolo -p "..."`

### Antigravity

Antigravity commonly uses an `mcp_config.json` file with a shape similar to Gemini CLI. Verify the current product behavior in your installed version before grading against exact UI steps.

## Deliverable Checklist

- working FastMCP server
- SQLite database and seed data
- `search`, `insert`, `aggregate` tools
- schema resource and schema resource template
- verification steps
- automated tests or repeatable verification script
- client configuration example
- README with setup and demo steps
- Inspector startup command or helper script
- at least one verified Gemini CLI or Claude/Codex client test

## Bonus

Optional bonus:

- add authentication for SSE or HTTP transport
- support both SQLite and PostgreSQL with the same MCP surface
- add richer output annotations or pagination

## Local Implementation Guide

This repository includes a completed implementation in `implementation/`.

### Setup

If you already have a virtual environment from another lab, such as `day4`, activate it first and install the requirements there:

```bash
path\to\day4\Scripts\activate
pip install -r requirements.txt
python implementation/init_db.py
```

Or create a new environment for this repository:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python implementation/init_db.py
```

### Run the MCP Server

```bash
python implementation/mcp_server.py
```

The server uses stdio by default, which is the simplest transport for local MCP clients.

### Run the Smoke Verification

```bash
python implementation/verify_server.py
```

This resets the SQLite database, then demonstrates:

- searching students in cohort `A1`
- inserting a new student
- averaging enrollment scores
- counting students by cohort
- reading `schema://database`
- reading `schema://table/students`
- returning a clear error for an invalid table

### Run Automated Tests

```bash
pytest implementation/tests
```

### Inspector

The easiest way is to activate the environment where `fastmcp` is installed, then run the helper script. For your setup, activate `day4` first.

PowerShell:

```bash
path\to\day4\Scripts\activate
.\implementation\start_inspector.ps1
```

Windows command prompt:

```bash
path\to\day4\Scripts\activate.bat
implementation\start_inspector.cmd
```

The helper scripts disable browser auto-open to avoid the common Windows `spawn EPERM` error. They print the Inspector URL in the terminal, and you open that URL manually in your browser.

Manual command, if you want to type it yourself:

```bash
BROWSER=none npx -y @modelcontextprotocol/inspector C:\ABSOLUTE\PATH\TO\.venv\Scripts\python.exe C:\ABSOLUTE\PATH\TO\implementation\mcp_server.py
```

In Inspector, verify:

- tools: `search`, `insert`, `aggregate`
- resources: `schema://database`, `schema://table/{table_name}`
- valid call: search `students` with `{"cohort": "A1"}`
- invalid call: search a missing table

### Example Codex MCP Config

```toml
[mcp_servers.sqlite_lab]
command = "C:\\ABSOLUTE\\PATH\\TO\\.venv\\Scripts\\python.exe"
args = ["C:\\ABSOLUTE\\PATH\\TO\\implementation\\mcp_server.py"]
```

This repository also includes a ready-to-edit example file at [.codex/config.toml.example](<C:/Users/ADMIN/Day26-Track3-MCP-tool-integration/.codex/config.toml.example>). You can copy the same values into your real Codex config at `~/.codex/config.toml` and adjust the Python path if needed.

### Demo Evidence

This repository includes an evidence folder for screenshots:

- [evidence/README.md](<C:/Users/ADMIN/Day26-Track3-MCP-tool-integration/evidence/README.md>)
- [evidence/screenshots.md](<C:/Users/ADMIN/Day26-Track3-MCP-tool-integration/evidence/screenshots.md>)

Use the four screenshot filenames documented there so the rendered Markdown page shows the complete demo evidence clearly.
