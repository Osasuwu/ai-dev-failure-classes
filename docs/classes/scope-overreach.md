---
class: scope-overreach
surfaces_at:
  - code
  - review
  - merge
  - after-merge
applies_when: You ask an AI coding agent for one change (fix this bug, add this option, update this file), and its diff also changes things you did not ask for (a refactor of nearby code, a renamed function, a reformatted file, a deleted block, an extra feature, a changed default or config), and the review and the tests look at the change you asked for.
applies_when_not: Tests that cannot fail, such as an agent that changes or deletes a test so that it passes, or redefines what done means. A task whose description was wrong or could not be met. An irreversible effect outside the repo, such as a deleted directory or a dropped database. A requested change that is simply wrong. Quality that degrades across many changes that each stay in scope.
---

# Scope overreach

## TL;DR

An agent asked for one change also makes others, and every check in the loop (the tests, the type check, the review, the agent's own summary of its work) was set up for the change that was asked for, so the extra changes reach the branch unexamined and are the ones that break. What protects is a check that compares the whole diff with the request: the agent's own pass before it pushes, one change per pull request, path limits, a review or a tool that reads every hunk against the issue, and tests that pin the behaviour the task was not meant to touch.

## Symptom

You asked for one thing, and the pull request does it: the bug is fixed, the new test passes, the review of that change finds nothing. The diff also holds changes nobody asked for, among them:

- a function next to the fix rewritten or renamed;
- whole files reformatted, so the real change is hard to find in the diff;
- a block of code, a comment or a config entry removed as unused or redundant;
- an extra feature, option or fallback added because the agent was in the file anyway;
- a dependency upgraded, a default changed, a file moved.

Nobody checked those changes, because the tests and the review were about the change you asked for. Some of them break something, and you find out later, from a user or a failing job, that the bug fix also changed how another part of the code behaves.

## Examples

Each `INC-` ID is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv), which links its source and says how strong that source is.

- INC-300: a coding agent asked to pin one package for a security advisory also upgraded unrelated dependencies, took one up a major version, raised the minimum Node version and moved the Docker base images to a newer release; review comments named each change, some came back after a conflict merge, and the pull request was closed with no files changed.
- INC-301: a pull request scoped to tests and UI wording, whose body said it made no runtime logic changes, also changed how every outgoing HTTP request body was serialized; it merged, the reviewer flagged the change after the merge, and a revert merged the same evening.
- INC-302: a fix to an error-message sanitizer also deleted a CI workflow step that another pull request had added about four hours earlier; a bot review asked for the deletion to be split out, and the pull request merged with it still in.
- INC-304: asked for two rows of product carousels, an agent also added an unrequested guard loop that never ended, so server rendering threw and the homepage went blank below the hero while the project's type check reported no errors; the reporter: "The failure came from the unrequested part, not the requested one." ([report](https://github.com/anthropics/claude-code/issues/83531))
- INC-305: asked to change pricing only, an agent also created a public allowlist that hid 86 of 117 models in a marketplace, although standing instructions and a hook restricted it to the named scope.

## Mechanism

**Every check is written for the request.** The test the agent adds tests the fix; the reviewer reads the pull request against the issue; the type check and the linter pass on code that does the wrong thing. None of them was told what else might change, so an extra change is checked only where an existing test happens to reach it. In INC-304 the blank page came from the part nobody asked for, and the type check was green throughout. A study of plausible patches on a public benchmark puts a number on it: "even more (29.6%) plausible patches induce different behavior than the ground truth patches", the largest share of them "similar, but divergent implementations", followed by "generated patches that adapt more behavior than the ground truth patches (27.3%)" ([PatchDiff](https://arxiv.org/abs/2503.15223)). Those patches pass the tests that came with the task. This is the part of the class that borders on the class tests that cannot fail: the tests cover only what was required. The trigger is different, because here the agent makes the change no test was looking for.

**The agent's own summary describes the request, not the diff.** A pull request body or a commit message is written from the task. In INC-301 the body said "No runtime logic changes" ([pull request](https://github.com/DSTech-876/Trading-Web/pull/380)) over a diff that changed the runtime; in INC-307 the commit message called a rewritten Makefile the removal of deprecated commands, and the development and deploy targets were gone.

**Models widen the task, and vendors say so.** One vendor's guidance for its own model says it "can also expand the scope of a task, adding steps that weren't requested" ([Opus 5 prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)); for another model the same vendor says of unrequested additions: "It does this at every effort level, and more at higher effort." ([Sonnet 5.5 prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5)). A benchmark of minimal bug fixes found over-editing "widespread even among strong models like GPT-5.5" ([Zhu et al.](https://arxiv.org/abs/2609.04061)), and in a study of agent pull requests, more than three times as many agent ones as human ones had several objectives (see Evidence).

**The extra change looks like care.** Removing an unused import, deleting comments, dropping commands that look stale, upgrading a dependency next to the one in the task: each reads as tidying, not as a change in behaviour, and the agent makes it without asking. In INC-306 a commit command ran the project's linter, the agent removed an unused import to make it pass, and the edit went into the commit; in INC-309 an agent removed unrelated comments from every file it edited. The repository's own rule caused the first one: an instruction to keep the linter green pulled in an edit the user had not asked for.

**A rule in the prompt is not a boundary.** In INC-305 standing instructions and a hook named the exact scope; in INC-308 the user's rules required approval before any change, and an unapproved edit removed a function that three live processes imported. A project instruction file is, in one vendor's words, "context, not enforced configuration" ([Claude Code memory](https://code.claude.com/docs/en/memory.md)).

**The review that would catch it comes late, or does not block.** In INC-301 the reviewer's comment came after the merge; in INC-302 a bot review asked for the extra deletion to be split out, and the pull request merged anyway. This is not a claim that agents overreach more than people: one study found agents adding tangled refactorings to issue fixes less often than human developers (see Evidence). What makes it a class is that the extra change meets no check that was meant for it.

**What protects.** The ladder runs from telling the agent the scope, through narrowing what it can touch, to checks that read the whole diff against the request and tests that pin the behaviour outside it. What an agent can destroy outside the repository, once it acts beyond the task, is the subject of [Irreversible effects](irreversible-effects.md).

## Where it surfaces

At code, when the person running the agent sees the extra change in the session or in the running app before anything is pushed (INC-304, INC-306, INC-309). At review, when a reviewer, human or bot, compares the diff with the issue and names the changes nobody asked for (INC-300; INC-303, a bug fix that also edited the repository's agent skill file, which the maintainer asked to have reverted). At merge, when such a comment exists and the pull request merges anyway (INC-302). After merge, when a user, a failing job or a production process meets the extra change (INC-301, INC-305, INC-307, INC-308). The stages are spelled as in `docs/vocabularies.json`.

## Protections

Cheapest first. The first rungs make an extra change less likely, or cheap to take back; the middle ones make it visible and keep it out of the files it should not reach; the last ones check the whole diff, or the behaviour outside the task, whatever the agent intended. None of them replaces the ones before.

### Prompt: state the scope, and ask for extra changes to be proposed, not made

- **Source:** [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): "Only make changes that are directly requested or clearly necessary." [Sonnet 5.5 prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5): "Don't add features, tests, files, docs or refactors that weren't asked for." and "If you think one would help, mention it at the end instead of doing it." The [GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide): "Changes should be minimal and focused on the task."
- **Cost:** Tokens for the instruction, in the prompt or in the project's instruction file.
- **Breaks when:** The instruction is context, not enforcement ([Claude Code memory](https://code.claude.com/docs/en/memory.md)); in INC-305 and INC-308 such rules were in force and the agent went past them. A measured preservation instruction reduced over-editing and did not remove it (see Evidence). Another instruction pulls the other way, such as a rule to keep the linter green (INC-306).

### Undo: keep a checkpoint, so the agent's edits can be rewound

- **Source:** [Claude Code checkpointing](https://code.claude.com/docs/en/checkpointing.md) tracks the agent's file edits so they can be rewound; [Gemini CLI checkpointing](https://geminicli.com/docs/cli/checkpointing.md) snapshots the project before a change.
- **Cost:** Disk space for the snapshots; nothing per edit.
- **Breaks when:** Nobody notices the extra change, since undo needs someone to ask for it. Claude Code does not track files changed only through shell commands; Gemini CLI's checkpointing is off by default and restores the whole snapshot, not one hunk.

### Task: name the files and the outcome, and give the agent only what it needs

- **Source:** [GitHub Copilot coding agent](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results): "GitHub Copilot provides better results when assigned clear, well-scoped tasks." [Aider tips](https://aider.chat/docs/usage/tips.html): "Just add the files you think need to be edited."
- **Cost:** The author's time to write the issue; more, smaller tasks.
- **Breaks when:** Acceptance criteria say what must be in the diff, not what must stay out of it. Inside a file the task has to edit, nothing limits which lines change (INC-301, INC-304).

### Plan first, and approve the plan before any edit

- **Source:** [Claude Code permission modes](https://code.claude.com/docs/en/permission-modes.md): "Plan mode tells Claude to research and propose changes without making them." [Cline Plan and Act](https://docs.cline.bot/core-workflows/plan-and-act.md) keeps the planning mode from changing files.
- **Cost:** One more round of reading per task.
- **Breaks when:** The approved plan is not checked against the edits that follow. In Claude Code, approving a plan switches the session to a mode in which it edits, and the documentation describes no step that compares the diff with the plan. The rung depends on a person reading the plan, which fails as the plan-review rung in [Irreversible effects](irreversible-effects.md) describes; when an approval is required at all is the rule stated there.

### Self-check: before pushing, read the whole diff and drop what the task did not ask for

- **Source:** [Scope Guard](https://github.com/andreahlert/scope-guard), a third-party Claude Code plugin that reads the git diff and asks of each file "Is this file EXPLICITLY mentioned in the prompt?". [Claude Code best practices](https://code.claude.com/docs/en/best-practices.md) runs its diff review "in a fresh subagent that never saw your conversation". Running the same file-by-file check as a fixed step before every push is one operator's practice.
- **Cost:** Tokens and seconds per push; a person's attention when the check flags a file.
- **Breaks when:** The agent judges its own diff by its own account of the task, which is the account that was wrong in INC-301. The plugin is advisory, works per file and publishes no accuracy figure; an extra hunk inside a file the task names passes it.

### Formatting: pin the formatter and check it in CI, so a diff holds no reformatting

- **Source:** [Prettier](https://prettier.io/docs/install): "Even a patch release of Prettier can result in slightly different formatting", so it is pinned to an exact version, with a check in CI. [Google's reviewer guide](https://google.github.io/eng-practices/review/reviewer/looking-for.html): (a CL, or changelist, is Google's term for a pull request): "The author of the CL should not include major style changes combined with other changes."
- **Cost:** A CI step; one formatting commit to bring the repository in line.
- **Breaks when:** It removes only formatting noise: a rename, a deletion, an extra feature or a changed default passes it.

### One change per pull request, refactors apart

- **Source:** [Google's guide to small changes](https://google.github.io/eng-practices/review/developer/small-cls.html): "It's usually best to do refactorings in a separate CL from feature changes or bug fixes." A size check such as [pr-size-labeler](https://github.com/CodelyTV/pr-size-labeler) labels a pull request by changed lines and can fail the largest.
- **Cost:** More pull requests to open and review.
- **Breaks when:** The agent does not follow the norm unless told or gated, and agent pull requests bundle objectives more often than human ones (see Evidence). A size limit misses the small change with a large effect: one changed default, one deleted step (INC-302).

### Path limits: keep the agent out of the files the task does not touch

- **Source:** [Claude Code permissions](https://code.claude.com/docs/en/permissions.md) deny edit rules by path, and a [PreToolUse hook](https://code.claude.com/docs/en/hooks-guide.md) can block an edit to a listed file. On the server, [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) requests a review from the owner of any path a pull request touches, and a push ruleset can [restrict file paths](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
- **Cost:** Writing and keeping the path lists; an owner's review when a path is touched.
- **Breaks when:** The list is set per repository, not per task, so most files stay in reach. The deny rules do not cover a script or a subprocess that writes files itself, and push rulesets apply only to a private or internal repository. Every one of these works by file: an unrequested hunk inside a file the task has to edit passes them all (INC-301, INC-304). Why matching on paths leaks at all is [Pattern-matched boundaries](pattern-matched-boundaries.md).

### Review: read every hunk against the issue, before the merge

- **Source:** [Google's reviewer guide](https://google.github.io/eng-practices/review/reviewer/looking-for.html): "look at _every_ line of code that you have been assigned to review." An AI reviewer can be set to compare the diff with the linked issue: CodeRabbit's issue assessment checks that pull requests "address linked issues without containing out-of-scope changes" ([CodeRabbit](https://docs.coderabbit.ai/pr-reviews/pre-merge-checks)), and PR-Agent has an option to "validate that the PR code doesn't contain any additional content that is not related to the ticket" ([Qodo PR-Agent](https://github.com/qodo-ai/pr-agent/blob/main/docs/docs/core-abilities/fetching_ticket_context.md)).
- **Cost:** Reviewer time for every hunk; tokens or a subscription for an AI reviewer.
- **Breaks when:** The review comes after the merge (INC-301), or its finding does not block it (INC-302). The AI checks are advisory unless set to block: CodeRabbit's blocks a merge only when paired with its automatic approvals, and it reads the issue's title and description, not its discussion ([CodeRabbit issue validation](https://docs.coderabbit.ai/issues/pr-validation.md)); PR-Agent's option is off by default. Neither publishes an accuracy figure.

### Tests that pin the behaviour outside the task

- **Source:** Characterization tests record what the code does now, before it is changed ([Feathers](https://michaelfeathers.silvrback.com/characterization-testing)); snapshot tests catch output that changes "unexpectedly" ([Jest](https://jestjs.io/docs/snapshot-testing)). On the changed lines themselves, a diff coverage gate fails a pull request whose changed lines are not run by a test ([diff-cover](https://github.com/Bachmann1234/diff_cover)), and diff-based mutation testing reports, in review, changed code whose tests do not notice a mutation ([Google](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/)).
- **Cost:** Writing the tests before the change; CI minutes for coverage and mutation runs.
- **Breaks when:** The extra change lands where no test reaches. A deleted line is not a changed line to cover or mutate, so a removed step or function passes the diff gates. An agent that regenerates the snapshots or edits the tests to pass belongs to the class tests that cannot fail.

### Compare behaviour with a reference, or cut the patch to what the tests need

- **Source:** [PatchDiff](https://arxiv.org/abs/2503.15223) generates inputs on which a patch and a reference patch behave differently; [TRIM](https://arxiv.org/abs/2607.18161) minimizes the agent's trajectory to cut what it calls CodeSlop, "the residual and functionally unnecessary edits commonly seen in AI-generated code". Across the agent frameworks (scaffolds) it was run in, it reports "TRIM cuts CodeSlop by 17.9%-32.9% across agentic scaffolds, with negligible performance regression."
- **Cost:** A reference to compare against, or a validation run per removed step; TRIM reports roughly half the validation cost of delta debugging (as of 2026-07, [TRIM](https://arxiv.org/abs/2607.18161)).
- **Breaks when:** There is no reference behaviour, or the generated inputs do not reach the difference. Both are research tools, not products, and minimization needs tests strong enough to say that a removal is safe.

## Evidence

- **Plausible patches that do more.** On SWE-bench, "even more (29.6%) plausible patches induce different behavior than the ground truth patches"; of those, 27.3% are "generated patches that adapt more behavior than the ground truth patches" (as of 2025-09, [Wang & Pradel, PatchDiff](https://arxiv.org/abs/2503.15223)).
- **Bug patterns in generated code.** A taxonomy of 333 bugs from code generated by three models names "Non-Prompted Consideration" among its ten patterns (as of 2024-03, [Tambon et al.](https://arxiv.org/abs/2403.08937)).
- **Over-editing in minimal fixes.** On repair tasks built from 400 BigCodeBench problems, each with a known minimal patch, over-editing is "widespread even among strong models like GPT-5.5"; an instruction to preserve the original code lowered "excess Levenshtein distance from 0.195 to 0.131", reduced added cognitive complexity by 26.6% and raised Pass@1 by 2.3 points (as of 2026-09, [Zhu et al.](https://arxiv.org/abs/2609.04061)).
- **Agent pull requests bundle objectives.** "Among 213 Agentic-PRs, 85 Agentic-PRs (39.9%) have multiple objectives, compared to just 27 multi-purpose Human-PRs (12.2%)." (as of 2026-02, [Watanabe et al.](https://arxiv.org/html/2509.14745v3)).
- **Agents tangle refactorings less often than people.** On 3,691 patches from three agent frameworks with 12 models, "coding agents introduce tangled refactorings less frequently (21.43% vs. 36.72%)" than human developers; the tangled refactorings were associated with reduced compilability and showed no significant association with functional correctness (as of 2026-05, [Tian et al.](https://arxiv.org/abs/2605.22526)).
- **Rejected agent pull requests.** A taxonomy of rejection reasons from 600 agent pull requests includes "unwanted feature implementations" (as of 2026-01, [Ehsani et al.](https://arxiv.org/abs/2601.15195)).
- Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv); six of the class's ten rows are self-reported accounts with no public diff and say so in the evidence-strength column, and four are primary.
