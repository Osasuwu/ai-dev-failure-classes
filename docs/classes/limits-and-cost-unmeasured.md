---
class: limits-and-cost-unmeasured
surfaces_at:
  - task
  - ci
  - review
  - after-merge
applies_when: You set a limit on an AI coding agent's work or on the machinery around it (a turn or iteration cap, a token or cost budget, a timeout, a retry count, a size cap on a diff, a file or a context, a quota), or you accept a change an agent made without knowing what it costs to run (time, tokens, CI minutes, money), and you want to know why the limit cuts off work that was going well, or never fires on work that was not, and what makes a limit's value or a change's cost a measurement instead of a guess.
applies_when_not: A fallback that catches a failure and hides it, so the run looks healthy. An agent that trims or reshapes its work to fit a cap or a score. An agent that repeats edits without new information until something stops it. A check that never ran and was counted as passed.
---

# Limits and cost unmeasured

## TL;DR

A limit on an agent's run or on the machinery around it (a turn cap, a timeout, a cost budget, a similarity threshold) holds a value that nobody measured, so it cuts off work that was going well, or lets bad work run on. A change merges whose cost to run (time, tokens, CI minutes) nobody measured, and the cost turns up later in someone else's run. Start by writing down what each limit's value rests on and putting cost in the acceptance criterion. Then record every run's turns, cost, duration and stop reason, give a limit that fires a stop reason of its own, and set its value from the measured runs that succeeded, in a unit the host's load does not change.

## Symptom

The agent's run stops at its turn limit with the task half done, and its log shows it was still making progress. Another run, on a harder task, spent every turn going round in circles, and the same limit let it. A CI job is killed at its timeout on a busy day and passes on a re-run, and nobody can say how long it usually takes. A hook refuses a file because it is over a size cap that someone picked once, and the agent splits the file to get under it. A change merges, and the next week's token use, CI minutes or bill is twice what it was; the acceptance criteria never mentioned cost. A retry count or a quota fires far more often than anyone expected, or has never fired. Each limit is in plain sight in a config file. None has a measurement behind its value, so nobody knows how often it cuts off good work or lets bad work run on.

## Examples

- INC-751: a worker agent made a one-line docs fix, its pull request passed every check and merged, and the workflow step that ran the agent still failed, because the agent took 51 turns and the cap was 40. The fix raised the cap to 100, about twice that one run.
- INC-757: a gate workflow capped its agent at 12 turns while its normal path takes about 13, so on every triggered run the agent was cut off before it posted its blocking comment, and the gate failed silently. The cap went to 20 on that estimate.
- INC-760: a smoke test's turn cap was cut from 10 to 3, described as calibrated to one observed pattern of three turns. Caps of 2 and then 3 both failed, the merged value is 5, and the pull request's description still says 3.
- INC-752: a hook refused any memory write whose similarity to a differently named one reached 0.75, while its own calibration note put legitimate writes at about 0.79. Its own comment records a scheduled daily write it blocked every day after the first.
- INC-755: turning a feature on by default made one pass of a pipeline about twenty times slower, from about 18 s to about 343 s. The slowdown was never explained or accepted, and a bisect found its cause about two weeks after the merge (private, not verifiable).

## Mechanism

**A limit is a number someone picked, and a run is measured against it as if it were a fact.** Turn caps, timeouts, budgets and thresholds are set once, often from one run or a round guess, and then decide which runs count as failed. Work that is going well and work that is going nowhere look the same to the limit: both are a count that grew. Agent runs make the guess worse, because the same task does not cost the same twice: runs on one task "can differ by up to 30x in total tokens" ([Bai et al.](https://arxiv.org/abs/2604.22750)). Five forms recur in this class's rows.

**The value comes from one run or a guess.** A review workflow took its turn cap from one dry run of 28 turns times 1.5, giving 42; the next six runs went up to 57, and four of the six ended unreviewable on the cap (INC-750). A cap of 40 was raised to 100 as "~2x headroom" over one run of 51 turns (INC-751). A cap of 12 sat one turn under an estimated normal path (INC-757). A cap was doubled from 25 to 50 with no measurement cited in the pull request (INC-758). A reviewer's default of 5 turns was raised to 20, in a pull request whose title and description say 10 (INC-759). A cap was cut to the "observed 3-turn" pattern and then raised twice in the same pull request (INC-760).

**Nobody knows what happens when the limit fires.** A limit can stop work that has already succeeded: in INC-750 and INC-751 the agent ended its session as a success after more turns than the cap, and the step failed anyway, because the count was checked after the run. A limit can fail to stop anything: a per-test timeout that cannot interrupt a call into native code left a CI job hanging until the job's own 20-minute limit killed it, on every pull request (INC-753, private, not verifiable). And a limit can stop the agent before its last action, so the run ends without an error and without its output, as with the blocking comment that was never posted in INC-757.

**A threshold that blocks was never calibrated.** A hook that denies a write above a similarity score is a measuring instrument whose cut-off was chosen, not measured. INC-752's cut-off sat under the score its own calibration note gave for legitimate writes, and the fix moved it to 0.80, just above that one reading.

**Cost and speed are outside the acceptance criterion.** A change can do what it should and cost far more to run, and no check reads the cost. A default turned on made a pipeline pass about twenty times slower (INC-755, private, not verifiable); a default flipped in another change took an integration test from about 42 s to 233.6 s and, under load, past its 600 s timeout, so the main branch's CI was red on every push for two days (INC-754, private, not verifiable). Agents rarely bring the measurement with them: agent-authored performance pull requests include explicit performance validation less often than human ones, "45.7% vs. 63.6%" ([Peng et al.](https://arxiv.org/abs/2512.21757)).

**The limit is in a unit the host changes.** A wall-clock limit measures the host's load as much as the work. Stages of a search cut off by a wall-clock limit gave different results for the same code and the same input, depending on how busy the host was; a stage bounded by a count of evaluations reproduced bit for bit, 8 of 8 (INC-756, private, not verifiable). A timeout that a test meets on an idle runner it misses under load (INC-754, private, not verifiable).

**Where this class ends.** Here the limit is in plain sight and its value has no measurement behind it. In [silent fallback](silent-fallback.md), code catches a failure and carries on with a substitute, so the run looks healthy; INC-757 sits on that line, since the capped run ended with no error, but it is here because the cause was a cap set under the work. In [proxy optimisation](proxy-optimisation.md), the agent trims or reshapes its work to fit a cap or a score: splitting a file to get under a size limit is that class, and the limit's value being a guess is this one. In [absence read as success](absence-read-as-success.md), a check never looked and its silence was counted as a pass; a capped run that a workflow counts as passed is that form, which a typed stop reason (below) prevents. An agent that repeats edits without new information until a limit stops it is non-progressive iteration, a candidate class with no doc yet; there the limit is what ends the loop, and a turn cap is no cure for the loop itself.

## Where it surfaces

Most often in CI: 5 of this class's 11 dataset rows were caught there. It shows as a red step after a run that succeeded (INC-750, INC-751), as a job killed at its timeout (INC-753, INC-754, both private, not verifiable), or as a cap changed three times inside one pull request (INC-760). In 4 rows it was found after merge: a gate that silently failed on every run (INC-757), a scheduled fixer that kept stopping at its cap (INC-758), an audit that read a hook's own comment (INC-752), and a bisect of a slow pipeline about two weeks after the change merged (INC-755, private, not verifiable). In review, it shows when the reviewer agent runs out of turns before it posts its review (INC-759). At the task stage, it shows when a repeated run of the same work gives a different result (INC-756, private, not verifiable). In no row did a value rest on more than one measured run before it first failed; where a row has a measured figure, it was taken after the limit or the cost had already caused a failure.

## Protections

Ordered from the cheapest rung to the strongest. The early rungs make the value and its basis visible; the later ones replace a guessed value with a measured one. No rung replaces another. A Source line that reads "one operator's practice" means the maintainer's practice, with no outside source behind it.

### Prompt and review: write each limit's basis beside it, and cost into the criterion

- **Source:** Anthropic's cost guide says to "establish a baseline before wider rollout" ([Claude Code costs](https://code.claude.com/docs/en/costs)); the .NET runtime team holds "no performance PR merges without empirical evidence, regardless of who contributes the PR" ([.NET Blog](https://devblogs.microsoft.com/dotnet/ten-months-with-cca-in-dotnet-runtime/)). A comment beside each limit naming the runs it came from, and a line on cost or speed in the acceptance criterion of a change that can move it, is one operator's practice.
- **Cost:** the time to write the basis, and tokens.
- **Breaks when:** the basis written is one run, which reads as a measurement: INC-751's fix calls its cap ~2x of a single 51-turn run, and INC-760's description calls a cap calibrated to one observed pattern. Or the text drifts from the value: INC-759's title says 10 and its diff sets 20, and INC-760's description says 3 and its diff sets 5.

### Record every run: turns, cost, duration and why it stopped

- **Source:** the Agent SDK returns an estimated `total_cost_usd` and per-model usage with each result ([Agent SDK cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)). GitHub's team logged token use per agentic workflow run and found, in workflows already in production, "a 64-turn fallback loop" and a tool "called 342 times in one run" ([GitHub Blog](https://github.blog/ai-and-ml/github-copilot/improving-token-efficiency-in-github-agentic-workflows/)).
- **Cost:** storage per run, and someone who reads it.
- **Breaks when:** the record is not written on the run that hit the limit: in one GitHub Action, when the agent reached its turn cap, the file with the turn count and the cost "is never created" ([claude-code-action#1226](https://github.com/anthropics/claude-code-action/issues/1226)); or the figures are estimates, since the SDK's cost fields "are client-side estimates, not authoritative billing data" ([Agent SDK cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)).

### A limit that fires is its own stop reason

- **Source:** the Agent SDK ends a run that hits a cap with its own result subtype, `error_max_turns` or `error_max_budget_usd`, apart from `success` ([Agent SDK agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)). One project's design record splits the reason a run stopped from its status, after "A budget stop and an iteration cap were indistinguishable" ([nr-llm ADR-092](https://docs.typo3.org/p/netresearch/nr-llm/0.30/en-us/_sources/Adr/Adr092AgentRunTerminationReason.rst.txt)). An agentic-workflow tool fails the workflow when the agent stops at its cap, where before "no error is raised" ([gh-aw#2235](https://github.com/github/gh-aw/pull/2235)).
- **Cost:** a field per run, and code that reads it.
- **Breaks when:** the check runs after the agent finished, so a run that succeeded past the cap is reported as a failure (INC-750, INC-751); the mechanism that should fire cannot reach the work, as a thread-based per-test timeout could not interrupt native code (INC-753, private, not verifiable); or the stop reasons are only as fine as their list, and a stop nobody named lands in a catch-all.

### A cost cap per run

- **Source:** the Agent SDK's `max_budget_usd` ([Agent SDK agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)); GitHub Copilot CLI's session limit, where "When the limit is hit, the agent stops cleanly and lets you know." ([GitHub Docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/set-session-limit)).
- **Cost:** the run that the cap stops, and its partial work.
- **Breaks when:** the cap is checked after a response arrives, so one response overshoots it: the SDK compares spend with the cap "after model responses arrive" ([Agent SDK agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)), and a test with a cap of $0.01 ended at about $0.084 after one turn (as of 2026-04, [LinuxJedi](https://linuxjedi.co.uk/when-the-docs-fall-short-investigating-claude-codes-budget-cap/)); Copilot's limits are "soft limits" ([GitHub Docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/set-session-limit)); or the value is itself a guess, and the expensive runs are the ones that succeed. In one benchmark run, 20 of the 22 instances that cost more than $10 each were resolved (as of 2026-06, [OpenHands/benchmarks#741](https://github.com/OpenHands/benchmarks/pull/741)), so a $10 cap would have cut them.

### A blocking threshold runs in warn mode first

- **Source:** Kubernetes Pod Security Admission has `enforce`, `audit` and `warn` modes, and in `warn` "Policy violations will trigger a user-facing warning, but are otherwise allowed." ([Kubernetes](https://kubernetes.io/docs/concepts/security/pod-security-admission/)). Running a new blocking hook in warn mode, counting what it would block and reading a sample of it before it denies anything, is one operator's practice.
- **Cost:** a period in which the hook does not protect, and the time to read what it would have blocked.
- **Breaks when:** nobody reads the warnings; or the sample is too small to place the cut-off. INC-752's fix moved the cut-off from 0.75 to 0.80 on one reading of 0.79 from the hook's own calibration note.

### Set the value from the measured distribution of runs that succeeded

- **Source:** on 100 SWE-bench Verified tasks, a turn cap at the 75th percentile of the uncapped runs' turns was a "sweet spot", "substantially reducing costs (by 24%-68%) with minimal impact on solve rates" across three models (as of 2025-11, [Gao and Peng](https://arxiv.org/html/2510.16786v2)). size-limit says "Add 25% to the current total size and use that as the limit" ([size-limit](https://github.com/ai/size-limit)); one CI change set each job's timeout from a table of observed durations: "Headroom is ~4× observed cold-cache durations" ([anthropics/buffa#19](https://github.com/anthropics/buffa/pull/19)). INC-750's second value, 1.5 times the largest of six measured runs, is one operator's practice.
- **Cost:** the runs to measure, with tokens and CI minutes for each; on the paper's three models a 75th-percentile cap changed the solve rate by −8.06% to +3.17% relative to no cap (as of 2025-11, [Gao and Peng](https://arxiv.org/html/2510.16786v2)).
- **Breaks when:** the sample is one run (INC-751, INC-760) or a few: INC-750's own pull request says its new cap "still undersells" a run that the first cap cut off at 43 turns, so its real need is unknown. Or the tail is heavy, and the expensive runs are the successful ones (the benchmark run in the rung above); or the task mix changes after the value is set.

### Count the budget in a unit the host does not change

- **Source:** one operator's practice: bound each stage by a count of evaluations or turns, and keep a wall-clock limit only as an emergency stop whose firing means "not finished", not a result. In INC-756 a stage bounded that way reproduced 8 of 8, while stages cut off by the clock did not (private, not verifiable).
- **Cost:** a counter in the code, and a wall-clock value still to set for the emergency stop.
- **Breaks when:** the cost of one unit varies, as a turn's tokens do, so a turn cap bounds the count and not the spend; or the emergency wall-clock limit is set as tight as the old one, and becomes the limit again.

### Measure cost and speed in CI against a baseline

- **Source:** github-action-benchmark compares each result with the previous one and alerts above a threshold that defaults to "200%" ([github-action-benchmark](https://github.com/benchmark-action/github-action-benchmark)); CodSpeed measures wall time and says "Walltime measures elapsed time, so it inherits the noise of the machine it runs on." ([CodSpeed](https://codspeed.io/docs/instruments/walltime)).
- **Cost:** CI minutes per run, and a benchmark per path that matters.
- **Breaks when:** the noise is as large as the change: on hosted runners "the amplitude of the benchmarks is about +- 10~20%" ([github-action-benchmark](https://github.com/benchmark-action/github-action-benchmark)); the benchmark does not run the path the change slowed, as no check covered the pipeline pass of INC-755 (private, not verifiable); or the answer to a red benchmark is a bigger timeout instead of a cheaper change, which INC-754's issue ruled out in its own acceptance criterion (private, not verifiable).

## Evidence

- No study found measures this class directly: how often a limit set on an agent's run cuts off work that would have succeeded, or how often a merged agent change raises the cost of running it unnoticed (as of 2026-11, external search for this doc).
- In the SWE-agent paper, 93.0% of resolved instances were submitted before their cost budget ran out, against 69.0% of all instances (as of 2024-11, [Yang et al.](https://arxiv.org/html/2405.15793v3)); the authors read it as a sign that a larger budget would add little. A cap that rarely cuts off success can still cut off some.
- In SWE-smith, 53% of one model's failures (SWE-agent-LM-32b) are associated with run-time limits (cost, number of model calls, run time), while this "rarely happens with Claude 3.7 Sonnet" (as of 2025-05, [Yang et al.](https://arxiv.org/html/2504.21798)). The same limits cut one model's runs far more than another's.
- Runs of the same agent on the same task "can differ by up to 30x in total tokens", and models predicting their own token use reach correlations of "up to 0.39" (as of 2026-04, [Bai et al.](https://arxiv.org/abs/2604.22750)). A value taken from one run carries that spread.
- A 75th-percentile turn cap cut cost by 24% to 68% across three models with a small change in solve rate, on 100 tasks (as of 2025-11, [Gao and Peng](https://arxiv.org/html/2510.16786v2)); the paper says repeating each experiment several times would be more robust than what it ran.
- Agent-authored performance pull requests carry explicit performance validation in 45.7% of cases, against 63.6% for human ones (as of 2025-12, [Peng et al.](https://arxiv.org/abs/2512.21757)).
- Most of the record is the maintainer's own: 7 of the class's 11 rows come from the maintainer's repositories, 4 of them private. In the maintainer's audit, fixes that moved a threshold were followed by no later incident found in 3 of 3 cases, over short windows, while fixes that changed a check were followed in 2 of 2 by the same defect in another place (as of 2026-10, one operator's audit, private, not verifiable).
- Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv); four of the class's rows are private sources and say so in the link column.
