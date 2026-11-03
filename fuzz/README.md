# Coverage-guided fuzzing

The Hypothesis properties in `tests/fuzz/` run through pytest and `make test-fuzz`.
The standalone Atheris target complements them with libFuzzer coverage feedback
and corpus mutation. It is not collected by pytest and adds no runtime dependency.

## Target and oracle

`fuzz_project_lookup.py` feeds arbitrary HTTP 200 response bodies through the real
`Client._send_request` JSON handling and `Client.find_project` validation. Imports
of the client and Requests are instrumented before use; the callback is also
instrumented. A fresh in-memory transport and response are created for each input.
No HTTP requests, environment changes, or per-input files are involved.

The query is fixed to name `sbom`, version `1`. The oracle checks that a list of
objects returns the unique exact match, or `None` when there is no match. Invalid
JSON, non-list responses, lists containing non-objects, and duplicate exact
matches must raise `ValidationError`. Only that expected rejection is caught;
assertions and unrelated exceptions fail the campaign. UTF-8 replacement decoding
matches the response's explicit encoding. JSON representations are compared to
avoid false failures for NaN values in unrelated metadata.

The 512-byte input limit applies inside the callback as well as in libFuzzer. It
bounds allocations and nesting for this first target; larger responses, other
status codes, and native-extension sanitizer coverage are outside its scope.
The seed corpus covers valid, malformed, ambiguous, near-match, missing-field,
mixed-type, and Unicode responses. The engine also exercises empty input.

## Install and run

Use CPython 3.11–3.14 on Linux (CI uses 3.14). The optional `fuzz` extra pins
[Atheris](https://github.com/google/atheris) separately from the ordinary `dev`
extra, so Python 3.10 and platforms without Atheris can still run pytest.

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,fuzz]'
make test-fuzz
make test-fuzz-coverage
```

The default campaign runs for 30 seconds, with a 5-second per-input timeout and
a 1 GiB RSS limit. CI additionally enforces a 90-second process timeout and a
5-minute job timeout, fails on crashes, and uploads `logs/fuzz/` even on failure.
The log includes libFuzzer's coverage (`cov`), feature (`ft`), corpus, and execution
statistics. A clean finite campaign is not proof of correctness.

For a longer local campaign:

```bash
make test-fuzz-coverage FUZZ_SECONDS=600
```

The first corpus directory, `logs/fuzz/corpus/project_lookup`, receives generated
inputs; the checked-in seed directory is read-only to libFuzzer. Reusing the
generated directory continues exploration. `logs/` is already ignored by Git.
Crash and timeout artifacts are written to `logs/fuzz/artifacts/`.

## Replay and retain failures

Replace `crash-HASH` with the actual saved artifact filename:

```bash
.venv/bin/python -m fuzz.fuzz_project_lookup logs/fuzz/artifacts/crash-HASH -runs=1
```

Replay all checked-in seeds without starting a mutation campaign:

```bash
.venv/bin/python -m fuzz.fuzz_project_lookup fuzz/corpus/project_lookup/* -runs=1
```

Record the Python/Atheris versions, command, log, and failing input. Confirm that
the failure is in production behavior rather than the oracle, minimize it, then
retain a small reviewed seed and a deterministic regression test under
`tests/unit/` (or a Hypothesis `@example`). Do not commit whole generated corpora
or inputs containing credentials or production data.
