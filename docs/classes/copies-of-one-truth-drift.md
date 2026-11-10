---
class: copies-of-one-truth-drift
surfaces_at:
  - task
  - code
  - ci
  - review
  - after-merge
applies_when: An AI coding agent edits a codebase where one fact is written down in more than one place (a duplicated function, a new version kept beside the old one, a constant or list repeated across files, a producer and a consumer that each encode the same format, a config or workflow copied between repositories, a template and the files made from it), and you want to know why a change or a fix lands in one copy and not the others, and what keeps the copies in step.
applies_when_not: Two agents or sessions writing the same file or state at the same time (shared state without ownership). A rule or lesson that exists but never reaches the agent at the point of action. A fact the agent states without checking it (claims from plausibility). A test whose expected value is copied from the code it tests, so it cannot fail (tests that cannot fail). An environment that differs from the one tested.
---

# Copies of one truth drift

## TL;DR

One fact lives in several places, and the agent changes some of them: the fix reaches one copy, the new version lands beside the old one, the deletion leaves references behind. Each copy passes its own checks, so the drift shows up after merge. What keeps copies in step is a mechanism that knows they are copies: one source with the rest generated and checked, a contract test between producer and consumer, a drift check against the template. Prompts and code search help the agent find copies, and clone detection finds copies that still look alike; nothing in the sources below checks that a change reached a copy nobody declared and that no longer looks like the others.

## Symptom

A change you asked for is done, its tests pass, and the same behaviour is still wrong somewhere else. The agent fixed the bug in one function and an older twin of it, in another module or another repository, still has it. It wrote a new version of a helper beside the old one instead of changing the old one, and callers now split between the two. A list of allowed values, a schema field, a version number or a path is written in three files, and the change reached two. A producer and its consumer each encode the same format; one was updated, both suites are green, and the two no longer understand each other. A workflow or config copied into several repositories was fixed in one. Something was deleted or renamed, and a reference to it lives on in a doc, a test fixture or a second copy. Each copy passes its own checks, so often nothing turns red until the copies meet at run time, in review by luck, or in an audit.

## Examples

The INC- codes are rows in [the incident dataset](../../incidents/incidents.csv).

- INC-181: a user reports that Claude Code keeps writing the same constant or path into several files instead of one ([anthropics/claude-code#37137](https://github.com/anthropics/claude-code/issues/37137)): "A bug in the shared value now requires fixing it in multiple places — and Claude may only fix one of them."
- INC-161: an agent fixed a parsing bug in one function of a media-session gate; review found, a round later, that its sibling function sharing the same logic still had the old behaviour.
- INC-169: one counter, kept in a spreadsheet, was written by three halves of an app (Dart, Kotlin, Python). They disagreed on cell type, row lookup and de-duplication, and user counts were undercounted for good; a parity test covered the sheet's header columns, and nothing checked the value types.
- INC-165: a review gate copied into two repositories had the same fail-open hole. It was fixed in one repository and never ported, and the other kept passing PRs with no review verdict until a cross-repository comparison found it.
- INC-159: a merge-hold check was deleted, and the documentation agents read still described it as live, so agents relied on a label that nothing enforced.

## Mechanism

Four ways the copies come apart recur in the dataset rows of this class.

**The agent edits where it is looking.** A fix starts at one site and stops when that site is green. Failure studies of issue-solving agents name this directly: one subcategory is changes that "adjust one implementer of an interface while neglecting others", another is that "recurring code patterns require simultaneous updates" ([Liu et al.](https://arxiv.org/html/2509.13941)). A refactoring benchmark found that "the dominant failure mode is _incomplete refactoring_", agents stopping before the peripheral call sites ([SWE-Bench ProMax](https://arxiv.org/html/2608.09802)). A sibling function, a twin in another language or a copy in another repository is not on the path the agent read, so it is not edited.

**The agent writes a new copy instead of changing the old one.** Asked for a change, an agent can re-implement logic that already exists rather than find it; the same study lists "re-implementing existing logic or ignoring tool extension points, adding redundant code and potentially new bugs" as its own subcategory ([Liu et al.](https://arxiv.org/html/2509.13941)). The old version keeps its callers, and from then on a fix to one does not reach the other (INC-182, INC-184). In one row the same happened to a rule: an agent told about a mistake appended a restated rule to its instruction file instead of finding the existing one (INC-183).

**Two components encode one contract separately.** A producer and a consumer, a template and a linter, a gate and the reviewer it calls each hold their own copy of a format, a vocabulary or a definition. One side changes and the other does not (INC-155, INC-156, INC-157, INC-160). In two rows the copy was an allowlist or a matcher, and the mismatch failed open: the guard stopped matching and said nothing (INC-150, INC-154).

**Copies outlive whatever made them.** A file synced from a template into several repositories, or a claim about a guard copied along with it, stays when the sync stops; a fix or a retirement in one copy then does not reach the others (INC-163, INC-165, INC-166, INC-167). A deletion that does not search the docs leaves them describing something that is gone (INC-159).

In these rows each copy typically passed its own tests, because each test was written against its own copy. A test that checks a twin's structure but not its values stays green while the values diverge (INC-169). The failure shows when the copies meet.

## Where it surfaces

Mostly after merge. Of the 35 rows of this class, 23 were caught after merge (as of 2026-11, this dataset): in use, by a later audit, or while the agent worked on something else. Four surfaced in CI, all of them gates whose own copies disagreed, so no PR could pass (INC-157, INC-158, INC-160, INC-167). Two surfaced in review, when a review bot spotted the missed sibling (INC-161, INC-162). Five surfaced while the code was being written, one during task planning. One operator's private audit covers the 31 rows from that operator's own repositories (INC-150 to INC-180) and records who noticed each one rather than the stage: in 18 of them it was the agent itself, later, while working on something else (as of 2026-10, private audit).

The class is spread across stages, and no single gate covers it: the copy that was missed is not in the diff, so diff-scoped review and tests do not see it.

## Protections

The rungs below either help the agent find copies or compare copies that were declared. One operator's record of 31 incidents of this class has no patch that compares copies: no parity test across twins, no reference check on deletion, no shared schema between producer and consumer. The checks that held in that record guard the merge machinery's own behaviour (fail closed, required checks), not copy agreement (as of 2026-10, private audit). The search of public tools, docs and studies behind this doc (its queries are listed in [the pull request that added it](https://github.com/Osasuwu/ai-dev-failure-classes/pull/306)) found no mechanism that finds an undeclared copy that no longer looks like the others and checks that a fix reached it; clone detection covers copies that still look alike. That gap is open; the ladder does not fill it.

### Prompt: tell the agent to look for siblings before it fixes or writes

- **Source:** the [dotnet/runtime code-review skill](https://github.com/dotnet/runtime/blob/main/.github/skills/code-review/SKILL.md) tells the reviewing agent to check sibling types and platform variants for the same issue or the same fix; GitHub's [coding-agent best practices](https://docs.github.com/copilot/tutorials/coding-agent/best-practices) show instructions that name derived files and the command that regenerates them.
- **Cost:** tokens; writing the instruction.
- **Breaks when:** the agent does not know the copy exists or does not search for it. Nothing checks that it obeyed. In one operator's record, standing instructions to grep for sibling instances did not stop sibling misses (INC-161, INC-162, INC-171).

### Navigation: give the agent references by symbol, not by text

- **Source:** [Claude Code code-intelligence plugins](https://code.claude.com/docs/en/plugins/code-intelligence) give the agent a language server that "finds definitions and references by symbol instead of by text search"; [VS Code](https://code.visualstudio.com/docs/editing/editingevolved) renames a symbol across files.
- **Cost:** a plugin and a language-server binary per language.
- **Breaks when:** the copy is duplicated logic, not a reference to the same symbol; the language server does not support cross-file rename; the session runs where the server is not started (the plugin page says cloud sessions do not start plugin language servers).

### Review: a reuse pass over the diff

- **Source:** [Claude Code `/simplify`](https://code.claude.com/docs/en/commands): "Four review agents run in parallel, covering reuse of existing helpers, simplification, efficiency".
- **Cost:** tokens per run.
- **Breaks when:** the stale copy is outside the diff, so it is not in the reviewers' input. The [same page](https://code.claude.com/docs/en/commands) says "The review doesn't look for correctness bugs."

### Search and rewrite every known copy at once

- **Source:** [ast-grep](https://ast-grep.github.io/guide/introduction.html) and [OpenRewrite](https://docs.openrewrite.org/) find and rewrite every site that matches a pattern; [Semgrep](https://docs.semgrep.dev/writing-rules/rule-ideas) can flag each remaining use of a deprecated API; [Sourcegraph Batch Changes](https://sourcegraph.com/docs/batch-changes) applies one change across many repositories.
- **Cost:** writing the pattern or recipe; Batch Changes needs an Enterprise plan.
- **Breaks when:** nobody knows the copies exist, so nobody writes the pattern (INC-161, INC-165); a copy differs in text from the pattern, so the pattern does not match it.

### Flag what a replacement left behind

- **Source:** [vulture](https://github.com/jendrikseipp/vulture) (Python) and [knip](https://knip.dev/) (JavaScript and TypeScript) find code, exports and files nobody uses, such as the old version after a new one replaced it.
- **Cost:** a CI step; an allowlist for false positives.
- **Breaks when:** the old copy still has callers, so it is not unused. [vulture's own documentation](https://github.com/jendrikseipp/vulture) warns it is "likely to miss some dead code". A stale doc reference or a stale figure is not code and is not checked.

### Detect duplicated blocks, and changes that reach only one of them

- **Source:** [jscpd](https://github.com/kucherenko/jscpd) can fail a run on new clones; [PMD CPD](https://pmd.github.io/pmd/pmd_userdocs_cpd.html) exits non-zero when it finds duplicates; [SonarQube](https://docs.sonarsource.com/sonarqube-server/latest/user-guide/code-metrics/metrics-definition/) reports duplicated blocks and can fail a quality gate on them. [Teamscale](https://docs.teamscale.com/reference/ui/activity/commits/) goes a step further and shows clone alerts per commit: "Alerts indicate inconsistent changes to code clones, i.e. a change to a copied code section that was only applied to one of the copies" (vendor documentation).
- **Cost:** a CI step, or a SonarQube or Teamscale server; tuning the minimum size.
- **Breaks when:** the copies are below the minimum size (a constant, a short list); they already differ in text; they are in another language or another repository. jscpd, PMD CPD and SonarQube report that copies exist, not that a change reached only some of them; Teamscale's check flags a commit for a person to judge and does not block it.

### Contract checks between producer and consumer

- **Source:** [Pact](https://docs.pact.io/) replays the consumer's recorded expectations against the provider; [buf breaking](https://buf.build/docs/breaking/) compares a Protobuf schema against a past version; [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) checks compatibility before it accepts a new schema version.
- **Cost:** test code on both sides and a broker, a CLI step, or a registry service.
- **Breaks when:** the consumer depends on something the contract does not record; [Pact's documentation](https://docs.pact.io/) says "Only parts of the communication that are actually used by the consumer(s) get tested." A registry set to no compatibility checks checks nothing.

### Generate the copies from one source and fail CI when they are stale

- **Source:** [cog](https://cog.readthedocs.io/en/latest/running.html): "You can use the `--check` option to run cog just to check that the files would not change if run again."; [embedme](https://github.com/zakhenry/embedme) verifies code blocks in markdown against their source files; Kubernetes runs [verify-codegen.sh](https://github.com/kubernetes/kubernetes/blob/master/hack/verify-codegen.sh) to fail when committed generated code is out of date.
- **Cost:** a generator and a CI step.
- **Breaks when:** a copy is written by hand outside what the generator writes. [cog's check](https://cog.readthedocs.io/en/latest/running.html) asks only whether "the files would not change if run again", so a copy the generator never writes is never compared. A check that is not wired into CI does not run.

### Check copied templates and configs against their source

- **Source:** [cruft](https://cruft.github.io/cruft/): "`cruft check` can be added to CI pipelines to ensure projects don't unintentionally drift."; [repo-file-sync-action](https://github.com/BetaHuhn/repo-file-sync-action) opens a PR in each target repository whose copy of a file is out of sync; [copier](https://copier.readthedocs.io/en/stable/updating/) replays template changes onto a generated project.
- **Cost:** a CI step per repository; a token that can open PRs in the target repositories.
- **Breaks when:** the sync PR is not merged; the target adapts the file and the adaptation has to be merged by hand; the sync is retired, and the copies stay (INC-166).

### One copy: reference the source instead of copying it

- **Source:** GitHub [reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) and Renovate [shared presets](https://docs.renovatebot.com/config-presets/) let repositories reference one definition; the Python packaging guide on a [single-source version](https://packaging.python.org/en/latest/discussions/single-source-version/) describes ways to keep the version in one place, and notes that "Some projects may choose to simply live with the data entry duplication, and rely on automated testing"; [syncpack](https://github.com/JamieMason/syncpack) lints a monorepo for packages that pin different versions of the same dependency.
- **Cost:** restructuring the code or config so there is one copy; migrating callers.
- **Breaks when:** a caller pins an old version of the shared source and keeps the old copy; the merged copy is left as a wrapper and grows its own logic again. In one operator's record, 4 of 6 consolidations held at their site while the next copy of the same fact diverged (as of 2026-10, private audit).

## Evidence

External evidence that agents miss copies is measured and from several independent studies. Evidence on which protection works against it is thin: none of the studies below tests a protection.

- **Incomplete changes are the main failure on multi-file refactors.** On SWE-Bench ProMax, "the dominant failure mode is _incomplete refactoring_"; gold patches touch 11.5 files on average and the best agent resolves 41.2% (as of 2026-08, [SWE-Bench ProMax](https://arxiv.org/html/2608.09802)).
- **Accuracy falls as a fix spreads.** On multi-hunk repairs, accuracy ranged from 26.98% to 92.82% across agents and fell as the hunks were further apart (as of 2025-11, [Nashid et al.](https://arxiv.org/abs/2511.11012)).
- **Redundant and partial edits are named failure categories.** A study of 150 failed issue-solving instances lists redundant re-implementation and edits to one implementer of several as subcategories; it gives no per-subcategory counts in its text (as of 2025-09, [Liu et al.](https://arxiv.org/html/2509.13941)).
- **Duplication grew in AI-heavy code.** GitClear reported an eightfold rise in code blocks with five or more duplicated lines during 2024, and fewer moved lines than copied ones, over 211 million changed lines (as of 2025-02, [DevClass report on GitClear](https://www.devclass.com/ai-ml/2025/02/20/ai-is-eroding-code-quality-states-new-in-depth-report/1626250)). That is a secondary report; the primary report was not reachable.
- **Not every study finds it.** A difference-in-differences study of Cursor adoption states that the effect on duplicate line density is insignificant, and its own table marks the same coefficient as significant (as of 2026-01, [He et al.](https://arxiv.org/html/2511.04427v3)). Read it as no clear measured effect.
- **Copied CI gates.** No external data was found on gates or workflows copied between repositories drifting apart. The rows here that show it (INC-163 to INC-167) come from one operator's repositories.
- **One operator's patches.** In a private audit of 31 incidents of this class, 10 of 11 fixes that corrected only the one copy were followed by a recurrence; 8 of 9 new checks held at their site while a sibling copy failed later; none of the 31 patches compared copies (as of 2026-10, private audit). The audit is not verifiable; its 9 private rows are in the dataset as "private, not verifiable".
