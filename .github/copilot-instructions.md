# Copilot Agent Instructions — ROM Farmer

## Persistent Memory (Engram)

You have access to **Engram**, a persistent memory service via MCP tools. **Use it.**

### Session Lifecycle
- **Start of every session**: Call `session_start(project="rom-farmer", task="<what you'll work on>")` to retrieve context from previous sessions.
- **End of every session**: Call `session_end(summary="<what was done>", handoff="<notes for next agent>")`.

### During Sessions
- `remember(content, kind, project="rom-farmer")` — store facts, decisions, procedures, patterns, preferences, issues
- `recall(query, project="rom-farmer")` — retrieve what you know about a topic
- `entity_track()` / `entity_relate()` — build the knowledge graph as you work with files, modules, concepts

### What to Remember
| Kind | When to use |
|------|-------------|
| `fact` | Discrete knowledge: CLI names, file locations, config details |
| `decision` | Why something was done a certain way — prevents re-litigating |
| `procedure` | How to do something: build commands, test commands, workflows |
| `pattern` | Recurring conventions or gotchas |
| `preference` | User's working style |
| `issue` | Known bugs, tech debt, limitations |

## General Preferences
- **Iterative verify-then-commit workflow**: make changes → verify with builds/tests → commit after success
- Prefer practical smoke tests (run an actual build) alongside unit tests
- Don't create markdown documentation files unless explicitly asked
- The `cache/` directory is .gitignored — source files there require `git add -f`

## See Also
- [AI_TOOLBOX.md](../AI_TOOLBOX.md) — Project architecture, key commands, and domain knowledge for AI assistants
