#!/bin/bash

echo "========================================================="
echo "🧪 Sanskrit Morph Converter (SMC) - Integration Test Suite"
echo "========================================================="

# ---------------------------------------------------------
# TEST BATCH 1: SH ↔ ByT5 (Thematic Core)
# ---------------------------------------------------------
echo -e "\n--- Test 1.A: [SH -> ByT5] (Noun Accusative) ---"
smc convert SH ByT5 -i '{"input": "अग्निम्", "status": "Success", "segmentation": ["अग्निम्"], "morph": [{"word": "अग्निम्", "stem": "अग्नि", "root": "", "derivational_morph": "", "inflectional_morphs": ["m. sg. acc."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 1.B: [ByT5 -> SH] (Noun Accusative) ---"
smc convert ByT5 SH -i "agnim_agni_Case=Acc|Gender=Masc|Number=Sing" --format json

echo -e "\n--- Test 2.A: [SH -> ByT5] (Verb Future) ---"
smc convert SH ByT5 -i '{"input": "करिष्यसि", "status": "Success", "segmentation": ["करिष्यसि"], "morph": [{"word": "करिष्यसि", "stem": "", "root": "कृ#1", "derivational_morph": "", "inflectional_morphs": ["fut. ac. sg. 2"]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 2.B: [ByT5 -> SH] (Verb Future) ---"
smc convert ByT5 SH -i "kariṣyasi_kṛ_Tense=Fut|Mood=Ind|Person=2|Number=Sing" --format json

# ---------------------------------------------------------
# TEST BATCH 2: SH ↔ Canonical
# ---------------------------------------------------------
echo -e "\n--- Test 3.A: [SH -> Canonical] (Noun Genitive) ---"
smc convert SH Canonical -i '{"input": "यज्ञस्य", "status": "Success", "segmentation": ["यज्ञस्य"], "morph": [{"word": "यज्ञस्य", "stem": "यज्ञ", "root": "", "derivational_morph": "", "inflectional_morphs": ["m. sg. g."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 3.B: [Canonical -> SH] (Noun Genitive) ---"
smc convert Canonical SH -i "yajñasya_yajña_Case=Genitive|Gender=Masculine|Number=Singular" --format json

echo -e "\n--- Test 4.A: [SH -> Canonical] (Gerundive Participle) ---"
smc convert SH Canonical -i '{"input": "ईड्यः", "status": "Success", "segmentation": ["ईड्यः"], "morph": [{"word": "ईड्यः", "stem": "ईड्य", "root": "ईड्", "derivational_morph": "pfp. [1]", "inflectional_morphs": ["m. sg. nom."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 4.B: [Canonical -> SH] (Gerundive Participle) ---"
smc convert Canonical SH -i "īḍyaḥ_īḍya_īḍ_Case=Nominative|Gender=Masculine|Number=Singular|VerbForm=Gerundive" --format json

# ---------------------------------------------------------
# TEST BATCH 3: SH ↔ DCS
# ---------------------------------------------------------
echo -e "\n--- Test 5.A: [SH -> DCS] (Pronoun) ---"
smc convert SH DCS -i '{"input": "त्वा", "status": "Success", "segmentation": ["त्वा"], "morph": [{"word": "त्वा", "stem": "युष्मद्", "root": "", "derivational_morph": "", "inflectional_morphs": ["* sg. acc."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 5.B: [DCS -> SH] (Pronoun) ---"
smc convert DCS SH -i "tvā\ttvad\tCase=Acc|Number=Sing" --format json

echo -e "\n--- Test 6.A: [SH -> DCS] (Verb Perfect) ---"
smc convert SH DCS -i '{"input": "ईडे", "status": "Success", "segmentation": ["ईडे"], "morph": [{"word": "ईडे", "stem": "", "root": "ईड्", "derivational_morph": "", "inflectional_morphs": ["pft. mo. sg. 3"]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 6.B: [DCS -> SH] (Verb Perfect) ---"
smc convert DCS SH -i "īḍe\tīḍ\tMood=Ind|Number=Sing|Person=3|Tense=Perf" --format json

# ---------------------------------------------------------
# TEST BATCH 4: SH ↔ SCL
# ---------------------------------------------------------
echo -e "\n--- Test 7.A: [SH -> SCL] (Noun) ---"
smc convert SH SCL -i '{"input": "अग्निम्", "status": "Success", "segmentation": ["अग्निम्"], "morph": [{"word": "अग्निम्", "stem": "अग्नि", "root": "", "derivational_morph": "", "inflectional_morphs": ["m. sg. acc."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 7.B: [SCL -> SH] (Noun) ---"
smc convert SCL SH -i "^agnim/agni<vargaH:nA><lifgam:puM><viBakwiH:2><vacanam:eka>$" --format json

echo -e "\n--- Test 8.A: [SH -> SCL] (Indeclinable) ---"
smc convert SH SCL -i '{"input": "उत", "status": "Success", "segmentation": ["उत"], "morph": [{"word": "उत", "stem": "उत#1", "root": "", "derivational_morph": "", "inflectional_morphs": ["ind."]}], "source": "SH-Local"}' --format string

echo -e "\n--- Test 8.B: [SCL -> SH] (Indeclinable) ---"
smc convert SCL SH -i "^uta/uta<vargaH:avy>$" -is IAST --format json

# ---------------------------------------------------------
# TEST BATCH 5: ByT5 ↔ Canonical
# ---------------------------------------------------------
echo -e "\n--- Test 9.A: [ByT5 -> Canonical] (Present Participle) ---"
smc convert ByT5 Canonical -i "rājantam_rājat_Case=Acc|Gender=Masc|Number=Sing|Tense=Pres|VerbForm=Part" --format string

echo -e "\n--- Test 9.B: [Canonical -> ByT5] (Present Participle) ---"
smc convert Canonical ByT5 -i "rājantam_rājat_Case=Accusative|Gender=Masculine|Number=Singular|Tense=Present|VerbForm=Participle" --format string

echo -e "\n--- Test 10.A: [ByT5 -> Canonical] (Verb Present) ---"
smc convert ByT5 Canonical -i "gacchati_gam_Tense=Pres|Mood=Ind|Person=3|Number=Sing" --format string

echo -e "\n--- Test 10.B: [Canonical -> ByT5] (Verb Present) ---"
smc convert Canonical ByT5 -i "gacchati_gam_Tense=Present|Mood=Indicative|Person=3|Number=Singular" --format string

# ---------------------------------------------------------
# TEST BATCH 6: ByT5 ↔ DCS
# ---------------------------------------------------------
echo -e "\n--- Test 11.A: [ByT5 -> DCS] (Noun) ---"
smc convert ByT5 DCS -i "agnim_agni_Case=Acc|Gender=Masc|Number=Sing" --format string

echo -e "\n--- Test 11.B: [DCS -> ByT5] (Noun) ---"
smc convert DCS ByT5 -i "agnim\tagni\tCase=Acc|Gender=Masc|Number=Sing" --format string

echo -e "\n--- Test 12.A: [ByT5 -> DCS] (Absolutive) ---"
smc convert ByT5 DCS -i "kṛtvā_kṛ_VerbForm=Conv" --format string

echo -e "\n--- Test 12.B: [DCS -> ByT5] (Absolutive) ---"
smc convert DCS ByT5 -i "kṛtvā\tkṛ\tVerbForm=Abs" --format string

# ---------------------------------------------------------
# TEST BATCH 7: ByT5 ↔ SCL
# ---------------------------------------------------------
echo -e "\n--- Test 13.A: [ByT5 -> SCL] (Verb Imperfect) ---"
smc convert ByT5 SCL -i "agacchat_gam_Tense=Impf|Mood=Ind|Person=3|Number=Sing" --format string

echo -e "\n--- Test 13.B: [SCL -> ByT5] (Verb Imperfect) ---"
smc convert SCL ByT5 -i "^agacCaw/gam<lakAraH:laf><puruRaH:pra><vacanam:eka><paxI:parasmEpaxI><prayogaH:karwari>$" --format json

echo -e "\n--- Test 14.A: [ByT5 -> SCL] (Pronoun) ---"
smc convert ByT5 SCL -i "tvā_tvad_Case=Acc|Number=Sing" --format string

echo -e "\n--- Test 14.B: [SCL -> ByT5] (Pronoun) ---"
smc convert SCL ByT5 -i "^tvā/tvad<vargaH:sarva><viBakwiH:2><vacanam:eka>$" --format json

# ---------------------------------------------------------
# TEST BATCH 8: DCS ↔ Canonical
# ---------------------------------------------------------
echo -e "\n--- Test 15.A: [DCS -> Canonical] (Future Participle) ---"
smc convert DCS Canonical -i "kariṣyantam\tkṛ\tCase=Acc|Gender=Masc|Number=Sing|Tense=Fut|VerbForm=Part" --format string

echo -e "\n--- Test 15.B: [Canonical -> DCS] (Future Participle) ---"
smc convert Canonical DCS -i "kariṣyantam_kṛ_Case=Accusative|Gender=Masculine|Number=Singular|Tense=Future|VerbForm=Participle" --format string

echo -e "\n--- Test 16.A: [DCS -> Canonical] (Noun Locative) ---"
smc convert DCS Canonical -i "vedeṣu\tveda\tCase=Loc|Gender=Masc|Number=Plur" --format string

echo -e "\n--- Test 16.B: [Canonical -> DCS] (Noun Locative) ---"
smc convert Canonical DCS -i "vedeṣu_veda_Case=Locative|Gender=Masculine|Number=Plural" --format string

# ---------------------------------------------------------
# TEST BATCH 9: DCS ↔ SCL
# ---------------------------------------------------------
echo -e "\n--- Test 17.A: [DCS -> SCL] (Verb Aorist) ---"
smc convert DCS SCL -i "abhūt\tbhū\tMood=Ind|Number=Sing|Person=3|Tense=Aor" --format string

echo -e "\n--- Test 17.B: [SCL -> DCS] (Verb Aorist) ---"
smc convert SCL DCS -i "^aBUw/BU<lakAraH:luf><puruRaH:pra><vacanam:eka><paxI:parasmEpaxI><prayogaH:karwari>$" --format json

echo -e "\n--- Test 18.A: [DCS -> SCL] (Present Participle Derivation) ---"
smc convert DCS SCL -i "gacchan\tgam\tCase=Nom|Gender=Masc|Number=Sing|Tense=Pres|VerbForm=Part" --format string

echo -e "\n--- Test 18.B: [SCL -> DCS] (Present Participle Derivation) ---"
smc convert SCL DCS -i "^gacCawi/gam<kqw_prawyayaH:Sawq_lat><XAwuH:gam>gacCaw<vargaH:nA><lifgam:puM><viBakwiH:7><vacanam:eka><level:2>$" --format string

# ---------------------------------------------------------
# TEST BATCH 10: Canonical ↔ SCL
# ---------------------------------------------------------
echo -e "\n--- Test 19.A: [Canonical -> SCL] (Absolutive) ---"
smc convert Canonical SCL -i "gatvā_gam_Case=IndeclinablePrimaryDerivative|VerbForm=Absolutive|PrimaryDerivative=kwvA" --format string

echo -e "\n--- Test 19.B: [SCL -> Canonical] (Absolutive) ---"
smc convert SCL Canonical -i "^gawvA/gam<kqw_prawyayaH:kwvA>$" --format json

echo -e "\n--- Test 20.A: [Canonical -> SCL] (Noun Dative) ---"
smc convert Canonical SCL -i "rāmāya_rāma_Case=Dative|Gender=Masculine|Number=Singular" --format string

echo -e "\n--- Test 20.B: [SCL -> Canonical] (Noun Dative) ---"
smc convert SCL Canonical -i "^rAmAya/rAma<vargaH:nA><lifgam:puM><viBakwiH:4><vacanam:eka>$" --format json

# ---------------------------------------------------------
# TEST BATCH 11: Empty State & Fallback Validations
# ---------------------------------------------------------
echo -e "\n--- Test 21.A: Empty Tags [SH -> ByT5] ---"
# SH tag string should output a double-underscore ByT5 string
smc convert SH ByT5 -i "m. pl. loc." --format string

echo -e "\n--- Test 21.B: Empty Tags [ByT5 -> SH] ---"
# ByT5 tag string should dynamically build an SH JSON with empty words/stems
smc convert ByT5 SH -i "__Case=Loc|Gender=Masc|Number=Plur" --format json

echo -e "\n--- Test 22.A: Empty Tags [SCL -> ByT5] ---"
# Bare tags in SCL string
smc convert SCL ByT5 -i "^/<viBakwiH:7><vacanam:bahu><lifgam:puM>$" --format string

echo -e "\n--- Test 22.B: Empty Tags [ByT5 -> SCL] ---"
smc convert ByT5 SCL -i "__Case=Loc|Gender=Masc|Number=Plur" --format string

echo -e "\n========================================================="
echo "✅ Matrix Test Suite Complete (44 Tests Executed)"
echo "========================================================="