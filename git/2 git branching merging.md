# Git branching & merging: parallel timelines, and bringing them back together

Second topic in the Git group. Every command below was genuinely run through `git 2.43.0` on a scratch repo - hashes, conflict markers, and merge output are all real, not reconstructed.

## 1. What a branch actually is (simple version)

A branch is not a copy of your files. It's a single, tiny label - just a name pointing at one specific commit. That's the whole mechanism. When you "switch branches," Git isn't copying anything around; it's just changing which commit that label points at, and rewriting your working directory to match that commit's snapshot.

**Real-life example:** imagine a shared document where "main" is a bookmark on page 40 (the current agreed-on version), and you stick a second bookmark, labeled "my-edit," on that same page 40 to start experimenting. As you write new pages, your "my-edit" bookmark moves forward with you, but "main" stays put at page 40 until someone decides to fold your new pages back in.

**Real-world use case:** you're fixing a bug in a shared codebase. You don't want half-finished, possibly-broken code sitting on `main` where everyone else pulls from. You make a branch, do your work there in isolation, and only bring it into `main` once it's done and reviewed (this is exactly the branch -> PR -> merge shape the Wknd 1-3 build asks for).

**Technical deep dive:** internally, a branch is a file in `.git/refs/heads/<name>` containing nothing but a commit hash. `HEAD` (what you're "currently on") is itself just a pointer to whichever branch pointer is currently active. Creating a branch is one tiny file write; it's intentionally cheap so you're not discouraged from making one for every small piece of work.

## 2. Creating and switching branches

```bash
$ git branch feature-login
$ git branch
```
```
  feature-login
* main
```
`git branch <name>` creates the new pointer, aimed at whatever commit `HEAD` currently points to - but it does **not** move you onto it. `git branch` (no args) lists all branches and marks the current one with `*`.

```bash
$ git switch feature-login
```
```
Switched to branch 'feature-login'
```
`git switch` moves `HEAD` onto that branch and updates every file on disk to match its commit. (Older tutorials use `git checkout feature-login` for the same thing - `switch` is the newer, purpose-built command that split off from `checkout`'s many overloaded jobs.)

## 3. A commit on a branch, and the graph that results

```bash
$ echo "def login(): pass" >> app.py
$ git add app.py
$ git commit -q -m "add login stub"
$ git log --oneline --graph --all --decorate
```
```
* e2406b3 (HEAD -> feature-login) add login stub
* 2a0f2d9 (main) add initial app.py
```
```
 main:           2a0f2d9
 feature-login:                e2406b3 (HEAD)
                 \___________/
                  same history up to here, then feature-login moved ahead alone
```
`--graph --all --decorate` together are the single most useful `git log` incantation for understanding branch state at a glance: `--all` shows every branch's history (not just the current one), `--graph` draws the ASCII lines connecting commits, and `--decorate` prints which branch names/`HEAD` point at which commit. Right now `main` is one commit behind `feature-login`.

## 4. Fast-forward merge: when there's nothing to actually reconcile

```bash
$ git switch main
$ git merge feature-login
```
```
Updating 2a0f2d9..e2406b3
Fast-forward
 app.py | 1 +
 1 file changed, 1 insertion(+)
```
```bash
$ git log --oneline --graph --all --decorate
```
```
* e2406b3 (HEAD -> main, feature-login) add login stub
* 2a0f2d9 add initial app.py
```
Because `main` hadn't moved at all since `feature-login` branched off it, there's no conflicting work to reconcile - Git just slides the `main` label forward to point at the same commit `feature-login` is already on. That's what "fast-forward" means: no new commit is created, no merge actually happens in the reconciliation sense - it's just a pointer update. This is why `git log` afterward shows both names on the same commit.

```bash
$ git branch -d feature-login
```
```
Deleted branch feature-login (was e2406b3).
```
Once a branch's work is fully merged elsewhere, it's safe to delete - the commits themselves aren't going anywhere (they're still reachable through `main`), only the now-redundant label disappears.

## 5. Real (3-way) merge: when both sides actually moved

Fast-forward only works if one side stood still. The far more common real situation is that `main` *also* got new commits while your branch was being worked on - now Git has to genuinely combine two different histories.

```bash
$ git branch feature-signup
$ echo "def logout(): pass" >> app.py
$ git add app.py && git commit -q -m "add logout stub on main"

$ git switch feature-signup
$ echo "def signup(): pass" >> app.py
$ git add app.py && git commit -q -m "add signup stub on feature-signup"

$ git log --oneline --graph --all --decorate
```
```
* 774d75e (HEAD -> feature-signup) add signup stub on feature-signup
| * 8ab1a35 (main) add logout stub on main
|/
* e2406b3 add login stub
* 2a0f2d9 add initial app.py
```
The graph now genuinely forks - `main` and `feature-signup` each have a commit the other doesn't. This is the shape that forces a **3-way merge**: Git looks at the common ancestor (`e2406b3`), and both tips (`8ab1a35` and `774d75e`), and tries to combine the changes each side made since that ancestor.

```bash
$ git switch main
$ git merge feature-signup -m "merge feature-signup into main"
```
```
Auto-merging app.py
CONFLICT (content): Merge conflict in app.py
Automatic merge failed; fix conflicts and then commit the result.
```
Both sides edited the *same file*, but Git couldn't tell whether the two new lines (`def logout()`, `def signup()`) were meant to both survive or replace each other - that judgment call is genuinely outside what a merge algorithm can decide on its own, so it stops and asks a human.

## 6. Resolving a real conflict, step by step

```bash
$ git status
```
```
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   app.py
```
Git leaves the repo in a special "mid-merge" state and tells you exactly what to do: fix the file, then `git add` it (staging now means something slightly different here - "I've resolved this," not just "here's a new change"), then commit.

The file itself now contains conflict markers:
```
print('hello from the CLI tool')
def login(): pass
<<<<<<< HEAD
def logout(): pass
=======
def signup(): pass
>>>>>>> feature-signup
```
`<<<<<<< HEAD` down to `=======` is *your current branch's* version of the conflicting lines; `=======` down to `>>>>>>> feature-signup` is *the incoming branch's* version. Resolving means editing this by hand into what the file should actually say, and deleting all three marker lines - Git will never guess this part for you.

```bash
$ cat > app.py << 'EOF'
print('hello from the CLI tool')
def login(): pass
def logout(): pass
def signup(): pass
EOF
```
Here, both stubs are genuinely wanted, so the fix is keeping both and dropping the markers.

```bash
$ git add app.py
$ git status
```
```
On branch main
All conflicts fixed but you are still merging.
  (use "git commit" to conclude merge)

Changes to be committed:
	modified:   app.py
```
```bash
$ git commit -q -m "merge feature-signup into main, keep both stubs"
$ git log --oneline --graph --all --decorate
```
```
*   1c7adb0 (HEAD -> main) merge feature-signup into main, keep both stubs
|\
| * 774d75e (feature-signup) add signup stub on feature-signup
* | 8ab1a35 add logout stub on main
|/
* e2406b3 add login stub
* 2a0f2d9 add initial app.py
```
The commit here (`1c7adb0`) is genuinely different from every commit seen so far: it has **two parents** (`8ab1a35` and `774d75e`), which is the technical definition of a merge commit - it's the one point in history that stitches two lines of development back into one.

## 7. `-d` vs `-D`: a safety rail, and how to override it on purpose

```bash
$ git branch throwaway
$ git switch throwaway
$ echo "TODO: never finished this" >> app.py
$ git add app.py && git commit -q -m "half-finished idea"
$ git switch main
$ git branch -d throwaway
```
```
error: the branch 'throwaway' is not fully merged.
If you are sure you want to delete it, run 'git branch -D throwaway'
```
`-d` (lowercase) checks first: is every commit on this branch reachable from somewhere else (already merged)? If not, deleting it would make that work unreachable and effectively lost, so `-d` refuses and tells you exactly what to type if you're sure.

```bash
$ git branch -D throwaway
```
```
Deleted branch throwaway (was 9dcf270).
```
`-D` is shorthand for "force delete, I know it's not merged, do it anyway." The commit object itself isn't instantly gone (it lingers, recoverable via `git reflog`, until Git's garbage collection eventually cleans it up - reflog and recovery is covered in the undo/history doc), but the branch's *name* - the easy way back to it - is gone the moment `-D` runs. This is the real reason `-d` defaults to being cautious: an accidental `-D` on genuinely unmerged work is one of the few Git mistakes that isn't a two-second undo.

```bash
$ git branch -d feature-signup
```
```
Deleted branch feature-signup (was 774d75e).
```
Ordinary cleanup once work is safely merged: `-d` succeeds silently here because every commit on `feature-signup` is reachable through `main`'s merge commit.

## Connecting it back

A branch is one small pointer; switching branches is Git rewriting your working directory to match wherever that pointer sits. Merging is just "make one branch's history include the other's" - and the *only* reason that's ever complicated is when both sides changed the same lines and Git can't guess which change should win. Fast-forward is the easy case (one side never moved); a real 3-way merge, with or without a conflict, is what happens once both sides have their own new commits. `-d`/`-D` is Git protecting you from deleting the *only remaining pointer* to work that isn't reachable any other way - which is the same theme the next doc (remotes and PRs) builds on: a pull request is, underneath, exactly this branch -> merge shape, just happening across two repositories instead of one.

---

## Practice questions

#1. Create two branches off `main` that each add a different new file (no shared lines, so no conflict is possible). Merge both into `main` and paste the `git log --oneline --graph --all --decorate` output. Was the second merge fast-forward or a real merge commit - explain why, referencing whether `main` had moved.

#2. Deliberately create a conflict (edit the *same line* of the *same file* differently on two branches), resolve it by hand, and paste the conflict-marker text you saw plus your resolved version. In a comment, explain what `<<<<<<<`, `=======`, and `>>>>>>>` each mark.

#3. After resolving a conflict but before running `git commit`, run `git merge --abort`. What state does the repo end up in - does it look like the merge never happened? Explain what you'd use this for in a real situation.

#4. Create a branch, commit on it, merge it into `main`, then try `git branch -d` on it. It should succeed. Now create a second branch, commit on it, but merge it into some *other* branch instead of `main` (or don't merge it at all) - then try `git branch -d` on `main` for that branch's name. Reproduce the refusal message and explain, in your own words, exactly what Git is protecting you from.

#5. Run `git switch -c quick-fix` (note the `-c`) from `main` instead of the separate `git branch` + `git switch` used throughout this doc. What did it do in one step? Then look up (or test) `git checkout -b` - is it the same thing under an older name?
