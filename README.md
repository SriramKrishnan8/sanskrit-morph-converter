# Sanskrit Morph Converter

[![PyPI version](https://badge.fury.io/py/sanskrit-morph-converter.svg)](https://badge.fury.io/py/sanskrit-morph-converter)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A Python engine for unifying, standardizing, and converting Sanskrit morphological tags across multiple computational paradigms. 

In Sanskrit Computational Linguistics, different tools like the Sanskrit Heritage engine, Samsaadhanii, neural models like ByT5, and baseline grammars like Svarupa output morphological analyses in vastly different formats and vocabularies. `sanskrit-morph-converter` provides a centralized, pivot-based architecture to translate these tagsets into a unified **Canonical Representation**.

## Installation

Install the package directly from PyPI:

```bash
pip install sanskrit-morph-converter
```

## Python API Usage

You can import the converter directly into your Python scripts to process strings or JSON outputs from various platforms. The core `.convert()` method takes a source platform, a target platform, and the raw input.

```python
from sanskrit_morph_converter.converter import RepresentationConverter

# Initialize the converter (automatically loads the compiled mapping TSVs)
converter = RepresentationConverter()
```

### Example 1: Converting ByT5 Output to Canonical
ByT5 outputs rely on underscore and pipe-separated strings. The converter easily parses these into standard Canonical properties.

```python
byt5_raw = "devam_deva_Case=Acc|Gender=Masc|Number=Sing"

# Convert ByT5 to Canonical
canonical_tags = converter.convert('ByT5', 'Canonical', byt5_raw)
print(canonical_tags)
# Output: [{'input': 'देवम्', 'stem': 'देव', 'root': '', 'morph': 'Case=Accusative|Gender=Masculine|Number=Singular'}]
```

### Example 2: Converting Sanskrit Heritage (SH) to DCS
The Sanskrit Heritage engine returns nested JSON dictionaries. You can pass the JSON string directly to convert it to another format, such as DCS.

```python
sh_raw = """{
    "input": "गच्छति", 
    "status": "Success", 
    "morph": [{"word": "गच्छति", "root": "गम्", "inflectional_morphs": ["pr. [1] ac. sg. 3"]}]
}"""

# Convert SH to DCS
dcs_tags = converter.convert('SH', 'DCS', sh_raw, output_format='string')
print(dcs_tags)
# Output (Example): ['gacchati\tgam\tMood=Ind|Number=Sing|Person=3|Tense=Pres']
```

## Command Line Interface (CLI)

The package includes a built-in CLI for batch processing files or testing quick strings directly from your terminal.

**Convert a single string:**
```bash
smc convert ByT5 Canonical -i "devam_deva_Case=Acc|Gender=Masc|Number=Sing"
```

**Process an entire file and save the output:**
```bash
smc convert SH Canonical -f data/sh_analysis.tsv -o data/canonical_results.tsv
```

**Change the output script (e.g., to WX or IAST):**
```bash
smc convert ByT5 SH -i "devam_deva_Case=Acc|Gender=Masc|Number=Sing" --script WX
```

## Architecture

This library operates on a flexible, three-stage pipeline: **Adapters** (to read the source format), a **Mapper** (to route to a mathematical Pivot), and an **Converter** (to format the target platform output).

### The Google Sheets Integration
To ensure this tool remains accessible to linguists and researchers who may not write code, **the mapping vocabulary is not hardcoded.** Instead, tag standardizations and lexical exceptions (like pronouns and causatives) are maintained collaboratively in a [**Master Google Sheet**](https://docs.google.com/spreadsheets/d/1dWyPWj-OKuikfyutYC4SYnESn712SUSir-VZ_eyigpA/edit?usp=sharing). 

When linguistic rules are updated in the sheet, you can use the built-in compiler to fetch the latest data and rebuild the internal `.tsv` files (`pivot_mapping.tsv`, `normalization.tsv`, etc.) without altering the Python engine.

**To fetch the latest mappings from the Google Sheet:**
```bash
sanskrit-morph update
```
*(Note: The pre-compiled `.tsv` files are already bundled with the PyPI package, so standard users do not need to run the compiler to use the tool).*

## 📜 License

This project is licensed under the GNU GENERAL PUBLIC LICENSE v3 - see the [LICENSE](LICENSE) file for details.