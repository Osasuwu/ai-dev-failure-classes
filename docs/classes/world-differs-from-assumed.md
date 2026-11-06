---
class: world-differs-from-assumed
surfaces_at:
  - task
  - code
  - ci
  - review
  - merge
  - after-merge
applies_when: An AI coding agent wrote, ran or checked a change in one world (its own machine, OS or shell, a worktree, an interactive session, a CI runner) or against its idea of how a platform behaves (how GitHub links and closes issues, what a token or a role may do, what a squash merge keeps, how concurrent runs interleave), and the change runs in another (a different device or OS, a headless or scheduled run, CI without the hardware, the real platform). You want to know why it worked where it was tried and fails where it runs, and what catches the difference before it does.
applies_when_not: An agent's claim of done that nobody checked at all (claims from plausibility). A check that never ran and counted as passed (absence read as success). Two copies of one fact, such as a doc and the code, that drifted apart (copies of one truth drift). Code that caught a failure and returned a default (silent fallback). A guard that matched the wrong spelling of a command or path (pattern-matched boundaries). Destroying data by accident.
---

# The world differs from the assumed one

## TL;DR

The agent checked its change where it could: on its own machine, in an interactive session, in the main checkout, against its idea of how GitHub or the OS behaves. The change then runs somewhere else, another device, a worktree, a headless run, the real platform, and fails there. The check was real; its result did not say which world it came from. The cheapest rungs remove the assumption (no hard-coded path or interpreter name, tests that set their environment instead of inheriting it). The stronger ones run the check in the target world: a preflight that executes the tool it needs, declared provisioning for headless runs, an OS matrix in CI, a read-back of the platform's state after acting, and a first rollout to one target before the rest.

## Symptom

It worked where it was tried. The agent ran the script, the tests passed on its machine, the workflow was green on the branch, the pull request said it would close the issue. Then the change runs where it was meant to run, and it does not work:

- a script or config that worked on the agent's machine fails on another device, because a path, a home directory or a user name differs, or a shell, a line ending or an encoding behaves differently on another OS;
- a hook, a tool or a setting that works in an interactive session does nothing in a headless or scheduled run, or in a worktree, where the file or the permission it relies on is not there;
- a test that passes in CI never touched the hardware, the service or the credential the code needs where it runs;
- a pull request merged and the issue it named stayed open; a token that worked locally lacks a permission in the workflow; two runs that each worked alone collided when they ran at the same time; a squash merge kept less than the branch history did.

Each time the agent did check something. It checked in a world that was not the one the change runs in, and nothing in the result said which world it came from.

## Examples

Each `INC-` ID is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv), which links its source and says how strong that source is.

- INC-353: shipped hook snippets ran `python3 "<hook>.py" || exit 2`. Rolling a guard out to the maintainer's two other Windows devices showed that `python3` there was the Microsoft Store stub, which prints an error and exits, so on such a machine the fail-closed snippet would block every tool call it matched.
- INC-352: the hooks were installed in the main checkout's untracked `.claude/settings.local.json`; a session in a worktree does not read that file, so none of the hooks ran there.
- INC-356: a fix moved merges to a GitHub App identity on the hypothesis that GitHub's issue auto-close would then fire; the fix's own merge had a valid `Closes` line, and three hours later the issue was still open.
- INC-364: a routine test run inserted 392 rows into a production database table over six minutes, and a daemon turned them into escalations with real chat pings, because two defects met: the test setup used `os.environ.setdefault`, which loses to the real `.env`, and the host's PATH lacked tools the tests expected, which sent the run down the production path.
- INC-372: an Android app inherited its target SDK, 36, from the framework default; Android 15 and later refuse a media-playback foreground service started from the boot receiver, so the app crashed at boot and its listener never came back after a reboot.

## Mechanism

**The check ran, in another world.** In [claims from plausibility](claims-from-plausibility.md) the agent says a thing works without checking it. Here the agent did check: it ran the script, the tests passed, CI went green, the pull request showed the issue as linked. The result is true of the world it ran in. Nothing in it records the device, the checkout, the kind of session or the platform's rule it relied on, so it is read as true of the world the change runs in. The fault is not the check but the unstated premise that the two worlds are the same.

**The device or the OS differs.** A path, a user name or an interpreter name is different on the next machine. A scheduled-task installer defaulted to the first `python3` on the PATH, which on the maintainer's Windows devices was the Store stub, so the task registered and then died at every start (INC-359); INC-353 is the same stub under a hook. A hook resolver had one machine's checkout path written into it and failed on a device with another layout, blocking the Bash and Write tools there (INC-362). User-level hooks pointed at `$CLAUDE_PROJECT_DIR`, right in the project they were written for and wrong in a session in any other project (INC-361). On the user's machine, autostart still launched a stale frozen build, not the install that was being fixed and tested (INC-371). Agent instances running in parallel on Windows opened pull requests that flipped line endings (INC-373, private).

**The checkout differs.** A worktree is not the main checkout: untracked files are not in it. The hooks' settings file was not there, so no hook ran (INC-352). A server looked for its `.env` one or two directories above itself, which reaches it from the main checkout and not from a worktree, so worktree sessions fell back to a weaker database key and their updates to existing rows failed (INC-363). Directories that looked like worktrees had no `.git` link, and agent work landed in the main checkout (INC-374, private).

**A headless run is not set up or permitted like the one that was tried.** The unattended worker's job installed no Python environment, so the `pytest` it was allowed to run was not there, and it pushed code it had never run; a fresh-context review found it (INC-369). A review run in CI, where nobody is there to approve a tool call, hit four permission denials; the run ended as an error and the steps meant to verify it were skipped (INC-358). A step approved in an issue was refused by the harness's own permission classifier, which the approval does not reach (INC-366). A self-hosted runner kept a corrupted workspace between jobs, and jobs on it failed and retried in a loop (INC-376, private).

**Real configuration reaches code that assumed its own.** The test setup filled in environment variables only where they were missing, so on a machine with a real `.env` the tests ran against production; a tool missing from the host's PATH was what sent them down that path (INC-364). A desktop client appended `/rest/v1` to the configured URL; a user pasted the URL with `/rest/v1` already on it, and requests went to a doubled path and failed (INC-370).

**The platform follows other rules than the agent's model of it.** This is the largest group, and the agent's local check cannot see it at all, because the rule lives on the platform:

- Linking and closing. Merges with a closing keyword did not close their issues, which were closed by hand (INC-355, and INC-356 above). A squash commit's title named one of two issues, so the other stayed open (INC-377, private). A pull request opened with a closing keyword kept that link after the keyword was edited out of its body, so it was closed and replaced by one with the same diff (INC-365, as the replacement pull request records it).
- Merging. A squash merge put a doc and its sign-off entry into one commit, which a gate check forbade, so `main` went red and each later pull request inherited the failure (INC-350, and again in INC-351). `gh pr merge --delete-branch` on the root of a stack deleted the branch its child pull requests targeted; GitHub closed them and would not reopen them, at least three times (INC-367).
- Actions. Two pull requests that a workflow opened had no checks at all, so they could not merge; the issue found this consistent with the rule that events from the default `GITHUB_TOKEN` start no workflow runs (INC-357). Workflow-level concurrency is resolved before a job's `if`, so any label added to an issue could cancel a running worker (INC-368). A plugin installer clones with `git clone --branch <ref>`, which takes a branch or a tag and not a commit SHA, so pinning the plugin to a SHA broke the review on each pull request (INC-360).
- The OS, the harness and other vendors. INC-372's Android rule. A setup skill assumed one rules-file name per harness, so in a repo with only `AGENTS.md` it would have created a `CLAUDE.md` that changes which file Claude Code loads (INC-354). A pull request body was posted as a literal `@path`, because the tool the agent used did not expand it (INC-375, private).

**Fixes close one world and leave the next open.** In the maintainer's record (the incidents from the maintainer's own repositories, and the maintainer's audit of the 28 incidents behind this class's rows, cited below as "one operator's audit"; see Evidence), path assumptions failed at three different sites (INC-361, INC-362, INC-363), and the Store stub was hit at four sites. Of the fixes that added a check, 7 held, 2 held only because the surface was deleted, and 12 recurred, moved or left a sibling open; none of the 3 fixes written only as an instruction held. A fail-closed check, rolled out to devices it had not run on, would have turned into a total block there (INC-353) (as of 2026-10, one operator's audit, private, not verifiable).

## Where it surfaces

Late. In 13 of the class's 28 dataset rows the failure was found after merge, in code that had already shipped, for example: on another device (INC-353, INC-359, INC-362), in a worktree (INC-363), on a user's machine (INC-370, INC-371), or as an issue still open after its merge (INC-355, INC-356). In CI, 5 rows: the runner was the first world that differed from the agent's (INC-358, INC-360; INC-376, private), or a merge semantics problem first showed as a red `main` (INC-350, INC-351). At merge, 4 rows: pull requests that would not merge because they had no checks (INC-357) or a stack that lost its children (INC-367). In review, 3 rows (INC-354, INC-369, INC-375); in code, 2 (INC-364 by its own effect, INC-374); at the task, 1 (INC-366). In the maintainer's audit, a person, not an agent or CI, found 8 of the 28, all of them cases where a device or the user's own configuration differed; none of the platform-rule cases was found by a person, since they left a stuck state (an open issue, a pull request with no checks) that an agent or CI found later (as of 2026-10, one operator's audit, private, not verifiable).

## Protections

Ordered by cost, from the cheapest rung to the strongest. The cheap rungs tell the agent what it cannot see, flag or remove an assumption, or read the platform's rule and its state after acting; the costly ones run the check in the world the change runs in: a declared headless environment, a shared container, a CI matrix or rig, the real service, one target before the rest. No rung replaces another. A Source line that reads "one operator's practice" means the maintainer's practice, with no outside source behind it.

### Prompt: tell the agent what it cannot see

- **Source:** what an agent cannot find is "the information that was never in the repo", such as "The environment variable your integration tests need" ([Claude Code best practices](https://code.claude.com/docs/en/best-practices.md)); [AGENTS.md](https://agents.md/) gives build, test and environment notes "a dedicated, predictable place". Naming there the worlds a change must run in (each device and its OS, worktrees, headless runs) is one operator's practice.
- **Cost:** tokens, and keeping the file current.
- **Breaks when:** the file describes one device while the others differ, or the rule is not in the context of the run that needs it; in INC-354 the setup skill itself held the wrong model of which rules file a harness reads. In the maintainer's record none of the 3 fixes written only as an instruction held (as of 2026-10, one operator's audit, private, not verifiable).

### Lint: flag code that behaves differently per platform

- **Source:** ruff PLW1514, a preview rule, flags `open` in text mode without an encoding, which "can lead to non-portable code," ([ruff](https://docs.astral.sh/ruff/rules/unspecified-encoding/)); "many Python developers using Unix forget that the default encoding is platform dependent." ([PEP 686](https://peps.python.org/pep-0686/)). ShellCheck flags syntax the target shell lacks: "In POSIX sh, `[[ ]]` is undefined." ([ShellCheck SC3010](https://www.shellcheck.net/wiki/SC3010)).
- **Cost:** CI seconds.
- **Breaks when:** the difference is in what a name resolves to on the next machine, not in a construct a rule knows: `python3` was the Store stub in INC-353 and INC-359, and a resolver held one machine's path in INC-362; or the script runs under another shell than it declares, or the difference is in external tools (GNU against BSD flags).

### Worktrees: carry what the checkout needs

- **Source:** "A worktree is a fresh checkout, so untracked files like `.env` or `.env.local` from your main repository are not present."; files matched by `.worktreeinclude` are copied into a new worktree ([Claude Code worktrees](https://code.claude.com/docs/en/worktrees.md)). Finding a server's `.env` from the repository root, not a fixed number of directories up, is one operator's practice.
- **Cost:** one file of patterns.
- **Breaks when:** the worktree is made another way, since a `WorktreeCreate` hook replaces the default creation and the file is not processed (Claude Code worktrees), or the directory is not a worktree at all (INC-374, private); or a listed file changes in the main checkout after the copy was made.

### Platform rules: read the documented rule before relying on it

- **Source:** in a pull request into another branch, closing keywords "are ignored, no links are created, and merging the PR has no effect on the issues." ([GitHub Docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)); "events triggered by the `GITHUB_TOKEN` will not create a new workflow run" ([GitHub Docs](https://docs.github.com/en/actions/concepts/security/github_token)), so a workflow whose pull requests need checks opens them with an App or personal token; a merge queue needs "the `merge_group` event to trigger your GitHub Actions workflow" ([GitHub Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)).
- **Cost:** reading time per platform feature the change relies on.
- **Breaks when:** the platform's behaviour differs from the rule as the reader understood it: INC-356's merge had a valid closing line and the issue was still open hours later, and INC-365's pull request kept a closing link after the keyword left its body; or two documented features interact, as a workflow-level concurrency group and a job's `if` do, where any label could cancel a running worker (INC-368).

### Read back: confirm the platform's state after acting

- **Source:** one operator's practice: before a merge, read the pull request's `closingIssuesReferences`; after it, read the issue's state and close it if it is still open; after a workflow opens a pull request, confirm its checks started (INC-357).
- **Cost:** one API call per action.
- **Breaks when:** the field it reads is the wrong one, as a link that outlived its keyword (INC-365) still reads as linked; or the read-back only reports: after INC-356's bot merges, which GitHub's auto-close skipped, the merge workflow commented on each linked issue and closed none of them.

### Code: remove the assumption instead of checking it

- **Source:** [pathlib](https://docs.python.org/3/library/pathlib.html) joins paths by the running OS's rules, and its pure classes let a test build another OS's paths: "you can instantiate PureWindowsPath". A Claude Code hook can anchor on `${CLAUDE_PROJECT_DIR}` ([Claude Code worktrees](https://code.claude.com/docs/en/worktrees.md)). Running the interpreter to probe for it and falling back to the next name (`python3`, then `python`), instead of naming one, is one operator's practice.
- **Cost:** engineering time per site.
- **Breaks when:** the anchor is itself an assumption: user-level hooks resolved through `$CLAUDE_PROJECT_DIR` worked in their own project and broke in every other (INC-361), and after a session moves into a worktree the variable "still points at the project root where the session started" (Claude Code worktrees). A fix covers the site that broke, not the next: path assumptions failed at three sites (INC-361, INC-362, INC-363), and the Store stub at four (as of 2026-10, one operator's audit, private, not verifiable).

### Guard: refuse the platform operations known to misbehave

- **Source:** one operator's practice: a `PreToolUse` hook ([Claude Code hooks guide](https://code.claude.com/docs/en/hooks-guide.md)) that refuses `gh pr merge --delete-branch` on a pull request that other pull requests target, after INC-367 closed a stack's children.
- **Cost:** writing the hook and keeping its list current.
- **Breaks when:** the same operation is spelled another way or goes through another tool, the failure described in [pattern-matched boundaries](pattern-matched-boundaries.md); or the next misbehaving operation is not on the list.

### Tests: set the environment, never inherit it

- **Source:** [Testcontainers](https://testcontainers.com/) runs tests against the real engine in a container: "No more need for mocks or complicated environment configurations." Setting every variable a test reads unconditionally, never with `setdefault`, and aborting when a URL points at production, is one operator's practice. A test that can write to production is an [irreversible effect](irreversible-effects.md).
- **Cost:** setup per service; slower tests with containers.
- **Breaks when:** the code reads a variable the fixture does not set, so the real `.env` fills it; or the code takes another branch on the test host than the fixture planned for, as a tool missing from the PATH did in INC-364; or the container's version or configuration differs from production's, or the dependency is a hosted service that does not run in a container.

### Headless runs: declare the environment and what the run may do

- **Source:** GitHub's coding agent builds its environment from a committed `copilot-setup-steps.yml` ([GitHub Docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/customize-the-agent-environment)); Codex runs a setup script in a declared container ([Codex](https://learn.chatgpt.com/docs/environments/cloud-environment)); Cursor reads a committed `.cursor/environment.json` ([Cursor](https://cursor.com/docs/cloud-agent/setup)). Claude Code's bare mode "is useful for CI and scripts where you need the same result on every machine", in a headless run "a call that needs approval is denied unless something approves it", and an MCP server that failed to load shows "only in the `mcp_server_errors` field", which a job can check ([Claude Code headless](https://code.claude.com/docs/en/headless.md)).
- **Cost:** CI minutes for setup, and an allow list to keep current.
- **Breaks when:** setup fails and the agent works on: Copilot "will skip the remaining setup steps and begin working with the current state of its development environment" (GitHub Docs); setup installs less than the allow list assumes, as INC-369's worker was allowed `pytest` with no Python environment; or the allow list leaves out a tool the run calls, which in a headless run is denied, not put to a person (INC-358).

### Preflight: run what the change depends on before depending on it

- **Source:** "Before the agent commits a single line, it should run a probe that asserts the local environment matches the manifest." ([Tian Pan](https://tianpan.co/blog/2026-06-01-the-coding-agent-that-passes-locally-and-fails-in-ci)). Probing by running the tool (`python3 -c ''`) rather than finding its name on the PATH, and warning instead of blocking when the probe fails, is one operator's practice.
- **Cost:** writing the manifest and the probe, and keeping them current.
- **Breaks when:** the manifest lists less than the target needs, since the probe checks only what someone thought to list; the probe only finds the name, while a Store stub is on the PATH and fails when run (INC-359); or a fail-closed check meets a device it never ran on, where INC-353's snippet would have blocked every matched call.

### Shared environment: one definition for the agent, CI and people

- **Source:** a `devcontainer.json` defines one toolchain, also usable "to aid in continuous integration and testing" ([dev containers](https://containers.dev/)), and [devcontainers/ci](https://github.com/devcontainers/ci) runs CI in that container; [twelve-factor](https://12factor.net/dev-prod-parity) asks for the same backing services in development and production.
- **Cost:** container builds, and Docker on every device that works on the code.
- **Breaks when:** the change runs outside that container: on the user's own machine (INC-371), on a phone OS (INC-372), on Windows devices whose `python3` was the Store stub (INC-353). Parity then holds between the agent and CI only.

### CI: run the check where the change will run

- **Source:** a matrix runs a job per OS, as in "a variable called `os` with the value `[ubuntu-latest, windows-latest]`" ([GitHub Docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations)); a job that needs a device or a GPU goes by label to a self-hosted runner that has it ([GitHub Docs](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow)); firmware tests run on the board, since "A passing west build doesn't mean the firmware runs on hardware" ([errata hunter](https://dev.to/erratahunter/the-build-passed-so-why-doesnt-it-run-automating-firmware-tests-on-real-hardware-2m5i)).
- **Cost:** runner minutes times the matrix size; owning and maintaining a self-hosted runner or a rig.
- **Breaks when:** the target is not in the matrix; with fail-fast, "all jobs that are in progress or queued will be cancelled" once one fails (GitHub Docs); or a self-hosted runner keeps state between jobs, as a corrupted workspace did in INC-376 (private).

### Target-side check: ask the real service before acting on it

- **Source:** a Kubernetes dry run evaluates a request "through the typical request stages (admission chain, validation, merge conflicts) up until persisting objects to storage." ([Kubernetes](https://kubernetes.io/docs/reference/using-api/api-concepts/)); consumer-driven contract tests check a provider against what its consumers expect ([Pact](https://docs.pact.io/)).
- **Cost:** access to the target, or a contract broker and both sides' cooperation.
- **Breaks when:** the dry run reaches another cluster than the deploy; or consumers call the provider in a way the contract never captured, for which Pact "does not provide any test based assurance" (Pact).

### Rollout: one target first, then the rest

- **Source:** canarying is "a partial and time-limited deployment of a change in a service and its evaluation." ([Google SRE workbook](https://sre.google/workbook/canarying-releases/)). For a change shipped to an operator's own devices, installing it on one other device before the rest is one operator's practice; INC-353's stub turned up while a guard was being rolled out to devices it had never run on.
- **Cost:** release machinery, and the time the first target runs before the rest.
- **Breaks when:** the first target is not representative: a canary needs "enough traffic on the system to ensure it has handled a representative sample" (Google SRE workbook), and a first device set up like the author's says nothing about the others.

## Evidence

- On SetupBench, coding agents had low success rates, "with particular challenges in repository setup (38.9-57.4%)", and made "non-persistent environment modifications that break agent-human collaboration workflows" (as of 2025-07, [Arora et al.](https://arxiv.org/abs/2507.09063)).
- Of 33,596 agent-written pull requests on GitHub, those not merged had more CI failures than those merged (Cliff's δ 0.24, a moderate effect), and CI or test failure was the reason in 99 of 562 categorised rejections (as of 2026-01, [Ehsani et al.](https://arxiv.org/abs/2601.15195)). The study does not say how many of those failures came from an environment difference.
- In CPython, "13% of the analyzed test files are OS-specific tests", 170 issues relate to such tests, and "Windows is the most targeted platform" (as of 2025-09, [Job and Hora](https://sol.sbc.org.br/index.php/sast/article/view/36882)). The code was not agent-written.
- "SRE has found that roughly 70% of outages are due to changes in a live system.", the book's case for progressive rollouts (as of 2016-04, [Google SRE book](https://sre.google/sre-book/introduction/)). Not agent-specific.
- The whole record is the maintainer's own: the class's 23 public rows come from the maintainer's repositories, and its 5 private rows say so in the link column of [`incidents/incidents.csv`](../../incidents/incidents.csv). The search for this doc found no source that measures how often agents get a platform's rules, such as issue closing or token triggers, wrong; only the docs that define the rules turned up.
- One operator's audit, as this doc cites it, is the maintainer's own review of the 28 incidents behind this class's rows: for each, who found it and at which stage, and whether its fix held, recurred or moved. The figures that cite it cannot be checked from outside (as of 2026-10, one operator's audit, private, not verifiable).
