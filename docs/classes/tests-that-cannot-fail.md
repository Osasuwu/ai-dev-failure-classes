---
class: tests-that-cannot-fail
surfaces_at:
  - code
  - ci
  - review
  - after-merge
applies_when: An AI coding agent writes or changes the tests for a change, the suite is green, and you take that green as evidence that the behaviour the tests are named after works, including a security control the change was meant to add or keep.
applies_when_not: A check that never ran, was skipped as a job or collected no tests. An agent reporting that tests pass when it never ran them. Code fitted to the tests (hard-coded expected outputs, special-cased test inputs) while the tests themselves can still fail. An agent that edits, weakens, skips or deletes a test that could fail until it passes. A test that is flaky rather than unable to fail.
---

# Tests that cannot fail

## TL;DR

A test passes whatever the code does: its expected value was read off the code, its mock replaces the very call that fails in real use, or a skip, an expected-failure marker, an `if` or a loose assertion keeps the failing case from ever being checked. The suite stays green while the behaviour it is named after is broken, and a security control nobody wrote a test for can be missing with nothing turning red. What protects is making each test show that it can fail: red before the fix, red when the code is broken on purpose, and an expected value that comes from somewhere other than the code under test.

## Symptom

The suite is green, the agent added tests for the change, and coverage went up. Later the behaviour those tests are named after turns out to be broken: on a device, in production, or when someone reverts the implementation and the tests still pass. In every incident behind this doc, the tests had one of these:

- the expected value was copied from what the code returned, so the test checks the code against itself;
- a mock replaced exactly the call that fails in real use (a subprocess, a web API, a database, the clock), so the test never meets the failure;
- the failing case sits behind a skip, an expected-failure marker, an `if` in the test, or an assertion so loose that any result satisfies it;
- the test is named after a behaviour its body never asserts;
- the functional tests all pass while a security property (an authorisation check, input validation, a secret kept out of logs) was never tested at all, so its absence turns nothing red.

## Examples

- INC-109: every "like" a mobile app sent to a music service's library endpoint failed with HTTP 400 in a release, because the request put a required parameter in the body instead of the query string. The tests asserted the request the code builds, so they agreed with the bug; a test on a device found it.
- INC-101: an end-to-end test of a dispatcher mocked the call that starts the worker process, so it checked the arguments but never the real start. In production the worker waited forever for a permission prompt nobody could answer, while the dispatcher logged success.
- INC-112 (private, not verifiable): a test for two pipelines started in the same second asserted that their session IDs do not collide only `if` the two IDs differed, so it skipped its assertion in exactly the colliding case it was written to catch.
- INC-111 (private, not verifiable): inverting an output bit in a robot driver, or reversing the order of two calls on its stop path, left a suite of over two thousand tests green; one joint-limit test passed only because a different check fired first.
- INC-103: an audit of 1,041 test functions asked of each whether it would fail if the behaviour it is named after broke, and found about a third that would not; one compared a module constant with a literal copy of itself.

## Mechanism

**The test is written by the author of the code, after the code.** An agent that writes the implementation and then its tests in one pass can carry the same understanding into both. Where that understanding is wrong, the test is wrong the same way: in INC-109 both sides held the same mistaken idea of the API. A study of test oracles written by language models found the same tendency at scale: the oracles mostly recorded what the program did, not what it should do ([Konstantinou et al.](https://arxiv.org/abs/2410.21136)). The quickest way to an expected value is to run the code and copy the result, which turns the test into a record of current behaviour rather than a check of intended behaviour. A test written that way passes on the day it is written by construction, and nobody has seen it fail. Simon Willison's test of a test is the inverse: "That test should fail if you revert the implementation." ([Your job is to deliver code you have proven to work](https://simonwillison.net/2025/Dec/18/code-proven-to-work/))

**Three shapes, one cause.** Below, the *oracle* is whatever decides that a result is right: an expected value, an assertion, a property every result must have.

- *The oracle comes from the code.* The expected value, the request shape or the mocked endpoint is taken from the implementation, so a wrong implementation matches its own test (INC-109; INC-108, where an HTTP mock was keyed on the production URL constant, so a wrong URL would match its own mock).
- *The mock sits on the failure.* Failures happen where the code meets something outside it: a process that needs a terminal, an API that rejects a shape, a store with a size limit. A mock there returns what the code expects, so the test cannot meet the failure (INC-101; INC-106, where CI ran only the in-memory store and a URL length limit crashed the real one).
- *The failing case is masked.* A skip or a non-strict expected-failure marker turns a failing test into a pass without a sound; an `if` or a `for` over an empty list in the test removes the assertion; a check that a key exists, that a count is `>= 1` or that the exit code is 2 is true for nearly any result (INC-112, INC-115, INC-110, INC-108).

**Why green is trusted.** A test suite is the cheapest oracle a project has, and the agent is steered toward it: the task looks done when the tests pass. Coverage counts the lines a test runs, not whether any assertion depends on them, so a test that cannot fail raises coverage as much as one that can; a study of five large Java programs found coverage not strongly correlated with a suite's ability to catch faults once the number of tests is held fixed ([Inozemtseva and Holmes, 2014](https://doi.org/10.1145/2568225.2568271)). The public audits behind INC-103, INC-105, INC-108 and INC-110 all asked the same question of every test, whether it fails when its behaviour breaks, and each found tests that do not, in suites that had been green.

**Security property outside every oracle (N4).** A private audit that sorted one operator's incidents into candidate classes listed this as a candidate of its own, numbered N4; it is folded in here ([#299](https://github.com/Osasuwu/ai-dev-failure-classes/issues/299)) because it is the same mechanism applied to security. The tests define what the change has to do; a security control (input validation, an authorisation check, an API that should have been replaced) is a property nobody wrote a test for, or whose only test cannot fail, so leaving it out turns nothing red. In INC-108 five tests of a secret-scanning hook asserted only that it exited with code 2, which, as the issue behind that row notes, is also what the interpreter returns when it cannot open the hook script. A study of agentic code repair found that patches which pass the functional tests most often fail on security by leaving a required control out (see Evidence).

**What protects.** A test is evidence only once it has been seen to fail for the right reason. The rungs below run from telling the agent so, through writing tests that start red and breaking the code on purpose to see them go red, to an oracle the agent did not write. None of them shows that the tests check the right behaviour; they show that the tests can fail.

## Where it surfaces

At code, when the agent runs a new test before the fix exists and it passes, or breaks the code on purpose and the suite stays green. In CI, when a mutation-testing job reports a change to the code that no test noticed, or when a test that was skipped or marked as an expected failure starts to run again. At review, when the reviewer reads the test diff apart from the code diff and asks where each expected value came from: in INC-107 the reviewing bot found that the pull request's own test asserted the value the faulty code produced. After merge, where most of the class's incidents were caught: in production, on a device, or in an audit of the suite months later (INC-109, INC-101, INC-103). The stages are spelled as in `docs/vocabularies.json`.

## Protections

Cheapest first. The first rungs ask the agent to show that a test can fail; the middle ones make a machine check it; the last ones bring an oracle the agent did not write, or a person. None of them replaces the ones before.

### Prompt: tests check the behaviour, they do not define it

- **Source:** [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): "Tests are there to verify correctness, not to define the solution."
- **Cost:** A paragraph of prompt.
- **Breaks when:** The rule is not in the context (a subagent started without it, a summary after compaction), or the model reads it and goes on: METR found that telling a model not to cheat had a nearly negligible effect on its reward hacking (gaming the check that scores a task instead of doing the task), in one task with one model (20 runs per prompt) ([METR, 2025-06](https://metr.org/blog/2025-06-05-recent-reward-hacking)). It says what a test is for, not where its expected value comes from, so an agent that follows it can still copy the output of its own code into a new test.

### Prompt: see the test fail before writing the fix

- **Source:** [Claude Code best practices](https://code.claude.com/docs/en/best-practices): "write a failing test that reproduces it, then fix it"; [Simon Willison](https://simonwillison.net/2025/Dec/18/code-proven-to-work/), quoted in Mechanism, gives the same test the other way round, by reverting the implementation.
- **Cost:** One more test run per test, before the fix exists.
- **Breaks when:** Nobody checks that the red run happened, or what made it red: a test that fails because the function it imports does not exist yet was red for the wrong reason and proves nothing about its assertion. A test seen red can still accept other wrong fixes, if its assertion is looser than the behaviour: on SWE-bench, patches that turned the benchmark's failing tests green still behaved differently from the reference fix (see Evidence). It does nothing for a test of code that already exists.

### Prompt: break the code on purpose and record that each new test goes red

- **Source:** one operator's practice: every added or changed test gets a probe, in which the agent changes the production line the test is named after, runs the test, sees it fail, reverts, and writes one line in the pull request naming the change and the failing test.
- **Cost:** A test run per probe and the agent's time; a longer pull request.
- **Breaks when:** It is held only by prose. When the same practice was a written rule with nothing checking it, it was used in none of eight pull requests sampled in the two days after it landed (as of 2026-08, [Osasuwu/jarvis#1735](https://github.com/Osasuwu/jarvis/issues/1735)). The agent picks the change it probes, so a test that catches only that change looks strong. A missing check cannot be broken on purpose: a security control nobody wrote (N4) has no line to change.

### Lint: flag tests with no assertion, an assertion under a condition, or a disabled test

- **Source:** [eslint-plugin-jest `expect-expect`](https://github.com/jest-community/eslint-plugin-jest/blob/main/docs/rules/expect-expect.md) and its sibling rules `no-conditional-expect` and `no-disabled-tests`; for pytest, Ruff's [PT017](https://docs.astral.sh/ruff/rules/pytest-assert-in-except/) (an assertion inside `except`) and [PT011](https://docs.astral.sh/ruff/rules/pytest-raises-too-broad/) (a `pytest.raises` that accepts any message); the [test smell catalogue](https://testsmells.org/pages/testsmells.html) behind tsDetect for Java.
- **Cost:** A line of configuration; seconds per run.
- **Breaks when:** The assertion sits in a helper the rule does not know, or it is there but true for nearly any result, like the exit-code checks in INC-108. An expected value copied from the code's output looks like any other literal, so no lint sees the first shape of this class. The rules differ by framework: check that yours covers the shape you fear, such as the `if` around the assertion in INC-112.

### CI: make an expected failure that passes fail the run, and count the skips

- **Source:** [pytest strict xfail](https://docs.pytest.org/en/stable/how-to/skipping.html), which makes a test marked as an expected failure fail the suite when it passes, where by default it does not; one operator's practice adds a check that compares the number of skipped tests with the base branch, and fails when a test file collects nothing.
- **Cost:** A configuration option and a short script; reading the skip list when it grows.
- **Breaks when:** The marker is not strict. In INC-115 non-strict expected-failure markers hid failing tests until CI caught them. A strict marker still passes when the test fails for an unrelated reason, unless `raises=` names the expected exception. A new `skip` with a plausible reason gets through unless something counts skips. It catches tests that do not run, not tests that run and cannot fail.

### CI: measure coverage over the test files too

- **Source:** [Ned Batchelder, "You should include your tests in coverage"](https://nedbatchelder.com/blog/202008/you_should_include_your_tests_in_coverage.html); one operator's practice fails the run on lines under `tests/` that never execute.
- **Cost:** Coverage on every run; excluding the lines that should not run.
- **Breaks when:** The assertion line executes but its outcome does not depend on the code. An assertion under an `if` counts as covered on every run where the condition held, which in INC-112 was every run without a collision, and a tautological assertion is covered every time. It finds the `for` over an empty list and the assertion nothing reaches, and nothing else.

### CI: the new test must fail on the parent commit

- **Source:** SWE-bench's [FAIL_TO_PASS field](https://huggingface.co/datasets/princeton-nlp/SWE-bench/blob/main/README.md), the tests the fix resolves, which fail before it and pass after it; one operator's practice runs each added test against the parent commit and requires it to fail on an assertion, not on an import error.
- **Cost:** One more run of the new tests on the base commit per change.
- **Breaks when:** The test fails on the parent for the wrong reason, or it fails there but is too weak to reject other wrong fixes: differential testing found many patches that passed the benchmark's own fail-to-pass tests and still behaved differently from the reference fix (see Evidence). A refactor has no expected red. A mock that fails on the parent and passes on the fix can still disagree with the real dependency, and a property no test covers is not checked at all.

### Review: have the tests written or read in a separate context, against the requirement

- **Source:** [Claude Code best practices](https://code.claude.com/docs/en/best-practices) describes a review that "reviews the diff in a fresh subagent that never saw your conversation. It isn't swayed by the reasoning that produced the code." and asks it to "check every requirement is implemented and the listed edge cases have tests"; a study of test oracles written by language models found that they "mainly capture the actual program behavior making bug detection difficult" ([Konstantinou et al.](https://arxiv.org/abs/2410.21136)), which suggests the tests be written from the requirement, not the implementation.
- **Cost:** Tokens for a second agent, and the time to act on what it finds.
- **Breaks when:** The reviewer gets the test and the code but not the requirement, so a test that matches a wrong implementation reads as consistent. It judges by reading, so it spots a wrong expected value only when it knows the right one, as the bot in INC-107 did; a reviewer from the same model family can hold the writer's mistaken idea of an API. A separate writer still mocks what is hard to run.

### Security: scan each change for a missing control

- **Source:** [GitHub code scanning](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning); [Claude Code `/security-review`](https://claude.com/blog/automate-security-reviews-with-claude-code) and its action, which runs on new pull requests.
- **Cost:** CI minutes or a model pass per pull request.
- **Breaks when:** The missing check is specific to the project's own rules (who may see which record) and matches no scanner rule. A model review is not deterministic and reports false positives, and a finding is advice unless the merge waits on it. Neither writes a test, so a control it found missing can go missing again later: in the study behind N4, reviewer roles did not catch the omissions (see Evidence).

### Doubles: prefer the real implementation, and test the fake against it

- **Source:** [Software Engineering at Google, ch. 13](https://abseil.io/resources/swe-book/html/ch13.html): "A real implementation should be preferred over a test double." The same chapter asks that a fake have its own tests against the real implementation's API.
- **Cost:** Slower and heavier tests (a real database, a hermetic server), or keeping a fake and its contract tests.
- **Breaks when:** The real dependency is too slow, costly or nondeterministic to run, and the fake's contract tests do not cover the failure the mock hid: a size limit (INC-106), a parameter the real API rejects (INC-109), a prompt that needs a terminal (INC-101). In each of those three the double accepted what the real dependency rejected, and nothing cheap closes that gap.

### Smoke: run the change once against the real thing before calling it done

- **Source:** one operator's practice: a change that touches a subprocess, file input and output, a database write, a hook registration or an outside API is run once on real input, and the side effect is checked, before the agent reports success. [Willison](https://simonwillison.net/2025/Dec/18/code-proven-to-work/) warns against skipping the manual test because an automated one seems to cover it.
- **Cost:** A person's or an agent's time per change; access to the device, account or environment.
- **Breaks when:** The failure appears only in production: under load, with real data sizes, with another user's settings. One run checks one input. Each of the three escapes through a mocked boundary cited here was found by real use, after merge: by a user (INC-106), a device test (INC-109) or production (INC-101).

### Oracle: write properties and relations, not values read off the output

- **Source:** [Hypothesis](https://hypothesis.readthedocs.io/en/latest/), where a test states what must hold for every input in a range; metamorphic testing ([Segura et al.](https://eprints.whiterose.ac.uk/id/eprint/110335)), which checks how the output changes when the input is transformed, without knowing any single output; differential testing against a reference implementation ([PatchDiff](https://arxiv.org/abs/2503.15223)).
- **Cost:** Thinking about the domain to state the property; many generated inputs per run; a reference implementation for differential testing.
- **Breaks when:** The property is weaker than the requirement (that the result is a list, say), or the agent derives it from its own implementation. In a study where an agent wrote property tests for popular Python packages, 44% of the bugs it reported were not real, so the findings need triage (as of 2025-10, [agentic property-based testing](https://arxiv.org/abs/2510.09907)).

### Mutation testing: change the code the diff touched and see whether any test notices

- **Source:** [cargo-mutants `--in-diff`](https://mutants.rs/in-diff.html), [Stryker](https://stryker-mutator.io/docs/stryker-js/configuration/) with a `break` threshold, [mutmut](https://mutmut.readthedocs.io/en/latest/) for Python; [Google](https://research.google/pubs/state-of-mutation-testing-at-google/) runs a diff-based version on the code changes its engineers author or review. One operator's practice keeps it advisory, reported in review, and blocking only on safety paths.
- **Cost:** The most compute of the CI rungs, growing with the number of mutants times the tests that cover them; triage of mutants that change nothing observable.
- **Breaks when:** It is not set to fail: Stryker's `break` threshold defaults to never failing the build. A diff-scoped run checks the changed code, not the tests, so a test weakened on code the diff did not touch is not re-checked. A skipped or dead test makes every mutant survive, so the report blames a weak test where the cause is a test that does not run. It cannot mutate code that is not there, so a missing security control (N4) passes.

### Security: write tests for the controls the change must keep (N4)

- **Source:** [OWASP ASVS 4.0.3](https://github.com/OWASP/ASVS/blob/v4.0.3/4.0/en/0x04-Assessment_and_Certification.md) recommends unit and integration tests for "specific and relevant fuzz and abuse cases"; the [OWASP Abuse Case Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html) turns what an attacker would try into security tests.
- **Cost:** A session per feature listing what an attacker would try, and the negative tests to write and keep.
- **Breaks when:** The list is incomplete: a control nobody listed still has no test, which is N4 again one level up. The cheat sheet is marked as archived and itself says abuse cases are rarely used in practice. A security test has the same failure modes as any other test in this class, so the rungs above apply to it too.

### Audit: ask every test in the suite whether it would fail

- **Source:** one operator's practice: an agent goes through a whole suite with one question per test, whether it fails when the behaviour it is named after breaks, and files what it finds (INC-103, INC-105, INC-108 and INC-110 are public audits of this kind).
- **Cost:** A long agent session per suite, then the fixes; the fix pull requests leak too.
- **Breaks when:** It is the only rung: an audit finds after merge and prevents nothing. In one project an audit sweep found loose oracles (INC-114) and a later whole-suite audit found the same shapes again (INC-113); in another, the fix after an audit left three of its findings behind (INC-108).

### Escalation: on paths where a failure cannot be undone, make the strong rungs blocking from the start

- **Source:** one operator's practice: where a test that cannot fail would let through an effect nobody can take back (a robot that moves, data that persists, a release users install), mutation testing blocks the merge and a smoke run on the real device or service is required for every change, instead of being added after an incident (INC-111 is the robot case, INC-109 the release case). Which of those changes also need a person to approve them is the rule in [irreversible effects](irreversible-effects.md); this rung depends on it.
- **Cost:** The slowest rungs on every change to those paths; device or environment time; the person's attention where the rule asks for it.
- **Breaks when:** The path is not marked as one where failure cannot be undone, so only the cheap rungs run. The blocking mutation gate still cannot see a missing control, and the smoke run still checks one input.

## Evidence

- In 1,030 execution traces from seven agent frameworks repairing security-relevant code, 170 patches passed functional verification but kept or introduced a vulnerability: "Omission accounts for 48.2% of the confirmed failures, Introduction for 30.6%, and Inadequacy for 21.2%", and "Current test-passing evaluation and LLM-based reviewer roles were insufficient to expose or intercept these failures in the confirmed cases." All runs used one model, GPT-4o-mini (as of 2026-06, [When Passing Tests Hides Vulnerabilities](https://arxiv.org/abs/2609.10548)). This is the evidence for N4.
- On SWE-bench Verified, the benchmark's own validation "causes 7.8% of all patches to count as correct while failing the developer-written test suite", and differential testing found that 29.6% of plausible patches behave differently from the reference fix (as of 2025-03, [Are "Solved Issues" in SWE-bench Really Solved Correctly?](https://arxiv.org/abs/2503.15223)).
- In 4,882 agent-written pull requests from five agents, 49.6% of the pull requests that changed code under test also included test changes; "error-handling constructs (e.g., try and catch blocks) are the most consistently under-tested, with miss rates reaching 86.0% in Java and 81.0% in Python" (as of 2026-07, [Test Coverage Analysis of Agentic Pull Requests](https://arxiv.org/abs/2607.18057)). The paths where a failure is handled are the ones least often tested.
- The private audit named in Mechanism counted 29 incidents of this class in one operator's projects, most of them caught after merge by the agent itself in a later audit (as of 2026-10, private, not verifiable). The dataset holds 15 rows for this class, a selection from those incidents; the rest are not in it. Four of the test audits behind those incidents are public; on 2026-09-30 they asked every test whether it fails when its behaviour breaks: about a third of 1,041 test functions in one suite did not (INC-103), 34 tests in another (INC-110), 21 of 826 collected tests in a third (INC-108), and 12 of 433 test functions in a fourth (INC-105).
- Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv); five of the class's rows are private sources and say so in the link column. All of the class's rows come from one operator's projects: the external sources above are studies and vendor guidance, not incident reports.
