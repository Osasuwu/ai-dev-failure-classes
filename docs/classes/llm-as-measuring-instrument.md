---
class: llm-as-measuring-instrument
surfaces_at:
  - review
  - after-merge
applies_when: You use a language model's output as a check on work, an AI coding agent's or anyone's: a review bot whose verdict gates a merge, a model that grades or scores output, an LLM judge in an eval, a script that parses a model's text into pass or fail. You act on the result as if it measured something, and you want to know when it does not and what makes it a measurement.
applies_when_not: An agent's own report of its work that nobody checks. An agent that changes its work until a check, model-based or not, is satisfied. A check that never ran or never saw the change and counted as passed. Text planted in the input to steer the model that reads it.
---

# LLM as the measuring instrument

## TL;DR

A model's verdict is a sample of generated text, not a reading: it varies between runs on the same input, does not say what it covered, cites what it did not check and can loop without converging. What makes it closer to a measurement is a fixed output contract, evidence a script can check, repeated runs with a rule set in advance, a bounded loop, calibration on known defects for the version you run, and a merge decided by deterministic checks and a person, with the model as an adviser.

## Symptom

The review bot approved the pull request, and the bug it should have caught was in the diff. Its comment discussed three of the twelve changed files, and nothing in it says whether it read the other nine. Run again on the same commit, it gives a different verdict, or a new set of findings that the first run did not have. A finding cites a line that is not in the file, a function the code never calls, or a check that it says it ran and did not. You fix every finding and push; the next round finds new problems, many in the text the fixes wrote, and the rounds do not converge. A script reads the model's answer for the word "PASS", and a sentence that only mentions passing counts as a pass. A score moves between two runs on the same input. Each result arrived in the same confident form, and none said how much of the input it covered or how sure it was.

## Examples

- INC-409: a document reviewer's prose wrapped so that a line began with an earlier finding's ID; the script that parsed the reply into a verdict took it for a malformed finding and failed the run as unreviewable, after a run that cost $12.43 and found nothing wrong.
- INC-405: the calibration runs that measured a review skill could read the main branch, which held the calibration corpus and so the answer key.
- INC-413: on the same commit, a retry of a code review turned a major finding into a clean result, the latest answer was the one the gate used, and the pull request merged (private, not verifiable).
- INC-420: five review rounds across three pull requests reported reading fewer files than the pull request changed, and all three merged; each was found by the maintainer after it had landed.
- INC-422: a bot-review loop ran for 156 rounds without converging, changing things the pull request never set out to change and in the end reverting its own earlier fixes.

## Mechanism

**A verdict is a sample.** The same model on the same input does not return the same text: the inference stack itself is not deterministic, even at temperature 0 (see Evidence). One operator ran the same diff with the same prompts through two ways of calling one model and got 7, 84 and 44 findings (INC-424). A retry is therefore a new draw, and a gate that keeps the latest answer can turn a blocking finding into a pass on an unchanged commit (INC-413, a private row).

**It does not say what it covered.** A review comment is written the same way whether the model read every changed file or three of them. In INC-420 the rounds that read fewer files than were changed looked like any other round; in INC-414, a private row, a reviewer on large diffs left no trace of what it had read. The study of agents that claim to have read files they did not is in [claims from plausibility](claims-from-plausibility.md).

**Its output is text, and something parses it.** The verdict reaches the gate through a script that looks for a word, a line or a field. Text that has the shape of a verdict passes for one: in INC-412, a private row, the gate never ran a real review and the model still wrote comments that looked like verdicts. The parser can also fail on text it was not written for, and the model decides that text, so the failure recurs (INC-409).

**Its citations are generated too.** A line number, a function name or a quoted passage is part of the same output. One project moved its review findings from line numbers to quoted anchors to "eliminate incorrect line numbers, which is a frequent issue with the review scripts." ([radius-project/radius#12017](https://github.com/radius-project/radius/pull/12017), INC-421).

**A model judging work has biases a ruler does not.** LLM judges prefer answers by their position, their length and whether a model like them wrote them, and a model's preference for its own output grows with how well it recognises that output (see Evidence). Without outside feedback, a model is weak at correcting its own answers, so a second pass by the same model is not an independent check (see Evidence).

**A review loop is a new measurement each round.** Each round reads text the previous round's fixes wrote, so findings keep arriving in new text: in INC-406 the fix-induced findings fell from 15 to 3 over two rounds and later rounds still found over-corrections of earlier fixes. A loop with no fixed point can oscillate or drift (INC-422), and a loop stopped by a round cap ends without having converged: in INC-423 the pipeline stopped at its bound with blocking findings still open.

**The instrument is rarely calibrated, and calibration is fragile.** Few teams measure how often their reviewer catches a known defect. When one does, the measurement belongs to one version of the reviewer and one corpus. In INC-402 the review pass changed after its calibration run, so no seeded run covered the version that merged. In INC-404 the calibration branches were the main branch plus the corpus documents, so other files were in their later state and three entries could not be measured. In INC-405 the runs could read the answer key. In INC-403 three runs of the same model on the same corpus agreed, and agreement between runs of one model is a floor on consistency, not a recall figure.

**Boundaries.** This class is about the model's output used as the check. When the agent's own report of its work is believed unchecked, the class is [claims from plausibility](claims-from-plausibility.md). When the agent changes its work until a check, including a review rubric, stops raising findings, the class is [proxy optimisation](proxy-optimisation.md); the same review loop can show both, the author following the reviewer and the reviewer not measuring. When the check never ran, or ran without seeing the change, and counted as passed, the class is [absence read as success](absence-read-as-success.md), where a reviewer that lost its shell and kept writing verdicts is INC-042. Text planted in the reviewed input to steer the reviewer is the separate injection class N-B. Review that stops catching problems as the volume or the number of rounds grows is the candidate class N5, review saturation, not yet written.

## Where it surfaces

At review, where the model's verdict is read and the gate acts on it. A rerun on the same commit that disagrees, a cited line that is not in the file, a coverage line that lists fewer files than the diff, a parser that fails a clean run (INC-409), and rounds whose findings move into the text the fixes wrote (INC-406, INC-422) all show there. After merge, where the verdict let through what it should have caught: the defects found by a person after the pull requests landed (INC-420), the major finding re-rolled away before the merge (INC-413, a private row), and calibration errors found only when someone checked how the measurement was built (INC-402, INC-404, INC-405). The stages are spelled as in `docs/vocabularies.json`.

## Protections

Cheapest first. The first rungs shape what the model writes; the middle ones check what it wrote and how often; the last ones measure the instrument and take the decision away from it. None of them replaces the ones before.

### Prompt: let the model say it does not know, and make it quote before it judges

- **Source:** [Anthropic, reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations): "Explicitly give Claude permission to admit uncertainty." and, for claims about a document, "If it can’t find a quote, it must retract the claim."
- **Cost:** Tokens for the instruction and for the quotes.
- **Breaks when:** The model does not follow it; [the same page](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) says the techniques "don’t eliminate them entirely". A quote the model supplies is generated text, so it needs the citation rungs below before it counts as evidence.

### Rubric: read the review rules from the base branch

- **Source:** [Claude Code code review](https://code.claude.com/docs/en/code-review.md) reads its `REVIEW.md` rules from the base or default branch, never from the pull request's own changes, so a pull request cannot rewrite the rules it is reviewed by.
- **Cost:** A change to the rules needs its own merge before it applies.
- **Breaks when:** The rules are one part of the instrument; the model, the workflow's prompt and the parser change it too. In INC-402 the review pass changed after it was calibrated, so the instrument that merged was not the one measured.

### Contract: a fixed verdict line, and no line means no verdict

- **Source:** [Claude Code code review in pull requests](https://code.claude.com/docs/en/code-review-pull-requests.md) tells a script reading its check run to "take the counts from the last line only", and, for a run without that line, "Treat that as no verdict rather than as zero findings."
- **Cost:** A parser with a failing branch for a missing or malformed line; reruns when the line is missing.
- **Breaks when:** The line is well formed and wrong: the contract checks the shape of the answer, not the measurement behind it, and in INC-412, a private row, verdict-shaped comments came from a gate that never ran a real review. The parser reads more than the line it was written for: in INC-409 a wrapped prose line made it fail a clean run. The vendor's check run itself "never concludes as a failure" ([the same page](https://code.claude.com/docs/en/code-review-pull-requests.md)), so the gate that reads the line is yours to write.

### Coverage: make the reviewer state what it read, and fail a partial round

- **Source:** [ptr727/ProjectTemplate#608](https://github.com/ptr727/ProjectTemplate/pull/608) (INC-420): the review reports how many changed files it read, a round that read fewer than were changed exits with its own code, and a report in a shape the gate does not recognise fails closed.
- **Cost:** A coverage line in the prompt and a comparison with the list of changed files on every round.
- **Breaks when:** The count is the model's own report, a claim like any other ([claims from plausibility](claims-from-plausibility.md)); it holds only when checked against a record of what the reviewer opened, and in INC-414, a private row, there was no such record. A round that read every file can still miss the defect in one of them.

### Citations: anchor each finding to a quoted snippet, not a line number

- **Source:** [radius-project/radius#12017](https://github.com/radius-project/radius/pull/12017) (INC-421): "The anchor — not the integer — is the source of truth." A helper finds the snippet in the file and fails loudly when it matches no line or more than one.
- **Cost:** A lookup per finding; findings whose snippet cannot be placed go back to the model or are dropped.
- **Breaks when:** The snippet occurs in several places or nowhere, and the helper refuses it, so the finding is lost unless someone re-anchors it ([radius#12017](https://github.com/radius-project/radius/pull/12017)). A snippet that exists proves where the finding points, not that the finding is right.

### Citations: check quoted text against its source mechanically

- **Source:** one operator's practice: this repo's [quote check](../../scripts/check_quotes.py) fetches the pages a document links and checks that each quoted passage is in one of them, on every pull request that changes a markdown file ([`quote-check.yml`](../../.github/workflows/quote-check.yml)).
- **Cost:** CI minutes and page fetches on every run.
- **Breaks when:** The page cannot be fetched, which the check reports but does not fail on; it fails only when a passage is not found. It checks wording, not whether the claim around the quote matches the source, and a paraphrase gives it nothing to check.

### Verdict: keep the worst result per commit

- **Source:** one operator's practice, after INC-413: when retries of a review on one commit disagree, any blocking result wins, so a retry cannot clear a finding on a commit that did not change; only a new commit gets a fresh verdict.
- **Cost:** Storing each run's verdict per commit; a false positive holds the pull request until a new commit or a person clears it.
- **Breaks when:** The finding was a false positive, which now sticks by design. It fixes the aggregation of retries, not the variance behind them: one run that missed the defect, with no retry, still passes.

### Repeat: run the check several times, with the rule for combining them set in advance

- **Source:** [Anthropic, reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) under best-of-N: "Run Claude through the same prompt multiple times and compare the outputs."; why one run is not enough is the nondeterminism measured in Evidence.
- **Cost:** One full run per repetition.
- **Breaks when:** The rule is chosen after the results, such as retrying until one run passes or keeping the latest: in INC-413, a private row, that turned a major finding into a pass. Runs of one model share its blind spots, so their agreement is not recall: in INC-403 all three runs caught none of the seeded defects in two of the classes.

### Debias: swap the order, and judge with a model from another family

- **Source:** [Zheng et al., MT-Bench](https://arxiv.org/abs/2306.05685) examines position, verbosity and self-enhancement bias in LLM judges and swaps answer positions to control the first; [Verga et al.](https://arxiv.org/abs/2404.18796): "we propose instead to evaluate models using a Panel of LLm evaluators (PoLL)", drawn from disjoint model families.
- **Cost:** A second model's tokens per item, or a panel's; the PoLL authors report the panel cheaper than one large judge (see Evidence).
- **Breaks when:** The task is not what the papers measured: both test judges of chat and question-answering output, not code review. A judge from the family that wrote the work prefers it, and the preference grows with how well it recognises its own output ([Panickssery et al.](https://arxiv.org/abs/2404.13076)).

### Verification: a second stage that checks each finding against the code

- **Source:** [Claude Code code review](https://code.claude.com/docs/en/code-review.md): "A verification step checks findings against the code before they're reported."
- **Cost:** The managed review that includes it averages $15–25 per review, scaling with the pull request's size (as of 2026-03, [Anthropic](https://claude.com/blog/code-review)).
- **Breaks when:** The verifier is a model too, and "a review works from reading the diff and the surrounding code, without building or running your code." ([Claude Code code review](https://code.claude.com/docs/en/code-review.md)). It checks the findings that were raised, so it cuts false positives, not misses: "A review with no findings doesn't mean your code is error-free or secure."

### Loop: bound the rounds, freeze the scope, and hand non-convergence to a person

- **Source:** [awesome-copilot, convergence](https://github.com/github/awesome-copilot/blob/main/skills/copilot-pr-autopilot/references/09-convergence.md): "default STOP at every 10th round (10, 20, 30, …) before looping back to step 1"; CodeRabbit's [`auto_pause_after_reviewed_commits`](https://docs.coderabbit.ai/reference/configuration) pauses automatic reviews after a set number of reviewed commits, five by default; [Claude Code code review in pull requests](https://code.claude.com/docs/en/code-review-pull-requests.md) leaves findings on unchanged code "outside the scope of this re-review and not posted"; [Contrast Security](https://www.contrastsecurity.com/security-influencers/when-ai-reviewers-cannot-agree): "First, instrument the loop to detect non-convergence." and, when it does not converge, "do not ship; hand the run to a human."
- **Cost:** Rounds up to the cap; a person's time on each run that reaches it.
- **Breaks when:** The cap ends the loop, not the problem: [Contrast's pipeline](https://www.contrastsecurity.com/security-influencers/when-ai-reviewers-cannot-agree) "exited at the round bound with the bypass still in place." (INC-423), and "Most AI review pipelines treat the round bound as a quality guarantee." The cap is a rule the agent follows, not a stop: in [awesome-copilot](https://github.com/github/awesome-copilot/blob/main/skills/copilot-pr-autopilot/references/09-convergence.md) "No script enforces a max-rounds cap or stops the loop". Each fix is new text that the next round reviews, so findings keep arriving after the scope is frozen (INC-406).

### Calibrate: measure the instrument on known defects, for the version you run

- **Source:** [Hamel Husain, LLM judges](https://hamel.dev/blog/posts/llm-judge/): "Treat the judge as a binary classifier." and report its true-positive and true-negative rates against a person's labels, because "Raw agreement can be misleading when classes are imbalanced."; one operator's practice: a corpus of documents with seeded defects that the reviewer is run on, to count what it catches.
- **Cost:** 27 runs for one calibration, roughly $250 (as of 2026-09, [Osasuwu/jarvis-oss#106](https://github.com/Osasuwu/jarvis-oss/issues/106)).
- **Breaks when:** The reviewer changes after it was measured (INC-402). The reviewer can reach the answer key (INC-405). The corpus is not the tree the reviewer meets in use (INC-404). The labels come from the same model, which gives agreement, not recall (INC-403).

### Authority: the model advises, and deterministic checks and a person decide

- **Source:** [Claude Code code review](https://code.claude.com/docs/en/code-review.md): "A review never approves or blocks the pull request, so the decision to merge stays with your team."; [GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review): "By default, Copilot's reviews do not count toward required approvals for the pull request."
- **Cost:** A person's review time on every merge; deterministic checks to write for what the model was trusted with.
- **Breaks when:** The setting is changed: "Copilot can submit an approving review that satisfies your repository's required-approval rule." ([GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review)). The person reads the verdict instead of the diff: in INC-420 three pull requests merged on partial rounds. When a merge or another step needs a person's approval is the rule in [irreversible effects](irreversible-effects.md); this rung depends on it.

## Evidence

- At temperature 0, 1,000 completions of one prompt gave 80 unique outputs; with batch-invariant kernels "all of our 1000 completions are identical", at 42 seconds against 26 for the default (as of 2025-09, [Thinking Machines](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)).
- On one diff with the same prompts, a model called through a CLI gave 7 findings and through the API gave 84 (Sonnet) and 44 (Opus), of which the author counted about 69 and 32 as false positives (as of 2026-03, [dev.to](https://dev.to/fole/claude-cli-vs-api-for-code-review-same-model-wildly-different-results-1oai)). Self-reported, one diff.
- In Anthropic's managed code review, "less than 1% of findings are marked incorrect"; on pull requests over 1,000 changed lines 84% get findings, 7.5 on average, and under 50 lines 31%, 0.5 on average (as of 2026-03, [Anthropic](https://claude.com/blog/code-review)). Marked incorrect by users, so a miss does not enter the figure.
- GPT-4 as a judge agreed with human preferences over 80% of the time, the level at which humans agree with each other, while showing position, verbosity and self-enhancement biases (as of 2023-06, [MT-Bench](https://arxiv.org/abs/2306.05685)).
- A panel of smaller judges from disjoint families matched human judgement better than one large judge, with less intra-model bias, at over seven times lower cost (as of 2024-04, [PoLL](https://arxiv.org/abs/2404.18796)).
- Fine-tuning showed "a linear correlation between self-recognition capability and the strength of self-preference bias" (as of 2024-04, [Panickssery et al.](https://arxiv.org/abs/2404.13076)).
- "our research indicates that LLMs struggle to self-correct their responses without external feedback" (as of 2023-10, [Huang et al.](https://arxiv.org/abs/2310.01798)).
- A review loop of an implementer and four reviewers, on a security-sensitive feature, ended at its round bound with 37 findings, 7 of them blocking, unresolved (as of 2026-07, [Contrast Security](https://www.contrastsecurity.com/security-influencers/when-ai-reviewers-cannot-agree)).
- In one calibration, three runs of the same reviewer on a seeded corpus caught 0 of 1 status defects and 0 of 2 plan defects in every run, and 0, 0 and 2 of 5 quote defects; the authors label it a floor on same-model agreement, not a recall figure (as of 2026-09, [Osasuwu/jarvis-oss#106](https://github.com/Osasuwu/jarvis-oss/issues/106)).
- Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv); three of the class's rows are private sources and say so in the link column.
