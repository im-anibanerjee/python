# Topic 5 — Virtual Environments & Package Management

*Phase 1, Intermediate group — item 2 of 6. Type every command yourself in your own terminal as you go — this topic is mostly muscle memory, not code.*

---

## 1. Why virtual environments exist

Every Python install has one shared pool of installed packages (`site-packages`) unless you tell it otherwise. Without a virtual environment, every project on your machine — this interview-prep repo, some old college assignment, a work script — all fight over the *same* set of installed package versions. Project A needs `requests==2.28`, Project B needs `requests==2.31` — with no isolation, installing one for one project silently breaks the other, because there's only ever one `requests` installed globally at a time.

A **virtual environment (venv)** is a self-contained, throwaway copy of the Python interpreter plus its own private `site-packages` folder, isolated from your system-wide Python and from every other project's venv. Each project gets its own sandbox of exactly the packages (and versions) it needs, with zero risk of one project's dependencies colliding with another's.

### The problem, made concrete with a real, verified example

Rather than take "they'd silently conflict" on faith, here's the actual, real difference between a fresh venv's package list and the system Python's package list, run back to back on the same machine:

```
Fresh venv's pip list:
    Package    Version
    ---------- -------
    pip        24.0
    setuptools 79.0.1

System python3's pip show for a package already installed system-wide:
    Name: requests
    Version: 2.33.1
    Location: /root/.local/lib/python3.11/site-packages
    Requires: certifi, charset_normalizer, idna, urllib3
    Required-by: conan, grip, markitdown, mkdocs-material
```

The venv genuinely starts life knowing nothing about `requests` at all — not "aware of it but a different version," *completely absent* — while the system Python already has a specific version installed, at a specific location, with its own web of dependents (`Required-by`) that could each have their own version expectations. That `Required-by` line is the concrete shape of the "every project fights over the same shared pool" problem: `conan`, `grip`, `markitdown`, and `mkdocs-material` are all system-wide tools that happen to depend on `requests` too — if any one of them needed a different, incompatible version, upgrading `requests` to satisfy it could quietly break the others. A venv sidesteps this entirely by giving each project's dependencies their own private copy, with no shared tenants at all.

## 2. Creating a venv

```
python -m venv .venv
```

Read this literally: `python -m venv` means "run the `venv` module as a script," and `.venv` is the folder name it creates *right here*, in your current directory — that's an argument to the module, not part of the command name. `.venv` (with the leading dot) is the common convention — the dot hides it from casual folder listings on Linux/Mac (Windows shows it regardless), and it visually signals "this is tooling, not project content." You could name it anything (`venv`, `env`) — just be consistent and make sure it's in your `.gitignore` (you already have `.venv/` in there from the earlier setup).

This creates a folder containing a private copy of the Python interpreter, `pip`, and an empty `site-packages` — nothing installed yet.

### Running this for real, and looking inside the folder it creates

**Real, verified output** — creating an actual `.venv` and listing what it contains:

```
$ python -m venv .venv
$ ls .venv
bin
include
lib
lib64
pyvenv.cfg
```

**Flow diagram — what each of those five items actually is:**

```
.venv/
├── bin/            ← contains the venv's OWN copies of `python`,
│                      `pip`, and `activate` — this is the folder
│                      that gets prepended to PATH on activation (§4)
├── include/         ← C headers, needed only if you ever compile a
│                      package with native C extensions — rarely
│                      touched directly
├── lib/             ← this is where the venv's PRIVATE site-packages
│                      lives — lib/python3.11/site-packages/ — this
│                      is the folder that stays empty until you
│                      pip install something INTO this venv specifically
├── lib64/            ← on many systems, just a symlink to lib/ (a
│                      Linux convention for 64-bit library paths)
└── pyvenv.cfg        ← a small text file recording which real Python
                         interpreter this venv was created from, and
                         its version — how the venv "remembers" its
                         own configuration
```

The genuinely important one to build intuition around is `lib/.../site-packages` — it starts life completely empty (confirmed by the `pip list` in §5 below, which only shows `pip` and `setuptools` — the two things every fresh venv bootstraps with, not anything you'd recognize as "your" dependencies) and stays that way until you explicitly `pip install` something while this venv is active. That emptiness *is* the isolation — there is no shared pool for this venv to accidentally inherit packages from.

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

### Running `source .venv/bin/activate` for real, and watching `PATH` and `VIRTUAL_ENV` change with your own eyes

**Real, verified output** — printing `PATH`'s first few entries and `VIRTUAL_ENV` before and after activation:

```
Before activation, PATH (first entries):
    /home/claude/.npm-global/bin
    /root/.local/bin
    /root/.cargo/bin
    ...

After  source .venv/bin/activate  :
    PATH (first entries):
    /tmp/.../venvdemo/.venv/bin        ← the venv's bin/ folder, NOW FIRST
    /home/claude/.npm-global/bin
    /root/.local/bin
    ...

    VIRTUAL_ENV=/tmp/.../venvdemo/.venv

    which python  -> /tmp/.../venvdemo/.venv/bin/python
    which pip     -> /tmp/.../venvdemo/.venv/bin/pip
```

**Flow diagram — exactly how `which python` finds a different answer after activation, tied directly to how your shell resolves any command name:**

```
Your shell resolves a bare command name (like "python") by searching
PATH — a colon-separated LIST of folders — checking each folder LEFT
TO RIGHT, and running the FIRST matching executable it finds.

BEFORE activation:
    PATH = /home/claude/.npm-global/bin : /root/.local/bin : ... : /usr/bin : ...
    "python" search order: .npm-global/bin (no python here) ->
        /root/.local/bin (maybe, maybe not) -> ... eventually reaches
        wherever the SYSTEM python actually lives (commonly /usr/bin)
    → finds the SYSTEM interpreter

`source .venv/bin/activate` runs a small shell script that does,
in effect:
    export PATH="/full/path/to/.venv/bin:$PATH"     ← PREPENDS, does
                                                        not replace
    export VIRTUAL_ENV="/full/path/to/.venv"

AFTER activation:
    PATH = /full/path/to/.venv/bin : /home/claude/.npm-global/bin : ...
                    ▲
                    └─ this is now checked FIRST, and .venv/bin DOES
                       contain a file literally named "python" (a
                       copy/symlink to the interpreter this venv was
                       built from)
    "python" search order: .venv/bin (FOUND immediately) → STOPS HERE
    → finds the VENV's interpreter, never even checks the rest of PATH
```

This confirms the doc's claim precisely: nothing about Python itself changed, nothing was reinstalled, no config file was rewritten — the *only* thing that happened is that one folder got moved to the front of a search list your shell was already using for every command you type, not just `python`. That's the entire mechanism, and it's also exactly why closing the terminal "undoes" activation automatically: `PATH` and `VIRTUAL_ENV` are just variables living in that one shell process's memory, gone the instant the shell exits, with nothing persisted anywhere.

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

### Running `pip list` and `pip show` for real, both inside a fresh venv and against the system Python

**Real, verified output** — `pip list` immediately after creating the venv in §2, before installing anything at all:

```
Package    Version
---------- -------
pip        24.0
setuptools 79.0.1
```

Confirms exactly what §2 already promised: a brand-new venv's package list contains only the two bootstrapping tools (`pip` itself, and `setuptools`, which `pip` relies on internally) — genuinely nothing else, not even packages that happen to already be installed system-wide.

**Real, verified output** — `pip show requests`, run against the *venv* (where `requests` was never installed) versus the *system* Python (where it already was, from other tooling on this machine):

```
Inside the venv:
    WARNING: Package(s) not found: requests

Against the system python3:
    Name: requests
    Version: 2.33.1
    Location: /root/.local/lib/python3.11/site-packages
    Requires: certifi, charset_normalizer, idna, urllib3
    Required-by: conan, grip, markitdown, mkdocs-material
```

This is a genuinely useful real-world demonstration of isolation, not a hypothetical: the *exact same command*, `pip show requests`, gives a completely different answer depending purely on which `pip` — venv or system — is being asked, because each one only knows about its own private `site-packages` folder. This is directly the scenario Practice Question 3 below asks you to reproduce and explain on your own machine — you now have a worked reference for what "isolation" looks like when you actually run it.

**Flow diagram — why `pip install X` and `pip show X` always answer relative to whichever Python they're attached to, never a global truth:**

```
Every `pip` executable is really just a thin wrapper that's
PERMANENTLY associated with one specific Python interpreter — the
one it was installed alongside. .venv/bin/pip and the system's pip
are two ENTIRELY separate programs that happen to share a name and
behavior, not "the same pip talking to two different scopes."

.venv/bin/pip install requests
    → downloads requests, writes its files into
      .venv/lib/python3.11/site-packages/requests/
    → this is INVISIBLE to any other pip, including the system one

.venv/bin/pip show requests   (after that install)
    → looks ONLY inside .venv/lib/.../site-packages/
    → finds it, reports it

/usr/bin/pip3 show requests   (the system one, run separately)
    → looks ONLY inside the SYSTEM's own site-packages
    → has no knowledge the venv's copy exists at all
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

### Running `pip freeze` for real, on the still-empty venv

**Real, verified output** — `pip freeze` run on the exact same fresh venv from §5, which has only `pip` and `setuptools` installed:

```
$ pip freeze
(nothing printed at all — empty output)
```

This is worth noticing precisely because it's a little surprising: `pip list` showed two packages (`pip`, `setuptools`) a moment ago, but `pip freeze` shows *nothing*. That's not a bug — `pip freeze`'s job is specifically to produce a `requirements.txt`-ready list of packages *you'd want reinstalled elsewhere*, and `pip` and `setuptools` are considered bootstrapping tools that every fresh venv already gets automatically from `python -m venv` itself — so `freeze` deliberately excludes them, on the reasoning that listing them in your `requirements.txt` would be redundant noise, not useful reproducibility information.

**Flow diagram — the "transitive dependency noise" limitation, made concrete with the `requests` example from §5, imagining it actually installed:**

```
You run:  pip install requests

pip doesn't just install requests — it also has to install everything
REQUESTS ITSELF depends on to function, recursively. From the real
`pip show requests` output in §5:

    Requires: certifi, charset_normalizer, idna, urllib3

So a single `pip install requests` actually populates site-packages
with FIVE packages total: requests, plus its four dependencies —
even though you only ever typed one package name.

pip freeze > requirements.txt   now captures ALL FIVE, each pinned to
whatever specific version pip happened to resolve at that moment:

    requests==2.33.1
    certifi==2025.1.1        ← you never asked for this directly
    charset_normalizer==...   ← you never asked for this directly
    idna==...                 ← you never asked for this directly
    urllib3==...               ← you never asked for this directly

Six months later, urllib3 releases a security fix — but your
requirements.txt has it hard-pinned to the old version, because
freeze captured it as a fixed snapshot, not as "whatever version
requests currently needs." Upgrading means manually noticing and
editing a dependency you never consciously chose to pin in the
first place — this is the "brittle" problem the doc is warning about.
```

The distinction the doc draws — "what I actually depend on" vs. "the exact resolved lock" — maps directly onto this: *you* only ever consciously wanted `requests`; everything else in that `requirements.txt` is an implementation detail of `requests` that `pip freeze` flattens into one undifferentiated list, with no record of *why* each line is there.

## 7. Version specifiers — pinning strategy

| Specifier | Means | Use when |
|---|---|---|
| `requests==2.31.0` | exactly this version, nothing else | you need perfect reproducibility (e.g. `pip freeze` output) |
| `requests>=2.28` | this version or newer, unbounded | rarely a good idea alone — a future breaking release could silently sneak in |
| `requests~=2.28` | "compatible release" — allows `2.28.x`, `2.29`... up to (not including) `3.0` | a common middle ground: bug fixes yes, breaking major versions no |
| `requests>=2.28,<3.0` | explicit range | same intent as `~=`, spelled out manually |

`==` is what you'll mostly reach for early on; `~=` is worth recognizing since it comes up in real `requirements.txt`/`pyproject.toml` files you'll read at a job.

### Verifying exactly what each specifier matches, for real, using the same parser `pip` itself uses internally

The table states what each specifier *means* in words — here's real, programmatic proof of what it actually *matches*, using Python's own `packaging` library (the same dependency-parsing engine `pip` is built on):

```python
from packaging.requirements import Requirement

for spec in ["requests==2.31.0", "requests>=2.28", "requests~=2.28", "requests>=2.28,<3.0"]:
    r = Requirement(spec)
    print(spec, "->", r.specifier)
```

**Real, verified output:**

```
requests==2.31.0 -> ==2.31.0
requests>=2.28 -> >=2.28
requests~=2.28 -> ~=2.28
requests>=2.28,<3.0 -> <3.0,>=2.28
```

And the part that's genuinely worth seeing rather than just reading a definition of — testing `~=2.28` against a spread of real candidate version numbers, to confirm exactly where its boundaries actually sit:

```python
from packaging.specifiers import SpecifierSet
spec = SpecifierSet("~=2.28")
for v in ["2.27.0", "2.28.0", "2.28.9", "2.29.0", "3.0.0"]:
    print(v, spec.contains(v))
```

**Real, verified output:**

```
2.27.0 False
2.28.0 True
2.28.9 True
2.29.0 True
3.0.0 False
```

**Flow diagram — why `~=2.28` accepts `2.28.9` and `2.29.0` but rejects both `2.27.0` and `3.0.0`, which is the exact behavior the "compatible release" description in the table is describing in prose:**

```
~=2.28   is defined as shorthand for   >=2.28, ==2.*

    "==2.*" means: the version number must start with "2." — any
    MINOR or PATCH version is fine, as long as the MAJOR version
    stays exactly 2.

    2.27.0  -> fails ">=2.28" (2.27 is older than 2.28)      -> False
    2.28.0  -> satisfies ">=2.28" AND starts with "2."         -> True
    2.28.9  -> satisfies ">=2.28" AND starts with "2."         -> True
    2.29.0  -> satisfies ">=2.28" AND starts with "2."         -> True
              (a newer MINOR version within the same major line
               is exactly what "bug fixes yes" in the table means)
    3.0.0   -> starts with "3.", NOT "2."                        -> False
              (a MAJOR version bump — by convention, this signals
               "may contain breaking changes" — is exactly what
               "breaking major versions no" in the table means)
```

This is precisely why `~=` sits as "a common middle ground" in the table: `>=2.28` alone would have let `3.0.0` through too (accepting genuinely anything newer, including breaking changes), while `==2.31.0` alone would reject even a harmless bug-fix release like `2.31.1`. `~=2.28` draws the line exactly at the semantic-versioning convention that a major-version bump is where breaking changes are expected to live.

## 8. The wider landscape — what else is out there

You'll hear several overlapping names; worth knowing what each actually is, briefly, since "what's the difference between X and Y" is a real interview question here:

`venv` — what you just used. Built into Python itself (stdlib), no install needed, one interpreter per environment, manages packages via plain `pip`.

`virtualenv` — the older, third-party tool `venv` was modeled on and eventually absorbed into the standard library. You'll see it in older codebases; functionally almost identical to `venv` today.

`conda` — a different ecosystem entirely, common in data science. Manages not just Python packages but entire binary dependencies (including non-Python things like specific C libraries, even different Python *versions* themselves) — heavier, but solves problems `pip`/`venv` alone can't (e.g. installing packages that need compiled C extensions with tricky system dependencies).

`pyenv` — solves a different problem: managing multiple *versions of Python itself* installed side by side (e.g. 3.9 for one project, 3.12 for another). Often used *together* with `venv` — `pyenv` picks the interpreter version, `venv` isolates that interpreter's packages per project.

`poetry` / `uv` — newer, all-in-one tools that combine dependency management, virtual environments, and packaging into one workflow, with proper lock files (the "resolved exact versions" file mentioned in §6) instead of hand-rolled `requirements.txt`. `uv` in particular has gotten a lot of attention recently for being dramatically faster than `pip`. You don't need either yet — `pip` + `venv` is what you should be fluent in first — but recognize the names if they come up.

### Where each tool actually sits, drawn as one picture

This section is names and definitions rather than runnable code, so instead of a code trace, here's the relationship between all five tools laid out spatially — this is the mental model worth having cold for the "what's the difference between X and Y" interview question the doc calls out:

```
                    WHICH PYTHON VERSION?
                    ┌─────────────────────┐
                    │       pyenv          │   ← manages 3.9 vs 3.11
                    │  (multiple Python     │      vs 3.12 etc., side
                    │   versions, side by    │      by side on one
                    │   side)                 │      machine
                    └──────────┬───────────┘
                               │  (pyenv picks WHICH interpreter;
                               │   venv then isolates ITS packages)
                               ▼
                    WHICH PACKAGES, PER PROJECT?
        ┌──────────────┬──────────────┬───────────────────┐
        │   venv /      │    conda      │   poetry / uv       │
        │   virtualenv   │               │                      │
        │                │  entire        │  dependency mgmt +   │
        │  stdlib, pip-   │  environments   │  venv + packaging,   │
        │  based,          │  incl. non-     │  all-in-one, with     │
        │  lightweight     │  Python binary   │  a real lock file    │
        │                │  deps            │  instead of freeze()  │
        └──────────────┴──────────────┴───────────────────┘
              ▲                                      ▲
              │                                      │
         what THIS doc has you              what requirements.txt's
         using — the foundational           "hand-rolled, brittle
         layer everything else               lock" limitation from
         either wraps or replaces            §6 is pushing toward
```

The practical reading of this diagram: `pyenv` and `venv` solve genuinely *different* problems (which interpreter, vs. which packages for one interpreter) and are commonly used *together*, not as alternatives to each other; `conda` is a heavier, broader alternative to the `venv`+`pip` combination specifically for cases involving non-Python dependencies; and `poetry`/`uv` are attempts to replace the `venv`+`pip`+hand-written-`requirements.txt` combination with one integrated tool that also fixes the "transitive dependency noise" problem from §6 via a proper lock file. None of them replace the concepts you just learned — `pip`, `venv`, and version specifiers are the vocabulary every one of these tools is still built on top of.

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
