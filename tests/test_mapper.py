import pytest
from sanskrit_morph_converter.mapper import PivotMapper

@pytest.fixture
def mock_mapper():
    mapper = PivotMapper()
    # Mocking the internal state so we don't rely on the actual TSV
    mapper.decode_map = {
        'SH': [
            (frozenset(['verbform_gdv', 'kqw_yaw']), 'pfp. [1]'),
            (frozenset(['verbform_gdv', 'kqw_anIyar']), 'pfp. [2]'),
        ],
        'SCL': [
            (frozenset(['tense_perf', 'mood_ind']), 'lakAraH:lit')
        ]
    }
    return mapper

def test_mapper_mode_b_fan_out(mock_mapper):
    """Test if DCS's generic Gerundive fans out to specific SH Gerundives."""
    generic_pool = {'verbform_gdv'} # Missing the specific suffix
    
    match_data = mock_mapper.from_pivot('SH', generic_pool)
    
    assert match_data['match_type'] == 'ambiguous'
    # It should fan out into two parallel realities!
    assert len(match_data['tag_sets']) == 2

def test_mapper_harmonious_intersection_filter():
    """Test if the mapper filters out bloated contradictory tags."""
    mapper = PivotMapper()
    # Simulate a pool branching into Active (size 4) and Passive (size 5)
    mapper.encode_map = {
        'SCL': {
            'SAnac': [
                frozenset(['verbform_part', 'prayoga_karwari', 'paxa_Awmane']),
                frozenset(['verbform_part', 'prayoga_karmaNi', 'paxa_Awmane'])
            ]
        }
    }
    
    # Input has an explicit explicit 'prayoga_karmaNi' context
    input_tags = ['SAnac', 'prayoga_karmaNi']
    pools = mapper.to_pivot('SCL', input_tags)
    
    # The filter should destroy the bloated Active pool and return exactly 1 reality
    assert len(pools) == 1
    assert 'prayoga_karmaNi' in pools[0]
    assert 'prayoga_karwari' not in pools[0]