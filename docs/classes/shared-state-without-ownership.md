---
class: shared-state-without-ownership
surfaces_at:
  - task
  - code
  - ci
  - review
  - merge
  - after-merge
applies_when: You run several AI coding agents, sessions, subagents or automated jobs against the same repository, issue tracker, branch, working tree, CI checks or shared record (a dispatcher that hands issues to workers, parallel sessions in one checkout, a review bot and an auto-merge, two hooks on the same tool call, a status file several runs write), and you want to know why work gets done twice, lost, merged too early or left claimed by nobody, and what gives each piece of shared state one owner.
applies_when_not: One fact written down in several places that drift apart (copies of one truth drift). An environment that differs from the one the agent assumed or tested in. A gate that reads a skipped or missing check as a pass. A merge or delete that cannot be undone, as such (irreversible effects). A single agent that does more than it was asked (scope overreach).
---

# Shared state without ownership

## TL;DR

Several agents, sessions or jobs read and write one piece of state (an issue's claim, a working tree, a check name, a status record), and nothing makes one of them its owner. Work is done twice, lost, merged before its verdict, or left claimed by a run that died. The protections the sources describe are mechanisms outside the agents: a separate workspace per writer, a claim made by an operation the server refuses to repeat, a conditional write, a verdict bound to the commit being merged, and a lease or sweep that frees what a dead run held. No source measures how often they prevent it. Telling agents to coordinate helps split the work; nothing enforces it.

## Symptom

Several agents, sessions or jobs work on the same project, and the results do not add up. The same issue is picked up twice, and two pull requests solve it in different ways. A batch of tickets is created twice. A pull request carries changes from another task, because two agents shared a working tree, or one worked in the main checkout and left it on a detached HEAD. A shared status record or notes file loses an entry, because two sessions wrote it and the later write replaced the earlier one, and a loop then redoes the lost work. A pull request merges seconds before the review bot posts a blocking finding, or before the fix for a finding reaches the branch, or because a quick skipped run reported the same check as passed while the real run was still going. An issue stays claimed after the run that claimed it died, so nobody picks it up again. A field such as the assignee or a label means two things to two tools, and one of them reads the other's meaning. Each actor did its own part correctly; what went wrong is between them.

## Examples

The INC- codes are rows in [the incident dataset](../../incidents/incidents.csv). The first four examples come from one operator's repositories, where agents pick up and work issues.

- INC-514: two parallel sessions implemented the same issue ([Osasuwu/music-intel-mcp#156](https://github.com/Osasuwu/music-intel-mcp/pull/156)). The operator's duplicate check looked for an existing branch, and the two sessions named their branches by different conventions, `feat/129-…` and `claude/implement-129-…`, so neither saw the other.
- INC-508: a shared status record was written whole by each session ([Osasuwu/jarvis#1473](https://github.com/Osasuwu/jarvis/issues/1473)). A concurrent session's write erased an entry, and a loop redid the lost work. The fix merges one section at a time and refuses a write when the record changed since it was read.
- INC-507: a review run was in progress on a pull request when a bot's rebase push started a second run of the same check ([Osasuwu/jarvis#1434](https://github.com/Osasuwu/jarvis/issues/1434)). The second run took a skip path and passed, auto-merge fired 57 seconds later, and the real review failed six minutes after the merge.
- INC-511: the assignee field meant both that a human owes a decision and that a worker has claimed the issue ([Osasuwu/jarvis#1932](https://github.com/Osasuwu/jarvis/issues/1932)), so an issue escalated to a person read as taken to the operator's dispatcher, the job that hands issues to workers.
- INC-517: worktree-isolated subagents whose worktree had been cleaned up were resumed without one ([anthropics/claude-code#104928](https://github.com/anthropics/claude-code/issues/104928)): "13 of the 31 subagents whose worktree had been removed this way were later resumed and ran Write, Edit or Bash in the main checkout".

## Mechanism

Each actor is correct about its own step. The defect is a piece of state that several of them write, or that one writes and another reads, with no rule for who owns it. Six forms appear in the rows of this class; four recur, and two rest on one row each.

**A claim made by check-then-act, or keyed on something the actors do not share.** A worker checks that nobody holds an issue, then claims it. Two workers that check in the same window both see it free; the same issues were dispatched on consecutive days under different branch names (INC-503, [Osasuwu/jarvis#931](https://github.com/Osasuwu/jarvis/issues/931)). When the check looks for a branch, a session that names its branch differently is invisible to it (INC-514). Creation that is not idempotent fails the same way: a ticket generator ran twice six minutes apart and opened two batches, 30 of them duplicates (INC-502, [Osasuwu/jarvis#874](https://github.com/Osasuwu/jarvis/issues/874)).

**A workspace shared by convention, not by construction.** Two agents in one working tree share its HEAD, index and uncommitted files; one pull request carried 663 lines from other tasks (INC-501), and a worker running in the main checkout left HEAD detached (INC-510). Per-agent worktrees remove most of this, but the tool has to apply them and they share one `.git`: a workflow-started agent ignored its isolation setting, and "One agent's `git checkout -b` moved HEAD under the other two, and a commit hit `.git/index.lock`." ([anthropics/claude-code#102657](https://github.com/anthropics/claude-code/issues/102657), INC-518). Parallel worktree creation raced on the shared git config and left orphaned branches (INC-519). About ten sessions in one clone pushed to one branch, and "`git reflog` showed close to 10 sessions committing and pushing within the same minute." ([anthropics/claude-code#98950](https://github.com/anthropics/claude-code/issues/98950), INC-516). A base rewritten by another actor left work built on the old one (INC-500).

**Claims that outlive their run.** A claim, a lock or a "blocked by" link is set by one run and cleared by nobody when that run dies or the condition changes. A run that exited with no commits left its issue claimed (INC-505), and so did runs killed by a host crash (INC-506). A worktree stayed locked by a process that no longer existed: "The worktree stays registered and locked after `/clear`, after `/exit` (when that pid is dead), and through two later sessions" ([anthropics/claude-code#107208](https://github.com/anthropics/claude-code/issues/107208), INC-520). A stale task was dispatched for work already done, and issues stayed blocked months after their blocker closed (INC-512, INC-513; private, not verifiable). A review finding that was out of scope for its pull request had no owner for 11 days (INC-515).

**Read-modify-write with no concurrency control.** Two sessions read one record, each changes its part and writes the whole record back; the later write erases the earlier change (INC-508).

**Two actors deciding about one pull request at different moments.** The merge acts on the state it sees when it fires: a check name, an approval, a resolved thread. Another actor is still about to change that state. A pull request merged 79 seconds after a review bot posted a CRITICAL finding, because `review`, the status check the repository's review bot reports, had already passed in 4 seconds without reading the finding (INC-504, [Osasuwu/jarvis#1131](https://github.com/Osasuwu/jarvis/pull/1131)). Auto-merge fired before the fix for a finding was pushed (INC-509). Two runs wrote one check name, and the quick one stood for the check (INC-507). GitLab, which calls a pull request a merge request (MR), has the same race on its own platform: "the MR gets merged (due to the thread being resolved) before the new commit is added to the MR." ([gitlab-org/gitlab#571737](https://gitlab.com/gitlab-org/gitlab/-/issues/571737), INC-522), and "The merge is accepted before the async approval removal job processes the new commit" ([gitlab-org/gitlab#580182](https://gitlab.com/gitlab-org/gitlab/-/issues/580182), INC-523).

**One field with two meanings.** A field written for one purpose is read for another, so one writer's act triggers or blocks a reader that means something else by it (INC-511).

The same gap exists inside one agent's harness. Claude Code's [hooks reference](https://code.claude.com/docs/en/hooks) says "its matching hooks run in parallel" and gives a precedence rule for their allow and deny decisions; a hook can also replace the tool's input, and the page gives no rule for two hooks that both do. That rests on reading the page, not on an incident.

**Neighbouring classes.** [Copies of one truth drift](copies-of-one-truth-drift.md) is several copies of one fact drifting apart; this class is one copy written by several actors with no owner. A gate that reads a skipped check as a pass is [absence read as success](absence-read-as-success.md); INC-507 is filed here because two runs wrote the one check name, and it sits on that boundary. A merge or delete that cannot be undone is [irreversible effects](irreversible-effects.md).

## Where it surfaces

At every stage, and no one stage catches most of it; the stages are the six in [the dataset's vocabulary](../vocabularies.json), from task to after merge. Of the 24 rows of this class, 7 were caught while code was being written, 6 at task time (a claim found stuck, a duplicate found on pickup), 5 after merge, 4 in review, 1 in CI and 1 at merge (as of 2026-11, this dataset). The rows from public tool trackers are mostly caught while writing code, because the person who filed them saw the collision in their own checkout. The 16 rows from one operator's repositories (INC-500 to INC-515) spread wider: 6 at task time, 4 in review, 4 after merge and 2 while writing code. One operator's private audit of 15 incidents of this class records who noticed each one: the agent itself, later, in 9; a person in 4; a review bot in 2 (as of 2026-10, private audit). In 9 of them the defect was introduced in the orchestration around the agents (the dispatcher, the launcher, the merge automation), not in code an agent wrote (as of 2026-10, private audit).

No gate sees the whole of it, because each actor's own diff and checks are correct; the defect is in their interaction, which no single diff contains.

## Protections

Each subsection below is one rung of a ladder ordered from the cheapest to the strongest, from a rule the agents are told to a design in which only one actor writes. In one operator's record of this class, every patch that only told the agents what to do was followed by a recurrence, and of the mechanical checks that held where they were written, most left a sibling path unguarded: a manual run, a step the agent is told to run instead of one that runs for it, a copy of the workflow (as of 2026-10, private audit). In that record the claim mechanism itself did not fail; a path that did not go through it did. A rung covers the paths routed through it, not the ones around it.

### Prompt: split the work so each agent owns different files

- **Source:** Claude Code's [agent teams documentation](https://code.claude.com/docs/en/agent-teams): "Two teammates editing the same file leads to overwrites. Break the work so each teammate owns a different set of files."
- **Cost:** planning time for the lead; tokens.
- **Breaks when:** the split is wrong or a file is shared by nature (a lockfile, a generated map, a dataset). Nothing checks that an agent stays in its set: the same page's file locking covers task claims, not file edits.

### Pre-flight: look for an existing claim before starting

- **Source:** one operator's practice: before a worker starts, it checks for an assignee, an open pull request and a remote branch for the issue.
- **Cost:** a few API calls per start.
- **Breaks when:** the check is keyed on a name the actors do not share, such as two branch-naming conventions (INC-514); two workers check in the same window, since check-then-act is not atomic (INC-503); the field it reads means something else to another tool (INC-511).

### Reconcile outcomes on a schedule

- **Source:** Kubernetes [controllers](https://kubernetes.io/docs/concepts/architecture/controller/): "a control loop is a non-terminating loop that regulates the state of a system", comparing the desired state with the current one and acting on the difference. Applied here, a scheduled job checks outcomes rather than paths: at most one open pull request per issue, no claim without a live run, no "blocked by" link to a closed issue.
- **Cost:** one scheduled job and the time to write each invariant.
- **Breaks when:** the invariant is not written, so the loop does not compare it. It reports or repairs after the fact, so damage done between sweeps stays (INC-502's duplicates existed until someone closed them).

### One workspace per writer

- **Source:** Claude Code [worktrees](https://code.claude.com/docs/en/worktrees): "Running each Claude Code session in its own worktree gives it a separate copy of the files to edit"; [Cursor worktrees](https://cursor.com/docs/configuration/worktrees); [Codex worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees), where "Git only allows a branch to be checked out in one place at a time."
- **Cost:** disk and setup per worktree; Cursor's page gives "The default cap is 25 worktrees per machine" (as of 2026-11, Cursor docs).
- **Breaks when:** a shell command writes outside the worktree; the [worktrees page](https://code.claude.com/docs/en/worktrees) says "None of them tracks which files a shell command writes". The worktrees share one `.git`, so parallel creation races on it (INC-519). The tool does not apply the isolation, or drops it on resume (INC-517, INC-518). A worktree placed inside the repository is staged and committed by a later `git add -A`, and "Nothing excludes that path." ([anthropics/claude-code#104013](https://github.com/anthropics/claude-code/issues/104013), INC-521). Git stages each nested worktree as a gitlink, a submodule entry that `.gitmodules` does not list, so it has no URL; per that report, once the commit is pushed, every CI checkout of the branch fails, because the checkout step cannot find a URL for that submodule.

### Serialize CI runs and merges

- **Source:** GitHub Actions [concurrency groups](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency): "there can be at most one running job or workflow in a concurrency group at any time"; the [merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) tests each pull request against the target branch plus the pull requests ahead of it.
- **Cost:** a few lines of workflow configuration; for the queue, a CI run per entry and a rebuild of the entries behind one that jumps the queue.
- **Breaks when:** a newer pending run replaces the older one, and the [concurrency page](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) says "ordering is not guaranteed". The group covers runs inside Actions, not a local session or a manual run. A queue serializes merges, not review verdicts, and workflows must also run on the queue's `merge_group` event.

### Make creation idempotent

- **Source:** Stripe [idempotent requests](https://docs.stripe.com/api/idempotent_requests): the server keeps the first result for a client key and replays it on a retry.
- **Cost:** a key per operation and storage for it on the server.
- **Breaks when:** the key is pruned; Stripe says it may "remove keys from the system automatically after they're at least 24 hours old". The API takes no key: GitHub's [create-an-issue endpoint](https://docs.github.com/en/rest/issues/issues#create-an-issue) documents none, so a ticket generator has to derive one and check it (INC-502).

### Claim by an operation the server refuses to repeat

- **Source:** one operator's practice, the fix for INC-503: the claim is the push that creates the issue's branch, and the server refuses to create a branch that already exists. [Temporal](https://docs.temporal.io/workflow-execution/workflowid-runid) gives the same guarantee for workflow IDs: "there can be at most one Workflow Execution with a given ID running at any point in time".
- **Cost:** one branch push or one start call per claim.
- **Breaks when:** the key is not derived the same way by every actor, so two actors claim two names for one issue (INC-514); a path skips the claim, such as a manual run or a step the agent is told to run; a redesign replaces it with check-then-act (as of 2026-10, private audit).

### Give claims an expiry and requeue what a dead run held

- **Source:** Amazon SQS [visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html): a received message is hidden from other consumers, and "If you don't delete it before the timeout expires, the message becomes visible again in the queue and can be retrieved by another consumer."; Kubernetes [Leases](https://kubernetes.io/docs/concepts/architecture/leases/). One operator's practice: requeue an issue whose run exited with no commits.
- **Cost:** a heartbeat from each holder; a sweeper job.
- **Breaks when:** the holder is alive but slow, and its lease expires while it is still acting. A [fencing token](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) stops its late writes, but "this requires the storage server to take an active role in checking tokens", and an issue tracker does not. The claim has no expiry: GitHub [assignment](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users) has none, and a lock is not released when its holder dies (INC-520). The run dies before it writes anything the sweeper looks for (INC-506). Claude Code's [agent teams](https://code.claude.com/docs/en/agent-teams) claim tasks under a file lock and still note "Task status can lag".

### Write shared records conditionally, or merge them

- **Source:** HTTP [If-Match](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match): "If-Match can be used to prevent the lost update problem."; [git push --force-with-lease](https://git-scm.com/docs/git-push); LangGraph refuses concurrent updates to one state key unless a [reducer](https://docs.langchain.com/oss/python/langgraph/errors/INVALID_CONCURRENT_GRAPH_UPDATE) defines how they merge. One operator's practice, the fix for INC-508: write one section of the record, under a check that it has not changed since it was read.
- **Cost:** a retry path for each writer.
- **Breaks when:** a writer does not send the condition; in one operator's record, sessions that fell back to another write path lost their writes silently (as of 2026-10, private audit). `--force-with-lease` with no expected value "interacts very badly with anything that implicitly runs git fetch on the remote to be pushed to in the background" ([git-push](https://git-scm.com/docs/git-push)). A reducer makes the merge defined, not correct: two agents' duplicate entries both survive.

### Bind the verdict to the commit being merged, with one writer per check

- **Source:** GitHub [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches): required checks, "Dismiss stale pull request approvals when new commits are pushed", and a required check pinned to the app that sets it: "If the status is set by any other person or integration, merging won't be allowed." One operator's practice: keep the pull request in draft until its last commit is pushed, so auto-merge is not armed before the fix lands.
- **Cost:** settings; a re-review on every push.
- **Breaks when:** two runs of the same app report one check name on one commit; pinning the app does not tell them apart (INC-507), and GitHub's [troubleshooting page](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks) warns that "Using the same job name in multiple workflows can cause ambiguous status check results". The check passes before the reviewer posts, and the merge reads the check, not the finding (INC-504). Auto-merge is armed before the fix is pushed (INC-509). Approval removal runs asynchronously after the push (INC-523). The merge itself cannot be undone; for that, see [irreversible effects](irreversible-effects.md).

### One writer: a single-threaded agent or a synchronous lead

- **Source:** Cognition, [Don't build multi-agents](https://cognition.com/blog/dont-build-multi-agents) (2025-06): "The simplest way to follow the principles is to just use a single-threaded linear agent"; Anthropic's [multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (2025-06), where "our lead agents execute subagents synchronously".
- **Cost:** the parallelism; for the multi-agent form, "multi-agent systems use about 15× more tokens than chats" (as of 2025-06, Anthropic).
- **Breaks when:** other actors still write the same state: a human, a bot rebasing the branch, a review bot racing auto-merge (INC-500, INC-504, INC-507). Briefs that overlap still produce duplicate work under a synchronous lead; Anthropic reports "2 others duplicated work investigating current 2025 supply chains" ([same post](https://www.anthropic.com/engineering/multi-agent-research-system)).

## Evidence

External evidence on this class is incident reports, not measurement. None of the sources below measures how often a protection prevents it.

- **The study of multi-agent failures does not cover shared external state.** MAST, the Multi-Agent System Failure Taxonomy, annotated "1600+ annotated traces collected across 7 popular MAS frameworks" (MAS: multi-agent system) and grouped failures into 14 modes, with inter-annotator agreement of kappa 0.88 (as of 2025-03, [Cemri et al.](https://arxiv.org/abs/2503.13657)). Its modes are about conversation between agents; none names a race on a repository, a tracker or CI.
- **A vendor saw duplicated work under a synchronous lead.** Anthropic's research system used about 15 times the tokens of chat, outperformed a single agent by 90.2% on its internal eval, and still had subagents duplicate each other's work when their briefs overlapped (as of 2025-06, [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)). That is research, not coding; the post says "most coding tasks involve fewer truly parallelizable tasks than research".
- **Tool trackers report the workspace form with counts.** One reporter found that 13 of the 31 subagents whose worktree had been removed were later resumed and wrote into the main checkout ([anthropics/claude-code#104928](https://github.com/anthropics/claude-code/issues/104928), INC-517); another, "13 failures in 4 repositories between 2026-10-01 and 2026-10-20" from parallel worktree creation ([anthropics/claude-code#104026](https://github.com/anthropics/claude-code/issues/104026), INC-519) (as of 2026-10, the two defect reports; both rows are `primary`).
- **No public report was found of two AI agents opening duplicate pull requests for one issue.** The search behind this doc (its queries are in [Osasuwu/jarvis-oss#318](https://github.com/Osasuwu/jarvis-oss/pull/318), the pull request that added it) found that form only in one operator's repositories; the public rows are harness bugs and two platform races on GitLab.
- **One operator's patches.** In a private audit of 15 incidents of this class, all 3 patches that told the agents what to do were followed by a recurrence. Of the mechanical checks, 6 held where they were written: 5 of them left a sibling path unguarded or moved the defect, and 1 blocked work it should not have. One more, a guard on the review verdict, recurred in kind (INC-507). Some protections were later removed in a rebuild that replaced an atomic claim with check-then-act, so the hold figures are an upper bound (as of 2026-10, private audit). The audit is not verifiable; its 2 private rows are in the dataset as "private, not verifiable".
