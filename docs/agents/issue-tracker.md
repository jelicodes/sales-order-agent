# Issue Tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

**Repo:** `jelicodes/sales-order-agent` (inferred from `git remote -v`)

## Conventions

### Create an issue

```bash
gh issue create --title "feat: add email notification for order confirmation" --body "## Summary
Add email notification when order status changes to confirmed.

## Acceptance Criteria
- [ ] Send email via SMTP on order confirmation
- [ ] Include order summary in email body
- [ ] Handle SMTP failures gracefully (log, don't crash)

## Technical Notes
- Use existing `src/config/settings.py` for SMTP config
- Add to `src/api/orders.py` confirmation flow"
```

Use a heredoc for multi-line bodies. Keep the title prefixed with conventional commit type: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

### Read an issue

```bash
# Full issue with comments
gh issue view <number> --comments

# JSON format for programmatic access
gh issue view <number> --json number,title,body,state,labels,comments

# Filter specific fields
gh issue view <number> --json title,body --jq '.body'
```

### List issues

```bash
# All open issues
gh issue list --state open

# JSON with full details
gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'

# Filter by label
gh issue list --label "needs-triage" --state open

# Filter by assignee
gh issue list --assignee "@me" --state open

# Search by title
gh issue list --search "in:title refactor" --state open
```

### Comment on an issue

```bash
gh issue comment <number> --body "## Update
Fixed in commit abc123. Verified via:
- Unit tests: 97/97 pass
- E2E: Playwright manual test passed

Ready for review."
```

### Apply / remove labels

```bash
# Add label
gh issue edit <number> --add-label "ready-for-agent"

# Remove label
gh issue edit <number> --remove-label "needs-triage"

# Replace label (remove old, add new)
gh issue edit <number> --remove-label "needs-triage" --add-label "ready-for-agent"
```

### Close an issue

```bash
gh issue close <number> --comment "## Done
Implemented in commit 6e768cc. All 97 tests pass."
```

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE` (drop `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either — resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

1. Check for existing issues with similar title/body
2. Create with appropriate labels (`needs-triage` for new work)
3. Return the issue URL

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

Parse the issue body and comments to extract:
- **Title**: the issue title
- **Body**: the full description
- **Labels**: current triage state
- **Comments**: discussion history

## When a skill says "update the ticket"

```bash
# Add progress comment
gh issue comment <number> --body "## Progress
- [x] Explored codebase
- [x] Identified root cause
- [ ] Implement fix
- [ ] Add tests"

# Update labels when triage state changes
gh issue edit <number> --remove-label "ready-for-agent" --add-label "needs-info"
```

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`gh api` on the sub-issues endpoint). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies** — the canonical, UI-visible representation. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only — the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me` — the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.

## Error handling

- **`gh` not authenticated**: Run `gh auth login` first
- **Issue not found**: Check if it was closed/merged, or if the number is a PR
- **Label not found**: Create it first, or check existing labels with `gh label list`
- **Rate limit**: GitHub API rate limit is 5000 requests/hour for authenticated users

## Workflow examples

### Feature request flow

1. User asks to add a feature
2. Create issue with `feat:` prefix, `needs-triage` label
3. Triage skill evaluates → applies `ready-for-agent` or `needs-info`
4. Agent implements → comments progress on issue
5. When done → `ready-for-human` for review, or close with completion comment

### Bug fix flow

1. User reports a bug
2. Create issue with `fix:` prefix, `needs-triage` label
3. Triage skill evaluates → applies `ready-for-agent`
4. Agent investigates → comments root cause analysis
5. Agent implements fix → comments with test results
6. Close with `fix:` commit reference
