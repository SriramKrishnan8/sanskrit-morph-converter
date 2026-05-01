import re
import json

class BaseAdapter:
    def decode(self, raw_data):
        """Converts raw platform output into a LIST of tuples: [(context_dict, tag_list)]"""
        raise NotImplementedError
        
    def encode(self, translated_analyses_list, output_format='json', source_platform='Unknown'):
        """Reconstructs the platform's native payload format."""
        raise NotImplementedError

class DCSAdapter(BaseAdapter):
    def decode(self, raw_data):
        """
        Parses either a CoNLL-U formatted line or a standard JSON array of dicts.
        Applies strict Stem vs. Root deduction based on the morphological tags.
        """
        # If the user passed the clean JSON array
        if isinstance(raw_data, list):
            items = raw_data
        # If the user passed a raw string, wrap it so the loop still works
        elif isinstance(raw_data, str):
            try:
                # Try to parse it as JSON first
                parsed = json.loads(raw_data)
                items = parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                items = raw_data.split(" ")
        else:
            items = [raw_data]
            
        analyses = []
        for item in items:
            if isinstance(item, dict) and 'morph' in item:
                word = item.get('word', '')
                lemma = item.get('lemma', '')
                morph_str = item.get('morph', '')
            elif isinstance(item, str):
                # Fallback to string/CoNLL-U parsing
                parts = item.split('\t')
                if len(parts) >= 6:
                    word = parts[1]
                    lemma = parts[2]
                    morph_str = parts[5]
                    if morph_str == '_': morph_str = ''
                elif len(parts) == 3:
                    # 2. Simplified CLI Format (word \t lemma \t tags)
                    word = parts[0]
                    lemma = parts[1]
                    morph_str = parts[2]
                else:
                    word = ""
                    lemma = ""
                    morph_str = item
            else:
                continue
                
            tags = [t for t in morph_str.split('|') if t.strip() and not t.endswith('=')]
        
            # --- CONTEXTUAL INDECLINABLE UPGRADE ---
            if "Case=Ind" in tags:
                has_verbform = any(t.startswith("VerbForm=") for t in tags)
                has_primary = any(t.startswith("PrimaryDerivative=") for t in tags)
                has_secondary_suffix = any(t.startswith("SecondaryDerivativeSuffix=") for t in tags)
                has_secondary_meaning = any(t.startswith("SecondaryDerivativeMeaning=") for t in tags)
                
                tags.remove("Case=Ind") # Remove the generic tag
                
                if has_verbform or has_primary:
                    tags.append("Case=IndeclinablePrimaryDerivative") # Upgrade to Krt
                elif has_secondary_suffix or has_secondary_meaning:
                    tags.append("Case=IndeclinableSecondaryDerivative") # Upgrade to Taddhita
                else:
                    tags.append("Case=Indeclinable") # Keep it generic
            
            # --- SHARED STEM VS ROOT DEDUCTION LOGIC ---
            has_tense = any(t.startswith("Tense=") for t in tags)
            has_mood = any(t.startswith("Mood=") for t in tags)
            has_verbform = any(t.startswith("VerbForm=") for t in tags)
            has_case = any(t.startswith("Case=") for t in tags)

            root = ""
            stem = ""

            if has_tense and has_mood:
                root = lemma
            elif has_verbform and has_case:
                stem = lemma
            elif has_verbform and not has_case:
                root = lemma
            else:
                # Default for nominals, indeclinables, and compounds
                stem = lemma

            context = {
                'full_input': '',
                'raw_word': word,
                'clean_word': word.rstrip('-'),
                'stem': stem,
                'root': root,
            }

            analyses.append((context, tags))
        
        return analyses

    def encode(self, translated_analyses_list, output_format='json', source_platform='Unknown'):
        """
        Reconstructs the DCS output (CoNLL-U format). 
        Dynamically selects whether to print the stem or root as the lemma.
        """
        if not translated_analyses_list:
            return []
            
        results = []
        for context, tags_set in translated_analyses_list:
            word = context.get('raw_word', '')
            root = context.get('root', '')
            stem = context.get('stem', '')
            
            # --- SHARED LEMMA SELECTION LOGIC ---
            has_tense = any(t.startswith("Tense=") for t in tags_set)
            has_mood = any(t.startswith("Mood=") for t in tags_set)
            has_verbform = any(t.startswith("VerbForm=") for t in tags_set)
            has_case = any(t.startswith("Case=") for t in tags_set)
            
            lemma = ""
            # If it's a Verb, Participle, Absolutive, Gerundive, or Infinitive
            # DCS/ByT5 overwhelmingly prefers the ROOT as the lemma.
            if has_tense or has_verbform or has_mood:
                lemma = root if root else stem
            # If it is a pure Nominal, Pronoun, or Indeclinable, use the STEM.
            else:
                lemma = stem if stem else root
                
            if not lemma: 
                lemma = word 
            
            if output_format == 'json':
                # Output as {"word": "", "lemma": "", "morph": ""}
                morph_dict = {}
                for t in sorted(tags_set):
                    if '=' in t:
                        k, v = t.split('=', 1)
                        morph_dict[k] = v
                    else:
                        morph_dict[t] = True # Fallback if TSV is missing "Key="

                out_obj = {
                    "word": word,
                    "lemma": lemma,
                    "morph": morph_dict,
                    "source": source_platform
                }
                if out_obj not in results:
                    results.append(out_obj)
            else:
                # Output as string with underscores for empty values
                morph_str = "|".join(sorted(tags_set)) if tags_set else "_"
                word_out = word if word else "_"
                lemma_out = lemma if lemma else "_"
                out_str = f"{word_out}\t{lemma_out}\t{morph_str}"
                
                if out_str not in results:
                    results.append(out_str)
                
        return results


class ByT5Adapter(BaseAdapter):
    def decode(self, raw_data):
        """
        Parses ByT5 format: word_lemma_morph
        Applies strict Stem vs. Root deduction based on the morphological tags.
        """
        if isinstance(raw_data, list):
            items = raw_data
        elif isinstance(raw_data, str):
            try:
                parsed = json.loads(raw_data)
                items = parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                items = raw_data.split()
        else:
            items = [raw_data]

        analyses = []
        for item in items:
            if isinstance(item, dict) and 'morph' in item:
                word = item.get('word', '')
                lemma = item.get('lemma', '')
                morph_str = item.get('morph', '')
            elif isinstance(item, str):
                parts = item.split('_')
                if len(parts) >= 3:
                    word = parts[0]
                    lemma = parts[1]
                    morph_str = "_".join(parts[2:]) 
                elif len(parts) == 2:
                    word, lemma, morph_str = parts[0], parts[1], ""
                else:
                    word, lemma, morph_str = item, "", ""
            else:
                continue
                
            tags = [t for t in morph_str.split('|') if t.strip() and not t.endswith('=')]
            
            # --- CONTEXTUAL INDECLINABLE UPGRADE ---
            if "Case=Ind" in tags or "Case=Indeclinable" in tags:
                has_verbform = any(t.startswith("VerbForm=") for t in tags)
                has_primary = any(t.startswith("PrimaryDerivative=") for t in tags)
                has_secondary_suffix = any(t.startswith("SecondaryDerivativeSuffix=") for t in tags)
                has_secondary_meaning = any(t.startswith("SecondaryDerivativeMeaning=") for t in tags)
                
                tags.remove("Case=Ind") # Remove the generic tag
                
                if has_verbform or has_primary:
                    tags.append("Case=IndeclinablePrimaryDerivative") # Upgrade to Krt
                elif has_secondary_suffix or has_secondary_meaning:
                    tags.append("Case=IndeclinableSecondaryDerivative") # Upgrade to Taddhita
                else:
                    tags.append("Case=Indeclinable") # Keep it generic
            
            has_tense = any(t.startswith("Tense=") for t in tags)
            has_mood = any(t.startswith("Mood=") for t in tags)
            has_verbform = any(t.startswith("VerbForm=") for t in tags)
            has_case = any(t.startswith("Case=") for t in tags)
            
            root = ""
            stem = ""
            
            if has_tense and has_mood:
                root = lemma
            elif has_verbform and has_case:
                stem = lemma
            elif has_verbform and not has_case:
                root = lemma
            else:
                stem = lemma
                
            context = {
                'full_input': '',
                'raw_word': word,
                'clean_word': word.rstrip('-'),
                'stem': stem,
                'root': root,
            }
            analyses.append((context, tags))
            
        return analyses

    def encode(self, translated_analyses_list, output_format='json', source_platform='Unknown'):
        """
        Reconstructs the ByT5 format: word_lemma_morph
        Dynamically selects whether to print the stem or root as the lemma.
        """
        if not translated_analyses_list:
            return []
            
        results = []
        for context, tags_set in translated_analyses_list:
            word = context.get('raw_word', '')
            root = context.get('root', '')
            stem = context.get('stem', '')
            
            # --- SHARED LEMMA SELECTION LOGIC ---
            has_tense = any(t.startswith("Tense=") for t in tags_set)
            has_mood = any(t.startswith("Mood=") for t in tags_set)
            has_verbform = any(t.startswith("VerbForm=") for t in tags_set)
            has_case = any(t.startswith("Case=") for t in tags_set)
            
            lemma = ""
            # If it's a Verb, Participle, Absolutive, Gerundive, or Infinitive
            # DCS/ByT5 overwhelmingly prefers the ROOT as the lemma.
            if has_tense or has_verbform or has_mood:
                lemma = root if root else stem
            # If it is a pure Nominal, Pronoun, or Indeclinable, use the STEM.
            else:
                lemma = stem if stem else root
                
            if not lemma: 
                lemma = word 
            
            if output_format == 'json':
                morph_dict = {}
                for t in sorted(tags_set):
                    if '=' in t:
                        k, v = t.split('=', 1)
                        morph_dict[k] = v
                    else:
                        morph_dict[t] = True
                out_obj = {
                    "word": word,
                    "lemma": lemma,
                    "morph": morph_dict,
                    'source': source_platform
                }
                if out_obj not in results:
                    results.append(out_obj)
            else:
                morph_str = "|".join(sorted(tags_set))
                word_out = word if word else ""
                lemma_out = lemma if lemma else ""
                out_str = f"{word_out}_{lemma_out}_{morph_str}"
                
                if out_str not in results:
                    results.append(out_str)
                
        return results

class SHAdapter(BaseAdapter):
    def decode(self, raw_data):
        """
        Parses the native Sanskrit Heritage JSON payload.
        Extracts both derivational and inflectional morphs, and preserves the lexical context.
        """
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                tags = [t for t in raw_data.split(' ') if t.strip()]
                if not tags:
                    return []
                
                # Create a minimal context for raw strings
                context = {
                    'full_input': '',
                    'raw_word': '', 
                    'clean_word': '',
                    'stem': '',
                    'root': '',
                }
                return [(context, tags)]
                
        # Abort if the API explicitly failed
        if not isinstance(raw_data, dict) or raw_data.get('status') != 'Success':
            return []
            
        analyses = []
        
        for morph_entry in raw_data.get('morph', []):
            # 1. Preserve the Lexical Context
            context = {
                'full_input': raw_data.get('input', ''),
                'segmentation': raw_data.get('segmentation', []),
                'raw_word': morph_entry.get('word', ''),
                'clean_word': morph_entry.get('word', '').rstrip('-'),
                'stem': morph_entry.get('stem', '').split('#')[0],
                'root': morph_entry.get('root', '').split('#')[0],
            }
            
            # 2. Extract the grammatical strings
            deriv = morph_entry.get('derivational_morph', '').strip()
            inflections = morph_entry.get('inflectional_morphs', [])
            
            if not inflections and deriv:
                inflections = [""]
                
            for infl in inflections:
                morph_string = f"{deriv} {infl}".strip()
                
                # Protect Lexicalized Suffixes (Fusion)
                morph_string = morph_string.replace("pfp. [1]", "pfp_1")
                morph_string = morph_string.replace("pfp. [2]", "pfp_2")
                morph_string = morph_string.replace("pfp. [3]", "pfp_3")

                if "aor." in morph_string:
                    for i in range(1, 8):
                        morph_string = morph_string.replace(f"aor. [{i}]", f"aor_{i}")
                
                # Extract tags
                tags = [feat for feat in morph_string.split(' ') if feat.strip()]
                if tags:
                    # Return the context alongside the tags!
                    analyses.append((context, tags))
                    
        return analyses

    def encode(self, translated_analyses_list, output_format='json', source_platform='Unknown'):
        """
        Reconstructs a strictly compliant SH JSON dictionary.
        Uses a heuristic to split the translated tags back into 'derivational' and 'inflectional'.
        """
        if not translated_analyses_list:
            return {'status': 'Failure', 'morph': []}
        
        # 1. Sort the tags based on SH morphotactic slots
        def get_slot_weight(tag):
            # Slot 0: Secondary Conjugations (Force to front)
            if tag in ['ca.', 'des.', 'int.', 'int_luk', 'ca_int', 'des_int', 'des_ca', 'des_ca_int']:
                weight = 5
            
            # Slot 1: Base Forms / Tense / Participle Type
            elif tag in ['pr.', 'imp.', 'opt.', 'ben.', 'pft.', 'impft.', 'fut.', 'aor.', 'subj.', 'inj.']:
                weight = 10 
            
            # Slot 2: Verb Classes / Formations
            if tag.startswith('['):
                weight = 20
                
            # Slot 3: Voice
            elif tag in ['ac.', 'md.', 'ps.', 'mo.']:
                weight = 30
                
            # Slot 4: Gender
            elif tag in ['m.', 'f.', 'n.', '*']:
                weight = 40
                
            # Slot 5: Number
            elif tag in ['sg.', 'du.', 'pl.']:
                weight = 50
                
            # Slot 6: Case (Nominals) or Person (Verbs)
            elif tag in ['nom.', 'acc.', 'i.', 'dat.', 'abl.', 'g.', 'loc.', 'voc.', 'iic.', 'ifc.']:
                weight = 60
            elif tag in ['1', '2', '3']:
                weight = 60
            else:
                weight = 15 # Default fallback
                
            return weight

        # This dictionary will group inflections by their unique base/stem
        # Format: { (word, stem, root, deriv_string): [infl_string1, infl_string2] }
        grouped_morphs = {}

        # Grab the raw input from the first available context
        first_context = translated_analyses_list[0][0] if translated_analyses_list else {}
        full_input_string = first_context.get('full_input', '')
        segmentation = first_context.get('segmentation', [])

        # If it's blank, we need to stitch it together (e.g., from DCS source)
        needs_stitching = not segmentation

        seg_string = ""
        morph_array_builder = []
        last_raw_word = None

        for context, tags_set in translated_analyses_list:
            raw_word = context.get('raw_word', '')
            
            # 0. SEQUENTIAL STITCHING & GROUPING
            # If the word changes, start a new group and add to segmentation
            if raw_word != last_raw_word:
                if seg_string and not seg_string.endswith('-'):
                    seg_string += " " # Add space between distinct words
                seg_string += raw_word
                last_raw_word = raw_word

                morph_array_builder.append({
                    'word': raw_word,
                    'stem': context.get('stem', ''),
                    'root': context.get('root', ''),
                    'derivational_morph': "",
                    'inflectional_morphs': []
                })
            
            # Check if this is a nominal (has case) but is missing gender
            has_case = any(t in ['nom.', 'acc.', 'i.', 'dat.', 'abl.', 'g.', 'loc.', 'voc.', 'iic.', 'ifc.'] for t in tags_set)
            has_gender = any(t in ['m.', 'f.', 'n.'] for t in tags_set)

            working_tags = set(tags_set)
            if has_case and not has_gender:
                working_tags.add('*')
            
            # 1. SORT BEFORE SPLITTING
            sorted_tags = sorted(list(working_tags), key=get_slot_weight)
            
            restored_tags = []
            for tag in sorted_tags:
                tag = tag.replace("pfp_1", "pfp. [1]")
                tag = tag.replace("pfp_2", "pfp. [2]")
                tag = tag.replace("pfp_3", "pfp. [3]")
                for i in range(1, 8):
                    tag = tag.replace(f"aor_{i}", f"aor. [{i}]")
                restored_tags.append(tag)
        
            # 2. The Split Heuristic: Derivational vs Inflectional
            # SH generally puts VerbForms, Participles, and Absolutives in derivational_morph.
            # It puts Voice, Gender, Number, Case, and Person in inflectional_morphs.

            derivational_list = []
            inflectional_list = []
        
            derivational_keywords = ['pp.', 'ppa.', 'ppr.', 'ppf.', 'pfu.', 'pfp.', 'abs.', 'inf.']

            for tag in restored_tags:
                if any(tag.startswith(dw) for dw in derivational_keywords):
                    derivational_list.append(tag)
                else:
                    inflectional_list.append(tag)
                
            derivational_string = " ".join(derivational_list)
            inflectional_string = " ".join(inflectional_list)

            # 3. APPEND TAGS TO CURRENT WORD'S GROUP
            # morph_array_builder[-1] represents the current word we are stitching
            if derivational_string and not morph_array_builder[-1]['derivational_morph']:
                morph_array_builder[-1]['derivational_morph'] = derivational_string
                
            if inflectional_string and inflectional_string not in morph_array_builder[-1]['inflectional_morphs']:
                morph_array_builder[-1]['inflectional_morphs'].append(inflectional_string)

        # 4. BUILD THE FINAL JSON PAYLOAD
        morph_array = []
        for entry in morph_array_builder:
            # Optional Ambiguity Filter
            infl_list = entry['inflectional_morphs']
            if any('iic.' in infl for infl in infl_list):
                infl_list = [infl for infl in infl_list if 'iiv.' not in infl]

            morph_dict = {
                'word': entry['word'],
                'stem': entry['stem'],
                'root': entry['root'],
                'inflectional_morphs': infl_list
            }
            if entry['derivational_morph']:
                morph_dict['derivational_morph'] = entry['derivational_morph']
            morph_array.append(morph_dict)
        
        # 5. Build the final SH-Compliant Dictionary
        if needs_stitching:
            # If the source (like ByT5) didn't provide a full input string, we build it!
            # seg_string looks like: "ratna-dhātamam"
            final_segmentation = [seg_string] if seg_string else []
            # SH input strips hyphens and spaces
            final_input = seg_string.replace('-', '').replace(' ', '')
        else:
            # If the source (like SH) already provided them, pass them straight through
            final_segmentation = segmentation
            final_input = full_input_string
        
        # We assume 'Success' since the translation engine successfully generated these tags.
        sh_json = {
            'input': final_input,
            'status': 'Success',
            'segmentation': final_segmentation,
            'morph': morph_array,
            'source': source_platform
        }

        return sh_json

class SCLAdapter(BaseAdapter):
    def decode(self, raw_data):
        """
        Parses SCL output formats:
        ^word/root1<tag1:val1>stem1<tag2:val2>/stem2<tag3:val3>$
        """
        if isinstance(raw_data, list):
            items = raw_data
        elif isinstance(raw_data, str):
            try:
                parsed = json.loads(raw_data)
                items = parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                # SCL outputs are usually newline or space separated
                items = raw_data.split('\n')
        else:
            items = [raw_data]
            
        analyses = []
        for item in items:
            # Handle JSON inputs
            if isinstance(item, dict):
                word = item.get('input', '') or item.get('word', '')
                morphs = item.get('morph', [])
                for morph in morphs:
                    stem = morph.get('stem', '')
                    root = morph.get('root', '')
                    tags = morph.get('tags', [])
                    context = {
                        'full_input': '',
                        'raw_word': word,
                        'clean_word': word,
                        'stem': stem,
                        'root': root
                    }
                    analyses.append((context, tags))
                continue

            # Handle native SCL string format
            item = item.strip().strip('^$')
            if not item:
                continue
                
            parts = item.split('/')
            word = parts[0]
            
            for analysis in parts[1:]:
                if not analysis:
                    continue
                
                # 1. Extract all key-value tags
                scl_tags = re.findall('<(.*?)>', analysis)

                # 2. Extract text chunks by removing all <tags>
                # Using filter to remove empty strings caused by adjacent tags
                text_chunks = [chunk for chunk in re.split('<.*?>', analysis) if chunk]
                
                root = ""
                stem = ""
                
                # --- THE ROOT VS STEM DEDUCTION LOGIC ---
                if len(text_chunks) >= 2:
                    # Derivation (Krt) typically has both spatially separated
                    root = text_chunks[0]
                    stem = text_chunks[1]
                elif len(text_chunks) == 1:
                    # Disambiguate the single chunk using its tags
                    val = text_chunks[0]
                    
                    has_verbal = any(t.startswith('lakAraH:') or t.startswith('puruRaH:') for t in scl_tags)
                    has_nominal = any(t.startswith('vargaH:') or t.startswith('lifgam:') or t.startswith('viBakwiH:') for t in scl_tags)
                    
                    if has_verbal:
                        root = val
                    elif has_nominal:
                        stem = val
                    else:
                        # Fallback for indeclinables (avyaya) or unknowns
                        stem = val
                
                upasarga = ""
                clean_tags = []
                
                for tag in scl_tags:
                    if tag.startswith('upasarga:'):
                        upasarga = tag.split(':')[1]
                    elif tag.startswith('level:'):
                        pass # Ignore structural metadata
                    else:
                        clean_tags.append(tag) # e.g., "lifgam:puM"
                
                # Prepend Upasarga exactly like the legacy script did
                if upasarga:
                    root = f"{upasarga}-{root}" if root else root
                    stem = f"{upasarga}-{stem}" if stem else stem
                    
                context = {
                    'full_input': item,
                    'raw_word': word,
                    'clean_word': word.rstrip('-'),
                    'stem': stem,
                    'root': root
                }
                
                # We pass the raw SCL tags (e.g., "viBakwiH:1"). 
                # The engine handles the pivot mapping!
                analyses.append((context, clean_tags))
                
        return analyses

    def encode(self, translated_analyses_list, output_format='json', source_platform='Unknown'):
        """
        SCL is primarily an analyzer (input). Generating perfect native SCL output strings 
        requires generating <level:X> structural hierarchies, which is outside the scope of SMC.
        We output a functional representation instead.
        """
        if not translated_analyses_list:
            return []

        results = []
        
        # 1. STRING MODE: Fallback representation
        if output_format == 'string':
            word_groups = {}

            for context, tags in translated_analyses_list:
                word = context.get('raw_word', '')
                stem = context.get('stem', '') 
                root = context.get('root', '')
                clean_tags = [t for t in tags if t and t.strip()]
                
                # --- TAG PARTITIONING LOGIC ---
                if stem and root and stem != root:
                    # Derivation: Separate tags into Root-specific and Stem-specific
                    root_tags = []
                    stem_tags = []
                    
                    for t in clean_tags:
                        # Identify stem-specific tags
                        if any(t.startswith(prefix) for prefix in ['vargaH:', 'lifgam:', 'viBakwiH:', 'vacanam:', 'level:']):
                            stem_tags.append(t)
                        else:
                            # Everything else (XAwuH, kqw, lakAraH, etc.) attaches to the root
                            root_tags.append(t)
                            
                    root_tag_str = "".join([f"<{t}>" for t in root_tags])
                    stem_tag_str = "".join([f"<{t}>" for t in stem_tags])
                    
                    if not root_tags:
                        # If mapping failed and we have no root tags, do NOT glue root and stem!
                        # Fallback to the stem natively.
                        chunk = f"{stem}{stem_tag_str}"
                    else:
                        chunk = f"{root}{root_tag_str}{stem}{stem_tag_str}"
                    
                else:
                    # Simple word (either pure verbal root OR pure nominal stem)
                    tag_str = "".join([f"<{t}>" for t in clean_tags])
                    
                    if root and not stem:
                        chunk = f"{root}{tag_str}"
                    else:
                        # Default to stem if they are the same or only stem exists
                        chunk = f"{stem}{tag_str}"
                    
                # Group chunks by their specific word
                if word not in word_groups:
                    word_groups[word] = []
                    
                if chunk not in word_groups[word]:
                    word_groups[word].append(chunk)
                    
            # Compile each word's group into a separate SCL string
            final_strings = []
            for word, chunks in word_groups.items():
                analyses_str = "/".join(chunks)
                final_strings.append(f"^{word}/{analyses_str}$")
                
            return final_strings

        # 2. JSON MODE: Flat Dictionary
        for context, tags in translated_analyses_list:
            word = context.get('raw_word', '')
            stem = context.get('stem', '')
            root = context.get('root', '')
            
            clean_tags = [t for t in tags if t and t.strip()]
            
            entry = {
                "word": word,
                "stem": stem,
                "root": root,
                "tags": clean_tags,
                "source": source_platform # Injected exactly like ByT5/Canonical
            }
            
            if entry not in results:
                results.append(entry)
            
        return results

class SvarupaAdapter(BaseAdapter):
    def decode(self, raw_string):
        """Parses Svarupa baseline strings separated by | and ,"""
        if not raw_string or raw_string.strip() in ['_', '']: 
            return []
            
        context = {
            'full_input': '',
            'raw_word': '',
            'clean_word': '',
            'stem': '',
            'root': ''
        }
        
        all_tags = []
        components = [c.strip() for c in raw_string.split('|') if c.strip()]
        for comp in components:
            for feat in comp.split(','):
                feat = feat.strip()
                if '=' in feat:
                    # Optional: Strip out the key if you only mapped values in the TSV
                    # Or keep it as "Key=Value" if that's exactly what's in your TSV's svarupa column
                    all_tags.append(feat)
                    
        return [(context, all_tags)] if all_tags else []

    def encode(self, translated_analyses_list, output_format='json', source_platform='Unknown'):
        """UPDATED: Accepts the full payload list."""
        if not translated_analyses_list:
            return []
            
        results = []
        for context, tags_set in translated_analyses_list:
            out_str = ", ".join(sorted(tags_set))
            if out_str not in results:
                results.append(out_str)
                
        return results
    
class CanonicalAdapter(BaseAdapter):
    def decode(self, raw_data):
        """Parses Canonical strings (word_lemma_tags) or flat JSON arrays."""
        if isinstance(raw_data, list):
            items = raw_data
        elif isinstance(raw_data, str):
            try:
                parsed = json.loads(raw_data)
                items = parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                items = raw_data.split() 
        else:
            items = [raw_data]

        analyses = []
        for item in items:
            word = ""
            stem = ""
            root = ""
            lemma = ""
            morph_str = ""
            
            if isinstance(item, dict):
                word = item.get('word', '')
                stem = item.get('stem', '')
                root = item.get('root', '')
                
                # Reconstruct tags from flat JSON
                tags = item.get('inflectional_morphs', []).copy()
                if item.get('derivational_morph'):
                    tags.extend(item.get('derivational_morph').split('|'))
                    
            elif isinstance(item, str):
                parts = item.split('_')
                if len(parts) >= 4:
                    word = parts[0]
                    stem = parts[1]
                    root = parts[2]
                    morph_str = "_".join(parts[3:]) 
                elif len(parts) >= 3:
                    word = parts[0]
                    lemma = parts[1]
                    morph_str = "_".join(parts[2:]) 
                elif len(parts) == 2:
                    word, lemma, morph_str = parts[0], parts[1], ""
                else:
                    word, lemma, morph_str = item, "", ""
                
                tags = [t for t in morph_str.split('|') if t and t.strip()]

                has_tense = any(t.startswith("Tense=") for t in tags)
                has_mood = any(t.startswith("Mood=") for t in tags)
                has_verbform = any(t.startswith("VerbForm=") for t in tags)
                has_case = any(t.startswith("Case=") for t in tags)

                if stem and root:
                    pass
                elif has_tense and has_mood:
                    root = lemma
                elif has_verbform and has_case:
                    stem = lemma
                elif has_verbform and not has_case:
                    root = lemma
                else:
                    stem = lemma
            
            context = {
                'full_input': '',
                'raw_word': word,
                'clean_word': word.rstrip('-'),
                'stem': stem,
                'root': root,
            }
            analyses.append((context, tags))
            
        return analyses

    def encode(self, translated_analyses_list, output_format='json', source_platform='Unknown'):
        """Outputs exactly: input, stem, root, and a sorted morph string."""
        if not translated_analyses_list:
            return []
            
        results = []
        for context, tags_set in translated_analyses_list:
            word = context.get('raw_word', '')
            stem = context.get('stem', '')
            root = context.get('root', '')

            # Clean tags immediately for both formats
            clean_tags = [t for t in tags_set if t and t.strip()]

            # -----------------------------------------
            # JSON MODE
            # -----------------------------------------
            if output_format == 'json':
                derivational_morphs = []
                inflectional_morphs = []

                # 1. Identify the Structural Anchor of the word
                is_derivative = any(t.startswith(("VerbForm=", "PrimaryDerivative=", "SecondaryDerivative=")) for t in clean_tags)
                is_finite_verb = any(t.startswith("Mood=") for t in clean_tags)

                # Heuristic to separate Canonical tags into Derivational vs Inflectional
                for tag in tags_set:
                    # ALWAYS INFLECTIONAL (Declensions & Verb Persons/Numbers)
                    if tag.startswith(("Case=", "Gender=", "Number=", "Person=")):
                        inflectional_morphs.append(tag)
                    # ALWAYS DERIVATIONAL (The Anchor Tags)
                    elif tag.startswith(("VerbForm=", "PrimaryDerivative=", "SecondaryDerivative=")):
                        derivational_morphs.append(tag)
                    # THE POLYMORPHIC TAGS: Context-Dependent Routing
                    elif tag.startswith(("Tense=", "Prayoga=", "PaxI=", "Class=", "Conjugation=", "Formation=")):
                        if is_finite_verb and not is_derivative:
                            # For a finite verb (e.g., bhavati), Tense/Voice/Class are part of the inflection
                            inflectional_morphs.append(tag)
                        else:
                            # For a participle (e.g., bhavan), Tense/Voice/Class describe the krt suffix
                            derivational_morphs.append(tag)
                    # Fallback for anything else (Mood, NounType, etc.)
                    else:
                        inflectional_morphs.append(tag)

                entry = {
                    "word": word,
                    "stem": stem,
                    "root": root,
                    "derivational_morph": "|".join(sorted(derivational_morphs)),
                    "inflectional_morphs": ["|".join(sorted(inflectional_morphs))],
                    "source": source_platform
                }

                if entry not in results:
                    results.append(entry)

            # -----------------------------------------
            # STRING MODE
            # -----------------------------------------
            else:
                # Sort alphabetically so evaluations are mathematically consistent
                morph_str = "|".join(sorted(clean_tags))
            
                if stem and root:
                    lemma = f"{stem}_{root}"
                elif stem:
                    lemma = stem
                elif root:
                    lemma = root
                else:
                    lemma = stem
                
                word_out = word if word else ""
                lemma_out = lemma if lemma else ""
                
                out_str = f"{word_out}_{lemma_out}_{morph_str}"

                if out_str not in results:
                    results.append(out_str)
                    
        return results