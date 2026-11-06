---
class: done-is-not-the-effect
surfaces_at:
  - task
  - code
  - review
  - after-merge
applies_when: An AI coding agent reports a task finished (the code is written and its tests pass, the pull request merged, the command or migration ran, the issue is closed), each step it names really happened, and you want to know why the thing the task was for still does not happen where it was meant to, and what makes "done" mean that the effect was seen.
applies_when_not: A check that never ran or read nothing and was counted as a pass (absence read as success). An agent's report that a step happened when it did not (claims from plausibility). Code that catches an error at run time and carries on with a substitute (silent fallback). A test that runs but cannot fail. An agent that bends the tests or the criterion until they pass (proxy optimisation).
---

# Done is not the effect

## TL;DR

The agent reports a task done, and every step it names did happen: the code was written and its tests pass, the pull request merged, the command exited 0, the issue closed. The thing the task was for still does not happen where it was meant to. The report is about the step that produced the work; the effect lands somewhere else. Start by writing the effect into the acceptance criterion and asking for evidence of it; then make "done" a check that reads the place where the effect lands: a caller in production code, the version actually installed or running, the state of the target system, an issue that closes only on evidence from after the deploy.

## Symptom

The agent says the task is done, and every step it lists did happen. The function was written and its tests pass; the pull request merged; the command exited 0; the issue closed. Days later someone uses the feature, and nothing has changed. The new function has no caller outside its tests. The merge reached the main branch, but nothing deployed it, or the deploy shipped the previous build. The acceptance criterion said the bot answers in the channel, and nobody ever sent it a message. The script exited 0 and wrote nothing. The setting went into a file the program does not read. Each report was true of its step; none of them was about the effect the task was for.

## Examples

- INC-454: the issue for a poller was closed as done, and the poller was written and tested, but both call sites in the production driver passed it in as `None`, so it never ran outside its tests.
- INC-453: a pull request raised a dependency to a new major version; CI installed fresh and passed, but the long-lived local environment the service ran from was never upgraded, so the service crashed on import and its tools vanished from every session on the device, with no error shown, for a full session before anyone traced it.
- INC-456: six worker runs exited 0, and the supervisor marked each one done on its exit code; none opened a pull request, because the supervisor never told the workers which issue to work on.
- INC-455: the code for a label migration merged and its issue closed; the migration itself was never run, and about two weeks passed before anyone noticed.
- INC-459: a phone app likes the song playing on Spotify when a button pattern is pressed, and a fallback was written to like it when the app is not running. It could not run in that case: after the app was swiped away, a flag still said the app was attached, so every trigger went to an engine that no longer existed. The service and its notification stayed up, so nothing looked wrong, and the song was never liked.

## Mechanism

**The done signal comes from the step that produced the work.** A merge, a closed issue, an exit code and a passing test are each emitted by the step that made the change, and each is true of that step. The effect the task was for lands somewhere else: in the production call path, on the device, in the running service, in the target system's data. Nothing in the producing step looks there. Five shapes recur in this class's rows.

**Built and tested, but nothing calls it.** The tests are the only caller, so the tests pass. A poller was wired in as `None` at both production call sites (INC-454); a code review found that a module's admission logic was fully unit-tested and had no production caller (INC-466); asked for two modes of a feature, an agent wired one into the execution path and the API, marked its tasks done with the tests passing, and left the other with no caller (INC-467); on a robot, a resume path that ran the collision checks had no production caller, so the robot's motion went ahead without them (INC-463, private, not verifiable). The code can also be reachable while the condition that turns it on never holds: the setup wizard never asks for the setting a feature needs (INC-458); the documented `.env` file is never loaded, because nothing calls the loader (INC-457); a fallback written for when the app is not running is never reached then, because a flag still says the app is attached (INC-459).

**Merge is not install.** The repository is right and the installed or running copy is not. A skill (a file of instructions the agent loads from a directory on each device) merged with a commit message saying it was discoverable that day, and it was not in that directory on the device; the merge had not installed it (INC-451). A dependency bump passed CI on a fresh install and never reached the long-lived environment the service ran from (INC-453). A change that moved CI jobs to new runner labels merged before the runners were registered under those labels, so the jobs queued with nothing to run them (INC-464, private, not verifiable).

**A criterion outside the code closes with the code.** When the acceptance criterion needs an action that is not a code change (run the migration, measure the part, update the install instructions), the pull request still closes the issue: on GitHub, "When you merge a linked pull request into the default branch of a repository, its linked issue is automatically closed." ([GitHub Docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)). The code for a label migration merged, and the migration was never run (INC-455). An issue closed as code-complete while a physical offset in it was still a placeholder value (INC-462, private, not verifiable). A decision with two halves shipped one; the install lines in the README never changed (INC-450).

**Success is counted at a step before the effect.** The step that is easy to observe stands in for the one that matters. Runs were marked done on exit code 0 with no check that a pull request existed (INC-456); every point of a motion was reported sent and none was executed (INC-460, private, not verifiable). The agent's own stopping rule has the same shape: "Claude stops when the work looks done." ([Claude Code best practices](https://code.claude.com/docs/en/best-practices)). That page's answer is a check the agent can run, and its list of checks includes "A build's exit code", which on its own is the step, not the effect.

**A check is built and never run.** A test suite or an evaluation exists and reads as coverage, and no job runs it. Of three evaluation systems in one repository, one had not run once in about three and a half months and another's CI mode was never wired (INC-452); frontend tests, lint and type checks existed and no CI job ran them (INC-465, private, not verifiable).

**Where this class ends.** Here each step the report names really happened and succeeded, and the effect did not follow. In [absence read as success](absence-read-as-success.md), a check never looked, or read nothing, and its silence was counted as a pass. INC-452 and INC-465 sit on that line: a suite that no job runs is a check that never looks. They are in this class because no check reported green over them. The work reported done was building the check, and that work really happened; what never followed was its effect, a regression caught. Had a CI job run the suite, collected nothing and passed, the row would belong to absence read as success. In [claims from plausibility](claims-from-plausibility.md), the report of the step is itself false: the tests did not run, the file does not say that. INC-467 has that half too, since asked, the agent said both modes were supported; it is here because each step it reported (written, tested, marked done) did happen. In [silent fallback](silent-fallback.md), code catches an error at run time and carries on with a substitute. INC-453 has that half too, since nothing reported the crash to the session, but the cause is that a merge was read as an install. In [tests that cannot fail](tests-that-cannot-fail.md), the test cannot go red; here the tests can fail, and they test the unit, not whether anything calls it (INC-466). In [proxy optimisation](proxy-optimisation.md), the agent bends the test or the criterion until it passes; here nothing is bent, and the step that passed was never the effect.

## Where it surfaces

Mostly after merge: in 14 of this class's 18 dataset rows the missing effect was found after the work had merged or the issue had closed. It shows when someone uses the thing: a session finds its tools missing (INC-453), the author's own manual run finds no install line in the README (INC-450), a scan of the device finds the skill absent (INC-451). Or a later look at the code or the record finds it: a poller passed `None` (INC-454), a migration never run (INC-455), an evaluation that never ran (INC-452). Or the next CI run breaks, as when jobs queued with no runner (INC-464, private, not verifiable). Where the rows record how long it went unseen, it runs from about two weeks (INC-455) to about three and a half months (INC-452). At the task stage, it shows when someone looks for the artifacts the runs should have left: six runs reported done, and there was no pull request, branch or comment among them (INC-456). In code, it shows when the change is run against the real target, as with a motion reported sent that did not happen (INC-460, private, not verifiable), or when the user asks whether the feature can be reached, as in INC-467. In review, it shows when the reviewer asks who calls the new code; the review of INC-466 found that nothing did. No row was caught in CI, and INC-453 shows why: CI checked a fresh install, which was not where the effect was missing.

## Protections

Ordered from the cheapest rung to the strongest. The early rungs act on the agent and the code; the later ones read the place where the effect lands, and only those can see an effect that is missing outside the diff. No rung replaces another. A Source line that reads "one operator's practice" means the maintainer's practice, with no outside source behind it. Where the effect is physical and cannot be undone (a robot's motion, INC-460, INC-462, INC-463, all private, not verifiable), the approval side is in [irreversible effects](irreversible-effects.md).

### Prompt: write the effect into the criterion, and ask for evidence of it

- **Source:** "In order to provide value, the Increment must be usable." ([Scrum Guide](https://scrumguides.org/scrum-guide.html)); Anthropic's guide says to ask for evidence: "the command it ran and its output, or the screenshot" ([Claude Code best practices](https://code.claude.com/docs/en/best-practices)). Writing each criterion as the effect seen at its target (the bot answers in the channel, the label exists in the repository) rather than as the step is one operator's practice.
- **Cost:** tokens, and the time to write the criterion.
- **Breaks when:** the evidence offered is the step's own signal: INC-456's runs were judged on their exit code, and the same page lists "A build's exit code" among the checks to give the agent ([Claude Code best practices](https://code.claude.com/docs/en/best-practices)). Asking is not checking: asked whether both modes were reachable, the agent in INC-467 said they were while one had no caller.

### Static: find code that only the tests reach

- **Source:** Knip's production mode leaves the tests out of the entry points, because "Test files usually import production files." ([Knip production mode](https://knip.dev/features/production-mode)); [Vulture](https://github.com/jendrikseipp/vulture) finds unused Python code. Searching for a call site outside the tests before closing the task is one operator's practice.
- **Cost:** CI seconds, and the time to declare the entry points.
- **Breaks when:** the tool runs in its default mode, where a test counts as a caller; the code is reached by name at run time, since "Due to Python's dynamic nature, static code analyzers like Vulture are likely to miss some dead code." ([Vulture](https://github.com/jendrikseipp/vulture)); or there is a caller and the condition that turns the code on never holds, which no call graph shows (INC-458, INC-459). In the maintainer's record, code with no production caller shipped again while a written rule to search for call sites was in force, and a review caught it, not the rule. The code and the review are INC-466; that the rule was in force comes from the maintainer's audit (as of 2026-10, one operator's audit, private, not verifiable).

### Review: a fresh reader asks who calls it and where the effect lands

- **Source:** `/code-review` "reviews the diff in a fresh subagent" ([Claude Code best practices](https://code.claude.com/docs/en/best-practices)); the review of INC-466 is the one in this class's rows that found a module with no production caller.
- **Cost:** tokens per pull request, and the time to triage its findings.
- **Breaks when:** the missing effect is outside the diff, where nothing in the code is wrong: a skill not on the device (INC-451), a migration never run (INC-455), runners not yet registered under new labels (INC-464, private, not verifiable).

### Integration test: run the real entry point, not the unit

- **Source:** "Integration tests determine if independently developed units of software work correctly when they are connected to each other." ([Fowler, integration test](https://martinfowler.com/bliki/IntegrationTest.html)). Starting such a test from the production entry point (the driver, the service's start, the setup wizard), so that it uses the production wiring, is one operator's practice.
- **Cost:** a test environment per entry point; broad integration tests "require live versions of all services, requiring substantial test environment and network access" ([Fowler, integration test](https://martinfowler.com/bliki/IntegrationTest.html)).
- **Breaks when:** the test builds the wiring itself, so a test that constructs its own poller says nothing about the production driver of INC-454, which passed `None`; or the test's configuration is not the one a user ends up with, so an action that is tested but gated on a setting the setup wizard never asks for (INC-458), and a `.env` file that nothing loads (INC-457, whose fix added a test through the real loader), stay hidden.

### Run the app: the agent checks the change by using it

- **Source:** the `/verify` skill is meant to "Build and run your app to confirm a code change does what it should, without falling back to tests or type checks" ([Claude Code skills](https://code.claude.com/docs/en/skills)); Anthropic's long-running harness keeps a feature list the agent may change only by setting a pass status, after seeing "Claude's tendency to mark a feature as complete without proper testing." ([Anthropic, effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).
- **Cost:** tokens and run time per check.
- **Breaks when:** the app needs more than a plain start: "That inference gets unreliable for projects that need anything beyond a standard launch: a database, an env file, a graphical session, a multi-step build." ([Claude Code skills](https://code.claude.com/docs/en/skills)); the run differs from what ships, as when an agent testing its own change "temporarily bypassed the feature flag gating the marketplace page, then reverted before pushing." ([Cursor](https://cursor.com/blog/agent-computer-use)); or the effect lands where the agent cannot run anything: a phone after the app is swiped away (INC-459), a robot (INC-460, private, not verifiable).

### Harness: a check the agent cannot skip before it stops

- **Source:** a Stop hook "sends Claude back to work if the script exits with code 2", and with `/goal` "a separate model checks against the conversation after every turn" ([Claude Code best practices](https://code.claude.com/docs/en/best-practices)). A vendor reports one harness change, which included a check against the task before the agent exits, raising its Terminal Bench 2.0 score from 52.8 to 66.5 (as of 2026-02, [LangChain](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering)); the figure is for the whole change, not the check alone.
- **Cost:** a script per check, or tokens per turn for a second model.
- **Breaks when:** the script reads the step: INC-456's supervisor was such a check, and it read exit codes; or the checker reads the conversation, which holds what the agent reported, not the target.

### Done reads the target's state, not the step's signal

- **Source:** in Anthropic's agent evaluations the outcome "is the final state in the environment at the end of the trial", and for a flight booking "the outcome is whether a reservation exists in the environment's SQL database." ([Anthropic, demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)). Writing one such check per kind of task (the pull request exists, the label exists, the row exists) and marking a run done only when it passes is one operator's practice.
- **Cost:** one check per kind of effect, written and kept.
- **Breaks when:** the state read is still a step: in INC-459 the service and its notification stayed up, so a check that the service runs passes while no song is liked; or the target cannot be read from where the check runs, as with motion on a robot (INC-460, private, not verifiable).

### Close on evidence: no closing keyword for a criterion outside the code

- **Source:** a merged pull request closes its linked issue ([GitHub Docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)), so a criterion outside the code closes with the code. Linking such an issue without a closing keyword, and closing it by hand with the evidence from after the deploy, is one operator's practice.
- **Cost:** a manual close per issue; issues waiting for their evidence stay open and need a sweep.
- **Breaks when:** the evidence attached is itself a step (INC-459's service was running); or someone closes the issue on the code anyway, as INC-462 was closed as code-complete with a placeholder value in it (private, not verifiable).

### Reconcile: the installed copy matches what merged

- **Source:** a GitOps controller reports whether the live state matches the repository: "Is the deployed application the same as Git says it should be?" ([Argo CD](https://argo-cd.readthedocs.io/en/stable/core_concepts/)). INC-453's fix was a check at each session start that compares a hash of the dependency manifest with a stamp written at the last install, probes the imports and repairs a mismatch; it is one operator's practice. For settings, the Kubernetes API server under strict validation "rejects the request with a 400 Bad Request error when it detects any unknown or duplicate fields." ([Kubernetes API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)).
- **Cost:** a hash and an import probe at each start; for a controller, its setup and upkeep.
- **Breaks when:** the installed versions still satisfy a widened range, so the install is a no-op and the check goes green without the environment changing (INC-453's own stated limit); the step is outside what the reconciler sees, such as registering runners (INC-464, private, not verifiable) or a skill installed per device (INC-451); or the live copy is in sync and broken, since Argo CD reports health apart from sync: "is it running correctly? Can it serve requests?" ([Argo CD](https://argo-cd.readthedocs.io/en/stable/core_concepts/)). Strict validation catches an unknown key, not a correct key in a file the program never loads (INC-457).

### Live probe: exercise the effect where it lands

- **Source:** synthetic monitoring "runs a subset of an application's automated tests against the live production system on a regular basis" ([Fowler, synthetic monitoring](https://martinfowler.com/bliki/SyntheticMonitoring.html)), which covers a bot nobody has sent a message to; Terraform check blocks run an assertion after apply ([Terraform checks](https://developer.hashicorp.com/terraform/language/checks)); a canary compares a partial deployment with a baseline ([Google SRE workbook](https://sre.google/workbook/canarying-releases/)).
- **Cost:** a probe per effect and somewhere to run it; a canary also needs traffic: "We need to receive enough traffic on the system to ensure it has handled a representative sample" ([Google SRE workbook](https://sre.google/workbook/canarying-releases/)).
- **Breaks when:** the probe reads the service and not the effect (INC-459's service was up); a failed check does not stop anything: "When a check block's assertion fails, Terraform reports a warning and continues executing the current operation." ([Terraform checks](https://developer.hashicorp.com/terraform/language/checks)); or the target is a device or a robot that no probe can reach (INC-459; INC-460, private, not verifiable). A probe that returns no data is the case in [absence read as success](absence-read-as-success.md).

### Usage: count whether the new path ever runs

- **Source:** Unleash shows a flag that is "created, but Unleash hasn't detected any metrics in any environments" as its own stage ([Unleash](https://docs.getunleash.io/concepts/feature-flags)); [Coverband](https://github.com/danmayer/coverband) records which lines run in production; Meta's dead-code tool combines static, run-time and application analysis ([Meta engineering](https://engineering.fb.com/2023/10/24/data-infrastructure/automating-dead-code-cleanup/)).
- **Cost:** instrumentation per path, and someone reading the counts.
- **Breaks when:** the path is meant to be rare, as a fallback is, so a zero count cannot tell code that is dead from code not yet needed (INC-459's fallback had never been exercised in normal use); or the count is read once and too early. Meta's tool accepts misses to avoid deleting live code: "this approach can cause false negatives, but avoids false positives" ([Meta engineering](https://engineering.fb.com/2023/10/24/data-infrastructure/automating-dead-code-cleanup/)).

## Evidence

- No study found measures this class directly: how often agent-written code ships with no production caller, merges without being deployed, or writes a setting where it is not read (as of 2026-11, external search for this doc).
- Maintainers of three repositories reviewed 296 agent pull requests that passed the tests of the SWE-bench Verified benchmark and would not have merged roughly half of them (as of 2026-03, [METR](https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/)); the agents were not given a chance to iterate on the feedback. A passing test is a step, not the effect.
- A study of 20,574 coding-agent sessions from 1,639 repositories counts inaccurate self-reporting among the ways agents fail their users (as of 2026-05, [arXiv 2605.29442](https://arxiv.org/abs/2605.29442)); its category also holds false reports of a step, which belong to [claims from plausibility](claims-from-plausibility.md).
- Anthropic built its long-running harness around "Claude's tendency to mark a feature as complete without proper testing." (as of 2025-11, [Anthropic, effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).
- Most of the record is the maintainer's own: 17 of the class's 18 rows come from the maintainer's repositories, 6 of them private. In the maintainer's audit of about 16 incidents, an agent found 7 later, the user found 5 in use, 2 were found late or never and CI found 1; and fixes written only as rules for the agent were followed by the same failure again (as of 2026-10, one operator's audit, private, not verifiable).
- Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv); six of the class's rows are private sources and say so in the link column.
