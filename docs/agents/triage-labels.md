# Triage Labels

The skills speak in terms of five canonical triage roles. In this repo they map
1:1 to Linear labels grouped under the **"Agentic State Machine"** parent label on
the Photon Ventures team.

| Canonical role    | Linear label      | Label ID                               | Meaning                                  |
| ----------------- | ----------------- | -------------------------------------- | ---------------------------------------- |
| `needs-triage`    | `needs-triage`    | `a9de843a-bcf0-4906-83a1-aad4eecaeb59` | Maintainer needs to evaluate this issue  |
| `needs-info`      | `needs-info`      | `13054a54-9621-4f80-96e8-1021185fa227` | Waiting on reporter for more information |
| `ready-for-agent` | `ready-for-agent` | `ea516c06-a7a3-43f5-a0dc-c0f0855ad2e4` | Fully specified, ready for an AFK agent  |
| `ready-for-human` | `ready-for-human` | `47f69587-129e-477d-8957-29790bf88103` | Requires human implementation            |
| `wontfix`         | `wontfix`         | `ccef58cc-9cd1-43a2-90e1-432e96e5a83b` | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), apply the
corresponding Linear label with `mcp__linear__save_issue` (set `labels`). These
coexist with the required `hearsay` label and with Linear's own workflow state.
