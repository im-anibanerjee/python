# Git undo & history rewriting: reset, revert, stash, cherry-pick, amend, reflog

Fourth and last topic in the Git group, closing it out. Every command below was genuinely run through `git 2.43.0` on a scratch repo, including a deliberately-caused "oops" and its real recovery.

## 1. Two philosophies of "undo" (simple version)

Git actually gives you two fundamentally different kinds of undo, and mixing them up is the single most common source of real confusion:

- **Revert**: "I want to cancel out what this commit did, but keep it in the record that it happened, and that I later undid it." Nothing disappears from history - a new commit is added that does the opposite.
- **Reset**: "I want to act as if certain commits never happened." History actually moves backward. This is genuinely destructive to *reachability* (not always to the underlying data, as you'll see with reflog) and is the one to be careful with, especially once something has been pushed and other people may already have it.

**Real-life example:** revert is like writing a follow-up email that says "ignore my last email, here's the corrected version" - the original email still exists in the thread. Reset is like reaching into someone's inbox and deleting your original email outright, as if it never got sent.

**Real-world use case:** on a shared branch that others have already pulled, you almost always want `revert` - rewriting shared history out from under people breaks their local repos. On your own private, not-yet-pushed work, `reset` (and the rest of this doc's history-rewriting tools) is exactly the right, safe tool.

## 2. `git revert`: undo by adding a new commit

```bash
$ echo "version 1" > notes.txt
$ git add notes.txt && git commit -q -m "commit 1: version 1"
$ echo "version 2" > notes.txt
$ git add notes.txt && git commit -q -m "commit 2: version 2"
$ echo "version 3 - oops, broke it" > notes.txt
$ git add notes.txt && git commit -q -m "commit 3: version 3 (bug)"
$ git log --oneline
```
```
23f1ca9 commit 3: version 3 (bug)
d62bec2 commit 2: version 2
268cffe commit 1: version 1
```
```bash
$ git revert --no-edit HEAD
```
```
[main a8caf01] Revert "commit 3: version 3 (bug)"
 1 file changed, 1 insertion(+), 1 deletion(-)
```
```bash
$ git log --oneline && cat notes.txt
```
```
a8caf01 Revert "commit 3: version 3 (bug)"
23f1ca9 commit 3: version 3 (bug)
d62bec2 commit 2: version 2
268cffe commit 1: version 1
version 2
```
Four commits now, not three - `commit 3` is still right there in the log, honestly, but its *effect* has been cancelled by the new commit on top (`notes.txt` is back to "version 2"). `--no-edit` just skips the editor for the auto-generated message; a normal `git revert HEAD` would open one, pre-filled with `Revert "commit 3: version 3 (bug)"`, letting you add more context if you want.

## 3. `git reset` - three modes, same starting point, three different amounts of damage

```
              --soft            --mixed (default)         --hard
 HEAD:      moves back         moves back                moves back
 staging:   unchanged          reset to match new HEAD   reset to match new HEAD
 files:     unchanged          unchanged                 reset to match new HEAD  (DESTRUCTIVE)
```

```bash
$ git log --oneline
```
```
a8caf01 Revert "commit 3: version 3 (bug)"
23f1ca9 commit 3: version 3 (bug)
d62bec2 commit 2: version 2
268cffe commit 1: version 1
```
```bash
$ git reset --soft HEAD~1
$ git log --oneline
$ git status
```
```
23f1ca9 commit 3: version 3 (bug)
d62bec2 commit 2: version 2
268cffe commit 1: version 1

On branch main
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   notes.txt
```
`HEAD` moved back one commit - `a8caf01` is no longer the tip - but every change that commit made is sitting right there, fully staged, ready to be committed again (with a different message, combined with something else, whatever you want). `--soft` is the "I want to redo the *commit*, not the work" mode.

```bash
$ git commit -q -m "Revert commit 3: version 3 (bug)"
$ git reset HEAD~1
```
```
Unstaged changes after reset:
M	notes.txt
```
```bash
$ git status
```
```
On branch main
Changes not staged for commit:
	modified:   notes.txt

no changes added to commit (use "git add" and/or "git commit -a")
```
Plain `git reset` (no flag) is `--mixed`, the default: `HEAD` moves back *and* the staging area is reset to match, but the actual file content on disk is untouched - so the change is still there, just back to "not staged yet," as if you'd edited the file but never run `git add`.

```bash
$ git add notes.txt && git commit -q -m "Revert commit 3: version 3 (bug)"
$ echo "some uncommitted scratch edit" >> notes.txt
$ cat notes.txt
```
```
version 2
some uncommitted scratch edit
```
```bash
$ git reset --hard HEAD~1
$ git log --oneline && cat notes.txt
```
```
HEAD is now at 23f1ca9 commit 3: version 3 (bug)
23f1ca9 commit 3: version 3 (bug)
d62bec2 commit 2: version 2
268cffe commit 1: version 1
version 3 - oops, broke it
```
`--hard` is the dangerous one, deliberately reproduced here: `HEAD` moved back, *and* the working directory was force-overwritten to match - the previous commit (`Revert commit 3...`) is gone from the branch, **and** the uncommitted `"some uncommitted scratch edit"` line, which was never committed anywhere, is gone too, with no staging-area or working-directory copy left behind at all. This is the one line in this whole doc worth remembering above the rest: `--hard` throws away uncommitted work with no confirmation prompt.

## 4. `git reflog`: the safety net reset doesn't warn you about

```bash
$ git reflog
```
```
23f1ca9 HEAD@{0}: reset: moving to HEAD~1
289a3f1 HEAD@{1}: commit: Revert commit 3: version 3 (bug)
23f1ca9 HEAD@{2}: reset: moving to HEAD~1
289a3f1 HEAD@{3}: commit: Revert commit 3: version 3 (bug)
23f1ca9 HEAD@{4}: reset: moving to HEAD~1
a8caf01 HEAD@{5}: revert: Revert "commit 3: version 3 (bug)"
23f1ca9 HEAD@{6}: commit: commit 3: version 3 (bug)
d62bec2 HEAD@{7}: commit: commit 2: version 2
268cffe HEAD@{8}: commit (initial): commit 1: version 1
```
Here's the nuance that makes `--hard` less catastrophic than it looks: **every commit Git ever creates stays in its internal object database for a while even after no branch points at it anymore**, and `reflog` is the log of everywhere `HEAD` has pointed, including commits that are no longer reachable from any branch. `289a3f1` (the "lost" revert commit) is right there at `HEAD@{1}` and `HEAD@{3}`.

```bash
$ git reset --hard 289a3f1
$ git log --oneline && cat notes.txt
```
```
HEAD is now at 289a3f1 Revert commit 3: version 3 (bug)
289a3f1 Revert commit 3: version 3 (bug)
23f1ca9 commit 3: version 3 (bug)
d62bec2 commit 2: version 2
268cffe commit 1: version 1
version 2
```
Recovered completely - the commit is back on `main`. What genuinely does *not* come back, and this matters: `"some uncommitted scratch edit"` from before. Reflog only ever tracks **commits** - it has no memory of uncommitted working-directory changes, because those were never given a permanent object id in the first place. This is exactly why the next section (stash) exists: it's the tool for making sure in-progress, not-yet-committed work is never in this kind of danger to begin with.

## 5. `git stash`: shelving unfinished work without committing it

```bash
$ echo "half-written thought" >> notes.txt
$ git status
```
```
Changes not staged for commit:
	modified:   notes.txt
```
```bash
$ git stash
```
```
Saved working directory and index state WIP on main: 289a3f1 Revert commit 3: version 3 (bug)
```
```bash
$ git status && cat notes.txt
```
```
On branch main
nothing to commit, working tree clean

version 2
```
`git stash` takes everything uncommitted (staged or not) and tucks it away on a separate stack, leaving the working directory clean - as if you'd committed, except nothing shows up in `git log`. This is exactly what lets you switch branches, pull, or handle something urgent without either committing half-finished work or losing it.

```bash
$ git switch -c urgent-fix
$ echo "urgent patch" > urgent.txt
$ git add urgent.txt && git commit -q -m "urgent patch"
$ git switch main
```
Simulating exactly the situation stash exists for: an urgent, unrelated task came up mid-work.

```bash
$ git stash list
```
```
stash@{0}: WIP on main: 289a3f1 Revert commit 3: version 3 (bug)
```
```bash
$ git stash pop
$ cat notes.txt
```
```
Dropped refs/stash@{0} (0d3ffe6f...)
version 2
half-written thought
```
`git stash pop` re-applies the shelved changes to the working directory and removes them from the stash stack (`git stash apply` does the same re-apply but *keeps* the stash entry, useful if you might want to apply the same shelved changes somewhere else too).

## 6. `git cherry-pick`: taking one specific commit, not a whole branch

```bash
$ git log --oneline urgent-fix
```
```
6a7a0b8 urgent patch
289a3f1 Revert commit 3: version 3 (bug)
...
```
```bash
$ git cherry-pick $(git log --format=%H urgent-fix -1)
```
```
[main 9d673dc] urgent patch
 1 file changed, 1 insertion(+)
 create mode 100644 urgent.txt
```
```bash
$ git log --oneline
```
```
9d673dc urgent patch
289a3f1 Revert commit 3: version 3 (bug)
...
```
Unlike `merge` (doc 17), which brings in an entire branch's history and creates a link between the two branches, `cherry-pick` copies the *changes* from one specific commit and replays them as a brand-new commit on your current branch - notice `9d673dc` is a genuinely different hash from `6a7a0b8`, even though it contains the same change. This is the tool for "I need just that one bugfix from that other branch, not everything else on it."

## 7. `git commit --amend`: fixing the most recent commit instead of adding another

```bash
$ echo "readme draft" > README.md
$ git add README.md && git commit -q -m "add readme"
$ echo "typo fix" >> README.md
$ git add README.md
$ git commit --amend -q -m "add README with typo fix folded in"
$ git log --oneline -3
```
```
ef908aa add README with typo fix folded in
9d673dc urgent patch
289a3f1 Revert commit 3: version 3 (bug)
```
```bash
$ cat README.md
```
```
readme draft
typo fix
```
Notice there's still only one new commit at the top (`ef908aa`), not two - `--amend` folds the currently-staged changes into the previous commit and lets you rewrite its message, rather than creating a fresh commit on top. This is genuinely useful for "I just committed and immediately noticed a typo," but the same caution from `reset --hard` applies in spirit: `--amend` replaces a commit's hash entirely, so amending something you've already pushed and someone else may have pulled rewrites history out from under them - safe on your own unpushed, private commits; risky on shared ones.

## Connecting it back

Every tool in this doc is really answering one of two questions: "how do I make a mistake's *effect* go away while being honest that it happened" (revert), or "how do I make Git act like a mistake never happened at all, on history that's still entirely mine" (reset, amend, and cherry-pick for picking exactly the part I meant to keep). Stash is the one tool here that isn't about mistakes at all - it's about safely pausing work that isn't a mistake, just not done yet. And reflog is the reason `reset --hard` is dangerous but not usually catastrophic: Git keeps its own paper trail of every commit that ever existed under `HEAD`, for a good while after nothing else points at it - it's the actual answer to "I think I just deleted something important" far more often than people expect.

---

## Practice questions

#1. Make three commits. `git revert` the middle one (not the most recent - you'll need `git revert <hash>`, not `HEAD`). Explain, from the actual `git log` output, why this is different from reverting `HEAD` and whether a conflict can happen here (it can, if the most recent commit touches the same lines).

#2. Reproduce all three reset modes yourself against the same starting commit (make three separate copies of the repo, or reset and rebuild between each), and paste `git status` right after each one. In your own words, state exactly which of the three states (working directory / staging / repo history) each mode touches.

#3. Deliberately lose a commit with `git reset --hard`, then recover it with `git reflog` + `git reset --hard <hash>`. Paste the reflog output you used to find the hash, and explain why reflog could find it but wouldn't have been able to recover an *uncommitted* change lost the same way.

#4. Start some work, `git stash` it, switch to a different branch and back, then `git stash pop`. Now do it again but use `git stash apply` instead of `pop`, and run `git stash list` afterward - what's still sitting on the stack, and why would you ever want that over `pop`?

#5. Create two branches that each get their own commits. Cherry-pick one specific commit from branch B onto branch A, and compare its commit hash to the original on branch B - are they the same or different, and explain why, referencing what a commit hash is actually a fingerprint of (content + metadata, including parent) from doc 16.
