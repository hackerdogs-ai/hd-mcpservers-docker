<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# GitLab MCP Server

MCP server wrapper for [GitLab](https://gitlab.com/) — manage repositories, issues, merge requests, and CI/CD pipelines via the GitLab API using the `@zereight/mcp-gitlab` npm package. See [zereight/mcp-gitlab](https://github.com/zereight/mcp-gitlab) for full documentation.

## What is GitLab MCP?

`@zereight/mcp-gitlab` is an MCP server that wraps the GitLab REST API, giving AI assistants the ability to list and create issues, review and merge MRs, inspect pipeline status, browse repository file trees, and read file contents — all authenticated with a GitLab personal access token. It supports both gitlab.com and self-hosted GitLab instances via the `GITLAB_URL` environment variable.

**Personal access token required** — create one at GitLab Settings → Access Tokens with `api` scope and set `GITLAB_PERSONAL_ACCESS_TOKEN`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `merge_merge_request` | Merge Merge Request |
| `approve_merge_request` | Approve Merge Request |
| `unapprove_merge_request` | Unapprove Merge Request |
| `get_merge_request_approval_state` | Get Merge Request Approval State |
| `get_merge_request_conflicts` | Get Merge Request Conflicts |
| `list_merge_request_pipelines` | List Merge Request Pipelines |
| `create_or_update_file` | Create Or Update File |
| `search_repositories` | Search Repositories |
| `create_repository` | Create Repository |
| `create_group` | Create Group |
| `get_file_contents` | Get File Contents |
| `push_files` | Push Files |
| `create_issue` | Create Issue |
| `create_merge_request` | Create Merge Request |
| `fork_repository` | Fork Repository |
| `create_branch` | Create Branch |
| `get_branch` | Get Branch |
| `list_branches` | List Branches |
| `delete_branch` | Delete Branch |
| `list_protected_branches` | List Protected Branches |
| `get_protected_branch` | Get Protected Branch |
| `protect_branch` | Protect Branch |
| `unprotect_branch` | Unprotect Branch |
| `update_default_branch` | Update Default Branch |
| `get_merge_request` | Get Merge Request |
| `get_merge_request_diffs` | Get Merge Request Diffs |
| `list_merge_request_changed_files` | List Merge Request Changed Files |
| `list_merge_request_diffs` | List Merge Request Diffs |
| `get_merge_request_file_diff` | Get Merge Request File Diff |
| `list_merge_request_versions` | List Merge Request Versions |
| `get_merge_request_version` | Get Merge Request Version |
| `get_branch_diffs` | Get Branch Diffs |
| `update_merge_request` | Update Merge Request |
| `create_note` | Create Note |
| `create_merge_request_thread` | Create Merge Request Thread |
| `resolve_merge_request_thread` | Resolve Merge Request Thread |
| `mr_discussions` | Mr Discussions |
| `delete_merge_request_discussion_note` | Delete Merge Request Discussion Note |
| `update_merge_request_discussion_note` | Update Merge Request Discussion Note |
| `create_merge_request_discussion_note` | Create Merge Request Discussion Note |
| `create_merge_request_note` | Create Merge Request Note |
| `delete_merge_request_note` | Delete Merge Request Note |
| `get_merge_request_note` | Get Merge Request Note |
| `get_merge_request_notes` | Get Merge Request Notes |
| `update_merge_request_note` | Update Merge Request Note |
| `get_draft_note` | Get Draft Note |
| `list_draft_notes` | List Draft Notes |
| `create_draft_note` | Create Draft Note |
| `update_draft_note` | Update Draft Note |
| `delete_draft_note` | Delete Draft Note |
| `publish_draft_note` | Publish Draft Note |
| `bulk_publish_draft_notes` | Bulk Publish Draft Notes |
| `list_merge_request_emoji_reactions` | List Merge Request Emoji Reactions |
| `list_merge_request_note_emoji_reactions` | List Merge Request Note Emoji Reactions |
| `create_merge_request_emoji_reaction` | Create Merge Request Emoji Reaction |
| `delete_merge_request_emoji_reaction` | Delete Merge Request Emoji Reaction |
| `create_merge_request_note_emoji_reaction` | Create Merge Request Note Emoji Reaction |
| `delete_merge_request_note_emoji_reaction` | Delete Merge Request Note Emoji Reaction |
| `update_issue_note` | Update Issue Note |
| `create_issue_note` | Create Issue Note |
| `list_issue_emoji_reactions` | List Issue Emoji Reactions |
| `list_issue_note_emoji_reactions` | List Issue Note Emoji Reactions |
| `create_issue_emoji_reaction` | Create Issue Emoji Reaction |
| `delete_issue_emoji_reaction` | Delete Issue Emoji Reaction |
| `create_issue_note_emoji_reaction` | Create Issue Note Emoji Reaction |
| `delete_issue_note_emoji_reaction` | Delete Issue Note Emoji Reaction |
| `list_issues` | List Issues |
| `my_issues` | My Issues |
| `get_issue` | Get Issue |
| `update_issue` | Update Issue |
| `update_issue_description_patch` | Update Issue Description Patch |
| `delete_issue` | Delete Issue |
| `list_todos` | List Todos |
| `mark_todo_done` | Mark Todo Done |
| `mark_all_todos_done` | Mark All Todos Done |
| `list_issue_links` | List Issue Links |
| `list_issue_discussions` | List Issue Discussions |
| `get_issue_link` | Get Issue Link |
| `create_issue_link` | Create Issue Link |
| `delete_issue_link` | Delete Issue Link |
| `list_namespaces` | List Namespaces |
| `get_namespace` | Get Namespace |
| `verify_namespace` | Verify Namespace |
| `get_project` | Get Project |
| `list_projects` | List Projects |
| `update_project` | Update Project |
| `list_project_members` | List Project Members |
| `list_labels` | List Labels |
| `get_label` | Get Label |
| `create_label` | Create Label |
| `update_label` | Update Label |
| `delete_label` | Delete Label |
| `list_group_projects` | List Group Projects |
| `get_repository_tree` | Get Repository Tree |
| `validate_ci_lint` | Validate Ci Lint |
| `validate_project_ci_lint` | Validate Project Ci Lint |
| `list_ci_catalog_resources` | List Ci Catalog Resources |
| `get_ci_catalog_resource` | Get Ci Catalog Resource |
| `list_merge_requests` | List Merge Requests |
| `get_users` | Get Users |
| `get_user` | Get User |
| `whoami` | Whoami |
| `list_commits` | List Commits |
| `get_commit` | Get Commit |
| `get_commit_diff` | Get Commit Diff |
| `get_file_blame` | Get File Blame |
| `list_commit_statuses` | List Commit Statuses |
| `create_commit_status` | Create Commit Status |
| `list_group_iterations` | List Group Iterations |
| `upload_markdown` | Upload Markdown |
| `download_attachment` | Download Attachment |
| `health_check` | Health Check |
| `list_events` | List Events |
| `get_project_events` | Get Project Events |
| `discover_tools` | Discover Tools |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all open merge requests in my-group/my-project and summarize the changes."
- "Show the status of the latest CI/CD pipeline for my-group/my-project on the main branch."
- "Create a new issue in my-group/my-project titled 'Fix authentication timeout' with a description of the problem."
- "Read the contents of src/main.py from the main branch of my-group/my-project."
- "List all open issues labeled 'critical' in my-group/my-project."
- "Show me the failed jobs in pipeline #12345 for my-group/my-project and explain the errors."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e GITLAB_PERSONAL_ACCESS_TOKEN \
  hackerdogs/gitlab-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8642:8642 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8642 \
  -e GITLAB_PERSONAL_ACCESS_TOKEN \
  hackerdogs/gitlab-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "gitlab-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "GITLAB_PERSONAL_ACCESS_TOKEN",
        "hackerdogs/gitlab-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "GITLAB_PERSONAL_ACCESS_TOKEN": ""
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "gitlab-mcp": {
      "url": "http://localhost:8642/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8642` | HTTP port (only used with `streamable-http`) |
| `GITLAB_PERSONAL_ACCESS_TOKEN` | — | GitLab personal access token with `api` scope |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/gitlab-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name gitlab-mcp-test -p 8642:8642 \
  -e MCP_TRANSPORT=streamable-http \
  -e GITLAB_PERSONAL_ACCESS_TOKEN \
  hackerdogs/gitlab-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8642/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8642/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8642/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop gitlab-mcp-test
```
