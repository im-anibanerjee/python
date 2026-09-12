# Topic 5 — Virtual Environments & Package Management

*Phase 1, Intermediate group — item 2 of 6. Type every command yourself in your own terminal as you go — this topic is mostly muscle memory, not code.*

---

## 1. Why virtual environments exist

Every Python install has one shared pool of installed packages (`site-packages`) unless you tell it otherwise. Without a virtual environment, every project on your machine — this interview-prep repo, some old college assignment, a work script — all fight over the *same* set of installed package versions. Project A needs `requests==2.28`, Project B needs `requests==2.31` — with no isolation, installing one for one project silently breaks the other, because there's only ever one `requests` installed globally at a time.

A **virtual environment (venv)** is a self-contained, throwaway copy of the Python interpreter plus its own private `site-packages` folder, isolated from your system-wide Python and from every other project's venv. Each project gets its own sandbox of exactly the packages (and versions) it needs, with zero risk of one project's dependencies colliding with another's.

## 2. Creating a venv

```
python -m venv .venv
```

Read this literally: `python -m venv` means "run the `venv` module as a script," and `.venv` is the folder name it creates *right here*, in your current directory — that's an argument to the module, not part of the command name. `.venv` (with the leading dot) is the common convention — the dot hides it from casual folder listings on Linux/Mac (Windows shows it regardless), and it visually signals "this is tooling, not project content." You could name it anything (`venv`, `env`) — just be consistent and make sure it's in your `.gitignore` (you already have `.venv/` in there from the earlier setup).

This creates a folder containing a private copy of the Python interpreter, `pip`, and an empty `site-packages` — nothing installed yet.

## 3. Activating and deactivating

"Activating" a venv doesn't run anything from inside your code — it's a shell-level change to *your terminal session*, telling it "when I type `python` or `pip` from now on, use the copies inside `.venv`, not the system ones." The activation command differs by shell, which matters for you specifically since you've already hit shell differences with git:

**Windows, `cmd.exe`** (this is your prompt style — `D:\interview prep\python>`):
```
.venv\Scripts\activate.bat
```

**Windows, PowerShell:**
```
.venv\Scripts\Activate.ps1
```

**Git Bash / Linux / Mac:**
```
source .venv/Scripts/activate      # Git Bash on Windows
source .venv/bin/activate            # Linux / Mac (note: bin, not Scripts)
```

Once active, your prompt changes to show the venv name, e.g. `(.venv) D:\interview prep\python>` — that prefix is your confirmation it's actually active. To leave it:

```
deactivate
```

(same command on every shell).

## 4. What activation actually changes, mechanically

This is the part worth understanding rather than memorizing as ritual. Activation does two things to your current terminal session only (it doesn't touch anything permanently, and closing the terminal undoes it automatically):

It prepends `.venv\Scripts` (Windows) or `.venv/bin` (Mac/Linux) to your `PATH` environment variable — so when you type `python`, your shell searches `PATH` folder by folder and finds the venv's `python.exe` *before* it ever reaches the system one further down the list. Same for `pip`.

It sets an environment variable `VIRTUAL_ENV` pointing at the venv's folder — some tools check this to confirm a venv is active.

That's it — no magic, no hidden config file rewriting your imports. `python -m venv` just gives you a second, isolated copy of the interpreter and its package folder, and activation is purely a `PATH` trick to make your shell prefer that copy for as long as the session is active. This is exactly the kind of "how does it actually work under the hood" answer that separates "I ran the commands" from genuine understanding in an interview.

## 5. `pip` fundamentals

With a venv active, everything you install with `pip` goes into *that* venv's `site-packages`, not your system Python:

```
pip install requests                  # latest version
pip install requests==2.31.0          # exact version — pin it
pip install "requests>=2.28,<3.0"      # a version range
pip uninstall requests
pip list                                 # everything currently installed in THIS venv
pip show requests                       # version, location, and dependencies of one package
```

## 6. `requirements.txt` — reproducible environments

The whole point of isolating dependencies per-project is worthless if you can't recreate that exact set of packages somewhere else — a new machine, a teammate's laptop, a CI pipeline. `requirements.txt` is the standard, dead-simple answer:

```
pip freeze > requirements.txt
```

`pip freeze` prints every installed package *and its exact version* in the active venv; `>` redirects that output into a file. Anyone else can then recreate your exact environment with:

```
pip install -r requirements.txt
```

Worth knowing the actual limitation here, since it's a real gotcha: `pip freeze` dumps *everything* installed, including packages that got pulled in only as someone else's dependency, not things you directly asked for — so your `requirements.txt` ends up listing transitive dependencies pinned to whatever versions happened to be resolved at freeze-time, which can make later upgrades brittle. More disciplined projects separate "what I actually depend on" (hand-maintained, loosely pinned) from "the exact resolved lock" (auto-generated, fully pinned) — which is part of why newer tools like `poetry` and `uv` exist (§9below). For a learning-stage project, plain `pip freeze` is completely fine — just know it's the beginner tool, not the only one.

## 7. Version specifiers — pinning strategy

| Specifier | Means | Use when |
|---|---|---|
| `requests==2.31.0` | exactly this version, nothing else | you need perfect reproducibility (e.g. `pip freeze` output) |
| `requests>=2.28` | this version or newer, unbounded | rarely a good idea alone — a future breaking release could silently sneak in |
| `requests~=2.28` | "compatible release" — allows `2.28.x`, `2.29`... up to (not including) `3.0` | a common middle ground: bug fixes yes, breaking major versions no |
| `requests>=2.28,<3.0` | explicit range | same intent as `~=`, spelled out manually |

`==` is what you'll mostly reach for early on; `~=` is worth recognizing since it comes up in real `requirements.txt`/`pyproject.toml` files you'll read at a job.

## 8. The wider landscape — what else is out there

You'll hear several overlapping names; worth knowing what each actually is, briefly, since "what's the difference between X and Y" is a real interview question here:

`venv` — what you just used. Built into Python itself (stdlib), no install needed, one interpreter per environment, manages packages via plain `pip`.

`virtualenv` — the older, third-party tool `venv` was modeled on and eventually absorbed into the standard library. You'll see it in older codebases; functionally almost identical to `venv` today.

`conda` — a different ecosystem entirely, common in data science. Manages not just Python packages but entire binary dependencies (including non-Python things like specific C libraries, even different Python *versions* themselves) — heavier, but solves problems `pip`/`venv` alone can't (e.g. installing packages that need compiled C extensions with tricky system dependencies).

`pyenv` — solves a different problem: managing multiple *versions of Python itself* installed side by side (e.g. 3.9 for one project, 3.12 for another). Often used *together* with `venv` — `pyenv` picks the interpreter version, `venv` isolates that interpreter's packages per project.

`poetry` / `uv` — newer, all-in-one tools that combine dependency management, virtual environments, and packaging into one workflow, with proper lock files (the "resolved exact versions" file mentioned in §6) instead of hand-rolled `requirements.txt`. `uv` in particular has gotten a lot of attention recently for being dramatically faster than `pip`. You don't need either yet — `pip` + `venv` is what you should be fluent in first — but recognize the names if they come up.

## 9. Interview-distilled

"Why use a virtual environment?" — dependency isolation per project; without it, every project on a machine shares one global package pool and silently conflicts.

"What's in a `requirements.txt`?" — package names and pinned versions, generated by `pip freeze`, consumed by `pip install -r` to recreate an environment elsewhere.

"What does `pip install` actually do?" — downloads the package (and its declared dependencies) from PyPI (the Python Package Index, the default public registry) and installs it into whichever `site-packages` folder the currently active Python interpreter is using — the venv's, if one's active; the system's, if not.

"Difference between `pip` and `conda`?" — `pip` installs Python packages into an existing Python interpreter; `conda` manages entire environments including the interpreter version and non-Python binary dependencies, at the cost of being heavier and slower.

---

## Practice questions

1. **Create and inspect.** Create a venv named `.venv` in a scratch folder, activate it, and run `pip list`. Compare that output to `pip list` from a plain terminal with no venv active (deactivate first). Explain in a line or two what the difference tells you about isolation.

2. **Install, freeze, recreate.** Inside an active venv, install any two packages of your choice. Run `pip freeze > requirements.txt` and open the file — note that it likely lists more than the two packages you installed. Explain why (tie this to §6).

3. **Break isolation on purpose, then fix it.** With your venv active, run `pip show <a package you installed>` and note the `Location` line. Deactivate the venv and run the same `pip show` command again (it'll likely fail with "not found," or show a completely different location if that package happens to also be installed system-wide). Explain what changed about your shell between the two calls that caused this — tie your answer to §4 specifically (`PATH`, not "magic").

4. **Version specifier reasoning.** You're adding a package to a `requirements.txt` for a project you'll come back to in six months. Would you pin it with `==`, `~=`, or leave it unbounded? Justify your choice in 2-3 lines — there's a real tradeoff here between reproducibility and getting stuck on an old, possibly vulnerable version forever.

5. **Explain in your own words**, in 2-3 lines: what's the actual difference between `venv` and `pyenv`? (Hint: one manages *packages* for one interpreter; the other manages *which interpreter* you're even using.)

---

*Same as always — work through these in your own terminal, tell me what you find (especially for Q3, since the "not found" vs "different location" outcome depends on your specific machine setup), and say "next" when you're through and I'll build the doc for comprehensions & generators.*
