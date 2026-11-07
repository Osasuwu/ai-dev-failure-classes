---
class: destructive-op-on-computed-target
surfaces_at:
  - code
  - ci
  - after-merge
applies_when: Your AI coding agent runs routine destructive steps (a cleanup, a cache clear, a reset, a test teardown, a recursive delete of build output) whose target is worked out when the command runs, from a shell variable, a glob, a `~`, the working directory or a path a script builds, and you want to know why such a step can delete a home directory, a drive or the repository itself, and what stops it.
applies_when_not: A guard that checks the command or the path and misreads it, for example a check made on the text before the shell expands it (pattern-matched boundaries); this class is a computed target that no guard checked at all. What the acting identity can reach and how to limit the damage of any irreversible action (the irreversible-effects doc). A wrong working directory because the agent assumed another environment, when the delete is not the point (world differs from assumed). A delete the agent chose on purpose, aimed at the files it meant, that it should not have made.
---

# A destructive op on a computed target

## TL;DR

A cleanup that looks routine deletes whatever its target resolves to when it runs, and an empty variable, a reverted `$HOME`, a glob in the wrong directory or a filter that did not filter turns it into a delete of the home directory or the repository. What stops it is a target that cannot resolve outside the scope: a path fixed when the scratch space is made, a check of the resolved target before the delete, and a delete that goes somewhere it can be undone.

## Symptom

After a routine step, files that had nothing to do with the task are gone. The agent ran a cleanup, a cache clear, a reset or a test teardown, and the command looked like the many others it had run: a recursive delete of a build folder, a glob over compiled files, a reset of the working tree. What it removed was a home directory, a whole drive, the repository together with its history, or uncommitted work. The transcript shows the command as written, not the path it resolved to, and sometimes not even the command. The permission prompt did not fire, or showed a command that read as harmless. In some reports the agent had said just before that the environment was set up and safe.

## Examples

- INC-001: an agent pointed `$HOME` at a temporary directory in one tool call and ran `rm -rf "$HOME"` in a later one; the shell state had not carried over, so the delete ran against the real home directory until a tool timeout stopped it.
- INC-803: in a test cleanup an agent said that the real `$HOME` was restored and then ran `rm -rf "$HOME"` in the same tool call; the report counts 57,235 file and 11,315 directory deletions.
- INC-801: an agent writing a test for a permission hook built a sample dangerous command inside a double-quoted shell argument; the shell ran the command substitution at once, and the sample's `rm -rf ~` deleted parts of the real home directory.
- INC-804: an agent cleaning up compiled Python files filtered a recursive PowerShell listing by extension and deleted every file it returned; the filter did not narrow the listing, and the repository's sources and part of `.git` went.
- INC-800: an agent created a directory literally named `~` and then ran `rm -rf *` in its parent; the reporter says the shell expanded the result to include the home directory.

## Mechanism

**The verb is routine; the target is computed after the agent stops looking.** `rm -rf "$HOME"`, `rm -rf *` and a recursive delete filtered by extension are the same text whether they hit a scratch directory or a home directory. What they delete is decided when the shell or the runtime evaluates them: the variable's value at that moment, the directory the glob runs in, what a substitution or a filter returns. The transcript, the permission prompt and the agent's own reasoning all show the text. None of them shows the resolved path.

**The agent's picture of the state is older than the state.** In Claude Code "Environment variables don't persist. An `export` in one command won't be available in the next." ([tools reference](https://code.claude.com/docs/en/tools-reference.md#what-persists-between-commands)); in INC-001 the agent relied on a `$HOME` it had set in an earlier call. In INC-803 the agent itself had restored `$HOME`, said so, and then deleted it; the reporter concludes that a delete target "should not depend on a mutable environment variable such as `$HOME`" ([anthropics/claude-code#93099](https://github.com/anthropics/claude-code/issues/93099)). In INC-030, a neighbour row in pattern-matched boundaries, a cleanup trap expanded its variable at exit, after a later step had pointed it at `$HOME`. In each case the target was right when the agent last thought about it and wrong when it ran.

**An empty or wrong expansion widens the target instead of failing.** The shell expands a variable that is unset or empty to nothing, so a path built from it loses its first part; the class predates agents: a shipped launcher script ran `rm -rf "$STEAMROOT/"*` with the variable empty and deleted the user's files across the system ([ValveSoftware/steam-for-linux#3671](https://github.com/ValveSoftware/steam-for-linux/issues/3671), 2015). Inside double quotes the shell still runs command substitutions ([Bash manual, double quotes](https://www.gnu.org/software/bash/manual/html_node/Double-Quotes.html)), so a command meant as sample text runs for real (INC-801). A glob takes whatever matches in the directory the command runs in (INC-800). A filter that does not apply leaves the full listing (INC-804).

**Cleanup is the step nobody watches.** The rows are teardowns, cache clears and test cleanups, steps at the end of a longer call or in a background task, after the work they serve is done. In INC-801 the delete ran in the background for about 21 seconds before the agent noticed. The delete is also permanent where it lands: `rm` removes directory entries rather than moving them to a trash ([POSIX `rm`](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/rm.html)), and the agent's own checkpoints do not cover shell deletes (the reversibility rungs in [Irreversible effects](irreversible-effects.md)).

**The record is often gone with the files.** In INC-802 and INC-805 no destructive command is in the transcript at all; both reporters reconstruct a glob delete from what survived, since a `*` glob skips dot-entries by default and the dot-entries were all that remained. That is the reporters' inference, and the rows are marked self-reported.

**Neighbours.** When a guard did look at the command or path and let it through because it read the text, not what the text resolves to, the case is [pattern-matched boundaries](pattern-matched-boundaries.md): INC-030's permission check saw only `bash script`. This class is the case with no check of the resolved target at all. What the acting identity can reach, and when a person must approve an irreversible effect, is [Irreversible effects](irreversible-effects.md), which this doc does not restate. A wrong working directory because the agent assumed another environment is [world differs from assumed](world-differs-from-assumed.md) when the delete is incidental; when the delete is the damage, it is here. A delete the agent chose on purpose and aimed at the files it meant, such as INC-003, is not this class, and neither is a production resource the agent believed was staging (INC-006): there the target was chosen, not computed.

## Where it surfaces

At code, when the command runs: in every row cited here the deletion itself is the first sign, found by the person when folders are missing (INC-001) or by the agent when its working directory or its sign-in is gone (INC-803). In CI, when a cleanup script the agent wrote is committed: a shell linter would flag a delete built from a variable that can be empty (see the lint rung); none of the rows in Examples was caught that way, since none ran from a committed script. After merge, when a shipped script runs on a machine its author did not foresee, as the launcher script above did. The stages are spelled as in `docs/vocabularies.json`.

## Protections

The ladder runs from the cheapest rung to the strongest. The early rungs make the delete step itself fail closed; the later ones catch it from outside. Limiting what the agent can reach and keeping its work restorable are the reach and reversibility rungs of [Irreversible effects](irreversible-effects.md); the last rung here only says where they break for this class.

### Prompt: name what a cleanup may delete, and have the agent delete by literal path

- **Source:** [Claude Code best practices](https://code.claude.com/docs/en/best-practices.md), which says a rules file is guidance and that "Claude is allowed to decide a guideline doesn't apply"; anything that must happen every time belongs in a hook, a deny rule or a managed setting.
- **Cost:** Context tokens in every session.
- **Breaks when:** The agent follows the rule in the text it writes and the text resolves elsewhere: in INC-803 the agent had just said the real `$HOME` was restored. A guideline can also be dropped as the session grows, and a rule the agent decides does not apply is not followed.

### Tool defaults: let `rm` refuse the root and stay on one file system

- **Source:** [GNU `rm`](https://www.gnu.org/software/coreutils/manual/html_node/rm-invocation.html): `--preserve-root` is the default for a recursive delete, and `--one-file-system` skips directories on other file systems; [POSIX `rm`](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/rm.html) also refuses an operand that resolves to the root directory.
- **Cost:** None for the default; one flag for `--one-file-system`.
- **Breaks when:** The target is anything but the root itself: `"$EMPTY/"*` expands to the root's children, not to `/`, and a home directory, a drive or a repository is not protected. `--one-file-system` does not help when the wrong target is on the same file system as the right one, as a home directory usually is.

### Shell: make an empty or unset expansion fail instead of shrinking the path

- **Source:** The POSIX shell ([Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)): `${VAR:?}` writes an error and exits when the variable is unset or null, and `set -u` fails the expansion of an unset variable. [ShellCheck SC2115](https://www.shellcheck.net/wiki/SC2115) gives `${VAR:?}` as the fix for the launcher script's line. In Bash, `failglob` refuses to run a command whose glob matches nothing ([bash(1)](https://man7.org/linux/man-pages/man1/bash.1.html)). In PowerShell, [`Set-StrictMode`](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/set-strictmode) refuses references to uninitialized variables.
- **Cost:** A few characters per expansion in a delete path, or one line per script.
- **Breaks when:** The variable is set and wrong. In INC-001 and INC-803 `$HOME` held a real path, so neither guard would have fired. `set -u` names only an unset variable, so one set to the empty string passes. `Set-StrictMode` version 1.0 exempts variables inside strings, which is how a path is usually built, and it holds only in the scope it is set in and its child scopes. An agent's one-off command carries a guard only if the agent writes it.

### Shell: stop when the step before the delete fails

- **Source:** [ShellCheck SC2164](https://www.shellcheck.net/wiki/SC2164): a `cd` that fails lets the script "keep going and do all its operations in the wrong directory"; the fix is `cd dir || exit`. `set -e` stops a script on a failed command ([Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)).
- **Cost:** A few characters per `cd`.
- **Breaks when:** The step before succeeds into the wrong place: in INC-800 the agent ran the glob in a directory it had chosen. POSIX ignores `set -e` in the condition of an `if` or `while` and in every member of an `&&` or `||` list but the last, and ShellCheck does not report SC2164 once `set -e` appears.

### CI: lint committed shell scripts for deletes built from expansions

- **Source:** [ShellCheck](https://www.shellcheck.net/wiki/SC2115) rules SC2115 (a delete under a variable that can be empty), [SC2114](https://www.shellcheck.net/wiki/SC2114) (a delete of a system directory, as from a stray space in a path) and SC2164 (above), run in CI or in the editor.
- **Cost:** CI minutes on the pull requests that change a script.
- **Breaks when:** The delete never passes through a committed script. The five rows in Examples are commands the agent ran, not lines in a file, so a linter would not have seen any of them. SC2114 can be switched off with a directive.

### Scratch: create the scratch directory once, and delete only the name it returned

- **Source:** [mktemp(1)](https://man7.org/linux/man-pages/man1/mktemp.1.html) creates a temporary directory safely and prints its name. Claude Code does not keep environment variables from one Bash call to the next ([tools reference](https://code.claude.com/docs/en/tools-reference.md#what-persists-between-commands)), so the returned name has to be written into the delete as a literal, not carried in a variable.
- **Cost:** One line per scratch directory, and a delete command that names it.
- **Breaks when:** The name is lost and the variable that should hold it is empty (combine with the expansion rung). The agent rebuilds the path from memory or from `$HOME` instead of the name it was given, as in INC-001 and INC-803, where the scratch space was a temporary `$HOME`.

### Preview: list what the delete would remove, and read it

- **Source:** `git clean -n` shows what would be removed, and git refuses to clean without `-f` by default ([git-clean](https://git-scm.com/docs/git-clean)); rsync advises a `--dry-run` before `--delete` and caps deletions with `--max-delete` ([rsync(1)](https://download.samba.org/pub/rsync/rsync.1)); PowerShell's `-WhatIf` shows what the cmdlet would do without running it ([Remove-Item](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/remove-item)).
- **Cost:** One extra command and the time to read its output.
- **Breaks when:** The real run computes the target again and gets a different answer: a new Bash call without the variable (INC-001), another working directory, a variable changed in between. Nobody reads the preview. A wildcard the shell expands before rsync sees it changes what `--delete` acts on. The Remove-Item page also says `-Exclude` with `-Recurse` filters only the top directory, so a preview that trusts the filter misleads, the shape of INC-804.

### Check: resolve the target, and refuse a delete outside the scope

- **Source:** [realpath(1)](https://man7.org/linux/man-pages/man1/realpath.1.html) prints the resolved absolute path, and `-e` requires that it exist; Python's [`Path.resolve()`](https://docs.python.org/3/library/pathlib.html) resolves symlinks. The delete step compares the resolved target with the directory it is allowed to clean and stops when it lies outside. This is the delete checking itself; a guard doing the same for every command is the paths rung in [Pattern-matched boundaries](pattern-matched-boundaries.md).
- **Cost:** A few lines per delete site, and someone has to define the scope.
- **Breaks when:** The comparison runs on the unresolved string: Python's `is_relative_to` is lexical, so a path with `..` in it passes. The allowed root is itself computed and wrong, for example a working directory that resolved to the home directory. The path changes between the check and the delete; that race is in the paths rung linked above. On platforms without fd-based functions, [`shutil.rmtree`](https://docs.python.org/3/library/shutil.html) can be led through a symlink during the delete.

### Harness: let the agent's own check refuse deletes of critical paths

- **Source:** [Claude Code permission modes](https://code.claude.com/docs/en/permission-modes.md): "Critical paths are the directories Claude Code protects from `rm` and `rmdir` commands, such as the filesystem root, your home directory, and your working directory." The page lists computed forms it flags as well, among them a glob directly under a variable that can be empty and a recursive delete whose target is only the output of a command substitution; a target whose expansions are all guarded with `:?` passes.
- **Cost:** A prompt on each flagged delete.
- **Breaks when:** The [same page](https://code.claude.com/docs/en/permission-modes.md) says the check "can miss some commands, so it doesn't replace an operating-system control such as sandboxing", and that it covers only `rm` and `rmdir`, so other commands, such as INC-804's PowerShell delete, can remove the same paths. A wrong target that is not on the list, such as a sibling project, is not flagged. Environment variables switch parts of the check off.

### Classifier: block a delete whose target the reviewer cannot see

- **Source:** In Claude Code's auto mode the classifier blocks by default a recursive forced delete whose target is a shell variable "that isn't assigned anywhere in the conversation the classifier sees", and the block clears when the delete is re-run with the resolved literal path ([permission modes](https://code.claude.com/docs/en/permission-modes.md)). The classifier itself is the classifier rung of [Pattern-matched boundaries](pattern-matched-boundaries.md).
- **Cost:** A model call per action that reaches it, and some harmless deletes blocked.
- **Breaks when:** The variable was assigned earlier in the conversation, as in INC-001, where the agent set `$HOME` in one call and deleted it in a later one: the rule as written does not block that case, though the value no longer held. An independent stress test found cleanup the family most often missed (see Evidence).

### Trash: delete to a trash the person can restore from

- **Source:** [trash-cli](https://github.com/andreafrancia/trash-cli) moves files to the freedesktop.org trash from the command line; on Windows, .NET's [`DeleteDirectory`](https://learn.microsoft.com/en-us/dotnet/api/microsoft.visualbasic.fileio.filesystem.deletedirectory) can send a directory to the Recycle Bin, though its default is a permanent delete.
- **Cost:** Disk space until the trash is emptied.
- **Breaks when:** The agent calls `rm` or `Remove-Item` instead of the trash tool, which nothing stops; trash-cli's own README advises against aliasing `rm` to it. trash-cli does not support Btrfs volumes, and .NET's Recycle Bin option is not supported in applications that are not user-interactive.

### Reach and reversibility: confine writes to the workspace, and keep its work restorable

- **Source:** The reach and reversibility rungs of [Irreversible effects](irreversible-effects.md): a sandbox on the agent's shell, work kept in a remote repository, backups out of the agent's reach. For agent-scale rollback, a research filesystem holds an agent's changes until the user approves them and snapshots state so the agent can revert ([Zhong et al., YoloFS](https://arxiv.org/html/2604.13536)).
- **Cost:** As listed in that doc. For YoloFS the paper reports throughput matching Ext4 and a 4% overhead on `stat` (as of 2026-09, Zhong et al.).
- **Breaks when:** The computed target is inside the reach the sandbox grants. A sandbox that allows writes to the working directory still lets a delete there take the repository's sources and part of its `.git` (INC-804), unless `.git` is protected separately, as Codex does ([Codex approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md)). A dev container's bind-mounted workspace is the host's folder, so a delete in it is a delete on the host ([Claude Code dev containers](https://code.claude.com/docs/en/devcontainer.md)). YoloFS is a Linux stackable filesystem from a research group, not a packaged tool.

## Evidence

- A study of 290 public reports of coding agents misusing the filesystem found deletion in 39% of its incidents and exploits; "42% of reports involve harm outside the project"; of the reports with known recoverability, 40% were unrecoverable; and where the agent's reaction is known, in 68% it carried on as if nothing had gone wrong (as of 2026-09, [Zhong et al.](https://arxiv.org/html/2604.13536)). These are counts of reports, not rates per session; no source found gives how often a destructive command occurs in normal use.
- An independent stress test of Claude Code's auto mode measured an end-to-end false-negative rate of 81.0% on 253 state-changing actions, with 36.8% of them outside the classifier's scope; the paper calls that share the Tier 2 coverage gap and finds it "most pronounced on artifact cleanup (92.9% FNR)" (as of 2026-10, [Ji et al.](https://arxiv.org/abs/2604.04978)). The authors attribute the difference from the vendor's own, lower figure (in [Irreversible effects](irreversible-effects.md)) to a different workload.
- Every incident cited here is a row in [`incidents/incidents.csv`](../../incidents/incidents.csv). Three of the class's rows, INC-800, INC-802 and INC-805, are self-reported: the destructive command is not in a log, and the mechanism is the reporter's reconstruction; they say so in the evidence-strength column. None of the class's rows comes from the maintainer's repositories.
