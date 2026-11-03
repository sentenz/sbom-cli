# Coverage-guided fuzzing

The `tests/fuzz/` suite is property-based testing with **Hypothesis**.
This directory contains a separate **Atheris/libFuzzer** target that uses
instrumented execution coverage to guide byte-level mutations.

## Target

`fuzz_project_lookup.py` exercises `Client.find_project()` with arbitrary
Dependency-Track HTTP response bodies. A deterministic in-memory session
supplies status 200 and never opens a network connection. The oracle checks:

- malformed JSON and non-list/mixed-type payloads are rejected;
- multiple exact matches raise `ValidationError`;
- zero or one exact match returns `None` or the corresponding project;
- exactly one GET request is performed with the expected parameters.

The committed seed corpus includes valid, absent, duplicate, malformed,
and wrong-shape project lookup responses. No live API, credentials, or
production data are required.

## Run

Requires CPython 3.12-3.14 on Linux and the optional fuzz dependencies.
Atheris 3.1.0 is installed independently of `[dev]` so normal tests remain
portable. From the repository root:

```bash
make test-setup
.venv/bin/python -m pip install -e '.[fuzz]'
make test-fuzz-guided
```

This runs **2,000 coverage-guided executions** (configurable with
`FUZZ_RUNS`) with a 2,048-byte maximum input and a five-second
per-input timeout. GitHub Actions also enforces a ten-minute job limit.
The harness itself rejects data longer than 2,048 bytes.

```bash
make test-fuzz-guided FUZZ_RUNS=10000 FUZZ_MAX_LEN=2048
```

Seeds are copied into `logs/fuzz/corpus/project_lookup/`; Atheris may
write newly discovered coverage-increasing inputs there. Crash artifacts
are saved under `logs/fuzz/artifacts/`. Both directories are ignored by
Git. Review and minimize a useful regression before checking it in.

## Reproduce a failure

```bash
.venv/bin/python -m fuzz.fuzz_project_lookup \
  logs/fuzz/artifacts/<crash-file> -runs=1
```

After confirming a defect, add a deterministic regression test and
retain a minimal seed with no sensitive data. A successful bounded
campaign provides evidence of explored paths, not proof of correctness.
