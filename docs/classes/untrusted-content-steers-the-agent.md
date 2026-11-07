---
class: untrusted-content-steers-the-agent
surfaces_at:
  - code
  - ci
  - review
  - after-merge
applies_when: You run an AI coding agent that reads text other people can write (an issue, a pull request or a comment on a public repository, a support ticket, a fetched web page, a file in a cloned repository or a dependency, the output of a tool or of an MCP (Model Context Protocol) server), and the agent holds something that text's author does not (a token, write access, a shell on your machine, secrets in a CI job); or a CI job that holds release or publish credentials can be reached by such text or by the agent.
applies_when_not: An allow or deny list that a command or a path gets past, when the user's own request chose the action (pattern-matched-boundaries). The damage an action does once it is chosen (irreversible-effects). The agent changing more than it was asked, with no outside text involved (scope-overreach).
---

# Untrusted content steers the agent

## TL;DR

An agent reads text someone else wrote, takes an instruction in it for part of its task, and carries it out with your access: it copies private data to a public place, runs a command, or, in CI, uses the job's tokens. The agent's answer to you looks normal. What protects is keeping untrusted text, private data and a way out (any channel that carries data to someone outside) from meeting in one session, and keeping release and publish credentials out of any job that untrusted text or an agent can reach.

## Symptom

Nobody on your side asked for what the agent did, and the session or the job log shows where the idea came from: a line in something the agent read. Among the forms it takes:

- an agent working on a public issue opens a pull request, or posts a comment, that carries data from a private repository or from your environment;
- a CI job that runs an agent on new issues or pull requests makes a commit, edits a label, calls an outside URL or prints a secret, and the trigger was an issue anyone could open;
- a support ticket, a web page or a dependency's README the agent was asked to summarize leads it to run a query, a command or a tool call that has nothing to do with the summary;
- the agent's own settings change after it opens a repository someone else wrote;
- a version of your package appears on the registry that you did not release, and the credential that published it was one your CI job held.

The agent's answer to you can describe only the task you gave it, so the extra action may show only in the log, the diff or the outside system.

## Examples

Each `INC-` ID is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv), which links its source and says how strong that source is. None of them comes from the maintainer's own repositories.

- INC-550: a user asked an agent connected to a code host's official MCP (Model Context Protocol) server to look at the open issues of a public repository; one issue, written by an attacker, told it to collect data from the user's private repositories, and the agent put that data in a pull request on the public repository. A researcher's proof of concept, not an attack seen in the wild.
- INC-551: a customer wrote instructions into a support ticket; when the developer's assistant, connected to the database with a role that bypasses row-level security, read the ticket, it read a private table and copied its rows into a reply the customer could see. A researcher's demonstration on dummy data.
- INC-555: CI workflows that put the title or body of an issue or pull request into an agent's prompt, in a job that also held a write token or other secrets, so that whoever opened the issue could steer the agent; the researchers found the pattern in workflows of at least five Fortune 500 companies and in the agent vendor's own repository, which was patched within four days of the report.
- INC-556: an issue-triage workflow ran an agent with shell access on every new issue from any account; an issue could make it poison the CI cache that the nightly release workflows used, and so reach their publish credentials. The maintainers removed the AI workflows after public disclosure, but a publish token was not properly revoked, and an unknown actor used it to publish an unauthorized version of the project's command-line tool to the package registry.
- INC-005: no agent was the route in. A pull request's title was echoed unsanitized into a shell step of a workflow that ran with the repository's secrets, which exposed the registry publish token; malicious versions were published under the project's name for four hours, and their install script tried to use the AI command-line tools on each victim's machine to search it for secrets.

## Mechanism

**To the model, everything in its context is text.** An instruction from you and a sentence in an issue arrive the same way, and no part of the input is marked as data only. The researchers behind INC-550 ran it on a model trained for safety and conclude that "even state-of-the-art aligned models are vulnerable to these attacks" ([Invariant Labs](https://invariantlabs.ai/blog/mcp-github-vulnerability)); the cause is in the system, not in one model.

**The agent acts with your identity, not the text's author's.** In INC-552 an assistant built into a code host ran "in the same context as the victim user" and could read the user's private projects ([Legit Security](https://www.legitsecurity.com/blog/remote-prompt-injection-in-gitlab-duo)); in INC-553 another one "operates with the same permissions as the user making the request" ([Legit Security](https://www.legitsecurity.com/blog/camoleak-critical-github-copilot-vulnerability-leaks-private-source-code)); in INC-551 the database role bypassed row-level security by design ([General Analysis](https://generalanalysis.com/blog/supabase-mcp-blog)). Whatever the text asks for is done with whatever the agent holds.

**The text does not have to be visible.** In INC-552 the researchers planted instructions in merge-request descriptions and comments, commit messages, issue descriptions and source code, and used encodings and invisible characters to hide them; every placement worked. In INC-553 the instruction sat in a hidden comment in a pull-request description, which the page and the notification do not show. A human reading the same page sees nothing to warn them. Those write-ups describe the form; this doc does not repeat the text.

**The leak needs a way out.** Reading private data harms nobody until it leaves. In INC-550 the way out was a public pull request; in INC-551 a reply the customer could read; in INC-552 and INC-553 an image link that the user's browser fetched, with the data encoded in its address. The fixes in the last two closed the way out: one vendor stopped rendering unsafe HTML tags, the other disabled image rendering in its chat.

**In CI, anyone can write the input, and the job holds the keys.** A workflow triggered by an issue or a pull request takes its title, body or comments from whoever opened it. In INC-555 those fields went straight into the agent's prompt in jobs that held a token with write access or cloud credentials; in INC-556 the workflow let any account trigger it and gave the agent a shell. The steered agent then needs no outside channel: the job's own token is the reach.

**CI credentials can publish.** This case was first planned as a class of its own; it is folded into this one because it shares the route into a CI job and the CI and Publish rungs below. The case: a job that holds release or publish credentials can be reached by untrusted input or by an agent. In INC-005 the route was a shell injection through a pull-request title, not a prompt; in INC-554 an inappropriately scoped token in a build configuration let a threat actor commit malicious code to an extension's repository, and the commit was included automatically in a release ([GHSA-7g7f-ff96-5gcw](https://github.com/aws/aws-toolkit-vscode/security/advisories/GHSA-7g7f-ff96-5gcw)); in INC-556 an agent was the route to the same kind of credential. Whoever reaches the job, the result is a release under the project's name. What that release can then do to the people who install it is the subject of [Irreversible effects](irreversible-effects.md).

**Approval can be switched off.** The assistant in INC-550 asked before each tool call by default, but, the researchers note, many users choose to always allow and stop watching individual actions. A prompt that is always allowed no longer stops anything, and a job in CI has no one to answer a prompt.

**Neighbours.** When the steered agent runs a command that an allow list was supposed to stop, the list's failure is the class [Pattern-matched boundaries](pattern-matched-boundaries.md), which also holds the case of a repository whose settings file changes the agent's permissions. This doc covers how outside text gets to choose the action; that one covers why the list did not catch it. What the action can reach once chosen is in [Irreversible effects](irreversible-effects.md).

## Where it surfaces

At code, when the developer or a researcher sees the agent's tool calls in the session: the query or the pull request that has nothing to do with the request (INC-550, INC-551). At review, when someone uses an assistant on a merge request or a pull request whose text carries the instruction (INC-552, INC-553), and the answer or the request the browser sends is where it shows. At CI, when someone reads a workflow that puts issue text into an agent's prompt next to a secret, or a job log shows an action nobody triggered (INC-555, INC-556, INC-005). After merge, when a release that carries code nobody on the team wrote reaches users (INC-554), as the unauthorized versions in INC-005 and INC-556 did. The stages are spelled as in `docs/vocabularies.json`.

## Protections

The protections form a ladder, one rung per heading, cheapest first. The first rungs make an injected instruction less likely to land, and a scanner finds the workflows that need the later ones; the middle ones take away what a landed instruction can use (the trigger, the tools, the token, the network, the secrets and the publish credentials); the last ones put a person in front of each call, or keep untrusted text, private data and a way out from meeting in one session at all. None of them replaces the ones before; the measured rates in Evidence say why the early ones cannot stand alone.

### Prompt: mark untrusted text as data, and keep it out of the instructions

- **Source:** [OWASP LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html): "Keep trusted instructions separate from untrusted data, but do not treat text labels or prompt wording as an enforcement boundary." [OpenAI, safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety): "Pass untrusted inputs through user messages to limit their influence."
- **Cost:** Tokens for the wrapper and the instruction; a change to each template where outside text enters the prompt.
- **Breaks when:** The same OWASP page: "labeling alone does not enforce that boundary". In a benchmark, delimiting untrusted text lowered the targeted attack rate and left most of it (see Evidence). In INC-555 and INC-556 the issue text went into the prompt itself, and a label around it would not have taken the token or the shell away.

### Sanitize: strip hidden content before the agent reads it

- **Source:** [claude-code-action security](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md): "The action sanitizes content by stripping HTML comments, invisible characters, markdown image alt text, hidden HTML attributes, and HTML entities". [GitHub Copilot cloud agent risks](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations): "GitHub filters hidden characters before passing user input to Copilot cloud agent".
- **Cost:** A filter step on each input; nothing per call where the hosted agent already does it.
- **Breaks when:** The instruction is in visible text: in INC-550 it was the body of an open issue, in INC-556 an issue title. The claude-code-action page adds "but new bypass techniques may emerge"; INC-552 hid instructions with encodings as well as invisible characters.

### Classifier: screen untrusted input with a prompt-injection detector

- **Source:** [Anthropic, prompt injection defenses](https://www.anthropic.com/research/prompt-injection-defenses): "We scan all untrusted content that enters the model's context window". The [OWASP cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) lists guardrail models among its defenses. The Classifier rung in [Pattern-matched boundaries](pattern-matched-boundaries.md) judges each action against the request; this one judges the input before the agent reads it.
- **Cost:** A classifier call per input; legitimate text that is flagged and held.
- **Breaks when:** The [OWASP cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html): "A guardrail LLM is itself an LLM and is itself susceptible to prompt injection", and "Screening does not stop an injection that it fails to detect". Measured evasion of deployed detectors and adaptive attacks on published defenses are in Evidence.

### Way out: do not render images or links that make the client send data

- **Source:** The fixes in INC-552 and INC-553: GitLab's patch "prevents Duo from rendering unsafe HTML tags such as <img> or <form> that point to external domains" ([Legit Security](https://www.legitsecurity.com/blog/remote-prompt-injection-in-gitlab-duo)); GitHub fixed CamoLeak "by disabling image rendering in Copilot Chat completely" ([Legit Security](https://www.legitsecurity.com/blog/camoleak-critical-github-copilot-vulnerability-leaks-private-source-code)).
- **Cost:** Plainer answers: no images or live links in the assistant's output.
- **Breaks when:** The way out is a channel the task itself uses: a public pull request in INC-550, a reply the customer reads in INC-551, the job's own write token in INC-555 and INC-556.

### Audit: scan workflows for dangerous triggers and for outside text in prompts

- **Source:** [zizmor](https://docs.zizmor.sh/audits/) audits workflows; its `dangerous-triggers` rule "Detects fundamentally dangerous GitHub Actions workflow triggers", and it has `template-injection` and `cache-poisoning` rules. Aikido [published](https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents) open rules for Opengrep, an open-source code-analysis engine, that find issue text placed into an AI prompt (INC-555).
- **Cost:** A CI step, and triage of its findings.
- **Breaks when:** The risk is in what the agent may do, not in the workflow text: a rule matches the expressions in the file, and an agent that fetches the issue with its own tools leaves no expression in the file for the rule to match. The tool list and the token's reach are the other half of INC-556, and a trigger rule only flags them where the scanner models them.

### Trigger: let only people with write access start the agent, and have a maintainer start runs on outside content

- **Source:** [claude-code-action security](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md): "The action can only be triggered by users with write access to the repository". [GitHub Copilot cloud agent risks](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations): "Comments from users without write access are never presented to the agent." [run-gemini-cli trust guidance](https://github.com/google-github-actions/run-gemini-cli/blob/main/docs/trust-guidance.md): "Prefer workflows where the PR review is kicked off intentionally by a maintainer".
- **Cost:** Outsiders cannot start the agent; a maintainer's time to start each run on their content.
- **Breaks when:** The check is switched off: the workflow in INC-556 ran claude-code-action, whose documentation calls its `allowed_non_write_users` setting "a significant security risk", and set it to every account. The same page notes: "Allowed bots are not checked for repository permissions". A maintainer who starts the run checks who starts it, not what the agent will read: an outsider's issue or pull request still carries its text into the run.

### Tools: give the agent only the tools the task needs, and no way to write where it reads

- **Source:** [Aikido, PromptPwnd](https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents) (INC-555): "Restrict the toolset available to AI agents" and "Avoid giving them the ability to write to issues or pull requests." [run-gemini-cli trust guidance](https://github.com/google-github-actions/run-gemini-cli/blob/main/docs/trust-guidance.md): "If you are processing untrusted data, you must strictly limit which tools the Gemini CLI is allowed to execute."
- **Cost:** A task that needs a missing tool fails or goes to a person.
- **Breaks when:** The task needs the tool the leak uses: an agent that triages issues has to comment on them. In INC-556 a triage agent was given a shell, which its write-up calls arbitrary code execution. In a benchmark, an agent that picked its tools for the task before reading any untrusted data still had a residual attack rate (see Evidence).

### Tokens: give the agent the least-privileged token, scoped to the repository and the job

- **Source:** [GitHub, secure use reference](https://docs.github.com/en/actions/reference/security/secure-use) recommends the "minimum required permissions" for the workflow token. [claude-code-action security](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md): "Do not use a personal access token". [Invariant Labs](https://invariantlabs.ai/blog/mcp-github-vulnerability) (INC-550) limits an agent to one repository per session. The Identity rung in [Pattern-matched boundaries](pattern-matched-boundaries.md) and the scoped-credentials Reach rung in [Irreversible effects](irreversible-effects.md) cover the rest; they are not repeated here.
- **Cost:** Declaring permissions per workflow; an app or a fine-grained token per job instead of one broad token.
- **Breaks when:** The token the task needs already reaches the data: in INC-550 the user's own token covered the private repositories, and in INC-551 the database role bypassed row-level security. In CI the token stays valid until the job ends, so a steered agent can use whatever it reaches until then. In INC-554 the token in the build configuration was inappropriately scoped.

### Isolation: turn the network off, or allow only named destinations

- **Source:** [OpenAI, agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security): "By default, the agent runs with network access turned off." [Claude Code sandboxing](https://code.claude.com/docs/en/sandboxing.md): "Effective sandboxing requires both filesystem and network isolation". The sandbox and container rungs in [Pattern-matched boundaries](pattern-matched-boundaries.md) and the sandbox Reach rung in [Irreversible effects](irreversible-effects.md) describe the setup; they are not repeated here.
- **Cost:** Setup; a task that needs the network asks for each destination.
- **Breaks when:** An allowed destination is itself a way out. Claude Code's page: "Allowing broad domains such as github.com can create paths for data exfiltration". [GitHub's agentic workflows](https://github.github.com/gh-aw/introduction/architecture/): "Domain allowlisting constrains destinations, not the safety of every request to an allowed service." In INC-550 the way out was the code host the agent was meant to use.

### CI: keep untrusted triggers away from secrets and from the release workflows

- **Source:** [GitHub Security Lab](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/): combining `pull_request_target` with a checkout of an untrusted pull request "is a dangerous practice". [GitHub, secure use reference](https://docs.github.com/en/actions/reference/security/secure-use): "Avoid using the pull_request_target and workflow_run workflow triggers with untrusted pull requests or code content", and for inline scripts an intermediate environment variable is "the preferred approach to handling untrusted input". [Adnan Khan, cache poisoning](https://adnanthekhan.com/2024/05/06/the-monsters-in-your-build-cache-github-actions-cache-poisoning/): "avoid using GitHub Actions caching entirely for release workflows".
- **Cost:** Split workflows; slower release builds without the cache.
- **Breaks when:** The environment variable stops a shell injection like the one in INC-005, not a prompt injection: the text still reaches the agent. GitHub Security Lab notes that gating a run on a label "is still prone to a race condition", since the author can push after the label. In INC-556 the agent ran with a shell in a default-branch workflow, which is the case the cache rule names: "Never run untrusted code within the context of the main branch if any other workflows use GitHub Actions caching".

### Publish: keep publish credentials out of every job that untrusted text or an agent can reach

- **Source:** [npm trusted publishers](https://docs.npmjs.com/trusted-publishers): "we strongly recommend restricting traditional token-based publishing access", with the package setting "Require two-factor authentication and disallow tokens". [GitHub, secure use reference](https://docs.github.com/en/actions/reference/security/secure-use): with OpenID Connect you can "stop storing these credentials as long-lived secrets". Trusted publishing and a required reviewer on the release environment are the Reach and Approval rungs in [Irreversible effects](irreversible-effects.md); they are not repeated here.
- **Cost:** Moving the release into its own workflow with short-lived credentials; a reviewer's time per release where one is required.
- **Breaks when:** The release job itself runs what untrusted input left behind: in INC-556 the nightly release workflows shared a cache with the triage workflow. npm: "Self-hosted runners are not currently supported". A registry that still accepts a long-lived token keeps it valid until it is revoked; in INC-556 one was not properly revoked after disclosure, and in INC-554 the token sat in the build configuration.

### Approval: have a person confirm the agent's tool calls

- **Source:** The [MCP tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools): "there SHOULD always be a human in the loop with the ability to deny tool invocations." How the prompt should name the effect, and when an approval is required at all, are the approval rungs in [Irreversible effects](irreversible-effects.md); they are not repeated here.
- **Cost:** A person's attention on each call the agent makes.
- **Breaks when:** The prompt is switched off: in INC-550 the assistant asked by default, and the researchers note that many users opt for an "Always Allow" policy and stop monitoring individual actions. In CI nobody is there to answer. A call that reads an issue or a table looks like the task, so a person approves it; it fails as the approval rungs in [Irreversible effects](irreversible-effects.md) describe.

### Architecture: split the session, so that no agent holds untrusted input, private data and a way out together

- **Source:** [Meta, Agents Rule of Two](https://ai.meta.com/blog/practical-ai-agent-security/): agents "must satisfy no more than two of the following three properties within a session". [Simon Willison, the lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) names the same three. [GitHub agentic workflows](https://github.github.com/gh-aw/introduction/architecture/): "The agent job runs with minimal read-only permissions", and "write operations are deferred to separate jobs that execute only after the agent completes". [CaMeL](https://arxiv.org/abs/2503.18813) enforces security policies when tools are called.
- **Cost:** A redesign of the workflow; a measured loss of tasks solved (see Evidence).
- **Breaks when:** Meta: "Designs that satisfy the Agents Rule of Two can still be prone to failure". An output the split permits, such as the comment a later job posts, can carry what the agent read. GitHub's agentic workflows: "A read-only GITHUB_TOKEN does not remove other credentials or privileged host access."

## Evidence

- **Defenses in a benchmark.** On AgentDojo with GPT-4o, the targeted attack success rate was 57.69% with no defense, 41.65% with delimiting, 7.95% with a prompt-injection detector (which cut utility under attack, the share of attacked tasks the agent still solved without the attacker's side effects, to 21.14%) and 6.84% with a tool filter (as of 2024-11, [Debenedetti et al., AgentDojo](https://arxiv.org/html/2406.13352v3), Table 5).
- **Detectors are evaded.** Against six protection systems, including Azure Prompt Shield and Meta's Prompt Guard, character injection and adversarial machine-learning evasion achieved "in some instances up to 100% evasion success" (as of 2025-07, [Hackett et al.](https://arxiv.org/abs/2504.11168)).
- **Adaptive attacks.** Tuned attacks "bypass 12 recent defenses (based on a diverse set of techniques) with attack success rate above 90% for most", where most of those defenses had reported near-zero rates (as of 2025-10, [Nasr et al.](https://arxiv.org/abs/2510.09023)).
- **A trained model with safeguards.** Against an adaptive attacker given 100 attempts per environment in browser use, Anthropic reports a 1% attack success rate and says it "still represents meaningful risk" (as of 2025-11, [Anthropic](https://www.anthropic.com/research/prompt-injection-defenses)).
- **The cost of a split design.** CaMeL solved 77% of AgentDojo tasks "with provable security", against 84% for an undefended system (as of 2025-06, [Debenedetti et al., CaMeL](https://arxiv.org/abs/2503.18813)).
- **This base.** Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv); the class has eight rows, all primary: vendor post-mortems, advisories and researchers' write-ups. None comes from the maintainer's own repositories. That is an absence in this base, not evidence that the class is rare.
