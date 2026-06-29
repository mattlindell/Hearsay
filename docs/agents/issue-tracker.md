# Issue tracker: Linear (MCP)

Issues and PRDs for this repo live in **Linear**, accessed through the Linear MCP
server (available in Zed). Skills like `to-issues`, `triage`, `to-prd`, and `qa`
read from and write to Linear using the `mcp__linear__*` tools.

## Coordinates

| Field          | Value                  | ID                                     |
| -------------- | ---------------------- | -------------------------------------- |
| Team           | Photon Ventures (`PV`) | `9e1c5abb-f150-44d7-9edc-edc40933c57e` |
| Project        | Tool Chest             | `138e9455-b8cb-4bc4-81d6-959fa5c4884f` |
| Required label | `hearsay`              | `2a40ac78-a324-48e0-b66d-024deb2ab065` |

**Every issue this skill set creates must be filed in the Tool Chest project, on
the Photon Ventures team, with the `hearsay` label applied** (alongside any triage
label). This is how Hearsay work is distinguished from other Tool Chest tools
(e.g. the Obsidian Summarizer, which uses the `summarizer` label).

## Conventions

- **Create an issue**: `mcp__linear__save_issue` with `team`, `project`, `title`,
  `description` (markdown), and `labels` including `hearsay`. Omit `id` to create.
- **Read an issue**: `mcp__linear__get_issue` by id/identifier;
  `mcp__linear__list_comments` for discussion.
- **List issues**: `mcp__linear__list_issues` filtered by `team`, `project`,
  and/or `label`. Use `label: "hearsay"` to scope to this app.
- **Comment**: `mcp__linear__save_comment` with the issue id and `body`.
- **Apply / change labels or state**: `mcp__linear__save_issue` with the issue
  `id` and the new `labels` / `state`.
- **Close / cancel**: `mcp__linear__save_issue` setting `state` to `Done`,
  `Canceled`, or `Duplicate`.

Pass markdown content directly (real newlines, no escaped `\n`).

## Workflow states (Linear) vs. triage labels

Linear has its own workflow states — Backlog, Todo, In Progress, In Review, Done,
Canceled, Duplicate — that track *execution*. The five triage **labels** (see
`triage-labels.md`) track *triage disposition* and are applied independently. An
issue can sit in `Backlog` with a `needs-triage` label, move to `ready-for-agent`
while still in `Backlog`, then `Todo` → `In Progress` once picked up.

## When a skill says "publish to the issue tracker"

Create a Linear issue in Tool Chest / Photon Ventures with the `hearsay` label.

## When a skill says "fetch the relevant ticket"

`mcp__linear__get_issue` by its identifier (e.g. `PV-123`).
