---
topic: base-eval-methodology
tags: area:eval, research
source_provenance: /research invocation, 2026-11-10, /grill research-pass gate for the base evaluation design
status: answered
audit: 2026-11-10 — 158 claims: 121 SUPPORTED, 32 PARTIAL, 0 UNSUPPORTED, 5 UNCHECKABLE
---

## Question

Methodology for evaluating whether a curated knowledge base helps a reader's AI coding agent find real, unguarded failure risks in the reader's own repo. Design under review (locked in /grill phase 2, 2026-11-10): within-subject, 3-5 outside readers each run arm A (README prompt pointing the agent at the base of 18 failure-class docs, pinned SHA) and arm B (same task + the 18 class names as a topic list + web search, no doc content) once each in their own repo, fresh sessions, memory off, B before A; a third session merges both reports into a shuffled unlabeled list; the reader (repo owner) groups same-risk findings and judges real / already guarded / would act; primary metric = distinct unguarded real risks A vs B; pre-registered rule: helps if A>B for all but at most one reader and median A-B>=1, does-not-help if A<=B for most (ties against A), else unclear; min 3 readers by 2026-12-20; pilot by maintainer in a clean agent config on openai/openai-agents-python, its numbers don't count. Questions: (1) evidence on whether curated context/knowledge files (AGENTS.md, rules, docs, retrieved guidance) improve coding-agent outcomes or risk-finding, and effect sizes; (2) small-n within-subject designs with owner-as-judge: order effects, carryover, judge bias, one-run-per-arm noise, tie handling; (3) blinding and vocabulary leakage when comparing two LLM reports (arm identifiable from terms/labels/URLs) and how to normalise; (4) anything in the design the literature says will make the result uninterpretable. Output: docs/research/base-eval-methodology-2026-11-10.md with findings mapped to concrete design changes.

Asked (4) "anything in the design the literature says will make the result uninterpretable", answering four named threats not covered by (1)-(3): contamination of the control arm by web search, counting findings as the outcome, cost and token budget between arms, and what to fix before the runs, because an open-ended sweep has no stopping point inside one run.

Sub-questions: Q1 does curated context or knowledge improve coding-agent outcomes, especially finding risks, and by how much; Q2 small-n within-subject design with the participant as judge: order and carryover, one run per arm, judge bias, ties and sample size; Q3 blinding the judge when two LLM reports are compared: source identifiability, style biases, normalisation, checking that blinding held; Q4 the four threats named above.

Earlier report in `docs/research/`: `doc-authoring-direction-2026-09-29.md` is about how the class docs are written, not about evaluating them; this report neither builds on nor overturns it.

## Summary

The design can run as locked, but five changes decide whether its verdict can be read at all; the rest make it cheaper to interpret.

**B is a strong control; none of the cited studies measures risk finding.** Repository context files did not measurably raise agent task success and raised cost by over 20% [C101], [C103], [C104]; a second study saw lower runtime instead, again with no success gain [C129], [C130]. The first left the security effect untested [C108]; the second reports runtime, tokens and completion [C129]. In vulnerability detection, adding the CWE description gave little or negative gain [C110], [C111], while retrieved knowledge specific to a vulnerability's cause and fix raised pair accuracy by 16-24% [C112], [C117]. A short, specific topic list — what arm B gets — gave the best result for six of seven models in security code review [C119], [C126]. Within these studies the guidance that helped was specific, but none compares specific and generic guidance head to head [C135].

**Design changes, in order of how much they decide:**

1. **Recalibrate the decision rule; it is a heuristic, and at n=3 it says "helps" too easily.** With 3-5 readers no count reaches p<0.05 except 5 of 5 [C232], [C234]. The rule's "helps" branch fires with probability 0.500 at n=3 when each reader is a coin flip for A, and 0.352 when each reader has A ahead with probability 0.4, as when a fifth of readers tie and the rest split evenly [C244]. The median clause never binds: with integer counts, "all but at most one A ahead" already forces median A−B ≥ 1 [C245]. Either require all readers A-ahead when n=3 (0.125 under a coin flip [C232]) or state the false-"helps" rate next to the verdict; keep "ties count against A" — it is stricter than the textbook convention of discarding ties [C228], [C229], [C234].
2. **Block or audit arm B's access to the base.** B's web search can reach the public base itself, turning the control into a partial treatment; one such run can erase that reader's A/B difference [C412], [C413]. Block the repo and its domain in B's search where the agent allows it [C407]; in any case log B's fetched URLs and match them against the base [C406], and report which mitigation ran [C408]. A B run that read the base is excluded by a rule written before the runs [C434], [C438].
3. **Blind the merged list against content, not only labels.** A source model stays identifiable after paraphrase to a classifier trained on paraphrased text (97.8% → 91.4%) [C303], [C311], and attributed authorship is a driver of judge bias [C339], [C340]. The merge must strip URLs, file links to the base, class names and the base's evidence labels, and normalise format [C305], [C324]; each rewritten finding is diffed against its original for claim, path and evidence before the judge sees it [C331], [C333]. An unblinded owner-judge of a subjective outcome exaggerates effects (0.23 SD for observers, 0.56 SD for self-assessing participants) [C218], [C219], though the largest meta-study found no average effect [C239], [C240] — the size is contested; the trial and HCI evidence predicts a bias toward A [C226].
4. **Check that blinding held.** Before the verdict on each finding, ask the reader which arm wrote it, with a don't-know option [C325], [C326]; asked after the verdict, a correct guess may come from quality rather than leaked style [C327], [C328].
5. **Pair the count with precision and cost.** Distinct confirmed risks is a recall-type count, which an arm wins by padding [C422]; record per arm the number of rejected and duplicate findings and the reader's triage time [C415], [C419]. Record tokens and dollar cost per run [C428], [C430]. The sources disagree on whether precision or recall matters more [C420], [C423], so the protocol fixes in advance that recall decides and precision is reported.

**Changes that cost little and close an interpretation gap:**

6. **Counterbalance the order, or state why not.** One fixed order confounds period and carryover with the A–B difference, and no analysis can separate them [C208], [C238]; varying the order lets them be estimated [C206]. Since every run is a fresh agent session with memory off, the agent carries nothing between arms; what remains is drift in the repo and in what the reader learned while launching B [C204], [C205]. Alternating AB/BA by reader costs nothing; if B-first is kept to stop A's vocabulary reaching the reader before B, write that reason into the protocol.
7. **Name one-run noise as a limit, and record what can be recorded.** Single-run agent scores swing by 2.2-6.0 points over ~500 tasks, and per-task outcomes can flip between runs [C209], [C211], [C213]; the authors call single-run evaluation unsound [C212]. One study saw small run-to-run variation in its aggregate score (SD 0.1-0.4) [C242]. Per-reader "A won" is therefore partly run noise [C217]; a second run per arm is the remedy [C214], else the protocol states the limit and records tokens per run, which vary up to 30x on one task [C429], [C430].
8. **Record length and link count per finding.** Human judges prefer longer [C335] and more assertive [C318] text, and style control after judging changed human-vote rankings [C320], [C322]; with a handful of findings regression has little power, but the covariates let the confound be inspected [C324].
9. **Write the pre-registration items into the protocol before any run:** repos and task text, the outcome definition and dedup rule, who judges and how blinded, the precision and cost measures, B's search restriction, exclusion rules, and each forecast; label the study exploratory [C431]-[C434], [C437], [C438]. The METR study's text does not mention pre-registration [C435].

## Findings

### Q1 — does curated context or knowledge improve coding-agent outcomes, especially finding risks, and by how much — answered with a gap

- **C101** [quoted] Across LLMs and agents, context files (LLM-generated or developer-committed) did not generally improve SWE task success and raised inference cost by over 20% on average — "Surprisingly, we find that providing context files does not generally improve task success rates, while increasing inference cost by over 20% on average. This observation holds across different LLMs, coding agents, and for both LLM-generated and developer-committed context files." — [S1], Abstract
- **C102** [quoted] LLM-generated context files lowered resolution by 0.5 pt (SWE-bench Lite, 300 tasks) and 2 pt (CTXbench, 138 tasks) — "Specifically, the average resolution rate is reduced by 0.5\% and 2\% on average on SWE-bench and CTXbench, respectively." — [S1], §4.2 Main Results
- **C103** [quoted] Developer-written context files gave +2.4 pt on average, not significant (p=21%), better than LLM-generated ones, and helped every agent except Claude Code — "Developer-provided context files improve agent performance by 2.4\% on average ( p=21\% ), significantly outperforming LLM-generated ones ( p=3.8\% ) (see Table 3). Despite not being agent-specific, they improve performance for all agents but Claude Code" — [S1], §4.2
- **C104** [quoted] Authors' conclusion: both effects marginal and neither statistically significant; all context files raise cost and step count — "LLM-generated context files have a marginal negative effect on task success rates, while developer-written ones provide a marginal performance gain, neither statistically significant." — [S1], §6 Conclusion
- **C105** [quoted] Mechanism: instructions in context files are followed, producing more testing and exploration, which drives the cost increase — "In a more detailed analysis of the agent traces, we observe that instructions in context files are well followed. This leads to increased exploration, testing, and reasoning by coding agents, and, as a result, increases costs by over 20%." — [S1], §1 Introduction
- **C106** [quoted] Tool mentions are followed strongly: uv used 1.6x/instance when mentioned vs <0.01 when not; repo-specific tools 2.5x vs <0.05 — "uv is used 1.6 times per instance on average when mentioned in the context files, compared to fewer than 0.01 times when it is not mentioned, and repository-specific tools are used 2.5 times per instance on average when mentioned" — [S1], §4.3
- **C107** [quoted] Repository overviews in context files did not speed up locating relevant files — "We conclude that context files are not effective at providing a repository overview." — [S1], §4.3 Context files do not provide effective overviews
- **C108** [quoted] Scope limit: Python only, task resolution only; security effect of context files explicitly left untested — "In this work, we evaluate the impact of context files on task resolution rate. However, other aspects of coding agent performance, such as code efficiency [14] and security [10], would be interesting directions for future work." — [S1], §5 Limitations
- **C109** [quoted] Baseline LLMs barely tell vulnerable code from its patched twin: pair accuracy 0.06-0.14 — "this study reveals their limitations in distinguishing between vulnerable and similar-but-benign patched code (only 0.06 - 0.14 accuracy)" — [S2], Abstract
- **C110** [quoted] Generic knowledge in the prompt (CWE descriptions) and CoT prompts gave limited gain; the CWE-enhanced prompt even lowered pair accuracy — "Even for the best case (CoT-1 for GPT-4o), its pairwise accuracy is only improved to 0.20, while others bring fewer improvements and some (CWE-enhanced) even harm the pair accuracy." — [S2], §3 empirical study, Table 2 discussion
- **C111** [quoted] The CWE-description prompt shifted most models toward calling code benign, i.e. it moved bias rather than discrimination — "The CoT-1 (explaining the code behaviors first) and CWE-enhanced (including the relevant CWE descriptions) dramatically lead most LLMs (except DeepSeek) to consider most code as benign." — [S2], §3, Unstable Bias
- **C112** [quoted] Retrieved, case-specific vulnerability knowledge (cause, trigger, fix distilled from past CVEs) raised pair accuracy 16-24% and balanced precision/recall 9-14%/7-11% — "Vul-RAG not only improves the pair accuracy of LLMs (with 16% - 24% increase) but also improves the balanced precision and recall by 9%-14% and 7%-11%." — [S2], §5.1 results
- **C113** [quoted] Distilled knowledge beat code-level RAG (retrieving similar code) by 16-27% pair accuracy — "Our ablation study shows the superiority of our knowledge-level RAG compared to existing code-level RAG based and fine-tuning based baselines, i.e., 16%-27% and 22%-26% increase in pair accuracy." — [S2], §1 contributions
- **C114** [quoted] Failure mode: in the CWE-119 bad-case sample, 10 false positives (47.6%) came from retrieving irrelevant vulnerability knowledge whose descriptions were often too general — "There are 10 (47.6%) false positives caused by Vul-RAG retrieving irrelevant vulnerability knowledge. Based on our manual inspection, these incorrectly-retrieved knowledge descriptions often generally contain “missing proper validation of specific values”, which is too general for GPT4 to precisely identify the vulnerability." — [S2], Appendix, bad-case analysis
- **C115** [quoted] Failure mode: in the CWE-119 bad-case sample, most false negatives (12 cases, 63.2%) came from missing relevant knowledge in the base — "the 12 cases (63.2 %) in this category are cased by the absence of relevant vulnerability knowledge in our knowledge base." — [S2], Appendix, bad-case analysis
- **C116** [quoted] The same knowledge raised human reviewers' detection accuracy from 60% to 77% (p=0.01) — "77% detection accuracy with knowledge v.s. 60% detection accuracy without knowledge, p = 0.01" — [S2], §5.2 RQ4
- **C117** [inference] In this study, retrieved knowledge specific to the vulnerability's cause and fix helped, while adding the relevant CWE's description did not and harmed pair accuracy; a class description alone did not recover the gain of the fuller knowledge — from [C110], [C111], [C112], [C114]
- **C118** [quoted] The prompt variants: basic; +project name; +generic 'use CWE' instruction (P_c); +specific list of top-level CWEs from VIEW-1000 (P_cid, a short topic list); CoT — "Prompt4 ( \textbf{P}_{cid} ): \textbf{P}_{b} + Specific CWE Instruction. \textbf{P}_{cid} provides a specific list of the first level CWEs in VIEW-1000 (Research Concepts)" — [S3], §2 prompt design
- **C119** [quoted] The short CWE topic list gave the best result for six of seven models (GPT-4 ChatGPT/API, GPT-4 Turbo, Gemini Pro, Llama 2 7B/70B) but an overall decline for the reasoning model DeepSeek-R1 — "Under \textbf{P}_{cid} , GPT-4 (via both ChatGPT and API), GPT-4 Turbo, Gemini Pro, Llama 2 7B and Llama 2 70B all achieved their best performance on the Python and C/C++ datasets. However, when applying \textbf{P}_{cid} to DeepSeek-R1, we observed a performance decline on the C/C++ dataset and an improvement on the Python dataset." — [S3], §3.1 RQ1.2
- **C120** [quoted] Naming specific CWE entries beat a generic instruction to use CWE; the gain was larger for general-purpose than for reasoning-optimised models — "it can be inferred that incorporating specific CWE entries into the prompt is more effective than providing a generic instruction related to CWE. Moreover, the prompting strategy of incorporating CWE information may yield a more significant performance improvement on general-purpose LLMs than on the reasoning-optimized LLM in security code review." — [S3], §3.1 RQ1.2
- **C121** [quoted] The generic 'use CWE' instruction significantly lowered DeepSeek-R1's performance on both datasets — "the performance of DeepSeek-R1 significantly decreases under \textbf{P}_{c} in both Python and C/C++ datasets" — [S3], §3.1 RQ1.2
- **C122** [quoted] Topic-list gain is coverage-dependent: R1 improved on Python, where the list included CWE-435, relevant to the dominant race-condition defects, and fell on C/C++; the authors note some high-level entries (e.g. CWE-682) do not exactly match certain security defect types — "We included solely high-level CWE entries in the CWE list and some of them, such as CWE-682 (Incorrect Calculation), do not exactly match certain security defect types" — [S3], §3.1 RQ1.2
- **C123** [quoted] Over-long lists hurt: the authors cite Bakhshandeh et al. (2023), where listing all 75 CWEs lowered detection and location accuracy, and call for a concise list — "In Bakhshandeh et al. (2023), providing a list of all 75 CWEs in their prompts decreased the accuracy of security defect detection and location by the LLMs." — [S3], §4 Discussion (secondary report of another paper, not read here)
- **C124** [quoted] Longer inputs (more tokens in the reviewed file) made defects harder to find; authors attribute it to distraction — "This is because many security defects are introduced by small code snippets, and longer inputs may distract LLMs from overlooking certain details, thereby failing to detect security defects introduced by small code snippets." — [S3], §4 Discussion
- **C125** [quoted] The persona effect was LLM-specific; the authors speculate a persona may add complexity and distract models that already understand the task — "introducing a persona could add unnecessary complexity to the prompt and lead to distractions" — [S3], §3.1 RQ1.2, P_r
- **C126** [inference] In this study a short, specific topic list (top-level CWE names) gave the best result for six of seven models and beat a generic instruction to use CWE; an exhaustive 75-CWE list hurt in the cited prior work; the reasoning model DeepSeek-R1 declined overall under the list — from [C119], [C120], [C121], [C123]
- **C127** [quoted] A security-focused prompt prefix cut vulnerabilities in generated code by up to 56% for GPT-4o/4o-mini (static-scanner measured); iterative prompting repaired 41.9-68.7% of prior vulnerabilities — "for GPT-4o and GPT-4o-mini, a security-focused prompt prefix can reduce the occurrence of security vulnerabilities by up to 56%. Additionally, all tested models demonstrated the ability to detect and repair between 41.9% and 68.7% of vulnerabilities in previously generated code when using iterative prompting techniques." — [S4], Abstract
- **C128** [quoted] The same study found that for GPT-3.5-turbo, prompt techniques for initial code generation did not reduce vulnerabilities and some increased them (model-dependent effect) — "For this model, prompt engineering techniques attempting to reduce vulnerabilities in initial code generation were unsuccessful and even produced more vulnerabilities (up to 31.1%) compared to the baseline." — [S4], HTML v1 (arxiv.org/html/2502.06039v1) §IV-A
- **C129** [quoted] Counter to C101 on cost: in a separate study (Codex, 10 repos, 124 PRs) AGENTS.md presence was associated with lower median runtime (-28.64%) and output tokens (-16.58%) with comparable completion; correlational wording, one agent — "Our results show that the presence of AGENTS$.$md is associated with a lower median runtime ($\Delta 28.64$%) and reduced output token consumption ($\Delta 16.58$%), while maintaining a comparable task completion behavior." — [S5], Abstract
- **C130** [inference] The two AGENTS.md studies disagree on cost direction but agree that task success does not measurably rise; the first explicitly left the security effect untested — from [C101], [C104], [C108], [C129]
- **C131** [quoted] Against easy gains in vuln detection: better prompts, larger models, more pre-training data and fine-tuning gave no significant improvement; SOTA reached only 54.5% balanced accuracy — "We explored prominent models and training settings to understand their effects on vulnerability detection performance -- including better prompts, larger models, more pre-training data, and fine-tuning -- but none led to significant improvements." — [S6], Abstract
- **C132** [quoted] Domain knowledge in the prompt helped some models with code semantics but not with the multi-step reasoning detection needs — "We also explored adding domain knowledge to prompts; although it helped certain models understand some code semantics, vulnerability detection requires multi-step reasoning, and these models still failed in steps, such as reasoning about variable relations." — [S6], Abstract
- **C133** [quoted] Qualifier on C127: even with relevant weaknesses to avoid named in context, frontier models still produced verifiable vulnerabilities 23% of the time (250 prompts); auditing-optimised system prompts cut that by up to 48% — "Even when frontier models are explicitly asked to write secure production code with relevant weaknesses to avoid in context, we find that they still produce verifiable vulnerabilities on average 23% of the time across a corpus of 250 benign coding prompts." — [S7], Abstract
- **C134** [quoted] SecureForge: system prompts optimised against observed failures reduced output vulnerabilities by up to 48% without losing unit-test success — "On frontier models, SecureForge yields a statistically significant Pareto improvement in both unit test success and output security, with output vulnerabilities reduced by up to 48%." — [S7], Abstract
- **C135** [inference] Within the cited studies, the guidance that helped was specific (retrieved CVE knowledge, specific CWE entries, prompts optimised on observed failures), while generic forms (repo overviews, the CWE description, a generic CWE instruction for DeepSeek-R1) and the exhaustive 75-CWE list did not help or hurt; no study compares specific and generic guidance head to head on one task — from [C107], [C110], [C112], [C120], [C121], [C123], [C125], [C134]

### Q2 — small-n within-subject design with the participant as judge — answered with a gap

- **C201** [quoted] In SE crossover experiments each subject gets all treatments and different subjects get them in different orders; this is what defines a crossover. — "In these, subjects apply more than one treatment in different orders." — [S8], Frattini, Fucci, Vegas (ESEM 2024), Introduction
- **C202** [quoted] The SE crossover literature names maturation/exhaustion as a threat: later observations differ because of learning or fatigue. — "(1) Maturation/exhaustion: Participants may perform better or worse in subsequent observations due to a learning or exhaustion effect." — [S8], Section 2, threats per Vegas et al. 2016
- **C203** [quoted] It also names optimal sequence as a threat: some treatment orders favour one treatment. — "(2) Optimal sequence: Some sequences in which the treatments are administered may be favorable over others." — [S8], Section 2
- **C204** [quoted] It names carryover: the first treatment's effect persists into the later period. — "(3) Carryover : The effect of an administered treatment might carry over to a subsequent period." — [S8], Section 2
- **C205** [quoted] In SE a washout period is usually not feasible, because participants cannot unlearn what the first treatment taught them. — "In SE research, a washout period is often not feasible since it would require participants to unlearn techniques or tools they were subjected to" — [S8], Section 2
- **C206** [quoted] Varying the order (sequence) separates these threats from the treatment effect but does not remove them; they still have to be modelled in the analysis. — "de-confounds the threats from the effect of the treatment, but the effect still applies to the response variable and needs to be modeled when analyzing the data." — [S8], Section 2
- **C207** [quoted] Even in published SE crossover experiments carryover is rarely handled: modelled in about 3% of cases. — "the carryover threat is only modeled in about 3% of the observed cases." — [S8], Abstract
- **C208** [inference] With every participant running B before A, there is one sequence only: period, maturation, optimal-sequence and carryover effects are fully confounded with the A-vs-B difference, and no analysis of the data can separate them (an AB/BA design at least lets them be estimated). — from [C201], [C202], [C203], [C204], [C206]
- **C209** [quoted] Ten repeated runs of six agent configurations on SWE-Bench-Verified: single-run pass@1 varied by 2.2 to 6.0 points across all twelve configurations, i.e. over ~500 tasks, not per task. — "Across all twelve configurations in the table, the ranges span 2.2 to 6.0 percentage points, representing substantial variability where a single run could report performance anywhere within this window." — [S9], Bjarnason, Silva, Monperrus, On Randomness in Agentic Evals, Sec. results
- **C210** [quoted] The variance persists at temperature 0, from inference-engine and environment nondeterminism. — "This variance persists across all configurations, including theoretically deterministic settings (temperature 0), where non-determinism from inference engines and environments still clearly produces measurable variance." — [S9], Introduction
- **C211** [quoted] Repeated agent runs diverge within the first few percent of tokens and end in different solution strategies. — "runs diverge early, often within the first few percent of tokens, and these initial differences cascade into fundamentally different solution strategies" — [S9], Introduction
- **C212** [quoted] The authors call single-run evaluation methodologically unsound. — "However, single-run evaluation is methodologically unsound for several reasons." — [S9], Introduction
- **C213** [quoted] The gap between solving a task at least once in 5 runs and the single-run rate reaches 24.9 points, so per-task outcomes depend heavily on stochastic exploration. — "the maximum improvement from pass@1 to pass@5 is 24.9 percentage points" — [S9], Sec. pass@k and pass^k
- **C214** [quoted] They recommend multiple independent runs per task and a power analysis to set the number of runs. — "(1) estimate pass@1 from multiple independent runs per task, especially when measuring small improvements, (2) use statistical power analysis to determine the number of runs needed to detect expected effect sizes" — [S9], Implications
- **C215** [quoted] A 10-task x 5-run SWE-bench study (Claude 4.5 Sonnet, GPT-5, Llama-3.1-70B) reports coefficients of variation of 15.2%, 32.2% and 47.0%, with higher consistency aligned with higher accuracy (58%, 32%, 4%). — "Claude achieves the lowest variance (CV: 15.2%) and highest accuracy (58%), GPT-5 is intermediate (CV: 32.2%, accuracy: 32%), and Llama shows the highest variance (CV: 47.0%) with lowest accuracy (4%)" — [S10], v1 Abstract
- **C216** [quoted] AgentLens: five repeats of one configuration, 16 of 32 scenario points flaky; variance concentrates in a few borderline tasks. — "15 passed formal verification in all five runs, one failed in all five, and the remaining 16 were flaky." — [S11], PDF, scenario-level results (Figure 2 discussion)
- **C217** [inference] With one run per condition per participant, each A-vs-B comparison is one draw from each condition's distribution; per C211 and C213 a single run's outcome on one task can flip between runs, so a per-participant "A won" is confounded with run noise, and no within-participant variance estimate exists to tell them apart. — from [C209], [C211], [C213], [C214]
- **C218** [quoted] Meta-research on clinical trials: non-blinded observers assessing subjective outcomes exaggerate effect sizes by a standardized mean difference of about 0.23 on average. — "On average, nonblinded observers in randomized clinical trials with subjective outcomes exaggerate effect sizes by –0.23 (–0.40 to –0.06)." — [S12], Hróbjartsson et al., Int J Epidemiol 2014;43(4):1272, Introduction (citing their CMAJ 2013 review)
- **C219** [quoted] When the assessor is the participant who received the intervention (patient-reported outcome), lack of blinding exaggerated effects by 0.56 SD on average, with wide variation. — "In 12 trials (3869 patients) with patient-reported outcomes, nonblinded patients exaggerated the standardized mean difference by an average of 0.56 standard deviation, but with considerable variation." — [S12], Abstract, Results
- **C220** [quoted] For a true moderate effect that bias more than doubles the estimate. — "In trials with a true moderate effect size of –0.5, nonblinded patients thus cause an exaggeration of the estimated effect by 112%." — [S12], Abstract
- **C221** [quoted] Caveat: all 12 main trials were complementary/alternative medicine, mostly acupuncture, and the bias was smaller in the two non-acupuncture trials, so the 0.56 figure may not transfer. — "All 12 main trials (3869 patients) investigated complementary/alternative interventions, predominantly acupuncture" — [S12], Results
- **C222** [quoted] Across seven meta-epidemiological studies, trials that were not double-blind exaggerated odds ratios by 13% on average, and by 22% for subjective outcomes. — "An overview of seven meta-epidemiological studies reported an average 13% exaggeration of odds ratios in trials not double-blind, and a 22% exaggeration when outcomes were subjective." — [S12], Discussion
- **C223** [quoted] HCI (Dell et al., CHI 2012): participants were about 2.5x more likely to prefer an artifact they believed the interviewer made, even when the alternative was identical. — "respondents are about 2.5x more likely to prefer a technological artifact they believe to be developed by the interviewer, even when the alternative is identical" — [S13], abstract
- **C224** [quoted] In the same study, university students showed a 2:1 response bias on identical videos. — "Identical videos: 2:1 response bias" — [S14], CHI 2012 talk slides, slides 29-30
- **C225** [quoted] One of the authors' mitigations is to dissociate the investigator from a particular design. — "Dissociate from a particular design or solution" — [S14], slide 39
- **C226** [inference] The design's judge is both the participant and an unblinded assessor of a subjective outcome; if A is the evaluator's own proposal and the judge can tell or guess which findings came from A, the trial and HCI evidence predicts a bias toward A. — from [C218], [C219], [C222], [C224], [C225]
- **C227** [prior] Standard remedy in trials: blind the assessor (here: strip source labels and shuffle the merged findings) and check blinding success by asking the assessor to guess the allocation (Bang/James blinding indexes); unblinding through recognisable output style is common. — not fetched in this run
- **C228** [quoted] The standard paired sign test discards tied pairs and tests the count of positive differences among the m untied pairs against Binomial(m, 0.5); this is the version in an R package built for SE experiments (reproducer). — "under the null hypothesis the number of positive differences among the non-tied pairs follows a Binomial(m, 0.5) distribution (equivalently, the shift algorithm of pairedRankTest applied with all absolute differences set to one). Tied pairs are discarded." — [S15], Description
- **C229** [quoted] statsmodels does the same: values equal to the null median are discarded, and the test is undefined when every value is a tie. — "Values equal to mu0 are discarded." — [S16], Notes
- **C230** [snippet] Coakley and Heise (Biometrics 1996) review the many procedures proposed for ties in the sign test and recommend an asymptotic UMP test, which gives zeros partial weight rather than discarding them or counting them against. — "The asymptotic uniformly most powerful (UMP) test performs very well for almost all settings considered, even when the sample size is small." — [S17], search snippet
- **C231** [snippet] A 2003 American Statistician paper reports that ignoring ties in the sign test can substantially inflate the Type I error rate (for the median test where ties are informative). — "ignorance of ties—that is, zero differences—in the sign test can substantially inflate the Type I error rate" — [S18], search snippet
- **C232** [measured] Exact one-sided sign test minima: with all n participants favouring A, p = 0.125 (n=3), 0.0625 (n=4), 0.03125 (n=5); only n=5 with 5 of 5 favouring A and no ties reaches p<0.05. — Own measurements, M1 (q2src/signp.py)
- **C233** [measured] Power of a unanimity rule (all n favour A, ties count against A): if each participant independently favours A with p=0.7, the rule passes with probability 0.343 (n=3), 0.240 (n=4), 0.168 (n=5); at p=0.9, 0.729 / 0.656 / 0.590. — Own measurements, M1 (q2src/signp.py)
- **C234** [inference] Counting ties against A is stricter than the textbook convention of discarding them (C228, C229): it keeps the false-pass rate at or below the untied binomial rate but lowers power further; with 3-5 participants no count can reach conventional significance except 5 of 5, so the rule is a pre-registered decision heuristic, not a significance test. — from [C228], [C229], [C232], [C233]
- **C235** [quoted] Single-case methodology (WWC): a two-phase AB design supports causal inference poorly because it lacks replication. — "It is difficult to draw valid causal inferences from traditional two-phase AB designs because the lack of replication in such designs makes it more difficult to rule out alternative explanations for the observed effect" — [S19], WWC Single-case designs technical documentation v1.0, AB designs
- **C236** [quoted] Repeating the same AB order across several independent cases does not fix this, unlike a multiple-baseline design that staggers the intervention in time. — "Furthermore, repeating an AB design across several cases in separate or independent studies would typically not allow for drawing valid inferences from the data" — [S19], AB designs
- **C237** [quoted] The WWC standard asks for three demonstrations of the effect, and says the number three is a conceptual norm, not a derived bound. — "Currently, there is no formal basis for the \"three demonstrations\" recommendation; rather, it represents a conceptual norm" — [S19], Replication criterion (Horner et al. 2005)
- **C238** [inference] Each participant's B-then-A pair is a one-replication AB comparison; 3-5 such pairs in the same order are, by C236, repeated AB designs rather than a design with experimental control, unless the order or timing varies. — from [C208], [C235], [C236]
- **C239** [quoted] Counter to C218: MetaBLIND (1153 trials, 142 meta-analyses) found no average exaggeration from non-blinded outcome assessors, ratio of odds ratios 1.01 for subjective observer-reported outcomes. — "was 1.01 (0.86 to 1.18) in 46 meta-analyses with subjective observer reported outcomes, with no clear impact of degree of subjectivity." — [S20], Moustgaard et al., BMJ 2020, Results
- **C240** [quoted] Its authors read the null as possibly a method artefact and keep blinding as a safeguard. — "These results could reflect that blinding is less important than often believed or meta-epidemiological" — [S20], Conclusion
- **C241** [quoted] A 2023 GRADE-based review (Wang, Guyatt et al.) found overestimation when outcome assessors of subjective outcomes are not blinded (ROR 0.69, 0.51-0.93, high certainty). — "lack of blinding of outcome assessors results in effect overestimation for subjective outcomes (ROR 0.69, 95% CI 0.51 to 0.93; high certainty)" — [S21], forum post quoting the review's abstract (not the review itself)
- **C242** [quoted] Counter to C217: a five-run study of coding agents on non-functional improvements found small run-to-run variation in aggregate improvement (SD 0.1-0.4 over five runs) for Codex, Claude Code and three Aider configurations. — "Codex, Claude Code Agent, and the three Aider configurations exhibit relatively small run-to-run variation in aggregate NFI improvement" — [S22], PDF, RQ on repeated runs (Table 5 discussion)
- **C243** [quoted] A build-agent benchmark reports 53.0% +/- 6.8 over three repeated runs (GPT-4o), attributed to retrieval trajectories differing between runs and LLM non-determinism compounding over turns. — "OSS-Build-Agent achieves 53.0% ± 6.8 strict and 57.6% ± 6.5 flexible validated success, indicating non-trivial variance" — [S23], PDF, repeated-runs results (Table 2 discussion)
- **C244** [measured] Pass probability of the design's own rule (A ahead for all readers but at most one; ties and B-ahead count against A), each reader independently A-ahead with probability w: w=0.5 gives 0.500 (n=3), 0.312 (n=4), 0.188 (n=5); w=0.7 gives 0.784 / 0.652 / 0.528; w=0.3 gives 0.216 / 0.084 / 0.031 — Own measurements, M2
- **C245** [measured] With integer counts of risks, every pattern in which A is ahead for all readers but at most one (n = 3, 4, 5) already has median A−B of at least 1, so the rule's median clause never changes the verdict — Own measurements, M2

### Q3 — blinding the judge when two LLM reports are compared — answered

- **C301** [quoted] A fine-tuned text-embedding classifier names which of five chat LLMs wrote a response with 97.1% held-out accuracy (chance 20%); within one model family (4 Qwen-2.5 sizes) it reaches 59.8%. — "a model can achieve 97.1% classification accuracy on the held-out validation data, compared to a 20.0% chance-level guess. Within the same model family, we obtain a non-trivial 59.8% accuracy across 4 model sizes" — [S24], Sun et al., Idiosyncrasies in LLMs, §1 Introduction
- **C302** [quoted] The source signal sits largely in word-level distribution: shuffling words (after stripping punctuation and markdown) lowers classifier accuracy only slightly. — "We find that randomly shuffling words in LLM-generated responses leads to only a slight decrease in classification accuracy. This suggests that a substantial portion of distinctive features is encoded in the word-level distribution." — [S24], §1 Introduction (findings list); Table 8
- **C303** [quoted] Rewriting by a separate LLM does not remove identifiability for a classifier trained on the rewritten responses: paraphrased or translated outputs stay near original accuracy (chat: 97.8 original, 91.4 paraphrased, 91.8 translated); only one-paragraph summarising drops it to 58.1, still well above the 20% chance. — "Paraphrasing or translating LLM outputs achieves an accuracy comparable to that using original counterparts. However, summarizing these texts makes the model less capable of predicting LLM identities." — [S24], §3.3 Semantics Rewriting, Table 10
- **C304** [quoted] The authors read the survival under paraphrase as the signal being in semantic content, not only in wording. — "These findings suggest that the semantic meanings of words play a more significant role in predicting LLM origins than the exact word choice." — [S24], §3.3 Semantics Rewriting
- **C305** [quoted] Markdown formatting is itself a moderate source signal that post-training adds. — "We also observe that markdown formatting contributes to a moderate degree of idiosyncrasies in the LLMs following post-training." — [S24], §1 Introduction (findings list)
- **C306** [inference] Caveat for transfer: C301–C305 measure a trained classifier on thousands of labelled samples, not a human reading a merged list once; they bound what is detectable in principle, not what a human judge actually detects. — from [C301], [C303]
- **C307** [quoted] In a blinded pairwise human-vote setup (Chatbot Arena hides which model answered), an attacker can still tell which model wrote a reply with more than 95% accuracy. — "an attacker can determine which model was used to generate a given reply with more than $95\%$ accuracy" — [S25], Huang et al., Exploring and Mitigating Adversarial Manipulation of Voting-Based Leaderboards, abstract
- **C308** [quoted] Counter-weight to C307: simple statistical identifiers (e.g. TF-IDF) are said to be easily mitigated by style normalisation and to fail on closely related models. — "these methods are easily mitigated by defenses like style normalization and often fail to distinguish closely related models" — [S26], InterPol (2026), §1 Introduction
- **C309** [quoted] Same paper, opposite direction: LM Arena's length/style normalisation removes only surface statistics; a stronger detector still identifies models under these defences, even GPT-4o vs GPT-4o-mini. — "even under these defenses, models can still be reliably identified even for closely related models ( e.g. , GPT-4o vs. GPT-4o-mini)" — [S26], §2 Related work, Defender strategies and limitations
- **C310** [quoted] Practice: LM Arena deploys length/style normalisation and sentiment control to reduce superficial identity cues. — "LM Arena employs techniques such as length/style normalization and sentiment control to diminish superficial cues of model identity" — [S26], §2 Related work (secondary report of LM Arena practice)
- **C311** [inference] Normalising text (style, length) lowers cheap surface identifiability but does not by itself make two systems' outputs indistinguishable; a stronger detector still separates them, and for a classifier trained on rewritten text paraphrase-level rewriting keeps most of the signal. — from [C303], [C308], [C309]
- **C312** [quoted] LLM auto-annotators keep a preference for longer outputs; AlpacaEval, though highly correlated with human preferences, is known to favour longer outputs. — "Even simple, known confounders such as preference for longer outputs remain in existing automated evaluation metrics." — [S27], Dubois et al., Length-Controlled AlpacaEval (COLM 2024), abstract
- **C313** [quoted] Length control is done after judging, by regression: fit a GLM of the judge's preference on length difference plus other features, then predict with length difference set to zero. — "we first fit a generalized linear model to predict the biased auto-annotator's preferences based on the mediators we want to control for (length difference) and other relevant features. We then obtain length-controlled preferences by predicting preferences while conditioning the GLM with a zero difference in lengths." — [S27], abstract
- **C314** [quoted] Length control made the metric more robust to verbosity manipulation and raised its Spearman correlation with Chatbot Arena from 0.94 to 0.98. — "it increases the Spearman correlation with LMSYS Chatbot Arena from 0.94 to 0.98" — [S27], abstract
- **C315** [quoted] LLM-as-a-judge has position, verbosity and self-enhancement biases (named and studied in the MT-Bench / Chatbot Arena paper). — "We examine the usage and limitations of LLM-as-a-judge, including position, verbosity, and self-enhancement biases, as well as limited reasoning ability, and propose solutions to mitigate some of them." — [S28], Zheng et al., Judging LLM-as-a-Judge (NeurIPS 2023 D&B), abstract
- **C316** [quoted] Self-preference: an LLM judge scores its own outputs higher than others' where humans rate them equal; out of the box GPT-4 and Llama 2 recognise their own outputs at non-trivial accuracy, and self-recognition strength correlates linearly with self-preference after fine-tuning. — "By fine-tuning LLMs, we discover a linear correlation between self-recognition capability and the strength of self-preference bias" — [S29], Panickssery et al., LLM Evaluators Recognize and Favor Their Own Generations, abstract
- **C317** [inference] For an LLM merger or LLM judge from the same family as one arm, self-preference is a live risk: its strength correlates with recognising the source, so it is partly a blinding failure, not only a scoring one. — from [C316], [C301]
- **C318** [quoted] Human judges are not immune: output assertiveness skews how many factuality errors human annotators perceive. — "We find that the assertiveness of an output skews the perceived rate of factuality errors, indicating that human annotations are not a fully reliable evaluation metric or training objective." — [S30], Hosking et al., Human Feedback is not Gold Standard (ICLR 2024), abstract
- **C319** [inference] Transfer to the two-arm setup: if one arm's findings sound more assertive (e.g. knowledge-base labels), a human judge may perceive fewer errors in them independent of correctness — the style confound acts even with perfect source blinding; LLM auto-annotators add a length preference. — from [C312], [C318]
- **C320** [quoted] Human-vote practice (Chatbot Arena): style is controlled after the votes, by adding length and markdown counts as covariates in the Bradley-Terry regression. — "We explicitly model style as an independent variable in our Bradley-Terry regression. For example, we added length as a feature" — [S31], LMSYS, Does style matter? (Aug 2024), Methodology
- **C321** [quoted] In human votes, length was the dominant style factor; markdown effects (lists, headers, bold) were second order. — "we found that length was the dominant style factor. All other markdown effects are second order." — [S31], Methodology / Style Control Ablation
- **C322** [quoted] Controlling for length and markdown changed the human-vote ranking (e.g. gpt-4o-mini moved from 4th to 7th–11th depending on the control). — "We controlled for the effect of length and markdown, and indeed, the ranking changed ." — [S31], introduction; ranking-shift table
- **C323** [quoted] Counter to style control: it is observational, and length can be positively correlated with substantive quality (e.g. a chain-of-thought explanation), so controlling length can also remove real quality signal. — "There are possible unobserved confounders such as positive correlation between length and substantive quality that are not accounted for by our study." — [S31], Limitations and Future Work
- **C324** [inference] Two normalisation routes exist: before judging (rewrite/strip so the judge never sees the cue — limited by C303, C309) and after judging (record the cue — length, link count, labels — and regress it out, C313, C320 — limited by C323). With few findings and one human judge, the after-route has little statistical power; recording the covariates still lets the confound be inspected. — from [C303], [C309], [C313], [C320], [C323]
- **C325** [quoted] Clinical-trial practice: blinding success is checked by asking blinded people to guess their allocation, optionally with a certainty rating; two quantitative indices exist (James' BI, Bang's BI). — "The two statistical methods, James' blinding index (BI) and Bang's BI, are currently available. Subjects could be asked to guess their treatment assignment, possibly with an option to express the degree of certainty." — [S32], Kolahi, Bang, Park, Towards a proposal for assessment of blinding success in clinical trials: up-to-date review, abstract
- **C326** [quoted] James' BI weights "do not know" answers highest and assumes such an answer is honest, not an avoidance of judgement — so the guess form must make an informed guess safe to give. — "An important assumption in the construction of James' BI is that when a respondent says that she or he does not know the treatment identity this represents an honest response, not just a socially desirable response or one that avoids making a judgement." — [S32], section on James' BI
- **C327** [quoted] Counter to guess-based checks: an end-of-trial guess may test a hunch from the observed effect rather than a blinding failure — the guesser infers the arm from the outcome. — "Some researchers believe that end-of-trial tests of blindness might actually be tests of hunches for efficacy or side effects rather than the success of blinding." — [S32], Timing
- **C328** [inference] Transfer: asking the human judge, per finding, "which arm wrote this?" (with a don't-know option and certainty) measures leakage; but a judge who guesses "the better findings are arm A" is guessing from quality, the analogue of C327 — so a correct guess is not on its own proof that style leaked. — from [C325], [C326], [C327]
- **C329** [quoted] Counter to C303: paraphrasing by a separate model does defeat detectors that were not trained on paraphrases — DIPPER drops DetectGPT's detection accuracy from 70.3% to 4.6% at 1% FPR, reportedly without changing meaning. Note the task differs (AI-vs-human detection with zero-shot detectors, 2023), while C303's classifier was trained on the paraphrased text. — "DIPPER drops detection accuracy of DetectGPT from 70.3% to 4.6% (at a constant false positive rate of 1%), without appreciably modifying the input semantics." — [S33], Krishna et al., Paraphrasing evades detectors of AI-generated text (NeurIPS 2023), abstract
- **C330** [inference] Reconciling C303 and C329: whether rewriting hides the source depends on whether the detector was trained on rewritten text — paraphrase defeats a detector not trained on it, not one that learned the rewritten distribution. — from [C303], [C304], [C329]
- **C331** [quoted] Counter on whether an LLM rewrite preserves content: a study that used GPT-4o for meaning-preserving rewrites (paraphrase, simplification, compression) states it cannot confirm, without human annotation, that every edit kept factual correctness. — "without human annotations, we cannot confirm with full certainty that all edits preserve factual correctness in every case. This may introduce noise into the interpretation of metric behavior" — [S34], Mujahid, Wright, Augenstein, Stress Testing Factual Consistency Metrics for Long-Document Summarization, Limitations
- **C332** [quoted] Same paper (v2 only; the passage is not in the v1 HTML): contradiction rates stayed low across most rewrite types, i.e. paraphrase and simplification generally preserved factual consistency. — "Across most perturbations, contradiction rates remain low, indicating that paraphrasing, simplification, vocabulary reduction, summarization, and source text insertion generally preserve factual consistency with respect to the original summaries." — [S35], v2 PDF, results on perturbation contradiction rates
- **C333** [inference] A normalising rewrite of findings is itself an unreviewed transformation: it mostly keeps facts (C332) but is not guaranteed to (C331), and the summarising rewrite that hides the source best (C303) is the one that drops the most detail. A diff of each rewritten finding against its original — at least the claim, file path and evidence — is needed before the judge sees it. — from [C303], [C331], [C332]
- **C334** [quoted] Counter to treating length as pure bias: length moves LLM-judge win rates through information mass (more content), separable from length-independent desirability (correctness, consistency); the proposed fix compares responses within equal length intervals (AdapAlpaca). — "found that response length impacts evaluations by influencing information mass" — [S36], Hu et al., Explaining Length Bias in LLM-Based Preference Evaluations, abstract
- **C335** [quoted] Humans show a length preference too, smaller than LLM judges' (Polyrating: 41 rating points for human judges vs 48 for LLM-based judges). — "length bias gaining 41 and 48 rating points for human and LLM-based judges respectively" — [S37], PDF, bias results
- **C336** [quoted] Polyrating's stated aim is to detect and quantify biases in human preferences, i.e. the after-judging covariate route applies to human ratings, not only LLM judges. — "Polyrating can detect and quantify biases affecting human preferences, ensuring fairer model comparisons." — [S38], Dekoninck, Baader, Vechev, Polyrating, abstract
- **C337** [prior] Pairwise vs pointwise: Zheng et al. compare pairwise comparison with single-answer grading; pairwise is more sensitive but exposes position bias (they mitigate by swapping order), pointwise grading is more stable but coarser. Not fetched in this run beyond the abstract (C315). — not fetched in this run
- **C338** [quoted] Counter to C316: the usual self-preference measure conflates bias with response quality — a stronger judge's own answers may simply be better. — "this approach conflates self-preference bias with response quality, as higher-quality responses from the judge model may also lead to positive score differences, even in the absence of bias" — [S39], Chen et al., Beyond the Surface: Measuring Self-Preference in LLM Judgments (EMNLP 2025), abstract
- **C339** [quoted] Under blind evaluation, LLM-judge self-preference disappears (a small opposite effect remains once quality and judge severity are controlled) — but self/other labels alone, without naming any model, shift scores both ways: attributed authorship is a distinct driver of the bias. — "Under blind evaluation, self-preference disappears, with a small effect remaining in the opposite direction once selection quality and judge severity are controlled. Under matched quality, however, self- and other-labels alone -- without naming any model -- shift scores bidirectionally." — [S40], Self- and Other-Labels Induce Bidirectional Bias in LLM Judges (EMNLP Findings 2026), abstract (v3)
- **C340** [inference] For the two-arm design this supports blinding as a lever: the bias acts partly through knowing (or inferring) authorship, so removing arm labels matters, and any residual cue that lets the judge attribute a finding to "the base arm" can reintroduce it — for a human judge invested in the base, the analogue of a self-label. — from [C316], [C318], [C339]

### Q4 — contamination, counting, cost, pre-registration — answered

- **C401** [quoted] Search-based agents retrieve evaluation datasets with answers from the open web during the evaluation itself; Scale AI names this search-time contamination (STC) — "We identify an analogous issue—search-time contamination (STC)—in evaluating search-based LLM agents which use tools to gather information from online sources when answering user queries." — [S41], Abstract
- **C402** [quoted] STC is defined by the retrieval step surfacing clues derived from the evaluation set itself — "Search-Time Contamination (STC) occurs in evaluating search-based LLM agents when the retrieval step contains clues about a question’s answer by virtue of being derived from the evaluation set itself." — [S41], 1 Introduction, Definition 1
- **C403** [quoted] Measured rate: about 3% of questions on HLE/SimpleQA/GPQA had ground truth found on HuggingFace; blocking HuggingFace dropped accuracy on that subset by about 15% — "for approximately 3% of questions, search-based agents directly find the datasets with ground truth labels on HuggingFace. … After HuggingFace is blocked, we observe a drop in accuracy on the contaminated subset of approximately 15%." — [S41], Abstract
- **C404** [quoted] Agents state in their reasoning that they found the question-answer pairs, so trajectories can be audited for contamination — "agents often explicitly acknowledge discovering question-answer pairs from HuggingFace within their reasoning chains" — [S41], Abstract
- **C405** [quoted] Blocking one site is not enough: other sources also contaminate — "publicly accessible evaluation datasets on HuggingFace may not be the sole source of STC" — [S41], Abstract
- **C406** [quoted] Detection method used: log every retrieved source and substring-match it against the evaluation material — "We log all retrieved sources and perform a simple HuggingFace contamination check based on substring matching." — [S41], 3.1 Measuring Search-Time Contamination
- **C407** [quoted] Mitigation 1: source filters on search that block the evaluation material before retrieval — "Implementing a comprehensive set of filters — similar to those used by the Perplexity API — can effectively control source sites during search operations, proactively preventing STC before it occurs." — [S41], Recommendations, Multiple search filters
- **C408** [quoted] Mitigation 2: report the mitigation used next to the result — "recommend that agent developers report their adopted mitigation strategies alongside their final performance results" — [S41], Conclusion
- **C409** [quoted] Counter-observation: Claude, Gemini and OpenAI agents with their own search tools almost never retrieved a HuggingFace link; contamination depends on the search tool — "We also experimented with Claude, Gemini, and OpenAI agents with their respective web search tools, but found they almost never retrieved a HuggingFace link" — [S41], 3.1
- **C410** [quoted] A second study defines three severity levels of STC, the mildest being leakage of benchmark metadata alone — "We define three contamination types with increasing severity, namely Benchmark Metadata Leakage, Question-Context Leakage, and Explicit Answer Leakage" — [S42], Abstract
- **C411** [quoted] Its recommended mitigations: isolated sandboxes, transparent search trajectories, controlled benchmark access — "we find that STC is widespread and can inflate performance by up to 4%. Our findings show that existing evaluations may overestimate true reasoning ability. We therefore advocate contamination-aware practices, including isolated sandboxes, transparent search trajectories, and controlled benchmark access." — [S42], Abstract
- **C412** [inference] For this A/B: arm B with open web search can reach the public base itself, which turns the control into a partial treatment arm (dilution, not inflation of A); measurable by logging B's fetched URLs and matching them to the base's repo and text, and preventable by a domain/repo block in B's search tool — from [C402], [C405], [C406], [C407]
- **C413** [inference] The benchmark-QA contamination rate (about 3% of questions) does not transfer to this setting: there the leak is a single answer, here the leaked artefact (the base) is the whole treatment, so even one B run that reads it can erase the A/B difference for that run — from [C403], [C410], [C412]
- **C414** [prior] Pretraining contamination: a base published after the model's training cutoff cannot be in its weights, but the public incidents and failure classes it draws on may be; the class-name topic list in arm B already transfers part of the treatment — not fetched in this run
- **C415** [quoted] A production LLM code-review system (ByteDance) chose precision over recall because numerous comments get ignored, like alert fatigue — "First, similar to alert fatigue, developers tend to ignore review comments entirely when faced with numerous comments, as they are unwilling to invest time in careful discrimination." — [S43], 4 Evaluation Metrics, Prioritizing Precision in Code Review Practice
- **C416** [quoted] Same source: early inaccurate comments damage trust, so they prioritised precision — "Second, inaccurate comments in the early stages significantly damage user trust, hindering continuous iteration and improvement of the system. These practical challenges lead us to prioritize precision over recall in our approach." — [S43], 4 Evaluation Metrics
- **C417** [quoted] Recall is hard to measure: ground truth on all defects needs heavy human effort and many defects surface only later — "Regarding recall, a fundamental challenge lies in the substantial human effort required for comprehensive issue detection." — [S43], 4 Evaluation Metrics
- **C418** [quoted] Technically correct comments can still lack value; correctness alone is a weak measure — "low practicality of comments that are technically correct but fail to provide substantial value" — [S43], 1 Introduction
- **C419** [quoted] They added an adoption-based measure (share of flagged lines later changed) because precision via manual labels does not show whether developers act — "The introduction of an Outdated Rate metric that addresses two key limitations of traditional precision measurements: the sustainability of manual evaluation and the ability to assess user acceptance of review comments." — [S43], 1 Introduction, contributions
- **C420** [quoted] Counter: security tooling defaults favour recall, on the argument that false positives get triaged while false negatives get exploited — "false positives get triaged, false negatives get exploited" — [S44], page text (curl grep)
- **C421** [quoted] Counter (vendor blog): benchmarks that measure only coverage understate the cost of using a tool in practice — "Benchmarks that measure only coverage systematically understate the cost of using a tool in practice." — [S45], page text (curl)
- **C422** [inference] A raw count of owner-confirmed risks is a recall-type measure; it needs a paired precision-type measure (count of rejected or duplicate findings, and owner time spent triaging) or an arm that pads its list wins on count while costing the owner more — from [C415], [C417], [C419], [C421]
- **C423** [inference] The counting threat is not settled by literature on which of precision or recall matters: the sources disagree by context (review noise vs missed vulnerabilities), so the evaluation must fix in advance which it values — from [C416], [C420]
- **C424** [quoted] Agent evaluations must be cost-controlled; otherwise costly agents win by spending — "Therefore, agent evaluations must be cost-controlled; otherwise it will encourage researchers to develop extremely costly agents just to claim they topped the leaderboard." — [S46], 1 Introduction
- **C425** [quoted] Score can rise by meaningless means such as retrying, so accuracy alone does not show progress — "Accuracy alone cannot identify progress because it can be improved by scientifically meaningless methods such as retrying." — [S46], 2.2
- **C426** [quoted] Repeated calls and majority voting raise accuracy, i.e. more spend buys score — "Calling language models repeatedly and taking a majority vote can lead to non-trivial increases in accuracy across benchmarks like GSM-8K, MATH, Chess, and MMLU" — [S46], 2.1 Maximizing accuracy can lead to unbounded cost
- **C427** [quoted] Mitigation: report results as a Pareto curve of accuracy against inference cost — "Visualizing evaluation results as a Pareto curve of accuracy and inference cost opens up a new space of agent design: jointly optimizing the two metrics." — [S46], 1 Introduction
- **C428** [quoted] Measure dollar cost, not a proxy — "We argue that downstream evaluation should account for dollar costs, rather than proxies for cost such as the number of model parameters." — [S46], 1 Introduction
- **C429** [quoted] Counter: on SWE-bench Verified, more tokens did not mean more accuracy; runs on one task vary up to 30x in tokens and accuracy peaks at intermediate cost — "runs on the same task can differ by up to 30x in total tokens, and higher token usage does not translate into higher accuracy; instead, accuracy often peaks at intermediate cost and saturates at higher costs" — [S47], Abstract
- **C430** [inference] Token budget is a confound in both directions: arm A's base text adds input tokens and may raise or not raise findings; since per-run token spend varies up to 30x on its own, a single run per arm cannot separate the base's effect from run-to-run variance; record tokens and dollar cost per run and compare at matched budget or report both axes — from [C424], [C427], [C429]
- **C431** [quoted] METR's RCT on AI tools for developers fixed tasks before randomizing them to arms, to avoid the treatment changing the task — "Crucially, the tasks are defined before they are randomized, limiting the impact of effects from AI assistance unrelated to productivity" — [S48], 1 Introduction, footnote 1
- **C432** [quoted] It used a fixed outcome measure defined on pre-randomization tasks — "Using a fixed outcome measure (speedup on tasks defined before randomized treatment assignment)" — [S48], page text (grep)
- **C433** [quoted] It collected developers' forecasts before randomization, giving a stated expectation to compare against — "Before tasks are randomized, developers forecast that allowing AI will reduce completion time by 24%." — [S48], Abstract
- **C434** [quoted] Screen recordings let it verify compliance; for the labelled-recording analysis it filtered out issues with cheating, broken recordings (>10%) or time discrepancy (>20%) — "we filter to remove issues where we find cheating, issues where the screen recording is broken for >10% of recording time, and issues with a >20% discrepancy between self-reported time and the recording time" — [S48], 2 Methods
- **C435** [measured] The METR paper text (v2 HTML) contains no occurrence of "regist" — Own measurements, M3
- **C436** [quoted] Pre-registration has been proposed for predictive ML because of data-dependent decisions and test-data reuse, with a lightweight template — "challenges such as overlooked contextual factors, data-dependent decision-making, and unintentional re-use of test data have raised questions about the integrity of results" — [S49], Abstract
- **C437** [quoted] Counter: preregistration may bias research toward confirmatory work and must allow reclassification as exploratory — "b) preregistration may bias NLP toward confirmatory research; c) preregistration must allow for reclassification of research as exploratory" — [S50], Abstract
- **C438** [inference] What to fix in advance for this A/B, from the practice above: the repo(s) and task text before arm assignment, the outcome definition (what counts as a distinct real unguarded risk, dedup rule, who judges, blind to arm), the paired precision and cost measures, B's search restrictions, exclusion rules, and the predicted direction with a stated expectation; label the study exploratory if n is one repo — from [C431], [C432], [C433], [C434], [C437], [C422], [C412]

## Disconfirming evidence

- [C101], [C104] — query: `AGENTS.md files improve coding agent efficiency runtime tokens empirical study 2026` — counter on cost [C129]: lower runtime and tokens with comparable completion; no study found showing a success-rate gain from context files.
- [C112], [C117] — query: `Steenhoek To Err is Machine vulnerability detection LLM prompt CWE information results` — [C131], [C132]: domain knowledge in prompts gave no significant gain on SVEN.
- [C119], [C126] — the same paper holds its own counter ([C119] DeepSeek-R1 decline, [C121], [C123] 75-CWE list hurt); [C131] also against. No independent replication of the topic-list gain found.
- [C127] — query: `secure code generation security prompt still vulnerable no improvement study 2025 2026 SecureForge system prompt` — [C133]: 23% residual vulnerabilities with weaknesses named in context; [C128]: no reduction, some increase, on GPT-3.5.
- [C208], [C238] — query: `single-case AB design fixed order threats history maturation replication` — confirmed, not countered ([C235]-[C237]); no source found defending one fixed order for a two-condition comparison.
- [C217] — query: `LLM coding agent outputs consistent across repeated runs low variance single run sufficient` — partial counter [C242] (small variation in an aggregate score); [C215]: variance differs by model. Per-task variance on a private codebase is measured nowhere found.
- [C218], [C219], [C226] — query: `MetaBLIND no evidence lack of blinding outcome assessors exaggerated` — real counter [C239], [C240]; [C241] and [C221] qualify both directions.
- [C234] — query: `sign test ties conservative Coakley Heise` — [C230], [C231]: the literature prefers giving ties partial weight; counting them against A is the strict end (no source states it for this rule).
- [C303] — query: `paraphrasing evades AI-generated text detection` — [C329]: paraphrase defeats detectors not trained on it; reconciled in [C330].
- [C333] — query: `LLM rewriting does not preserve meaning` — [C331], [C332].
- [C319], [C335] — query: `human evaluators do not prefer longer responses` — [C334]: length carries information mass; no study found with zero human length bias.
- [C316] — query: `self-preference not observed` — [C338], [C339].
- [C325], [C328] — no separate search; the source's own timing section is the counter [C327].
- [C320], [C324] — no separate search; the source's own limitations are the counter [C323].
- [C412] — query: `search-time contamination negligible performance inflation` — nothing calling it negligible; [C410], [C411] confirm; counter [C409]: some vendors' search tools rarely hit the leaking site.
- [C422] — query: `security vulnerability detection recall more important than precision` — counter [C420], [C421].
- [C430] — query: `agent accuracy does not improve with more tokens` — counter [C429]: more tokens need not buy accuracy.
- [C438] — query: `critique preregistration exploratory research small studies` — counter [C437].
- [C244], [C245], [C232], [C233] — measured; no search needed.

## Coverage

| Channel | Read | Gap |
|---|---|---|
| Users | | Q1: secondary practitioner reports on agent security review (a Semgrep-linked 14% TP figure, Checkmarx anecdotes) found but not read; none isolates added context. Q2-Q4: no practitioner thread relevant to design methodology |
| Specialists | [S15], [S16], [S19], [S31], [S43], [S44], [S45] | no source on SE experimenter bias when a researcher evaluates their own tool |
| Data | [S1]-[S12], [S20], [S22]-[S30], [S32]-[S42], [S46]-[S50] | no study on LLM evaluations that use the repo owner as judge; none measures whether added context makes an agent emit more findings (padding) |
| Adversarial | [S6], [S20], [S33], [S41], [S42] | |

Declared overruns of the ceiling (four searches, three full reads per sub-question): Q1 four abstract-only curl reads beyond the full reads; Q2 six searches (two over: one to locate the variance paper's arXiv ID, one for HCI demand characteristics); Q3 five searches and five full reads; Q4 four full reads (one over: BitsAI-CR was the only primary source on the counting outcome). Disconfirming searches are not counted. No connector was used; built-in search and fetch plus `curl` throughout.

## Own measurements

### M1 — exact sign-test minima and power of a unanimity rule

Command: `python q2src/signp.py`
Output:
```
n=3: min one-sided p (all 3 favour A) = 0.1250
   P(all 3 favour A | p=0.7) = 0.343
   P(all 3 favour A | p=0.9) = 0.729
n=4: min one-sided p (all 4 favour A) = 0.0625
   P(all 4 favour A | p=0.7) = 0.240
   P(all 4 favour A | p=0.9) = 0.656
n=5: min one-sided p (all 5 favour A) = 0.0312
   P(all 5 favour A | p=0.7) = 0.168
   P(all 5 favour A | p=0.9) = 0.590
```
(rows for p=0.6 and 0.8 trimmed)

### M2 — the design's own rule: pass probability and the median clause

Command: `python rulep.py` — (a) P(at least n−1 of n readers have A ahead) for per-reader probability w; (b) every integer vector of A−B in [−5, 5]^n that passes "all but at most one A ahead", checked for median < 1.
Output:
```
(a) w=0.3: n=3: 0.216  n=4: 0.084  n=5: 0.031
(a) w=0.4: n=3: 0.352  n=4: 0.179  n=5: 0.087
(a) w=0.5: n=3: 0.500  n=4: 0.312  n=5: 0.188
(a) w=0.7: n=3: 0.784  n=4: 0.652  n=5: 0.528
(b) n=3: 575 vectors pass the majority clause, median<1 in 0
(b) n=4: 3625 vectors pass the majority clause, median<1 in 0
(b) n=5: 21875 vectors pass the majority clause, median<1 in 0
```

### M3 — does the METR paper call itself pre-registered?

Command: `grep -ci "regist" q4pages/metr.txt` on the text of https://arxiv.org/html/2507.09089v2 (155,417 bytes)
Output: `0`

## Open questions

- Q1 — no source found — whether failure-class documents in an agent's context change how many real, unguarded risks it finds in a real repository; the studies found measure task success, cost or benchmark vulnerability detection. This study's pilot and reader runs are the first measurement; a direct study on risk finding would settle it.
- Q2 — sources conflict — the size of the bias from an unblinded assessor of a subjective outcome (a substantial exaggeration in two meta-analyses vs no average effect in the largest one) is unresolved; the design does not depend on it if the merged list is blinded and the blinding check of change 4 shows the reader could not tell the arms apart.
- Q2 — no new information — per-reader, per-task run-to-run variance of a risk-finding run on a private codebase; the pilot could settle it by running each arm twice on one repo and counting how many confirmed risks differ.
- Q3 — not searched — whether a human judge (not a trained classifier) can tell the two arms apart after stripping and normalising; the blinding check in change 4 measures it in this study.
- Q4 — no source found — whether added context makes an agent emit more findings (padding); precision and length per arm (changes 5 and 8) record it here.
- Q2 — no source found — SE studies of experimenter bias when a researcher evaluates their own tool with outside participants.

## Sources

- [S1] Evaluating AGENTS.md / context files for coding agents (Gloaguen et al.) — https://arxiv.org/html/2602.11988v3 — passage
- [S2] Vul-RAG: knowledge-level RAG for vulnerability detection (Du et al.) — https://arxiv.org/html/2406.11147v3 — passage
- [S3] Security code review by LLMs (Yu et al.) — https://arxiv.org/html/2401.16310v6 — passage
- [S4] Prompting techniques for secure code generation (Bruni et al.) — https://arxiv.org/abs/2502.06039v1 — passage
- [S5] AGENTS.md and agent efficiency (Lulla et al.) — https://arxiv.org/abs/2601.20404v1 — passage
- [S6] To Err is Machine: vulnerability detection with LLMs (Steenhoek et al.) — https://arxiv.org/abs/2403.17218v2 — passage
- [S7] SecureForge — https://arxiv.org/abs/2605.08382v1 — passage
- [S8] Crossover designs in software engineering experiments — https://arxiv.org/html/2408.07594v2 — passage
- [S9] Run-to-run variance of coding agents on SWE-bench Verified — https://arxiv.org/html/2602.07150v2 — passage
- [S10] Repeated-run variance study, SWE-bench Verified — https://arxiv.org/abs/2603.25764v1 — passage
- [S11] AgentLens — https://arxiv.org/pdf/2607.06624 — passage
- [S12] Bias from unblinded patient-reported and observer outcomes (meta-research) — https://pmc.ncbi.nlm.nih.gov/articles/PMC4258786/ — passage
- [S13] Dell et al., 'Yours is better!' (CHI 2012), abstract page — https://www.microsoft.com/en-us/research/?p=162695 — passage
- [S14] Dell et al., CHI 2012 slides — https://billthies.net/assets/pdf/responsebias-chi12-slides.pdf — passage
- [S15] reproducer::pairedSignTest documentation — https://www.rdocumentation.org/packages/reproducer/versions/0.7.0/topics/pairedSignTest — passage
- [S16] statsmodels sign_test documentation — https://www.statsmodels.org/dev/generated/statsmodels.stats.descriptivestats.sign_test.html — passage
- [S17] Coakley and Heise, ties in the sign test (Biometrics 1996), record — https://portal.mardi4nfdi.de/wiki/Item:Q4335579 — snippet only
- [S18] Ties in the sign test (American Statistician 2003), record — https://www.scilit.net/publications/94d00c47fb5a08f00b5e7c750d9ddf8f — snippet only
- [S19] WWC single-case design technical documentation — https://ies.ed.gov/ncee/WWC/Docs/ReferenceResources/wwc_scd.pdf — passage
- [S20] MetaBLIND study — https://pmc.ncbi.nlm.nih.gov/articles/PMC7190062/ — passage
- [S21] Forum post on Wang, Guyatt et al. 2023 — https://www.s4me.info/threads/%E2%80%A6-overestimation-of-effects-in-randomized-trials-that-fail-to-optimize-randomization-and-blind-patients-and-outcome-assessors-wang-guyatt-2023.36085 — passage
- [S22] Five-run study of coding agents on non-functional improvements — https://arxiv.org/abs/2607.27409 — passage
- [S23] Build-agent benchmark — https://arxiv.org/pdf/2509.25248 — passage
- [S24] Idiosyncrasies in large language models — https://arxiv.org/html/2502.12150v2 — passage
- [S25] Chatbot Arena identity attack — https://arxiv.org/abs/2501.07493 — passage
- [S26] Model identification under arena defences — https://arxiv.org/html/2603.15220v1 — passage
- [S27] Length-controlled AlpacaEval — https://arxiv.org/abs/2404.04475v2 — passage
- [S28] Judging LLM-as-a-judge with MT-Bench and Chatbot Arena — https://arxiv.org/abs/2306.05685v4 — passage
- [S29] LLM evaluators recognise and favour their own generations — https://arxiv.org/abs/2404.13076v1 — passage
- [S30] Human feedback is not gold standard — https://arxiv.org/abs/2309.16349v2 — passage
- [S31] LMSYS: Does style matter? (style control) — https://www.lmsys.org/blog/2024-08-28-style-control — passage
- [S32] Assessment of blinding in clinical trials — https://pmc.ncbi.nlm.nih.gov/articles/PMC3044082/ — passage
- [S33] Paraphrasing evades detectors of AI-generated text (DIPPER) — https://arxiv.org/abs/2303.13408v2 — passage
- [S34] Meaning-preserving LLM rewrites study (HTML) — https://arxiv.org/html/2511.07689v1 — passage
- [S35] Meaning-preserving LLM rewrites study (PDF) — https://arxiv.org/pdf/2511.07689v2 — passage
- [S36] Length bias decomposition (AdapAlpaca) — https://arxiv.org/abs/2407.01085v4 — passage
- [S37] Polyrating (PDF) — https://arxiv.org/pdf/2409.00696 — passage
- [S38] Polyrating (abstract) — https://arxiv.org/abs/2409.00696 — passage
- [S39] Self-preference conflated with quality — https://arxiv.org/abs/2506.02592v1 — passage
- [S40] Blind evaluation of LLM-judge self-preference — https://arxiv.org/abs/2608.18091 — passage
- [S41] Search-time contamination (Scale AI) — https://arxiv.org/html/2508.13180v1 — passage
- [S42] Search-time contamination severity levels — https://arxiv.org/abs/2606.05241v1 — passage
- [S43] BitsAI-CR: LLM code review at ByteDance — https://arxiv.org/html/2501.15134v1 — passage
- [S44] Appen security benchmark — https://www.appen.com/research/appens-security-benchmark — passage
- [S45] Nethermind: AuditAgent on EVMbench — https://www.nethermind.io/blog/auditagent-on-evmbench-what-the-data-shows — passage
- [S46] AI Agents That Matter — https://arxiv.org/html/2407.01502v1 — passage
- [S47] Token use vs accuracy on SWE-bench Verified — https://arxiv.org/abs/2604.22750v2 — passage
- [S48] METR: early-2025 AI and experienced open-source developer productivity — https://arxiv.org/html/2507.09089v2 — passage
- [S49] Pre-registration for predictive ML — https://arxiv.org/abs/2311.18807v1 — passage
- [S50] Preregistration critique — https://arxiv.org/abs/2302.10086v1 — passage

## Audit

| Claim | Verdict | Note |
|---|---|---|
| C101 | SUPPORTED | |
| C102 | SUPPORTED | script NOT FOUND: quote copies the LaTeX source of inline math; found in the HTML with math alttext kept |
| C103 | SUPPORTED | script NOT FOUND: quote copies the LaTeX source of inline math; found in the HTML with math alttext kept |
| C104 | SUPPORTED | cost and step-count clause checked in §6, outside the quote |
| C105 | SUPPORTED | |
| C106 | SUPPORTED | '<0.05' for repo-specific tools checked in the words after the quote |
| C107 | SUPPORTED | |
| C108 | SUPPORTED | 'Python only' checked in §5; quote differs from page only in citation spacing; script NOT FOUND for that spacing, found by hand in the HTML |
| C109 | SUPPORTED | |
| C110 | SUPPORTED | |
| C111 | SUPPORTED | 'moved bias' gloss matches the section heading 'Unstable Bias' |
| C112 | SUPPORTED | |
| C113 | SUPPORTED | |
| C114 | PARTIAL | result of a CWE-119 bad-case sample stated as general; condition and count added |
| C115 | PARTIAL | condition (CWE-119 bad-case sample, 12 of 19) added |
| C116 | SUPPORTED | script NOT FOUND: found in the curl'd HTML after stripping tags (text split across inline markup) |
| C117 | PARTIAL | source says the CWE description harmed pair accuracy; 'topic list did not recover the gain' went beyond C110-C114; narrowed to the class description |
| C118 | SUPPORTED | prompt list checked in §2; script NOT FOUND: quote copies the LaTeX source of inline math; found in the HTML with math alttext kept |
| C119 | SUPPORTED | seven models checked; R1 overall decline checked in the next sentence; script NOT FOUND: quote copies the LaTeX source of inline math; found in the HTML with math alttext kept |
| C120 | SUPPORTED | |
| C121 | SUPPORTED | script NOT FOUND: quote copies the LaTeX source of inline math; found in the HTML with math alttext kept |
| C122 | PARTIAL | source says some entries 'do not exactly match certain' defect types, not that they did not match the defects; Python gain tied to CWE-435 |
| C123 | SUPPORTED | call for a concise list checked; secondary report of Bakhshandeh et al. |
| C124 | SUPPORTED | RQ3 token-count finding checked in the preceding sentence |
| C125 | PARTIAL | 'project info gave small changes' not in quote; source speculates ('could'); rewritten to the persona effect |
| C126 | PARTIAL | 'generic instructions did not recover gains' contradicted for most models (all others improved under P_c); rewritten |
| C127 | SUPPORTED | |
| C128 | PARTIAL | snippet; passage found in HTML v1 §IV-A and relabelled quoted; source says prompting was unsuccessful and raised vulnerabilities up to 31.1%, not 'little effect'; read at arxiv.org/html/2502.06039v1 (cited abs page carries the abstract only) |
| C129 | SUPPORTED | Codex, 10 repos, 124 PRs checked in §3.1.1 |
| C130 | PARTIAL | 'neither measured bug finding' not in the claims it names; narrowed to S1 leaving security untested |
| C131 | PARTIAL | 'added domain knowledge' is not in the no-improvement list of the quote (it is in C132); removed |
| C132 | SUPPORTED | |
| C133 | SUPPORTED | 48% checked in the same abstract |
| C134 | SUPPORTED | |
| C135 | PARTIAL | 'helps most / least' ranking goes beyond the claims; narrowed to what the cited studies show and that none compares head to head; persona dropped (C125 is speculation) |
| C201 | SUPPORTED | |
| C202 | SUPPORTED | |
| C203 | SUPPORTED | |
| C204 | SUPPORTED | |
| C205 | SUPPORTED | |
| C206 | SUPPORTED | |
| C207 | SUPPORTED | |
| C208 | SUPPORTED | |
| C209 | SUPPORTED | setup (ten runs, six configurations, twelve in the table) checked |
| C210 | SUPPORTED | |
| C211 | SUPPORTED | |
| C212 | SUPPORTED | |
| C213 | SUPPORTED | |
| C214 | SUPPORTED | |
| C215 | PARTIAL | snippet; unversioned URL now serves v3 ('Confident and Wrong', 50 tasks) which lacks the figures; v1 abstract has them; relabelled quoted with the v1 passage, S10 set to v1; 'mini-SWE-agent', 'Verified' and 'low variance can mean consistently wrong' not in v1 abstract, dropped |
| C216 | SUPPORTED | snippet; passage found in the PDF (pdftotext), relabelled quoted; five runs of one configuration checked |
| C217 | SUPPORTED | |
| C218 | SUPPORTED | place is Discussion ('Other studies'), not Introduction |
| C219 | SUPPORTED | |
| C220 | SUPPORTED | |
| C221 | SUPPORTED | smaller bias in the two non-acupuncture trials checked in the abstract |
| C222 | SUPPORTED | |
| C223 | SUPPORTED | snippet; quote found verbatim on the S13 page, relabelled quoted |
| C224 | PARTIAL | 'order-of-magnitude on a degraded video, i.e. preferred even when worse' not in the quoted slide; narrowed to the 2:1 bias on identical videos |
| C225 | PARTIAL | slide's first point is awareness of response bias; 'first mitigation' changed to 'one of' |
| C226 | PARTIAL | 'of a size comparable to the effect' not supported by the named claims; dropped |
| C227 | UNCHECKABLE | prior |
| C228 | SUPPORTED | |
| C229 | SUPPORTED | 'undefined when every value is a tie' checked next to the quote |
| C230 | UNCHECKABLE | S17 is a record page with no abstract; paper on JSTOR, not read |
| C231 | UNCHECKABLE | S18 returned Access Denied |
| C232 | SUPPORTED | |
| C233 | SUPPORTED | binomial arithmetic re-derived |
| C234 | SUPPORTED | |
| C235 | SUPPORTED | |
| C236 | SUPPORTED | multiple-baseline contrast checked in the same paragraph |
| C237 | SUPPORTED | |
| C238 | SUPPORTED | |
| C239 | SUPPORTED | 142 meta-analyses / 1153 trials checked |
| C240 | SUPPORTED | 'blinding should remain a safeguard' checked in the same conclusion |
| C241 | SUPPORTED | snippet; passage found on the S21 forum page, which quotes the review's abstract; relabelled quoted; the review itself not read |
| C242 | PARTIAL | snippet; passage found in the PDF, relabelled quoted; 'because performance was consistently limited' is said of the Mini-SWE configurations, not these; dropped; script NOT FOUND on the abs page, passage read in the PDF (pdftotext) |
| C243 | PARTIAL | snippet; passage found in the PDF, relabelled quoted; source names two causes (retrieval trajectories and LLM non-determinism), claim named one |
| C244 | SUPPORTED | |
| C245 | SUPPORTED | M2 output re-derived by hand |
| C301 | SUPPORTED | |
| C302 | SUPPORTED | punctuation and markdown stripping checked in §3.1 |
| C303 | PARTIAL | classifier was trained on the rewritten responses; that condition added |
| C304 | PARTIAL | 'so a style-normalising rewrite leaves content-level differences that still reveal the source' is the author's extension; dropped |
| C305 | SUPPORTED | |
| C306 | SUPPORTED | |
| C307 | SUPPORTED | |
| C308 | SUPPORTED | |
| C309 | SUPPORTED | |
| C310 | SUPPORTED | |
| C311 | PARTIAL | C303 holds for a classifier trained on rewritten text, C309 for a stronger detector; 'determined or trained reader' narrowed |
| C312 | SUPPORTED | AlpacaEval favouring longer outputs checked in the abstract |
| C313 | SUPPORTED | |
| C314 | SUPPORTED | |
| C315 | SUPPORTED | |
| C316 | SUPPORTED | equal human ratings and out-of-the-box recognition checked in the abstract |
| C317 | PARTIAL | source reports a correlation; 'runs through recognising the source' narrowed to correlates |
| C318 | SUPPORTED | |
| C319 | PARTIAL | C312 is about LLM auto-annotators, not humans, and no claim covers URLs; narrowed to assertiveness for humans |
| C320 | SUPPORTED | |
| C321 | SUPPORTED | |
| C322 | SUPPORTED | gpt-4o-mini 4th to 7th-11th checked in the ranking table |
| C323 | SUPPORTED | |
| C324 | SUPPORTED | |
| C325 | SUPPORTED | |
| C326 | SUPPORTED | tail paraphrases the source's next sentence |
| C327 | SUPPORTED | |
| C328 | PARTIAL | 'asking before the verdict … separates the two' not in the named claims; dropped |
| C329 | SUPPORTED | |
| C330 | PARTIAL | human-judge transfer not supported by the named claims; narrowed to the detector being trained on rewritten text or not |
| C331 | SUPPORTED | |
| C332 | PARTIAL | snippet; passage found only in the v2 PDF (v1 HTML lacks it); relabelled quoted, S35 set to v2 |
| C333 | SUPPORTED | |
| C334 | SUPPORTED | equal-length-interval comparison checked in the abstract |
| C335 | PARTIAL | snippet; Polyrating figures found in the PDF, relabelled quoted; MTalk-Bench figures unread and 'no study found that humans have no length preference' dropped |
| C336 | SUPPORTED | |
| C337 | UNCHECKABLE | prior |
| C338 | SUPPORTED | |
| C339 | PARTIAL | source: 'small effect remaining in the opposite direction', and authorship labels are a driver, not 'what drives'; 'fingerprint-free items' framing dropped |
| C340 | PARTIAL | 'the main lever' goes beyond the named claims; 'a lever' |
| C401 | SUPPORTED | |
| C402 | SUPPORTED | script NOT FOUND: found in the curl'd HTML after stripping tags (text split across inline markup) |
| C403 | PARTIAL | quote joined two non-adjacent abstract sentences; ellipsis inserted |
| C404 | SUPPORTED | |
| C405 | SUPPORTED | |
| C406 | SUPPORTED | |
| C407 | SUPPORTED | |
| C408 | SUPPORTED | |
| C409 | SUPPORTED | |
| C410 | SUPPORTED | |
| C411 | SUPPORTED | |
| C412 | SUPPORTED | |
| C413 | PARTIAL | '3-4%' mixed C411's 4% inflation (not a rate) into the contamination rate; narrowed to about 3% of questions |
| C414 | UNCHECKABLE | prior |
| C415 | SUPPORTED | |
| C416 | SUPPORTED | |
| C417 | SUPPORTED | |
| C418 | SUPPORTED | |
| C419 | SUPPORTED | Outdated Rate definition checked |
| C420 | SUPPORTED | |
| C421 | PARTIAL | snippet not on the page; page has a passage on coverage-only benchmarks understating cost; relabelled quoted with it, 'precision measures cost' dropped |
| C422 | SUPPORTED | |
| C423 | SUPPORTED | |
| C424 | SUPPORTED | |
| C425 | SUPPORTED | |
| C426 | SUPPORTED | |
| C427 | SUPPORTED | |
| C428 | SUPPORTED | |
| C429 | SUPPORTED | |
| C430 | SUPPORTED | |
| C431 | SUPPORTED | |
| C432 | SUPPORTED | |
| C433 | SUPPORTED | |
| C434 | PARTIAL | 'pre-stated' not in the source; the filter is for the labelled-recording analysis; rewritten |
| C435 | PARTIAL | M3 shows no 'regist' in the v2 HTML; 'rests on secondary summaries only' is not in the output; dropped |
| C436 | SUPPORTED | |
| C437 | SUPPORTED | |
| C438 | SUPPORTED | |

Label verdict: answered — the Summary gives the design changes the question asked for, every claim it rests on is SUPPORTED or repaired, and resolving the Q1 and Q2 gaps unfavourably leaves the changes standing (the Q1 effect forecast was cut; blinding is recommended whatever the bias size).
Quote check: Quote check base-eval-methodology-2026-11-10.md: 124 quoted claim(s): 105 found, 10 NOT FOUND, 9 unfetchable, 0 no source

## Disposition

| Recommendation | State | Where |
|---|---|---|
| Recalibrate the decision rule; it is a heuristic, and at n=3 it says "helps" too easily | deferred | Osasuwu/ai-dev-failure-classes#333 — decided in the protocol after the design's Phase 3 critic |
| Block or audit arm B's access to the base | deferred | Osasuwu/ai-dev-failure-classes#333 |
| Blind the merged list against content, not only labels | deferred | Osasuwu/ai-dev-failure-classes#333 |
| Check that blinding held | deferred | Osasuwu/ai-dev-failure-classes#333 |
| Pair the count with precision and cost | deferred | Osasuwu/ai-dev-failure-classes#333 |
| Counterbalance the order, or state why not | deferred | Osasuwu/ai-dev-failure-classes#333 |
| Name one-run noise as a limit, and record what can be recorded | deferred | Osasuwu/ai-dev-failure-classes#333 |
| Record length and link count per finding | deferred | Osasuwu/ai-dev-failure-classes#333 |
| Write the pre-registration items into the protocol before any run | deferred | Osasuwu/ai-dev-failure-classes#333 |
