# ADR-001: Docstrings Style for Python

Architectural Decision Records (ADR) on the docstring style and its automated enforcement for Python source code.

- [1. State](#1-state)
- [2. Context](#2-context)
- [3. Decision](#3-decision)
  - [3.1. Google Style](#31-google-style)
  - [3.2. PEP 257 Baseline](#32-pep-257-baseline)
  - [3.3. Ruff pydocstyle Rules](#33-ruff-pydocstyle-rules)
- [4. Considered](#4-considered)
  - [4.1. PEP 257](#41-pep-257)
  - [4.2. Google Style](#42-google-style)
  - [4.3. NumPy Style](#43-numpy-style)
  - [4.4. reStructuredText Style](#44-restructuredtext-style)
  - [4.5. Ruff](#45-ruff)
  - [4.6. pydoclint](#46-pydoclint)
- [5. Consequences](#5-consequences)
- [6. Implementation](#6-implementation)
- [7. References](#7-references)

## 1. State

- Author(s): Sentenz
- Date: 2026-11-21
- Status: Proposed

## 2. Context

Python source code needs a single, explicit docstring convention. Without one, docstrings drift between formats (free text, reStructuredText field lists, Google sections, NumPy sections), reviews spend time on form instead of content, and tools that read docstrings (linters, API documentation generators, IDEs, AI coding agents) cannot rely on a consistent structure. Type annotations now carry parameter and return types, so the docstring convention must complement annotations instead of duplicating them.

1. Decision Drivers

    - Readability
      > Docstrings must be easy to read in source code and in terminal help output, for short and long descriptions alike.

    - Type Annotation Compatibility
      > Types are declared once in annotations; the docstring must not require repeating them.

    - Tool Support
      > Linters, documentation generators, and IDEs must parse the style natively or through a maintained extension.

    - Enforceability
      > Conformance must be verifiable automatically in pre-commit and CI rather than relying on code review alone.

    - Consistency
      > One style applies across all Python code; mixing styles is not allowed.

    - Low Maintenance Overhead
      > The convention must avoid duplicated information that drifts out of sync with the code.

## 3. Decision

The decision is a multiple selection of complementary options: Google style defines the docstring sections, PEP 257 defines the baseline structure, and Ruff enforces both.

### 3.1. Google Style

Google style is the docstring format for all Python code. Sections are introduced by a heading line ending in a colon and use indentation instead of markup. Types are taken from annotations.

| Element | Rule |
| ------- | ---- |
| Section headings | `Args:`, `Returns:`, `Yields:` (generators), `Raises:`, `Attributes:` |
| Indentation | Section contents use a 4-space hanging indent |
| Module | Starts with a docstring describing contents and usage |
| Class | Summary of what an instance represents; public attributes listed under `Attributes:` |
| Constructor | Parameters documented in the `__init__` docstring |
| Function or method | Required for public API, non-trivial size, or non-obvious logic; list each parameter by name under `Args:` |
| Types | Declared in annotations only; stated in the docstring only when no annotation exists |
| `Raises:` | Lists exceptions that are part of the interface, not exceptions raised on API misuse |
| Overrides | A method marked `@override` may omit its docstring unless it refines the base contract |
| Tests | Module, class, and `test_` method docstrings are optional |

```python
class Client:
    """A connection to a remote device.

    Attributes:
        host: Hostname or IP address of the device.
        timeout: Seconds to wait for a response.
    """

    def __init__(self, host: str, timeout: float = 2.0) -> None:
        """Initialize the client.

        Args:
            host: Hostname or IP address of the device.
            timeout: Seconds to wait for a response.
        """
        self.host = host
        self.timeout = timeout

    def read_register(self, address: int, *, retries: int = 3) -> int:
        """Read a holding register from the device.

        Args:
            address: Zero-based register address.
            retries: Additional attempts after a failed read.

        Returns:
            The raw 16-bit register value.

        Raises:
            TimeoutError: If the device does not respond after all attempts.
        """
        ...
```

1. Rationale

    - Readability
      > Indentation-based sections read well in source and in `help()` output without underline or field-list markup.

    - Type Annotation Compatibility
      > Parameters are listed by name only, so annotations remain the single source of type information.

    - Tool Support
      > Sphinx (Napoleon), mkdocstrings (Griffe), and Ruff support the style directly.

    - Enforceability
      > Ruff's `google` convention enables the missing-parameter check (D417), which the `numpy` and `pep257` conventions leave disabled.

    - Consistency
      > Google's guide fills gaps this ADR does not cover, so contributors have one reference for edge cases.

### 3.2. PEP 257 Baseline

PEP 257 is the baseline for docstring structure and applies to every docstring, independent of the section format in 3.1.

| Rule | Convention |
| ---- | ---------- |
| Quotes | Triple double quotes (`"""`) |
| Summary line | One physical line, imperative mood ("Read", not "Reads"), ends with a period, does not restate the signature |
| Structure | Blank line between summary and description; closing quotes on their own line for multi-line docstrings |
| Coverage | Public modules, classes, functions, and methods, including `__init__`, have docstrings |
| Content | Behavior, side effects, raised exceptions, and call restrictions; implementation details belong in code comments |

Where Google's guide permits descriptive or imperative summary lines, imperative mood applies, as PEP 257 prescribes.

1. Rationale

    - Consistency
      > One summary-line mood and one structure apply everywhere, instead of a per-file choice.

    - Tool Support
      > PEP 257 is the convention that docstring tools and the pydocstyle rule family implement.

    - Low Maintenance Overhead
      > Forbidding signature restatements removes information that changes with every refactoring.

### 3.3. Ruff pydocstyle Rules

Ruff enforces the docstring rules through its pydocstyle rule family (`D`) with `convention = "google"` set explicitly. The rules cover missing docstrings (D100 to D107), structure, and undocumented parameters (D417). Setting the convention explicitly avoids style auto-detection.

1. Rationale

    - Enforceability
      > Violations fail pre-commit and CI, so the convention does not depend on reviewer attention.

    - Tool Support
      > The standalone pydocstyle project is deprecated in favor of Ruff, which supports the same rule family.

    - Consistency
      > An explicit convention applies the same rules to every repository using the shared configuration.

## 4. Considered

### 4.1. PEP 257

[PEP 257](https://peps.python.org/pep-0257/) standardizes the high-level structure of docstrings without defining section markup.

- Pros

  - Official Python convention
    > Tool-independent and understood by every Python developer.

  - Minimal rules
    > Low adoption cost and little to maintain.

- Cons

  - No section syntax
    > Parameters, return values, and exceptions are free-form text that tools cannot parse into structure.

  - Weak enforcement
    > Ruff's `pep257` convention leaves the missing-parameter check (D417) disabled.

### 4.2. Google Style

[Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) is the docstring format of the Google Python Style Guide, using indented `Args:`, `Returns:`, and `Raises:` sections.

- Pros

  - Readable for short docstrings
    > Sphinx's Napoleon documentation rates the style as easier to read for short and simple docstrings.

  - Types from annotations
    > The guide asks for types in the docstring only when the code lacks an annotation.

  - Broad tool support
    > Supported by Sphinx Napoleon, Griffe and mkdocstrings, Ruff, and pydoclint.

  - Missing-parameter check
    > Ruff's `google` convention enables D417.

- Cons

  - Less suited to long docstrings
    > NumPy style tends to be easier to read for long, in-depth descriptions such as algorithm notes.

  - Whitespace-sensitive sections
    > Griffe treats a section without the required blank line above it as plain text, so typos fail silently.

  - Extension required in Sphinx
    > Sphinx needs the Napoleon extension to parse the sections.

### 4.3. NumPy Style

[NumPy Style](https://numpydoc.readthedocs.io/en/latest/format.html) is the numpydoc docstring standard, with hyphen-underlined section headings in reStructuredText.

- Pros

  - Suited to long docstrings
    > Underlined sections handle extended descriptions, notes, and mathematical content well.

  - Established in scientific Python
    > Mature standard with the numpydoc extension and parsers in Napoleon, Griffe, and Ruff.

- Cons

  - Vertical space
    > Sections take more lines than the Google equivalent, which adds noise to short docstrings.

  - Types repeated in docstrings
    > Parameter entries pair a name with a type, which duplicates annotations and drifts.

  - Missing-parameter check disabled
    > Ruff's `numpy` convention leaves D417 disabled, so undocumented parameters go unreported.

### 4.4. reStructuredText Style

[reStructuredText Style](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#info-field-lists) uses Sphinx field lists such as `:param name:`, `:type name:`, `:returns:`, and `:raises:`.

- Pros

  - Native to Sphinx
    > No extension is required, and the full reStructuredText feature set is available.

  - Parsed by Griffe and pydoclint
    > Documentation and consistency tooling can read the field lists.

- Cons

  - Visually dense
    > Napoleon exists because field lists are hard to read in source code.

  - Duplicated type information
    > `:type:` fields repeat what annotations already declare.

  - No Ruff convention
    > Ruff's pydocstyle conventions are `google`, `numpy`, and `pep257`, so a Sphinx-style convention is not available.

### 4.5. Ruff

[Ruff](https://docs.astral.sh/ruff/) is a Python linter and formatter that implements the pydocstyle rule family.

- Pros

  - Convention switch
    > A single setting selects `google`, `numpy`, or `pep257` rule sets.

  - Replaces pydocstyle
    > The pydocstyle project is deprecated in favor of Ruff.

  - Formatter integration
    > Ruff's formatter can format code examples inside docstrings.

- Cons

  - Form only
    > The rules verify structure and presence, not whether a docstring is accurate or useful.

  - Detection without a convention
    > Without an explicit convention, the section style is inferred heuristically, which can misclassify mixed docstrings.

### 4.6. pydoclint

[pydoclint](https://github.com/jsh9/pydoclint) checks that docstring sections match the function signature and implementation (arguments, returns, yields, raises).

- Pros

  - Signature consistency
    > Detects documented parameters that do not exist, wrong order, and missing `Raises:` or `Yields:` sections.

  - Multiple styles
    > Supports Google, NumPy, and Sphinx styles.

- Cons

  - Preview in Ruff
    > Ruff's pydoclint-derived `DOC` rules are documented as preview rules, so their behavior may change.

  - Additional tool
    > Standalone use adds a second docstring linter to the toolchain.

## 5. Consequences

- Positive

  - Single convention
    > One docstring format and one set of structural rules apply to all Python code.

  - Automated enforcement
    > Missing docstrings, structure errors, and undocumented parameters fail in pre-commit and CI.

  - Types declared once
    > Annotations remain the only place types are written.

  - Documentation tooling works out of the box
    > Sphinx with Napoleon and mkdocstrings parse the sections without custom parsing.

- Negative

  - Verbose for simple functions
    > A multi-line docstring must describe every parameter to satisfy D417.

  - Weaker fit for long, mathematical descriptions
    > Extended algorithm documentation reads better in NumPy style and moves into the description body or separate documents.

  - Form checks only
    > Linting cannot judge accuracy or usefulness; code review remains necessary for content.

- Risks

  - Legacy docstrings in other styles
    > They may be misparsed or ignored by section parsers; migrate them incrementally and keep the convention explicit.

  - Silent section parsing failures
    > A missing blank line before a section turns it into plain text; build the documentation in CI and review warnings.

  - Tooling changes
    > Ruff's `DOC` rules are in preview; revisit pydoclint-derived checks when they stabilize and record the change in a new ADR.

  - Upstream guide drift
    > This ADR is normative; the Google guide is a reference for unspecified cases and does not change the rules here.

## 6. Implementation

1. Configure Ruff

    Add the rules to `pyproject.toml` in every Python repository. The scope is all Python packages and scripts; generated and vendored code is excluded. The `docstring-code-format` setting is optional.

    ```toml
    [tool.ruff.lint]
    extend-select = ["D"]

    [tool.ruff.lint.pydocstyle]
    convention = "google"

    [tool.ruff.lint.per-file-ignores]
    "tests/**" = ["D"]

    [tool.ruff.format]
    docstring-code-format = true
    ```

2. Migrate existing code

    Baseline existing violations (for example with `ruff check --add-noqa`) and remove each suppression when its file is next changed. New and modified code must pass without suppressions.

3. Enforce in pre-commit and CI

    Run `ruff check` in the pre-commit configuration and in the CI pipeline so violations block merges.

4. Align documentation generation

    Where API documentation is generated, use Sphinx with `sphinx.ext.napoleon` or mkdocstrings-python with `docstring_style: google`, and treat section parsing warnings as build failures.

5. Publish the convention

    Reference this ADR from contributor guidelines and agent instructions so human and AI-generated code follow the same style.

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

6. Validate

    Confirm that `ruff check` passes, the documentation build reports no section parsing warnings, and code review verifies what linting cannot: imperative summary lines, accurate content, and no docstrings that only repeat the name.

## 7. References

- PEP 257 [Docstring Conventions](https://peps.python.org/pep-0257/) page.
- Google Python Style Guide [Comments and Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) section.
- numpydoc [style guide](https://numpydoc.readthedocs.io/en/latest/format.html) page.
- Sphinx [Napoleon extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) page.
- Griffe [docstring parsers](https://mkdocstrings.github.io/griffe/reference/docstrings) page for mkdocstrings.
- Ruff [undocumented-param (D417)](https://docs.astral.sh/ruff/rules/undocumented-param) rule page.
- Ruff [docstring-missing-returns (DOC201)](https://docs.astral.sh/ruff/rules/docstring-missing-returns/) rule page.
- Ruff FAQ on [NumPy and Google style docstrings](https://docs.astral.sh/ruff/faq/#does-ruff-support-numpy-or-google-style-docstrings) page.
- pydocstyle [repository](https://github.com/PyCQA/pydocstyle) page.
- pydoclint [repository](https://github.com/jsh9/pydoclint) page.
- Sentenz [ADR agent skill](https://github.com/sentenz/skills/blob/main/skills/adr/SKILL.md) page.

