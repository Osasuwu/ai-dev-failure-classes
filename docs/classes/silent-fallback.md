---
class: silent-fallback
surfaces_at:
  - code
  - review
  - after-merge
applies_when: You run code or operations that an AI coding agent wrote or changed (application code, scripts, scheduled jobs, services, hooks, deploy steps), and you want to know why they can keep running and look healthy while doing the wrong thing or nothing, because an error was caught and dropped, a default stood in where a failure should have been raised, or a process stopped and nothing alerted, and what makes such a failure visible.
applies_when_not: A CI check, review bot or merge gate that never looked at the change and counted as passed (absence read as success). A test that runs but cannot fail. An agent's claim of done that no one checked against the effect. A guard that matches the wrong spelling of a command or path (pattern-matched boundaries). Destroying data by accident.
---

# Silent fallback

## TL;DR

Code that knows something failed returns a value that looks valid (an empty list, `None`, a local count, a default), and a stopped process sends nothing, so the system looks healthy while it does the wrong thing or nothing. Agents add such fallbacks readily, often while fixing a crash. Start with a lint rule for swallowed errors and a test that injects the failure and checks the caller sees it; then make failures reach a place a person reads, and add checks that run outside the code: a heartbeat per scheduled job, an alert on missing data, a probe that checks the output's content.

## Symptom

Nothing looks wrong. The logs show no error, the job ends with success, the service answers its health check, and the agent reports the change works. Later someone finds the output was wrong or missing the whole time. A function caught an exception and returned an empty list, `None` or a cached value, so the caller carried on with nothing. A missing config value or environment variable was replaced by a default, and the code ran against the wrong place or with a feature turned off. A call to an external API failed, and the code fell back to a stale or placeholder result without saying so. A retry loop gave up and logged the failure at debug level. A scheduled job or background worker stopped running, and because it only ever reported when it ran, its silence raised no alert. Often the agent added the fallback itself: asked to fix a crash, it wrapped the failing call in a broad catch, and the crash went away along with the signal.

## Examples

- INC-201: a memory search caught any error on its semantic lookup and returned an empty list, fell through to a keyword search, and reported "Found N memories"; the telemetry meant to notice the degraded path fired only on success, so it never learned of the failure.
- INC-205: a shared like counter never wrote to its spreadsheet, because the user id it keyed rows by was set only as a side effect of creating a playlist; without it the code counted locally, and the count in the app kept going up.
- INC-203: a background orchestrator died on a dropped database connection and stayed dead for about 13 hours; the scheduler's restart setting did not bring it back, and nothing outside the process watched it.
- INC-211: a factory that built safety checks caught every exception and returned nothing, and the caller read nothing as no checks to run (private, not verifiable).
- INC-214: a user reports that Claude Code adds fallbacks and swallows errors often, although the project's instruction file forbids it, and that once it tried to handle a failed encryption by sending the data unencrypted.

## Mechanism

**The failure signal is turned into a valid value.** At the failing line the code knows something went wrong; a handler converts that into a value of the normal type, with no bit that says it is a stand-in. An empty list reads as no results (INC-201); a local count reads as a counted like (INC-205), `None` from a factory reads as nothing to check (INC-211, private), a returned "no collision" from an uncalibrated check reads as clear (INC-212, private). INC-202 is the same hole, found by an audit before it fired: had the embedding model been switched to one with larger vectors, the vector search would have failed on the size mismatch, and its handler would have returned an empty list for every query. Each layer can be reasonable on its own; stacked, they launder an infrastructure failure into a success the caller reports.

**A missing input is treated as a feature switched off.** A missing id or an uncalibrated sensor is handled as a feature that is off rather than as a fault (INC-205; INC-212, private). Nothing in the code marks the empty case as a fault; it runs down the same path as the off case, and the fallback it lands on looks like normal output.

**A status is dropped or replaced by a default.** A step's result is not read, so the run reports success over failed parts (INC-210, private). A default or a simpler method stands in for one that failed: a flat target instead of an error from a loader (INC-213, private), a simpler solver whenever the full one returns nothing (INC-209, private). Rust marks `Result` as must-use because "ignoring an error value can hide a failed operation" ([Rust `must_use`](https://doc.rust-lang.org/std/attribute.must_use.html)).

**The error is written where nobody looks.** A failure is logged, but to a debug channel a user on a release build never sees, while the app's own log screen gets nothing (INC-207); or a quiet flag dropped the stderr that carried the reason, so the run's diagnostic tail was empty, and the alert classifier had no pattern for the billing error, so no alert fired (INC-200). Logged and silent are the same thing to the person who would act.

**A stopped process says nothing.** A job or worker that reports only when it runs goes quiet when it dies, and quiet raises no alarm (INC-203, INC-208). A check in the same process stops with it. A scheduled job can fail on every run and still be unwatched if nothing aggregates its outcome: one ran 12 weeks failing on a statement timeout before a manual audit found it (INC-204).

**Agents add the fallback.** A study of automated issue solving names "evasive repair": the tool treats a symptom with defensive code such as a broad try-except or a null check, and "This prevents crashes but masks root causes." ([Liu et al.](https://arxiv.org/html/2509.13941)). A practitioner rule set for LLM-written Python says "Many models overuse broad try and except blocks, and one of the most problematic variants is catching every exception and ignoring it entirely." ([Dagster](https://dagster.io/blog/dignified-python-10-rules-to-improve-your-llm-agents)). Anthropic's prompting guide notes that some Claude models overengineer and suggests a sample prompt: "Don't add error handling, fallbacks, or validation for scenarios that can't happen." ([Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)). Two public reports show the rule in an instruction file not holding: the agent added fallbacks the file forbade (INC-214), and after a plan built under a fail-fast, no-fallback policy it reported an automatic fallback chain as a feature (INC-215).

**Fixes move the failure.** Making one site loud often leaves its sibling quiet, and making it fail closed can block legitimate work. In the maintainer's record (the incidents from the maintainer's own repositories, and one operator's audit of 12 of them; see Evidence), fixes that made a site report its failure moved the failure elsewhere in all three cases, and per-site fail-closed fixes with a pinning test held at their site but left a sibling site open in all six cases (as of 2026-10, one operator's audit, private, not verifiable). One soft-fail was right by design for a transient failure and wrong for a permanent one: a like must not fail because a spreadsheet was slow, but the same catch also swallowed an error that meant the counter could never work (INC-206).

## Where it surfaces

More than half the rows were found after merge: in 9 of this class's 16 dataset rows the failure, or the hole that would hide it, was found in code that had already shipped. For example, a user noticed the effect was missing (INC-205, INC-208), an audit of the code or of run transcripts found it (INC-201, INC-204, and INC-202 before it fired), or an outage was noticed after the fact (INC-200, INC-203). Where these rows record how long it went unseen, it runs from about 13 hours (INC-203) through at least five days (INC-200) to 12 weeks (INC-204). In code, it is found by reading a handler and asking what the caller sees on failure, the way the five private rows were found, and the way INC-215's user saw "falls back gracefully" in the agent's own summary. In review, it shows as a catch, a default or a `return null` in the diff, if the reviewer reads the error path at all; INC-214's user was stuck in review removing fallbacks the agent kept adding. No CI row exists: a test suite that exercises only the happy path passes with the fallback in place.

## Protections

Ordered from the cheapest rung to the strongest. The rungs that act on the code catch a fallback before it ships; the checks that run outside it catch the ones that shipped anyway, and are the ones that can see a process that stopped. No rung replaces another.

### Prompt: tell the agent to fail loudly and add no fallback

- **Source:** the Python norm "Errors should never pass silently." ([PEP 20](https://peps.python.org/pep-0020/)); projects write it into their agent instruction files, for example "Fail loudly, and never fall back to a silently wrong result." ([lanl/PyBNF#835](https://github.com/lanl/PyBNF/pull/835)); Anthropic's guide suggests a sample prompt telling Claude not to add fallbacks for cases that cannot happen ([Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)).
- **Cost:** tokens.
- **Breaks when:** the agent is fixing a crash, where a catch is the shortest path to green; and the rule did not hold in either public report (INC-214, INC-215), where it was in the project's instruction file. An audit of one project whose instruction file bans silent fallbacks counted 40 such sites in its code ([amd/gaia#2316](https://github.com/amd/gaia/issues/2316)); it does not say who wrote them. PEP 20's next line, "Unless explicitly silenced.", can be read as licensing the `return []` handler. In the maintainer's record, fixes written as prose recurred (as of 2026-10, one operator's audit, private, not verifiable).

### Lint: flag swallowed errors in the changed lines

- **Source:** ruff S110 flags `try`-`except`-`pass`, because "Suppressing exceptions may hide errors that could otherwise reveal unexpected behavior," ([ruff S110](https://docs.astral.sh/ruff/rules/try-except-pass/)), and BLE001 flags `except Exception` ([ruff BLE001](https://docs.astral.sh/ruff/rules/blind-except/)). Go: "errcheck finds silently ignored errors in Go code." ([errcheck](https://github.com/kisielk/errcheck)), with `-blank` for errors assigned to `_`. JavaScript: ESLint [no-empty](https://eslint.org/docs/latest/rules/no-empty) and typescript-eslint [no-floating-promises](https://typescript-eslint.io/rules/no-floating-promises/). Running the rules on the changed lines only, so old code does not drown them, is one operator's practice.
- **Cost:** CI seconds; noise on legacy code unless scoped to the diff.
- **Breaks when:** the handler logs and returns a default: BLE001 exempts a handler that logs the exception, so adding `exc_info` silences the rule while the code stays fail-open. A narrow catch, a `# noqa` the agent adds, an empty catch with a comment in it, or a fallback that is no catch at all (a default, an absent value read as off) passes. In the maintainer's record, BLE001 on one file before its fix flagged the real site as 1 of 9 hits (as of 2026-10, one operator's audit, private, not verifiable).

### Review: a pass that reads only the error paths

- **Source:** Anthropic ships a review agent for "silent failures, inadequate error handling, and inappropriate fallback behavior" ([silent-failure-hunter](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/pr-review-toolkit/agents/silent-failure-hunter.md)); a vendor report on AI-co-authored pull requests lists "Standardize exception-handling rules" among its safety rails and "Are error paths covered?" in its review checklist ([CodeRabbit](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)).
- **Cost:** tokens per pull request, and the time to triage its findings.
- **Breaks when:** the fallback is in code the diff does not touch, which a pass over the pull request does not read; or it is in a sibling of the fixed site, as it was after all six per-site fail-closed fixes in the maintainer's record (as of 2026-10, one operator's audit, private, not verifiable); or the reviewer accepts a documented fallback as intended. No catch rate for such a pass is published.

### Startup: refuse to start without required configuration

- **Source:** envalid "will log an error message and exit (in Node) or throw (in browser) if any required env vars are missing or invalid" ([envalid](https://github.com/af/envalid)); [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) raises a validation error for a required field with no value.
- **Cost:** a schema per service.
- **Breaks when:** the schema gives the field a default, an edit an agent can make to fix a startup crash; the value is present but wrong (a model name that would no longer match its index, INC-202); or the code reads configuration outside the schema.

### Heartbeat: an external dead man's switch per scheduled job

- **Source:** "It raises an alert as soon as a ping does not arrive on time." ([Healthchecks.io](https://healthchecks.io/docs/)); [Sentry Crons](https://docs.sentry.io/product/crons/job-monitoring/) does the same. [Absence read as success](absence-read-as-success.md) uses the same rung for checks that run on a schedule.
- **Cost:** free for 20 monitored jobs (as of 2026-10, [Healthchecks.io pricing](https://healthchecks.io/pricing/)); setup time per job.
- **Breaks when:** a job is never registered: INC-204 failed for 12 weeks with nothing watching its outcome, and in the maintainer's record an alarm held for the job it watched while a sibling job went unwatched (as of 2026-10, one operator's audit, private, not verifiable); the ping is sent whether or not the job succeeded; or the job is alive and its output is wrong. A watchdog inside the process is no substitute; in INC-203 the only checks ran inside the process, and the external restart setting itself failed.

### Missing data: alert when a series stops arriving

- **Source:** Prometheus `absent()` is for alerting when no time series exists ([Prometheus functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)); in Grafana, "The No Data state occurs when the alert rule query runs successfully but returns no data points at all." ([Grafana](https://grafana.com/docs/grafana/latest/alerting/fundamentals/alert-rule-evaluation/nodata-and-error-states/)).
- **Cost:** one rule per series that should keep arriving.
- **Breaks when:** the job keeps emitting its success metric while its output is empty, or the no-data state is set to normal to quiet noise. It catches a stop, not a wrong result.

### Watch the watcher

- **Source:** an always-firing Watchdog alert that an external receiver expects, so a dead alerting pipeline is itself noticed ([Prometheus Operator runbook](https://runbooks.prometheus-operator.dev/runbooks/general/watchdog/)). A monitor that runs as a scheduled workflow can be switched off by the platform itself; [absence read as success](absence-read-as-success.md) has the GitHub case.
- **Cost:** one alert rule and an external receiver.
- **Breaks when:** the receiver shares a failure with the thing it watches, or nobody is paged when the watchdog goes quiet.

### Errors: send them where a person reads them, and count them

- **Source:** one operator's practice: every error and every fallback taken goes to the channel a person already reads (the app's own log screen, a chat alert), and a count of fallbacks per day is watched. INC-207 logged to a debug channel a user never sees; INC-200 lost its error's text to a quiet flag, and its alert classifier had no pattern for that error.
- **Cost:** a sink per app and the attention to read it.
- **Breaks when:** the channel carries so much that a real error is lost in it: when pages come too often, people "second-guess, skim, or even ignore incoming alerts" ([Google SRE, ch. 6](https://sre.google/sre-book/monitoring-distributed-systems/)); or a new code path logs to the old place.

### Tests: inject the failure and assert the caller sees it

- **Source:** most catastrophic failures in five distributed systems came from wrong handling of errors the software had signalled, and simple tests of the error-handling code would have found many of them ([Yuan et al., OSDI 2014](https://www.usenix.org/conference/osdi14/technical-sessions/presentation/yuan)). Agent pull requests leave error-handling code the least covered ([Dipongkor et al.](https://arxiv.org/abs/2607.18057)).
- **Cost:** hours per failure path, and a fake or fault injector for each dependency.
- **Breaks when:** the test asserts the fallback value as the expected result, so it pins the silence; or it covers the fixed site and not its siblings. In the maintainer's record, per-site fixes pinned by a test held at their site in all six cases and left a sibling open in each (as of 2026-10, one operator's audit, private, not verifiable).

### Design: avoid the fallback, or run it constantly and alarm on its rate

- **Source:** "To begin with, fallback logic is hard to test." and "If fallback is essential in a system, we exercise it as often as possible in production"; for retries, "we maintain metrics that monitor overall retry rates and alarms that alert our teams if retries are happening frequently." ([AWS, avoiding fallback](https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/)). Where degrading is the right call, returning a typed "unavailable" result instead of a normal-looking value is one operator's practice.
- **Cost:** engineering time; metrics and an alarm per fallback.
- **Breaks when:** a fallback emits no metric, so how often it fires is unknown; or the caller converts the typed result back into a default.

### Content: probe the output from outside and check it is right

- **Source:** "black-box monitoring is symptom-oriented and represents active—not predicted—problems", and the same chapter names "an HTTP 200 success response, but coupled with the wrong content" ([Google SRE, ch. 6](https://sre.google/sre-book/monitoring-distributed-systems/)); "Anomaly detection can find divergence in the fleet that a server cannot detect about itself." ([AWS, health checks](https://aws.amazon.com/builders-library/implementing-health-checks/)).
- **Cost:** a probe per output that knows the right answer; hours to days to build each.
- **Breaks when:** the probe checks a status code or a shape, not the content; or it reads the output through the same fallback (a probe that searches memory through the keyword fallback of INC-201 sees results).

### Choke point: fail closed before an irreversible output

- **Source:** fail fast: software that stops at once and visibly on an error, instead of working around the error ([Shore, fail fast](https://www.jamesshore.com/v2/blog/2004/fail-fast)). Placing one fail-closed check in front of each output that cannot be undone (a write, a send, a move), so a missing input stops the action instead of defaulting it, is one operator's practice. The approval side of such outputs is in [irreversible effects](irreversible-effects.md).
- **Cost:** design time per output; false blocks when a legitimate empty case meets the check.
- **Breaks when:** a sibling path reaches the output without passing the choke point, or the false blocks lead someone to add a bypass. In the maintainer's record one such check blocked legitimate work (as of 2026-10, one operator's audit, private, not verifiable).

### Independent channel: a checker that cannot fail the way the producer does

- **Source:** in gray failure, "the system's failure detectors may not notice problems even when applications are afflicted by them"; the paper's answer is differential observability, "bridging the gap between different components' perceptions of what constitutes failure" ([Huang et al., HotOS 2017](https://www.microsoft.com/en-us/research/publication/gray-failure-achilles-heel-cloud-scale-systems/)). For a physical safety limit, enforcing it below the software that could fall back is one operator's practice.
- **Cost:** a second implementation, a separate service or hardware.
- **Breaks when:** the checker shares a dependency, a configuration or an input with the producer, or it also accepts the fallback output as valid.

## Evidence

- An analysis of 198 user-reported failures in five distributed systems found that most catastrophic failures came from incorrect handling of non-fatal errors the software had explicitly signalled, many of them catchable by simple tests of the error-handling code (as of 2014-10, [Yuan et al.](https://www.usenix.org/conference/osdi14/technical-sessions/presentation/yuan)). The code was not agent-written.
- In 27 Java libraries, catch blocks and throw instructions "are less covered, with statistical significance" than the rest of the code (as of 2021-05, [Lima et al.](https://arxiv.org/abs/2105.00500)).
- In 4,882 agent-written pull requests, "error-handling constructs (e.g., try and catch blocks) are the most consistently under-tested", with miss rates "reaching 86.0% in Java and 81.0% in Python" (as of 2026-07, [Dipongkor et al.](https://arxiv.org/abs/2607.18057)).
- A vendor's comparison of 470 pull requests found "Error handling and exception-path gaps were nearly 2× more common" in AI-co-authored pull requests than in human-only ones (as of 2025-12, [CodeRabbit](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)); CodeRabbit sells AI code review.
- A study of failures in automated issue solving names evasive repair, defensive code that hides the symptom, as a failure mode of the tools (as of 2025-09, [Liu et al.](https://arxiv.org/html/2509.13941)). Postmortems of 22 incidents over eight weeks in one LLM agent runtime have a category for swallowed errors and a class in which the model turns a failure into "fluent, plausible narrative delivered to the user" (as of 2026-06, [Wu](https://arxiv.org/abs/2606.14589)).
- Most of the record is the maintainer's own: 14 of the class's 16 rows come from the maintainer's repositories, 5 of them private. In the maintainer's audit of 12 incidents, 7 were found later by an agent auditing code, 3 by the user and 2 late or never; no class-wide lint rule was in use; and the checks that held best were the ones that fail independently of the code they check (as of 2026-10, one operator's audit, private, not verifiable).
- Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv); five of the class's rows are private sources and say so in the link column.
