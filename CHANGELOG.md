# Changelog

All notable changes to the `sanskrit_morph_converter` (SMC) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-04-30

### Added
- **Data Source Tracking:** Injected a `"source"` key (e.g., `"source": "DCS"`) directly into the final output dictionaries during JSON mode generation.
- **Cross-Platform Integration Test Suite:** Added a 14-test cases verifying translations between SH, ByT5, DCS, and Canonical formats.

### Changed
- **Canonical Schema Flattening:** Redesigned the Canonical JSON output to mirror the native SH JSON schema (`word`, `stem`, `root`, `inflectional_morphs`, `derivational_morph`).
- **CLI Output Normalization:** Standardized string-mode outputs across all adapters to return single-item lists `["word_lemma_tags"]` or empty lists `[]`.
- **CLI Input Unescaping:** Upgraded the CLI engine to safely translate literal `\t` and `\n` characters from bash inputs into actual tabs and newlines without mangling UTF-8 Sanskrit diacritics.

### Fixed
- **DCS Tab Parsing Bug:** Fixed a critical bug in `DCSAdapter` where it was splitting tokens using ByT5 underscores instead of CoNLL-U tabs (`\t`), and added fallback logic to parse 3-column CLI inputs correctly.
- **Trailing Underscore Deletion:** Eliminated a bug causing excessive underscores (underscores for empty output) (e.g., `word_lemma__`).
- **Duplicate JSON/String Output:** Fixed a logic loop error in the `encode` methods that was causing duplicate array appends depending on the format requested.

## [0.1.0] - Initial Release

### Added
- **Core Translation Engine (`converter.py`):** Established the base architecture for cross-platform Sanskrit morphological translation using a Pivot Tag Hub system.
- **Platform Adapters:** Introduced bidirectional adapters for Heritage (SH), ByT5, DCS, and SCL toolkits.
- **Dynamic Tag Mapping:** Implemented logic to map strictly-typed tags (e.g., SH's `pfp. [1]`) to Universal Dependencies (e.g., `VerbForm=Gerundive`).
- **Google Sheets Synchronization (`reference.tsv`):** Built the compiler pipeline to scrape, parse, and build normalizations, aliases, and deprecations directly from the project's central Google Sheet.
- **Batch Processing:** Enabled `convert_bulk` for high-throughput string and JSON array translations.
- **CLI Interface:** Built the terminal interface allowing users to pipe strings or JSON structures through the engine using `smc convert [SOURCE] [TARGET] -i [INPUT]`.