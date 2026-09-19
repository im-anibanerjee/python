# Git basics: the three states, and the core commands that move things between them

First topic in the Git group, folded into Wknd 1-3 as agreed. Everything below is genuinely run through `git 2.43.0` on a scratch repo, exactly as shown - no output was guessed.

## 1. Why Git exists (simple version)

Imagine every time you saved a Word document, the old version didn't disappear - it just sat there, labeled, so you could always go back to it, compare it to today's version, or ask "who changed this paragraph and why." That's all Git is: a save-history system for a folder of files, plus tools to compare, label, and jump between those saves.

**Real-life example:** you're writing an essay. Draft 1 was fine, but draft 3 broke a paragraph you liked. Without version control, you'd need a folder full of `essay_v1.docx`, `essay_v2_final.docx`, `essay_v2_FINAL_FINAL.docx` and hope you remember which is which. Git replaces that whole mess with one folder and a command that says "go back to how this looked after draft 1."

**Real-world use case:** every serious software team uses Git (or something like it) so that dozens of people can edit the same codebase without overwriting each other's work, and so any bug can be traced back to the exact change that introduced it (`git log`, `git blame`).

**Technical deep dive:** Git is a *distributed* version control system - every clone of a repository has the full history, not just a pointer to a central server (this is the actual technical distinction from older tools like SVN, which kept history only on the server). Git tracks *content*, not files-as-diffs the way some older tools do: every commit is a full snapshot of the whole tracked tree, and Git is just very good at storing those snapshots compactly by reusing unchanged file content between commits.

## 2. The three states - the idea everything else in Git builds on

```
 working directory  --git add-->  staging area  --git commit-->  repository (.git)
 (your actual files)              (what will go               (permanent history,
                                    into the next commit)        one snapshot per commit)
```

Every file in a Git repo is in one of these three "places" at any moment:

- **working directory** - the actual files on disk, exactly as you see them in a text editor. This is the only one of the three you edit directly.
- **staging area** (also called "the index") - a holding area. It's not "the last commit" and it's not "your current edits" - it's a separate, third thing: a list of exactly what will go into the *next* commit, decided by you, file by file, via `git add`.
- **repository** - the permanent, committed history, stored inside the hidden `.git` folder. Once something is committed, it has a permanent id (a commit hash) and generally isn't going anywhere.

**Why a staging area at all, and not just working directory -> commit directly?** Because it lets you commit *part* of what you changed. If you fixed a real bug and also left a stray `print()` debug line in the same file, you can `git add` just the bug-fix lines (yes, even down to a chunk of a single file, via `git add -p`) and leave the debug line unstaged, so it never makes it into the commit. Staging is the deliberate "yes, this exact stuff, right here, is what I want recorded" step.

## 3. Turning a folder into a repo: `git init`

```bash
$ git init
```
```
Initialized empty Git repository in /.../gitdemo1/.git/
```
`git init` creates the hidden `.git/` folder - that folder *is* the repository. Nothing about your existing files changes; Git just starts watching this directory from this point on. Run it once, at the top of the folder you want tracked.

```bash
$ git status
```
```
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to track)
```
`git status` is the command you'll run constantly - it always tells you, honestly, which of the three states everything is currently in. Right after `init`, there's nothing to report: no files yet, no commits yet.

## 4. `git add` and `git status`: watching a file move into staging

```bash
$ echo "print('hello from the CLI tool')" > app.py
$ git status
```
```
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	app.py

nothing added to commit but untracked files present (use "git add" to track)
```
A brand-new file Git has never seen is **untracked** - it exists in the working directory only. Git is telling you plainly: I see this file, I am not tracking it, here's the command to start.

```bash
$ git add app.py
$ git status
```
```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
	new file:   app.py

```
Now `app.py` is staged - it moved from "working directory only" into the staging area. Nothing is committed yet. `git status` even tells you the undo command (`git rm --cached`) in the same breath, which is worth noticing: staging is cheap and reversible.

```
 [untracked: app.py]  --git add app.py-->  [staged: new file app.py]
```

## 5. `git commit`: staging area becomes a permanent snapshot

```bash
$ git commit -m "add initial app.py"
```
```
[main (root-commit) bcf8091] add initial app.py
 1 file changed, 1 insertion(+)
 create mode 100644 app.py
```
`git commit` takes whatever is currently staged and seals it into a new, permanent snapshot in the repository, with a message (`-m "..."`) explaining what and why. `bcf8091` is the short form of that commit's hash - a fingerprint of the snapshot's content plus metadata (author, timestamp, message, parent commit). `(root-commit)` just flags that this was the very first commit in the repo - it has no parent.

**Why a commit message matters more than it looks:** six months from now, `git log` is how you or a teammate will figure out *why* a change was made, not just *what* changed (the diff already shows what). "add initial app.py" is a fine message here for a demo; in real work, "fix off-by-one in the discount loop" beats "fix bug" for the same reason a good code comment beats no comment.

## 6. `git log`: reading the history back

```bash
$ git log
```
```
commit bcf80913e0c6d99dfd605a784532e64aab476eb0
Author: Ani Banerjee <i.m.anirruddha.banerjee@gmail.com>
Date:   Sat Sep 19 12:18:35 2026 +0000

    add initial app.py
```
Full form: the complete hash, author, timestamp, and message, for every commit, newest first. Later, once there's more than one commit, `git log --oneline` becomes the everyday version:
```bash
$ git log --oneline
```
```
407cba0 log a second line on startup
bcf8091 add initial app.py
```
One line per commit - short hash plus message - scannable at a glance. This is genuinely the command you'll run the most while orienting yourself in a repo you haven't touched in a while.

## 7. `git diff` vs `git diff --staged`: two different comparisons that look similar

This is the part people usually get wrong at first, so it's worth being precise about what each one is actually comparing.

```bash
$ echo "print('added a second line')" >> app.py
$ git diff
```
```
diff --git a/app.py b/app.py
index 8f55760..5c041f2 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
 print('hello from the CLI tool')
+print('added a second line')
```
Plain `git diff`, with nothing staged, compares **working directory vs. staging area (which currently matches the last commit)**. It's showing you: "here's what you've changed that isn't staged yet."

```bash
$ git add app.py
$ git diff
```
```
(nothing printed)
```
Now that the change is staged, plain `git diff` goes quiet - working directory and staging area match exactly, so there's nothing left in *that* comparison to show.

```bash
$ git diff --staged
```
```
diff --git a/app.py b/app.py
index 8f55760..5c041f2 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
 print('hello from the CLI tool')
+print('added a second line')
```
`git diff --staged` compares **staging area vs. the last commit**. It's showing you: "here's what's about to go into the next commit if I run `git commit` right now." Same-looking diff text in this example only because there's just one change in flight - but the *comparison being made* is different in each case, and once you have several changes at once (some staged, some not), the two commands genuinely show different things.

```
 git diff            :  working directory  <-->  staging area
 git diff --staged   :  staging area        <-->  last commit
```

```bash
$ git commit -m "log a second line on startup"
$ git log --oneline
```
```
[main 407cba0] log a second line on startup
 1 file changed, 1 insertion(+)

407cba0 log a second line on startup
bcf8091 add initial app.py
```
Two real commits now, oldest at the bottom - `git log` always reads newest-first, top to bottom.

## 8. `.gitignore`: telling Git what to never even mention

Some files genuinely shouldn't be tracked: compiled bytecode, log files generated by running the program, secrets (`.env` files with real credentials), IDE-specific settings folders. Committing these bloats the repo, leaks secrets, or causes pointless "changed" noise for files nobody actually edited by hand.

```bash
$ mkdir -p __pycache__
$ touch __pycache__/app.cpython-311.pyc
$ touch debug.log
$ git status
```
```
On branch main
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	__pycache__/
	debug.log

nothing added to commit but untracked files present (use "git add" to track)
```
Without a `.gitignore`, Git treats these exactly like any other untracked file - it'll happily let you `git add` them if you're not paying attention.

```bash
$ printf "__pycache__/\n*.log\n.env\n" > .gitignore
$ git status
```
```
On branch main
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.gitignore

nothing added to commit but untracked files present (use "git add" to track)
```
The moment `.gitignore` exists with matching patterns, `__pycache__/` and `debug.log` disappear from `git status` entirely - not staged, not flagged, not mentioned. `.gitignore` itself is a normal file though, so it shows up as untracked until you commit it too - which you should, so the ignore rules travel with the repo for every collaborator.

```bash
$ git add .gitignore
$ git commit -m "add gitignore for pycache and logs"
$ git log --oneline
```
```
[main 6c43c5d] add gitignore for pycache and logs
 1 file changed, 3 insertions(+)
 create mode 100644 .gitignore
6c43c5d add gitignore for pycache and logs
407cba0 log a second line on startup
bcf8091 add initial app.py
```
Three commits now. Note what `.gitignore` does *not* do: if a file was already tracked before you added the ignore rule, `.gitignore` won't untrack it retroactively - you'd need `git rm --cached <file>` for that (covered as the undo tool for exactly this in the next doc's neighborhood).

## 9. `git config`: three layers, most specific wins

```bash
$ git config user.email
```
```
i.m.anirruddha.banerjee@gmail.com
```
This reads the **global** config (`~/.gitconfig` - applies to every repo on this machine unless overridden). It was set once with `git config --global user.name "..."` / `git config --global user.email "..."`.

```bash
$ git config --local user.email "ani.interview.prep@gmail.com"
$ git config user.email
```
```
ani.interview.prep@gmail.com
```
`--local` writes into *this specific repo's* `.git/config`, and it wins over the global setting - this is genuinely useful for e.g. using a work email on work repos and a personal email everywhere else, set once per repo.

```bash
$ git config --unset user.email
$ git config user.email
```
```
i.m.anirruddha.banerjee@gmail.com
```
Unsetting the local override falls back to whichever layer is next - global, in this case. The real precedence order, most specific first, is: `--local` (this repo) > `--global` (this user, this machine) > `--system` (everyone on this machine). Every commit's `Author:` line, seen back in §6, comes straight from whichever `user.name`/`user.email` was active at commit time - which is exactly why an accidentally-wrong email on a work machine is a genuinely common real mistake worth knowing how to check for (`git config user.email`, right before your first commit on a new machine or repo).

## Connecting it back

Every command above is really just moving something along the same one path: **working directory -> staging area -> repository**. `git status` tells you where things currently sit on that path. `git add` moves a file rightward by one step. `git commit` seals whatever is staged into permanent history. `git diff` / `git diff --staged` are just two different "compare adjacent stops on the path" commands. `.gitignore` keeps certain files off the path entirely. `git config` doesn't move anything - it just decides whose name goes on the commits you make. Once this three-state picture is solid, branching (next doc) is just "more than one version of this same path, existing at once."

---

## Practice questions

#1. In a fresh folder, `git init`, create a file, and prove to yourself (by actually running the commands and reading the real output) that `git status` reports it as untracked, then staged, then - after commit - reports nothing to commit at all. Paste the three `git status` outputs.

#2. Make a change to a tracked file but don't stage it yet. Run `git diff`. Now stage it and run `git diff` again (should be empty) followed by `git diff --staged`. Explain in your own words, in a comment, why the second `git diff` is empty even though the file is still "changed" relative to the last commit.

#3. Create a `.env` file and a `*.tmp` file. Add both patterns to `.gitignore`, commit the `.gitignore`, and confirm with `git status` that neither file is ever offered to be staged. Then deliberately `git add -f` (force-add) one of them anyway, and explain what `-f` did and why it's dangerous to reach for casually.

#4. Set a repo-local `user.email` that's different from your global one, make a commit, and use `git log` to prove the commit's `Author:` line used the local override, not the global email. Then `--unset` it and explain the fallback you'd expect on the next commit.

#5. `git commit` without `-m` at all. What happens (you'll need to either configure or quit out of whatever it opens)? Explain, in a short comment, what that flag is actually saving you from typing when you do remember to use it.
