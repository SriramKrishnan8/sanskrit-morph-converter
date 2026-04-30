import os
import pandas as pd
from .adapters import DCSAdapter, SCLAdapter, SHAdapter, ByT5Adapter, SvarupaAdapter, CanonicalAdapter
from .mapper import PivotMapper

from tqdm import tqdm
from aksharamukha import transliterate

class RepresentationConverter:
    def __init__(self, norm_path=None, pivot_path=None, nijanta_path=None, pronoun_path=None):
        self.mapper = PivotMapper(norm_path, pivot_path)
        self.adapters = {
            'DCS': DCSAdapter(),
            'SCL': SCLAdapter(),
            'SH': SHAdapter(),
            'ByT5': ByT5Adapter(),
            'Svarupa': SvarupaAdapter(),
            'Canonical': CanonicalAdapter(),
        }

        # 2. Define the native platform scripts
        self.default_scripts = {
            'DCS': 'IAST',
            'ByT5': 'IAST',
            'SCL': 'WX',
            'SH': 'Devanagari',  # Defaulting to Dev, but user can override to IAST
            'Svarupa': 'Devanagari',
            'Canonical': 'Devanagari'
        }
    
        # Setup paths for lexical maps
        base_dir = os.path.dirname(__file__)
        self.nijanta_path = nijanta_path or os.path.join(base_dir, 'data', 'nijanta_map.tsv')
        self.pronoun_path = pronoun_path or os.path.join(base_dir, 'data', 'pronoun_map.tsv')
        
        # Dictionaries for fast O(1) lexical mapping
        self.nijanta_sh_to_dcs = {}
        self.nijanta_dcs_to_sh = {}
        self.pronoun_sh_to_dcs = {}
        self.pronoun_dcs_to_sh = {}
        
        self._load_lexical_maps()

    def _load_lexical_maps(self):
        """Loads lexical mapping files safely, ignoring them if not found."""
        if os.path.exists(self.nijanta_path):
            df_n = pd.read_csv(self.nijanta_path, sep='\t').fillna("")
            for _, row in df_n.iterrows():
                # Fallback to column indices if headers aren't explicitly named
                dcs_byt5_val = row.get('DCS_ByT5', row.iloc[0])
                sh_scl_val = row.get('SH_SCL', row.iloc[1])
                if sh_scl_val and dcs_byt5_val:
                    self.nijanta_sh_to_dcs[sh_scl_val] = dcs_byt5_val
                    self.nijanta_dcs_to_sh[dcs_byt5_val] = sh_scl_val

        if os.path.exists(self.pronoun_path):
            df_p = pd.read_csv(self.pronoun_path, sep='\t').fillna("")
            for _, row in df_p.iterrows():
                dcs_byt5_val = row.get('DCS_ByT5', row.iloc[0])
                sh_scl_val = row.get('SH_SCL', row.iloc[1])
                if sh_scl_val and dcs_byt5_val:
                    self.pronoun_sh_to_dcs[sh_scl_val] = dcs_byt5_val
                    self.pronoun_dcs_to_sh[dcs_byt5_val] = sh_scl_val

    
    def convert(self, source_platform, target_platform, raw_input, output_format='json', output_script=None):
        if source_platform not in self.adapters or target_platform not in self.adapters:
            raise ValueError(f"Platform must be one of {list(self.adapters.keys())}")

        # 0. Ensure the input string correctly interprets literal \t and \n from the CLI        
        if isinstance(raw_input, str):
            raw_input = raw_input.replace('\\t', '\t').replace('\\n', '\n')

        # 1. Decode returns a list of tuples: [(context, tags), (context, tags)]
        source_analyses = self.adapters[source_platform].decode(raw_input)

        # This will hold all successfully translated (context, tags) tuples
        translated_analyses = []

        is_source_sh_scl = source_platform in ['SH', 'SCL']
        is_target_dcs_byt5 = target_platform in ['DCS', 'ByT5']
        is_source_dcs_byt5 = source_platform in ['DCS', 'ByT5']
        is_target_sh_scl = target_platform in ['SH', 'SCL']

        # Determine the final script to use
        target_script = output_script or self.default_scripts.get(target_platform)
        
        for context, tags in source_analyses:
            # 2. Normalize aliases (e.g., Aor -> Past)
            clean_tags = self.mapper.normalize(source_platform, tags)
            
            # 3. Aggregate into the Pivot Hub
            pivot_pools = self.mapper.to_pivot(source_platform, clean_tags)
            
            for pivot_pool in pivot_pools:
                if not pivot_pool:
                    continue
                
                # If SH provided the '*' (which maps to gender_none)
                if 'gender_any' in pivot_pool:
                    stem = context.get('stem', '')
                    # You can load this list from a new numeral_map.tsv later
                    numerals = ['paFcan', 'Rar', 'saptan', 'arwan', 'navan', 'xaSan'] 
                    pronouns = [
                        "sarva", "viSva", "uBa", "uBaya", "dawara", "dawama", "anya", "anyawara", 
                        "iwara", "wvaw", "wva", "nema", "sama", "sima", "pUrva", "para", "avara", 
                        "xakRiNa", "uwwara", "apara", "aXara", "sva", "anwara", "wyax", "wax", 
                        "yax", "ewax", "ixam", "axas", "eka", "xvi", "yuRmax", "asmax", "Bavaw", "kim",
                        "mad", "wvax",
                    ]
                    
                    # Inject the correct NounType into the Pivot Hub!
                    if stem in pronouns:
                        pivot_pool.add('nt_dei')
                    elif stem in numerals:
                        pivot_pool.add('nt_num')
                
                # 4. Generate Target Tags
                match_data = self.mapper.from_pivot(target_platform, pivot_pool)

                # 5. Apply Lexical Mappings & Encode
                for target_tags in match_data.get("tag_sets", []):
                    if target_tags:
                        # Create a copy so we don't mutate the original context for other branches
                        mapped_context = dict(context)
                        root = mapped_context.get('root') or ''
                        stem = mapped_context.get('stem') or ''
                        
                        # --- 1. PRE-TRANSLATE TO WX FOR LOOKUP ---
                        wx_stem = stem
                        wx_root = root
                        
                        if transliterate:
                            if stem: wx_stem = transliterate.process('autodetect', 'WX', stem)
                            if root: wx_root = transliterate.process('autodetect', 'WX', root)
                        
                        # --- 2. LEXICAL MAPPING LOGIC ---
                        if is_source_sh_scl and is_target_dcs_byt5:
                            # Rule A: Pronoun check for all stems
                            if wx_stem in self.pronoun_sh_to_dcs:
                                mapped_context['stem'] = self.pronoun_sh_to_dcs[wx_stem]
                                mapped_context['_is_wx_stem'] = True # Flag for safe transliteration later
                                
                            # Rule B: Nijanta (Causative) check
                            # Check the SOURCE tags for 'ca.' and map the SH root to the DCS stem
                            # SCL to be added
                            if 'ca.' in tags and wx_root in self.nijanta_sh_to_dcs:
                                mapped_context['stem'] = self.nijanta_sh_to_dcs[wx_root]
                                mapped_context['root'] = '' 
                                mapped_context['_is_wx_stem'] = True
                                
                        elif is_source_dcs_byt5 and is_target_sh_scl:
                            # Rule C: Always check both maps and supply to root (and stem)
                            # Pronouns
                            if wx_stem in self.pronoun_dcs_to_sh:
                                mapped_context['stem'] = self.pronoun_dcs_to_sh[wx_stem]
                                mapped_context['root'] = self.pronoun_dcs_to_sh[wx_stem]
                                mapped_context['_is_wx_stem'] = True
                                mapped_context['_is_wx_root'] = True
                            elif wx_root in self.pronoun_dcs_to_sh:
                                mapped_context['stem'] = self.pronoun_dcs_to_sh[wx_root]
                                mapped_context['root'] = self.pronoun_dcs_to_sh[wx_root]
                                mapped_context['_is_wx_stem'] = True
                                mapped_context['_is_wx_root'] = True
                                
                            # Nijanta
                            if wx_stem in self.nijanta_dcs_to_sh:
                                mapped_context['root'] = self.nijanta_dcs_to_sh[wx_stem]
                                mapped_context['_is_wx_root'] = True
                            elif wx_root in self.nijanta_dcs_to_sh:
                                mapped_context['root'] = self.nijanta_dcs_to_sh[wx_root]
                                mapped_context['_is_wx_root'] = True
                        
                        # --- 3. TRANSLITERATION LOGIC ---
                        if transliterate and target_script:
                            # We only transliterate the lexical fields, NOT the morphological tags!
                            lexical_keys = ['full_input', 'raw_word', 'clean_word', 'stem', 'root']
                            for key in lexical_keys:
                                val = mapped_context.get(key)
                                if val:
                                    # If we pulled this from the TSV, we strictly force the source to WX
                                    # Otherwise, we trust autodetect for the original words
                                    source_script = 'WX' if mapped_context.get(f'_is_wx_{key}') else 'autodetect'
                                    mapped_context[key] = transliterate.process(source_script, target_script, val)
                            
                            # Clean up the temporary flags so they don't pollute the final context
                            mapped_context.pop('_is_wx_stem', None)
                            mapped_context.pop('_is_wx_root', None)

                        translated_analyses.append((mapped_context, target_tags))

        # 6. Pass the ENTIRE batch of translations to the target adapter to build the final payload!
        return self.adapters[target_platform].encode(
            translated_analyses,
            output_format=output_format,
            source_platform=source_platform
        )
    
    def convert_bulk(self, source_platform, target_platform, raw_inputs_list, output_format='json', output_script=None):
        """
        Processes a list of inputs with a terminal progress bar.
        Returns a list of dictionaries containing the input, output, and status.
        """
        results = []
        
        # Wrap the list in tqdm to automatically generate the progress bar
        for raw_input in tqdm(raw_inputs_list, desc=f"Converting {source_platform} ➔ {target_platform}"):
            try:
                output = self.convert(source_platform, target_platform, raw_input, output_format=output_format, output_script=output_script)
                if isinstance(output, list):
                    if len(output) > 1:
                        status = "Ambiguous"
                    elif len(output) == 1:
                        status = "Success"
                    else:
                        status = "Unrecognized"
                elif isinstance(output, dict):
                    # SH Output handling
                    morphs = output.get('morph', [])
                    if not morphs:
                        status = "Unrecognized"
                    # Count total inflections across all grouped stems
                    elif len(morphs) > 1 or sum(len(m.get('inflectional_morphs', [])) for m in morphs) > 1:
                        status = "Ambiguous"
                    else:
                        status = "Success"
                else:
                    status = "Success"
                
                results.append({
                    "input": raw_input,
                    "output": output,
                    "status": status
                })
            except Exception as e:
                # Prevents one bad token from crashing the entire batch
                results.append({
                    "input": raw_input,
                    "output": str(e),
                    "status": "Error"
                })
                
        return results