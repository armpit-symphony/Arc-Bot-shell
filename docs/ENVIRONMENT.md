# This repository needs an interpreter of its own

Arc pins `lima-runtime` to `40d6f13` and holds it there deliberately: it is the
v0.10 trust baseline, and `arc_bot_shell/service/config.py` refuses to start
against any other commit.

Lima-Office pins the same package to `0718af2` and tracks it forward.

Both are correct. Neither can move to satisfy the other. A single shared
interpreter can therefore only ever serve one of the two repositories, and the
failure is silent — the loser's tests import the wrong runtime and pass.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e . pytest    # Windows
.venv/bin/python -m pip install -e . pytest        # macOS and Linux
```

`.venv/` is ignored by git. Do not install this repository into a system or
user-level interpreter, and do not reuse Lima-Office's environment.

## Proving the environment is the right one

```bash
.venv/Scripts/python scripts/check-stack-pins.py --check-installed
```

This reads the commit pip recorded in `direct_url.json` at install time and
compares it with `stack.lock.json`. It is offline and takes no measurable time,
so it costs nothing to run before a test run.

Against the correct environment:

```
- installation checked: yes
- interpreter: C:\Users\limap\Arc-Bot-shell\.venv\Scripts\python.exe
- lima-runtime: installed 40d6f13 matches the lock
- failures: 0
Result: PASS
```

Against Lima-Office's environment:

```
- FAIL lima-runtime: ...\Lima-Office\.venv\Scripts\python.exe imports 0718af2,
  the lock pins 40d6f13; this interpreter belongs to another repository or is
  stale
Result: FAIL
```

## Why a version number is not enough

Both pins build `lima-runtime 0.1.0rc1`. The version string cannot tell them
apart, which is why the check reads the resolved commit instead.

The same reasoning rules out editable installs. An editable checkout can
contain any working tree at all, so `--check-installed` reports it as
unverifiable rather than accepting it.

## When the check fails after a pin moves

A bumped pin does not update an environment that already exists. Reinstall:

```bash
.venv/Scripts/python -m pip install -e . --force-reinstall --no-deps
.venv/Scripts/python -m pip install -e .
```

## What this check is not

It does not replace the consistency check. Files agreeing with the lock and the
interpreter agreeing with the lock are separate questions, and both have gone
wrong here independently. See [DEPENDENCY_PIN_LOCK.md](DEPENDENCY_PIN_LOCK.md).

It is deliberately not part of the default `check-stack-pins.py` run, because
consistency must stay offline and environment-independent so it can block a
pull request without depending on how CI installed anything.
