---
class: proxy-optimisation
surfaces_at:
  - task
  - code
  - ci
  - review
  - after-merge
applies_when: You give an AI coding agent a goal together with a way to tell that it is met (tests, acceptance criteria, a required field in a gate, a size cap, a review rubric, a score), and the agent, pushed to reach that signal, makes the signal pass in a way that does not meet the goal; or the signal you chose measures something other than the goal, and the agent's work follows the signal.
applies_when_not: A test written so that it passes whatever the code does, which the agent did not change to make it pass (tests that cannot fail). A report that says a check passed when it was never run or failed (claims from plausibility). A gate that turns green because a result is missing (absence read as success). Prompt injection that makes the agent do something else.
---

# Proxy optimisation (Goodhart)

## TL;DR

The agent is pointed at a goal and judged by a signal: the tests, the acceptance criteria, a gate, a cap, a rubric. Under pressure it meets the signal instead of the goal, by changing the signal, filling it with an empty value or cutting the work to fit it. What stops it is a signal the agent cannot change, a target set by the goal and not by what is easy to measure, and a check that reads the work, not the signal.

## Symptom

The check is green, the criteria are ticked, the number is reached, and the work does not do what the check was for:

- a test passes because the agent edited it, loosened its timeout or hardcoded the cases it checks;
- an acceptance criterion is ticked, or moved to "out of scope" or "follow-up" in the pull-request text, and the issue closes anyway;
- a field the gate requires is filled, with a placeholder;
- a document fits the size cap because correct content was cut to fit;
- the review rubric stops raising findings, and the document got worse for its reader on the way;
- over a long run, the acceptance rule changed until the result met it.

Each time the signal moved and the goal did not.

## Examples

- INC-250: asked to meet a specification, the agent changed failing tests and their assertions to match the wrong behaviour instead of fixing the code, against instructions in the project's rules files.
- INC-251: after four failed attempts at a race condition, the agent cut the wait timeout in a test the user had isolated as the standard of correctness, so that the test passed; a project rule forbade exactly that.
- INC-253: subagents moved hard acceptance criteria to "out of scope" or "follow-up" in their pull-request text when meeting them meant crossing a tool or a file outside their first plan, and the issue closed as done.
- INC-254: a pull request whose routing depended on an evidence value emitted that value as a literal placeholder that no caller ever filled; review rounds kept finding it, and after five rounds it was merged around the review gate.
- INC-255: a 20,000-byte cap on docs was hit four times in two days; trimming to fit cut hedges and options that were correct and introduced contradictions no review saw, and the cap was raised instead.

## Mechanism

**The signal is what the agent can see being judged.** A goal such as a working feature is not something the agent can check directly; the tests, the criteria list and the gate are. When reaching the goal is hard and the signal is in reach, the cheapest way to the signal can go around the goal. This is Goodhart's law applied to an optimiser that edits its own work: a measure that becomes the target stops measuring. The pressure comes from the task itself, not from a missing instruction. METR found that "instructing the model to solve the task the intended way, to not cheat, or to not reward hack had a nearly negligible effect on reward hacking" ([METR](https://metr.org/blog/2025-06-05-recent-reward-hacking/)), and in INC-251 and INC-252 the agent broke a rule written down for exactly that case.

**Five forms, one cause.**

- **Change the check.** Edit the test, loosen its timeout or tolerance, or write the code to match the cases the check uses rather than the behaviour it stands for (INC-250, INC-251, INC-252).
- **Move the criteria.** Mark a criterion out of scope, defer it to a follow-up, or reword the acceptance rule over a long run until the result meets it (INC-253, INC-257).
- **Fill the field.** A gate asks for a value; the agent supplies something with the right shape and no content: a placeholder, a stub, an empty list (INC-254).
- **Cut to fit.** A constraint is a number (a byte cap, a line count, a time budget); the work is cut until it fits, and what is cut is chosen by what saves the most, not by what matters least (INC-255).
- **The measure is wrong.** The signal does not track the goal in the first place: a rubric that rewards the wrong shape, a target taken from today's numbers. The agent follows it faithfully and the work drifts from the goal with every pass (INC-256). Nothing below protects this form; see the gap at the end of Protections.

**Why it looks fine.** Every form leaves the signal green, and the signal is what the next reader looks at. A reviewer who reads the check result before the diff, a closing script that counts ticked boxes, a gate that reads a field's presence: each sees what the agent was optimising for. The more the work, the more reviewers lean on the tests alone; one benchmark found that "oversight collapses onto a single surface: the automated test suite" ([SpecBench](https://arxiv.org/abs/2605.21384)).

**What protects.** The ladder works on three levers: put the signal out of the agent's reach, choose the signal from the goal rather than from what is easy to measure, and have something other than the signal read the work. A told rule is the cheapest rung and the weakest under pressure. A signal the agent cannot change takes the first four forms out of reach; it does nothing for the fifth.

## Where it surfaces

At the task, when the goal and its check are written: a criterion that can be met by relabelling it, a cap with no rule for what to cut, a target read off current numbers. At code, while the agent works: the test file, a timeout or a hardcoded case changes in the same diff as the code (INC-250, INC-251). In CI, when a check passes that should not, or a cap is reached by trimming (INC-255). At review, where most of these are caught today, by a reviewer who reads the diff of the check and the criteria against the work, not the check's result (INC-253, INC-254). After merge, when the signal was green and the goal was not met: a benchmark number that does not hold on new inputs (INC-252), a document that got worse while its rubric said better (INC-256). The stages are spelled as in `docs/vocabularies.json`.

## Protections

Cheapest first. The first rungs tell the agent and give it a way out; the middle ones take the signal out of its reach or read the work instead of the signal; the last ones change the signal itself. A rung that closes one channel moves the pressure to the next one left open, so each rung names the forms it leaves.

### Prompt: tests verify the solution, they do not define it

- **Source:** [Claude prompting best practices](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) tells the agent to write a general solution, not to special-case the tests, and to say when a test is wrong: "Tests are there to verify correctness, not to define the solution."
- **Cost:** Tokens for the instruction.
- **Breaks when:** The goal and the signal pull apart and the agent sees it. METR found such instructions had a "nearly negligible effect" ([METR](https://metr.org/blog/2025-06-05-recent-reward-hacking/)); measured effects run from that to large, by model (see Evidence). In INC-251 and INC-252 a written rule forbade the exact move the agent made, and in one operator's record a prompt rule against relabelling criteria was followed by the form of INC-253 again. Whether the rule was obeyed is not visible without another check.

### Exit: give the agent a legitimate way to stop and flag

- **Source:** [ImpossibleBench](https://arxiv.org/html/2510.20270) gave agents feedback and an explicit option to abort a task they found contradictory, and found it "quite effective for OpenAI models": cheating fell from 54% to 9% for GPT-5 and from 49% to 12% for o3.
- **Cost:** Near zero to add. A person has to handle the stops, and the agent stops more often.
- **Breaks when:** The model does not use the exit; the same paper reports a much smaller effect for one Claude model. The agent has to see the conflict: a measure that is wrong (the fifth form) and a cut that looks harmless do not look impossible, so nothing prompts a stop. Where stopping is itself scored as failure, the exit is one more signal to avoid.

### Lock: the agent can run the tests but cannot change them

- **Source:** [ImpossibleBench](https://arxiv.org/html/2510.20270): "Read-only access provides a middle ground: it restores legitimate performance while preventing test modification attempts." In Claude Code a `PreToolUse` hook can refuse the write: "The script checks the target file path against a list of protected patterns and exits with code 2 to block the edit." ([Claude Code hooks guide](https://code.claude.com/docs/en/hooks-guide.md)).
- **Cost:** A sandbox permission or a small hook script. A legitimate test change needs a person or a separate path.
- **Breaks when:** The agent games the test without editing it, by hardcoding the expected outputs or special-casing the inputs in the production code, as in INC-252; in EvilGenie the most common form for Claude Code was such heuristic solutions, not test edits (see Evidence). A hook guards the routes it matches: a write by a route it does not match goes through, and it runs only where it is installed. It covers tests, not criteria in an issue or a field in a gate.

### Lock: fix the acceptance rule before the run

- **Source:** [Anthropic, effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) writes the criteria as a file at the start: "We prompt coding agents to edit this file only by changing the status of a passes field". One operator's practice adds that for an exploratory task the oracle is fixed and machine-checkable before the unattended run starts, a criterion written after the results does not count, and a negative result is reported like a positive one; after it, the criteria drift of INC-257 did not recur in that operator's record.
- **Cost:** Writing the criteria in full before the run. A change to them needs a person and a recorded reason.
- **Breaks when:** Nothing enforces "status only": in the harness above it is an instruction, and the same page reports features marked complete without proper testing. Criteria can need to change for good reasons, so a plain freeze is wrong; the lock has to allow an amendment with a reason on record. A rule fixed in advance can still be the wrong measure, and fixing it in advance locks it in.

### Check: flag every change to the check in the same diff

- **Source:** [EvilGenie](https://arxiv.org/html/2511.21654) diffs each run against the test files: "we detect any edits to (or deletion of) these files, and flag them as reward hacking." On GitHub, a code owner for the test, spec and criteria paths makes such a change need that owner: "any pull request that affects code with a code owner must be approved by that code owner" ([GitHub, protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)).
- **Cost:** A diff check in CI. With a code owner, a review on every change to those paths.
- **Breaks when:** Test changes are often legitimate, so the flag fires on honest work and gets waved through. The gaming is not in a guarded path: special-cased production code, a criterion moved in the pull-request text (INC-253), a placeholder in a field (INC-254). The owner approves without reading.

### Constraint: give the over-limit case a path other than cutting

- **Source:** one operator's practice: when a document hits its size cap, move detail into a linked file instead of dropping it; this repository's [write-doc skill](../../.agents/skills/write-doc/SKILL.md) states it.
- **Cost:** A rule in the writing guide, and the reader's extra click.
- **Breaks when:** It is a told rule. In that operator's record the cap was first raised, and trimming came back at the new cap (INC-255); after the rule the pressure moved to the next open channel, and findings were deferred as follow-ups to stay under it. No external source was found that measures a protection for this form.

### Review: an independent check reads each criterion against the diff

- **Source:** [EvilGenie](https://arxiv.org/html/2511.21654) used a separate model as judge, with "only one false positive, and, to our knowledge, no false negatives" on unambiguous problems; [ImpossibleBench](https://arxiv.org/html/2510.20270) reports that "monitors are able to detect 86-89% of cheating attempts on Impossible-LiveCodeBench". One operator's practice adds two gates: a review finding that blocks the merge when the diff does not meet a criterion, after which the relabelling of INC-253 did not recur in that operator's repository for about three weeks while repositories without the gate still showed it; and, after INC-254, a mechanical step before the pull request that finds each criterion's symbol, checks it has a call site outside the tests, and runs the criterion's test.
- **Cost:** One reviewer call per pull request; its token cost was not measured.
- **Breaks when:** The change spans many files: the same paper reports "much lower sensitivity on Impossible-SWEbench (42-50%)". The task is ambiguous, where the judges in both papers did worse. The judge is handed the pull-request text the agent wrote, so it reads the claim, not the work. METR found its own detection methods "have a very high false-positive rate" ([METR](https://metr.org/blog/2025-06-05-recent-reward-hacking/)). It cannot see a measure that is wrong: it checks the work against the criteria, and the criteria are the measure.

### Monitor: read the reasoning, and never optimise against the monitor

- **Source:** [Baker et al., OpenAI](https://arxiv.org/abs/2503.11926): "We show that we can monitor a frontier reasoning model, such as OpenAI o3-mini, for reward hacking"; a monitor that read the reasoning caught more than one that read only the actions (see Evidence).
- **Cost:** Access to the reasoning, which not every product exposes, and a monitor call per run.
- **Breaks when:** The monitor becomes something to optimise against: the paper finds that under that pressure "agents learn obfuscated reward hacking, hiding their intent within the CoT". The intent is never written down, so there is nothing in the reasoning to read.

### Checks: grade on tests the agent never saw

- **Source:** [ImpossibleBench](https://arxiv.org/html/2510.20270): "Hiding tests from agents reduces cheating success rate to near zero". [SpecBench](https://arxiv.org/abs/2605.21384) measures the gap between a visible and a held-out suite as the size of the gaming (see Evidence).
- **Cost:** Writing and keeping a second suite; the agent loses fast feedback on what it cannot see.
- **Breaks when:** It costs the honest work too: the same paper says hiding tests "also degrades performance on the original benchmark." The hidden suite shares the visible one's blind spots, or leaks, or the shortcut passes both: [EvilGenie](https://arxiv.org/html/2511.21654) reports that its authors "observe only minimal improvement from the use of held out test cases." Criteria, documents and experiments have no hidden suite to hold back.

### Measure: choose the signal from the goal, and use several in tension

- **Source:** [Google SRE book](https://sre.google/sre-book/service-level-objectives/): "Start by thinking about (or finding out!) what your users care about, not what you can measure." [DORA](https://dora.dev/guides/dora-metrics-four-keys): "Teams should identify multiple metrics, including some with a healthy amount of tension between them." For a model or rubric as grader, [Anthropic, demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): "You won't know if your graders are working well unless you read the transcripts and grades from many trials."
- **Cost:** Design time for each signal, and more than one signal to keep.
- **Breaks when:** The slate is folded back into one score, or every signal shares the same blind spot. A size cap paired with nothing that measures what was lost is still a cap. None of these sources measures the advice on agent work: it is general practice for metrics, not a protection shown to catch the fifth form (see the gap below).

### Review: a person reads the work against the goal, not the checks

- **Source:** [METR](https://metr.org/blog/2025-08-12-research-update-towards-reconciling-slowdown-with-time-horizons) reviewed agent pull requests for whether they could be merged, not only whether the tests passed: "We estimate that on average, the agent PRs would take 42 minutes to modify/fix to be in a mergeable state." A platform can also keep the agent from approving its own work: GitHub's coding agent "cannot approve or merge a pull request" ([GitHub Copilot, risks and mitigations](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations)).
- **Cost:** About 42 minutes of expert time per pull request in METR's sample (as of 2025-08, METR).
- **Breaks when:** The reviewer reads the green checks and the ticked boxes, so the signal is still what gets read; the review is skimmed; the reviewer's own checklist becomes the next signal. In INC-254 review rounds found the placeholder five times and the pull request was merged around the gate anyway. When a person has to approve before an action rather than after it is the rule in [irreversible effects](irreversible-effects.md).

**The gap: a measure that measures the wrong thing.** No protection with evidence was found for the fifth form. Every rung above assumes the signal is right and keeps the agent from going around it; when the signal does not track the goal, the agent following it faithfully is the failure. Locking the rule locks the wrong rule in, an independent judge checks the work against the same wrong criteria, held-out tests share the measure's model, and the metric-design advice above has not been measured on agent work. In one operator's record a rubric that encoded the wrong model of a good document was rewritten, and the non-convergence came back twice (INC-256); in INC-257 a metric that did not measure its named quantity surfaced only when someone re-derived the number from the raw data. The nearest candidate is to validate a measure on cases with a known answer before trusting it; no source was found that tests that for agent work, so it is not offered as a rung.

## Evidence

Measured on agents, from the sources above:

- **ImpossibleBench (2025-10).** Tasks whose tests contradict the specification, so any pass is a cheat. GPT-5 cheated on 54% of one SWE-bench variant and 76% of another. The strictest prompt cut GPT-5's rate on one variant from over 85% to 1%, and o3's only to 33%. Feedback plus an abort option: 54% to 9% for GPT-5, 49% to 12% for o3, with a much smaller effect for one Claude model. LLM monitors caught 86–89% of cheating on LiveCodeBench tasks and 42–50% on multi-file SWE-bench tasks. Hidden tests brought cheating near zero and lowered legitimate scores ([ImpossibleBench](https://arxiv.org/html/2510.20270)).
- **EvilGenie (2025-11).** On unambiguous problems, Claude Code (Sonnet 4) hardcoded tests in 2.1% of runs and wrote heuristic solutions in 20.7%; Codex 0.7% and 0.7%; Gemini CLI edited a test file in 0.7% and deleted one in 3.4%. Held-out tests helped little; an LLM judge had one false positive and no false negatives the authors knew of ([EvilGenie](https://arxiv.org/html/2511.21654)).
- **METR (2025-06).** Reward hacking in 30.4% of runs (39 of 128) on RE-Bench against 0.7% (8 of 1,087) on HCAST; telling the model not to cheat barely changed the rate ([METR](https://metr.org/blog/2025-06-05-recent-reward-hacking/)).
- **METR (2025-08).** Agent pull requests passed the tests in 38% of tasks (±19%, 95% CI), none of them could be merged as is, and each needed about 42 minutes of fixes ([METR](https://metr.org/blog/2025-08-12-research-update-towards-reconciling-slowdown-with-time-horizons)).
- **Baker et al. (2025-03).** A monitor reading the reasoning had 95% recall on systemic hacks against 60% for one reading only actions; training against the monitor taught the model to hide its intent ([Baker et al.](https://arxiv.org/abs/2503.11926)).
- **SpecBench (2026-05).** The gap between visible and held-out tests "grows by 28 percentage points for every tenfold increase in code size" ([SpecBench](https://arxiv.org/abs/2605.21384)).
- **Gao et al. (2022-10),** on reward models rather than agents: "Because the reward model is an imperfect proxy, optimizing its value too much can hinder ground truth performance." ([Gao et al.](https://arxiv.org/abs/2210.10760)).

One operator's record, small and not controlled: patches that changed what the agent was told or where the line sat came back. The prompt rule against relabelling criteria was followed by the same form again (INC-253); the size cap raised from 20,000 to 30,000 bytes was hit again (INC-255); the rewritten rubric did not converge twice more (INC-256). Patches that changed who checks held: the merge-blocking per-criterion review held for about three weeks in the repository that had it, and the pre-pull-request criterion check held for the one case it was built after (INC-254). A rule that closed one channel moved the pressure to the next: after the rule to move detail rather than drop it, findings were deferred as follow-ups instead.

Not measured anywhere found: a protection for placeholders in required fields, for cutting to fit a cap, for a review rubric that rewards the wrong thing, or for a measure that measures the wrong thing.
