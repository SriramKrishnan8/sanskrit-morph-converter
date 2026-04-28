import pytest
from sanskrit_morph_converter.adapters import DCSAdapter, ByT5Adapter, SHAdapter

# --- BYT5 ADAPTER TESTS ---
def test_byt5_decode_nominal():
    adapter = ByT5Adapter()
    raw = "īḍyaḥ_īḍ_Case=Nom|Gender=Masc|Number=Sing|VerbForm=Gdv"
    result = adapter.decode(raw)
    
    context, tags = result[0]
    assert context['word'] == "īḍyaḥ"
    assert context['stem'] == "īḍ" # It correctly deduced Stem because of Case+VerbForm!
    assert context['root'] == ""
    assert "Case=Nom" in tags

def test_byt5_decode_verbal():
    adapter = ByT5Adapter()
    raw = "īḍe_īḍ_Tense=Pres|Mood=Ind|Person=1|Number=Sing"
    result = adapter.decode(raw)
    
    context, tags = result[0]
    assert context['root'] == "īḍ" # It correctly deduced Root because of Tense+Mood!
    assert context['stem'] == ""

# --- SH ADAPTER TESTS ---
def test_sh_decode_json():
    adapter = SHAdapter()
    raw_json = {
        "status": "Success",
        "morph": [{
            "word": "samavetAH",
            "stem": "sam-ava-iwa",
            "derivational_morph": "pp.",
            "inflectional_morphs": ["m. pl. nom."]
        }]
    }
    result = adapter.decode(raw_json)
    
    context, tags = result[0]
    assert context['stem'] == "sam-ava-iwa"
    assert "pp." in tags
    assert "m." in tags

def test_sh_encode_payload_stitching():
    adapter = SHAdapter()
    # Mocking a list of translated analyses (like DCS to SH)
    translated_list = [
        ({'raw_word': 'kavi-', 'clean_word': 'kavi', 'stem': 'kavi', 'full_input': ''}, {'iic.', 'Case=Cpd'}),
        ({'raw_word': 'kratuH', 'clean_word': 'kratuH', 'stem': 'kratu', 'full_input': ''}, {'nom.', 'm.', 'sg.'})
    ]
    
    result = adapter.encode_payload(translated_list)
    
    # Did it stitch the input correctly?
    assert result['input'] == "kavikratuH"
    assert result['segmentation'] == ["kavi", "kratuH"]
    # Did it create two separate morph entries?
    assert len(result['morph']) == 2