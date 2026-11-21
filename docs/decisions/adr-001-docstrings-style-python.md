# ADR-001: Docstrings Style for Python

This record proposes a convention for documenting the behavior of the SBOM client and CLI in Python source.

- [1. State](#1-state)
- [2. Context](#2-context)
- [3. Decision](#3-decision)
  - [3.1. Google-style docstrings](#31-google-style-docstrings)
- [4. Considered](#4-considered)
  - [4.1. Google-style docstrings](#41-google-style-docstrings)
  - [4.2. NumPy-style docstrings](#42-numpy-style-docstrings)
  - [4.3. PEP 257 with free-form prose](#43-pep-257-with-free-form-prose)
- [5. Consequences](#5-consequences)
- [6. Implementation](#6-implementation)
- [7. References](#7-references)

## 1. State

- Author(s): Codex
- Date: 2026-11-21
- Status: Proposed

## 2. Context

The Python package serves two audiences. A caller of `Client.find_project` needs to know when a lookup returns `None` and when it raises an exception. A caller of a CLI command handler needs to know which failures become exit codes. Type annotations such as `dict | None` and `int` leave those distinctions open.

The client, CLI handlers, and HTTP helpers already use `Args:`, `Returns:`, and `Raises:` where applicable. Summary placement varies, and the current `find_project` docstring does not identify duplicate exact matches as a cause of `ValidationError`. The repository's Ruff configuration selects `E`, `F`, `W`, and `C90`. Docstring rules are outside that selection.

1. Decision Drivers

    - Caller-visible behavior
      > A reader should be able to handle meaningful outcomes from the docstring alone.
    - Readability in source
      > Summaries and section labels should be easy to scan in an editor or in Python's `help()` output.
    - Cost of adoption
      > Existing accurate descriptions should carry forward with minimal editing.

## 3. Decision

### 3.1. Google-style docstrings

Use PEP 257 conventions with Google-style sections for public modules, classes, functions, and methods under `src/sbom/`. Apply the same format to private helpers when their behavior warrants a docstring.

- Open with triple double quotes and a one-sentence summary ending in a period. Use an imperative verb for functions and methods. A simple contract can fit on one line. For longer docstrings, leave a blank line after the summary.
- Use `Args:` for parameters that need explanation. Match signature names and order, omit `self` and `cls`, and describe constraints, units, or meaningful defaults. Keep type declarations in annotations. For classes such as `Client`, document constructor arguments once in the class docstring.
- Use `Returns:` for meaningful results and `Yields:` for generator items. Explain the meaning of sentinels or exit codes. Omit a return section for a procedure that only returns `None`.
- Use `Raises:` for caller-visible exceptions, pairing each exception with the condition that triggers it. When a CLI handler translates a failure into an exit code, describe the code under `Returns:`.

1. Rationale

    - Familiar structure
      > Keeping the labels already used by the client and CLI preserves useful descriptions and limits the migration to gaps and inconsistencies.
    - Explicit outcomes
      > Separate result and exception sections give callers a predictable place to look for each outcome.

## 4. Considered

### 4.1. Google-style docstrings

Short labels introduce indented descriptions of parameters, results, and exceptions. [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods)

- Pros
  - Low migration cost
    > Most structured docstrings in the client and CLI already use these labels.
- Cons
  - Repetition
    > Listing every obvious parameter can obscure the few constraints that affect a call.

### 4.2. NumPy-style docstrings

Underlined headings separate sections such as `Parameters` and `Returns`. [numpydoc style guide](https://numpydoc.readthedocs.io/en/latest/format.html)

- Pros
  - Detailed parameter descriptions
    > Separate entries provide room for units, shapes, or longer explanations.
- Cons
  - Conversion cost
    > Existing sections would need rewriting, and typed parameter entries would duplicate information in the client signatures.

### 4.3. PEP 257 with free-form prose

PEP 257 defines summary and layout conventions while leaving section markup open. [PEP 257](https://peps.python.org/pep-0257/)

- Pros
  - Concision
    > A short paragraph suits a helper with a single straightforward effect.
- Cons
  - Variable placement
    > In a longer client method, readers must search the prose for each failure condition.

## 5. Consequences

- Positive
  - Predictable lookup
    > A reader can find the distinction between an empty result and an HTTP error under the same headings across client methods.
- Negative
  - Mixed formatting during adoption
    > Existing docstrings retain their current layout until the corresponding code is touched.
- Risks
  - Stale descriptions
    > A well-formatted docstring can still describe the wrong behavior. Review changed contracts against the implementation and relevant tests, including delegated exceptions.

## 6. Implementation

1. Apply the convention when adding a public interface or changing its behavior. Update the affected docstring in the same change. Start with the public client methods and CLI handlers, where callers act on the outcome.

2. Use the following docstring for `Client.find_project` as a review example. A successful response with zero exact matches and an HTTP 404 have distinct outcomes.

    ```python
    """Find a project by its exact name and version.

    Args:
        name: Project name to match.
        version: Project version to match.

    Returns:
        The matching project, or None if a valid result list has no exact match.

    Raises:
        exceptions.ValidationError: Either argument is empty, the result is
            not a list of project dictionaries, or multiple projects match.
        exceptions.NotFoundError: The lookup endpoint returns HTTP 404.
        exceptions.HTTPError: The endpoint returns another non-success status.
        exceptions.Error: The HTTP request fails at the network level.
    """
    ```

3. During review, compare parameter names with the signature and trace the documented results and exceptions through the method and its helpers. For the example above, check the lookup cases and the HTTP error cases in the client tests. Use code review for conformance under the current Ruff configuration.

## 7. References

- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)
- [Google Python Style Guide — Functions and Methods](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods)
- [numpydoc style guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Client implementation](../../src/sbom/client.py)
- [CLI handlers](../../src/sbom/cli.py)
- [HTTP helpers](../../src/sbom/utils/http.py)
- [Client unit tests](../../tests/unit/test_client.py)
- [Ruff configuration](../../pyproject.toml)
