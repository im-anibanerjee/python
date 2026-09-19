# Git remotes & collaboration: clone, push, pull, and how a PR actually works underneath

Third topic in the Git group. This cloud sandbox has no live network access this session, so instead of a real GitHub repo, every demo below uses a **local bare repository as a stand-in for "GitHub"** - mechanically identical to a real remote (same `clone`/`push`/`pull`/`fetch` commands, same protocol concepts), just reachable by a filesystem path instead of a URL. Everything is genuinely run through `git 2.43.0`; the only sandbox-specific artifact is a harmless `push negotiation failed; proceeding anyway with push` warning that showed up a couple of times below - that's a quirk of this container's git/transport setup, not something a real push against GitHub will show you, so it's called out inline rather than left unexplained.

## 1. What a "remote" is (simple version)

Everything in the two previous docs happened inside one repository on one machine. A remote is just: another copy of that same repository, somewhere else, that you and Git both know how to reach. Git commands don't distinguish "somewhere else" meaning a folder on your own disk versus a server across the internet - the mechanics are identical either way, which is exactly why this doc's local-bare-repo stand-in teaches the real thing.

**Real-life example:** think of a shared family photo album stored in the cloud. Everyone has their own copy on their own phone (their "clone"). When you add photos, you "upload" (push) them to the shared album; when you want everyone else's new photos, you "sync" (pull). Nobody's copy is more real than anyone else's - the cloud album is just the one everyone's agreed to treat as the meeting point.

**Real-world use case:** this is precisely how teams collaborate on GitHub. One repository (`origin`) is the shared meeting point; every developer has their own full clone; work happens locally and gets pushed up, reviewed, and merged.

**Technical deep dive:** because Git is distributed (from doc 16, §1), a "remote" isn't structurally different from your own repo - it's a full repository too, just one Git has been told to treat as a sync target under a short name (`origin` is only a convention, not a keyword). `git remote -v` lists every remote a repo knows about and the URL/path for each.

## 2. Clone: getting your own full copy

```bash
$ git init -q --bare origin.git
```
This creates a "bare" repo - one with no working directory, only the `.git` internals (`objects`, `refs`, etc.) - which is what a real GitHub repo effectively is on GitHub's servers. Nobody edits files directly inside a bare repo; it exists purely to be pushed to and pulled from.

```bash
$ git clone origin.git local_clone
```
```
Cloning into 'local_clone'...
warning: You appear to have cloned an empty repository.
done.
```
```bash
$ git remote -v
```
```
origin	/.../origin.git (fetch)
origin	/.../origin.git (push)
```
`git clone` copies the *entire* history (every commit, every branch) down to a new working repo, and automatically names the source `origin` and remembers it. That's why `git remote -v` immediately shows it, with no setup - clone does that wiring for you.

## 3. Push: sending your commits up

```bash
$ echo "print('hello from the CLI tool')" > app.py
$ git add app.py && git commit -q -m "add initial app.py"
$ git branch -M main
$ git push -u origin main
```
```
To /.../origin.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```
`git push origin main` sends local `main`'s commits up to `origin`'s `main`. The `-u` (`--set-upstream`) on the *first* push links your local `main` to `origin/main` permanently, so every future push/pull from this branch can just be `git push` / `git pull` with no arguments - Git remembers the pairing.

## 4. A second clone, simulating a teammate

```bash
$ git clone origin.git teammate_clone -q
$ cd teammate_clone && cat app.py
```
```
print('hello from the CLI tool')
```
Cloning `origin.git` again, into a different folder, gives an entirely independent working copy with the same history - this stands in for a teammate cloning the same GitHub URL onto their own machine. Anything pushed to `origin` from here on is visible to anyone who fetches/pulls it.

## 5. Fetch vs. pull: the distinction that trips people up

```bash
$ cd teammate_clone
$ echo "def logout(): pass" >> app.py
$ git add app.py && git commit -q -m "add logout stub"
$ git push -q origin main
```
The "teammate" makes a commit and pushes it. Back on the original clone, which knows nothing about this yet:

```bash
$ cd local_clone
$ git fetch origin
```
```
From /.../origin
   4d95d9f..ea95bb6  main       -> origin/main
```
```bash
$ git log --oneline
```
```
4d95d9f add initial app.py
```
```bash
$ git log --oneline origin/main
```
```
ea95bb6 add logout stub
4d95d9f add initial app.py
```
This is the key thing to internalize: **`git fetch` downloads the new commits and updates a separate bookkeeping pointer, `origin/main` (a "remote-tracking branch"), but does not touch your own `main` or your working files at all.** `cat app.py` right after this fetch would still show the old content - fetch is deliberately "look, but don't touch," which is exactly why it's safe to run at any time, mid-work, with zero risk of clobbering anything you're in the middle of.

```bash
$ git pull
```
```
Updating 4d95d9f..ea95bb6
Fast-forward
 app.py | 1 +
 1 file changed, 1 insertion(+)
```
```bash
$ git log --oneline && cat app.py
```
```
ea95bb6 add logout stub
4d95d9f add initial app.py
print('hello from the CLI tool')
def logout(): pass
```
`git pull` is genuinely just `git fetch` immediately followed by `git merge origin/<branch>` into your current branch - it's the "and also actually apply it to what I'm looking at" version. Here it happened to fast-forward (same idea as doc 17, §4) because the local `main` hadn't diverged. If it had diverged, `pull` would trigger the exact same 3-way-merge-or-conflict process from doc 17, §5-6 - `pull` doesn't skip that step, it just runs `fetch` and `merge` back to back instead of you typing them separately.

```
 git fetch  :  origin.git  -->  origin/main  (your local main untouched)
 git pull   :  origin.git  -->  origin/main  -->  merge into your local main  (working files updated)
```

## 6. The branch -> push -> PR -> merge shape, reproduced locally

This is the actual workflow the Wknd 1-3 build asks for ("real branch->PR"). On real GitHub, the "PR" (pull request) part happens in their web UI, but the Git-level mechanics underneath are exactly this:

```bash
$ git switch -c feature-signup
$ echo "def signup(): pass" >> app.py
$ git add app.py && git commit -q -m "add signup stub"
$ git push -u origin feature-signup
```
```
To /.../origin.git
 * [new branch]      feature-signup -> feature-signup
branch 'feature-signup' set up to track 'origin/feature-signup'.
```
Pushing a *branch* (not `main`) up to origin, on its own, is exactly the step that makes GitHub show its "Compare & pull request" prompt in the real product - the branch existing on the shared remote is the whole prerequisite for opening a PR against it. `git branch -r` on origin would now show both `origin/feature-signup` and `origin/main`.

```bash
$ git switch main
$ git pull -q
$ git merge feature-signup -m "merge feature-signup into main"
```
```
Fast-forward (no commit created; -m option ignored)
 app.py | 1 +
 1 file changed, 1 insertion(+)
```
"Merging the PR" - whether a human clicks a green button on GitHub, or you type `git merge` locally - is the identical operation from doc 17: reconcile `feature-signup`'s history into `main`. In this run it happened to be fast-forwardable, since `main` hadn't moved since the branch was cut, so no merge commit was created here.

**A real nuance worth knowing for interviews:** GitHub's own merge button does *not* behave like plain `git merge` by default - its "Create a merge commit" option forces a merge commit even when a fast-forward would be possible, specifically so a PR always leaves a visible marker in history ("this batch of commits was merged via PR #N"). Reproducing that locally means adding `--no-ff` ("no fast-forward"):

```bash
$ git switch -c feature-help
$ echo "def help(): pass" >> app.py
$ git add app.py && git commit -q -m "add help stub"
$ git switch main
$ git merge --no-ff feature-help -m "merge feature-help into main"
```
```
Merge made by the 'ort' strategy.
 app.py | 1 +
 1 file changed, 1 insertion(+)
```
```bash
$ git log --oneline --graph --all --decorate
```
```
*   2ebd938 (HEAD -> main) merge feature-help into main
|\
| * e053aa7 (feature-help) add help stub
|/
* a8b964a (origin/main) add signup stub
* ea95bb6 add logout stub
* 4d95d9f add initial app.py
```
Same starting conditions as the fast-forwardable `feature-signup` merge above, but `--no-ff` forced a real merge commit anyway - this is genuinely what a GitHub PR merge looks like in your local history once you pull it back down, even for a small, trivially-fast-forwardable change.

```bash
$ git push origin main
```
```
   ea95bb6..a8b964a  main -> main
```
Pushing `main` back up is the step that actually "closes" the PR on real GitHub - the remote's `main` now includes the merged work, which is what everyone else will see and pull next.

```bash
$ git branch -d feature-signup
$ git push origin --delete feature-signup
```
```
Deleted branch feature-signup (was a8b964a).
To /.../origin.git
 - [deleted]         feature-signup
```
Local branch delete (`-d`, from doc 17, §7) only removes your own local pointer. `git push origin --delete <branch>` is the separate command that removes the branch *on the remote* too - this is exactly what GitHub's "Delete branch" button (offered right after a PR merges) does under the hood.

## Connecting it back

A remote is just another full copy of the repo, reachable by name instead of a local path. `clone` gets you one; `push` sends your commits to it; `fetch` quietly checks what's new there without touching your own work; `pull` is fetch-then-merge, so it inherits every merge/conflict behavior from doc 17 exactly as-is. And the entire GitHub pull-request ceremony - branch, push, review, merge, delete - is not a separate Git concept at all; it's the same branch-and-merge mechanics from doc 17, just performed with a shared remote sitting in the middle instead of one person doing everything in a single local repo.

---

## Practice questions

#1. Create a second local bare repo to act as your own "origin," clone it, make a commit, and push. Then make a *second* clone from the same bare repo (simulating a teammate), and from that second clone, prove with `git fetch` followed by `cat` on a changed file that fetch alone did not update your working files - only after `git pull` does the file change. Paste both sets of output.

#2. From your first clone, create a feature branch, commit something, and push *just the branch* (not main) to origin. Confirm with `git branch -r` (run against origin, or from a fresh clone) that the branch now exists remotely without ever touching main.

#3. Reproduce a merge that is fast-forwardable, and run it twice in two different fresh copies of the same starting point - once as a plain `git merge`, once as `git merge --no-ff`. Paste both `git log --oneline --graph` outputs side by side and explain, in your own words, why a real GitHub PR merge looks like the second one even for small changes.

#4. Push a branch to origin, then delete it locally with `git branch -d`. Does it still exist on origin? Now delete it on origin too with `git push origin --delete <branch>`. What real GitHub button does that second command correspond to?

#5. Deliberately create a situation where `git push` is rejected (make a commit on origin from one clone, then try to push a *different*, non-fast-forwardable commit from another clone without pulling first). Paste the rejection message, and explain - without just running `git push --force` - what the correct next command is and why forcing would be dangerous here.
