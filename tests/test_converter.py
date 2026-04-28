import pytest
from sanskrit_morph_converter.converter import RepresentationConverter

@pytest.fixture
def converter():
    # This will load your actual compiled TSV files
    return RepresentationConverter()

def test_end_to_end_dcs_to_byt5(converter):
    dcs_input = "_\tīḍyaḥ\tīḍ\t_\t_\tCase=Nom|Gender=Masc|Number=Sing|VerbForm=Gdv"
    
    results = converter.convert('DCS', 'ByT5', dcs_input)
    
    # ByT5 should automatically format it with underscores and sort the tags
    assert len(results) > 0
    assert results[0].startswith("īḍyaḥ_īḍ_")
    assert "Case=Nom" in results[0]

def test_end_to_end_scl_to_sh(converter):
    scl_input = "<kqw_prawyayaH:SAnac_lat><prayogaH:karmaNi><paxI:AwmanepaxI>"
    
    results = converter.convert('SCL', 'SH', scl_input)
    
    # Result should be a single SH JSON payload
    assert isinstance(results, dict)
    assert results['status'] == 'Success'
    
    # The derivational morph should correctly resolve to passive
    assert "ppr." in results['morph'][0]['derivational_morph']
    assert "ps." in results['morph'][0]['inflectional_morphs'][0]