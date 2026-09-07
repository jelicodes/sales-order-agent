# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

## Label mapping

| Label in skills | Label in tracker | Meaning | When to apply |
| ---------------- | ---------------- | ------- | ------------- |
| `needs-triage` | `needs-triage` | Maintainer needs to evaluate this issue | Default label on new issues; awaiting initial assessment |
| `needs-info` | `needs-info` | Waiting on reporter for more information | Issue lacks reproduction steps, acceptance criteria, or technical details |
| `ready-for-agent` | `ready-for-agent` | Fully specified, ready for an AFK agent | Issue has clear scope, acceptance criteria, and no blockers |
| `ready-for-human` | `ready-for-human` | Requires human implementation | Issue needs architectural decisions, sensitive code changes, or manual review |
| `wontfix` | `wontfix` | Will not be actioned | Out of scope, duplicate, or not worth the effort |

## State machine

```
                    ┌─────────────┐
                    │ needs-triage│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │needs-info│ │ready-for │ │ ready-for│
        │          │ │  -agent  │ │  -human  │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             │  (when     │  (when     │  (when
             │  info      │  done)     │  done)
             │  provided) │            │
             ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │needs-tri-│ │ready-for │ │ready-for │
        │  age     │ │ -human   │ │  -agent  │
        └──────────┘ └──────────┘ └──────────┘

Any state → wontfix (when decision is made to not act)
```

## When to apply each label

### `needs-triage`

Apply when:
- New issue created (default label)
- Issue reopened after being closed
- New information provided but not yet evaluated

### `needs-info`

Apply when:
- No reproduction steps for bugs
- Missing acceptance criteria for features
- Unclear scope or technical requirements
- Need clarification on business rules

### `ready-for-agent`

Apply when:
- Issue has clear, specific acceptance criteria
- Technical approach is straightforward
- No blocking dependencies
- All required information is present
- Agent can implement autonomously

### `ready-for-human`

Apply when:
- Architectural decision needed
- Sensitive code areas (auth, payments, data migration)
- Requires manual testing or verification
- Needs design review or UX input
-涉及 deployment or infrastructure changes

### `wontfix`

Apply when:
- Issue is out of project scope
- Duplicate of existing issue
- Not worth the implementation effort
- Business requirement changed

## Label operations

### Apply a label

```bash
gh issue edit <number> --add-label "ready-for-agent"
```

### Remove a label

```bash
gh issue edit <number> --remove-label "needs-triage"
```

### Replace a label (state transition)

```bash
gh issue edit <number> --remove-label "needs-triage" --add-label "ready-for-agent"
```

### List issues by label

```bash
gh issue list --label "needs-triage" --state open
```

## Triage workflow

1. **New issue** → `needs-triage`
2. **Evaluate** → Apply appropriate label
3. **If needs-info** → Comment requesting specific info, apply `needs-info`
4. **When info provided** → Re-evaluate, apply `ready-for-agent` or `ready-for-human`
5. **When done** → Close with completion comment

## Customization

Edit the right-hand column to match whatever vocabulary you actually use. The skills reference the left-hand column names, so keep those unchanged.
