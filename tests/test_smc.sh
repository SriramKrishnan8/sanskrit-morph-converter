#!/bin/bash

echo "========================================================="
echo "🧪 Svarupa Morph Converter (SMC) - Integration Test Suite"
echo "========================================================="

# ---------------------------------------------------------
# TEST BATCH 1: Standard Nouns & Cases
# ---------------------------------------------------------
echo -e "\n--- Test 1.A: Noun [SH -> ByT5] (Accusative) ---"
smc convert SH ByT5 -i '{"input": "अग्निम्", "status": "Success", "segmentation": ["अग्निम्"], "morph": [{"word": "अग्निम्", "stem": "अग्नि", "root": "", "derivational_morph": "", "inflectional_morphs": ["m. sg. acc."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 1.B: Noun [ByT5 -> SH] (Accusative) ---"
smc convert ByT5 SH -i "agnim_agni_Case=Acc|Gender=Masc|Number=Sing" --format json

echo -e "\n--- Test 2.A: Noun [SH -> ByT5] (Genitive) ---"
smc convert SH ByT5 -i '{"input": "यज्ञस्य", "status": "Success", "segmentation": ["यज्ञस्य"], "morph": [{"word": "यज्ञस्य", "stem": "यज्ञ", "root": "", "derivational_morph": "", "inflectional_morphs": ["m. sg. g."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 2.B: Noun [ByT5 -> SH] (Genitive) ---"
smc convert ByT5 SH -i "yajñasya_yajña_Case=Gen|Gender=Masc|Number=Sing" --format json


# ---------------------------------------------------------
# TEST BATCH 2: Verbs & Moods
# ---------------------------------------------------------
echo -e "\n--- Test 3.A: Verb [SH -> ByT5] (Perfect) ---"
smc convert SH ByT5 -i '{"input": "ईडे", "status": "Success", "segmentation": ["ईडे"], "morph": [{"word": "ईडे", "stem": "", "root": "ईड्", "derivational_morph": "", "inflectional_morphs": ["pft. mo. sg. 3"]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 3.B: Verb [ByT5 -> SH] (Present Indicative) ---"
smc convert ByT5 SH -i "īḍe_īḍ_Tense=Pres|Mood=Ind|Person=1|Number=Sing" --format json

echo -e "\n--- Test 4.A: Verb [SH -> ByT5] (Future) ---"
smc convert SH ByT5 -i '{"input": "करिष्यसि", "status": "Success", "segmentation": ["करिष्यसि"], "morph": [{"word": "करिष्यसि", "stem": "", "root": "कृ#1", "derivational_morph": "", "inflectional_morphs": ["fut. ac. sg. 2"]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 4.B: Verb [ByT5 -> SH] (Future) ---"
smc convert ByT5 SH -i "kariṣyasi_kṛ_Tense=Fut|Mood=Ind|Person=2|Number=Sing" --format json


# ---------------------------------------------------------
# TEST BATCH 3: Derivational Morphs (Participles/Gerundives)
# ---------------------------------------------------------
echo -e "\n--- Test 5.A: Participle [SH -> ByT5] (pfp. [1]) ---"
smc convert SH ByT5 -i '{"input": "ईड्यः", "status": "Success", "segmentation": ["ईड्यः"], "morph": [{"word": "ईड्यः", "stem": "ईड्य", "root": "ईड्", "derivational_morph": "pfp. [1]", "inflectional_morphs": ["m. sg. nom."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 5.B: Participle [ByT5 -> SH] (VerbForm=Gdv) ---"
smc convert ByT5 SH -i "īḍyaḥ_īḍ_Case=Nom|Gender=Masc|Number=Sing|VerbForm=Gdv" --format json

echo -e "\n--- Test 6.A: Participle [SH -> ByT5] (ppr. [1] ac.) ---"
smc convert SH ByT5 -i '{"input": "राजन्तम्", "status": "Success", "segmentation": ["राजन्तम्"], "morph": [{"word": "राजन्तम्", "stem": "राजत्", "root": "राज्#1", "derivational_morph": "ppr. [1] ac.", "inflectional_morphs": ["m. sg. acc."]}], "source": "SH-Local"}' --format string


# ---------------------------------------------------------
# TEST BATCH 4: Indeclinables & Pronouns
# ---------------------------------------------------------
echo -e "\n--- Test 7.A: Indeclinable [SH -> ByT5] ---"
smc convert SH ByT5 -i '{"input": "उत", "status": "Success", "segmentation": ["उत"], "morph": [{"word": "उत", "stem": "उत#1", "root": "", "derivational_morph": "", "inflectional_morphs": ["ind."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 7.B: Indeclinable [ByT5 -> SH] ---"
smc convert ByT5 SH -i "uta_uta__" --format json

echo -e "\n--- Test 8.A: Pronoun [SH -> ByT5] ---"
smc convert SH ByT5 -i '{"input": "त्वा", "status": "Success", "segmentation": ["त्वा"], "morph": [{"word": "त्वा", "stem": "युष्मद्", "root": "", "derivational_morph": "", "inflectional_morphs": ["* sg. acc."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 8.B: Pronoun [ByT5 -> SH] ---"
smc convert ByT5 SH -i "tvā_tvad_Case=Acc|Number=Sing" --format json


# ---------------------------------------------------------
# TEST BATCH 5: The "Empty Context" Fallback Tests
# ---------------------------------------------------------
echo -e "\n--- Test 9.A: Tags Only [SH -> ByT5] ---"
# SH tag string should output a double-underscore ByT5 string
smc convert SH ByT5 -i "m. pl. loc." --format string

echo -e "\n--- Test 9.B: Tags Only [ByT5 -> SH] ---"
# ByT5 tag string should dynamically build an SH JSON with empty words/stems
smc convert ByT5 SH -i "__Case=Loc|Gender=Masc|Number=Plur" --format json

echo -e "\n========================================================="
echo "✅ Test Suite Complete"
echo "========================================================="