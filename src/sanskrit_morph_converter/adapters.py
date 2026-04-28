import re
import json

class BaseAdapter:
    def decode(self, raw_data):
        """Converts raw platform output into a LIST of tuples: [(context_dict, tag_list)]"""
        raise NotImplementedError
        
    def encode(self, translated_analyses_list, output_format='json'):
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
                items = [raw_data]
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

    def encode(self, translated_analyses_list, output_format='json'):
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
                    "morph": morph_dict
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
                items = [raw_data]
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

    def encode(self, translated_analyses_list, output_format='json'):
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
                    "morph": morph_dict
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

    def encode(self, translated_analyses_list, output_format='json'):
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
        needs_stitching = not full_input_string

        # Track the memory ID of contexts we have already stitched to prevent duplication
        seen_contexts = set()

        for context, tags_set in translated_analyses_list:
            # 0. STITCH THE COMPOUND CONTEXT
            ctx_id = id(context)
            if ctx_id not in seen_contexts:
                seen_contexts.add(ctx_id)

                raw_word = context.get('raw_word', '') # e.g., "kavi-"
                clean_word = context.get('clean_word', '') # e.g., "kavi"

                if needs_stitching:
                    if clean_word:
                        segmentation.append(clean_word)

                    # Build the full word (kavi- + kratuH -> kavikratuH)
                    if raw_word:
                        if full_input_string and not full_input_string.endswith('-'):
                            full_input_string += " " + raw_word # Add space for new word
                        elif full_input_string.endswith('-'):
                            full_input_string = full_input_string[:-1] + raw_word # Merge compound
                        else:
                            full_input_string = raw_word
            
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

            # 3. GROUP BY CONTEXT AND DERIVATIONAL BASE
            group_key = (
                clean_word,
                context.get('stem', ''),
                context.get('root', ''),
                derivational_string
            )

            if group_key not in grouped_morphs:
                grouped_morphs[group_key] = []
            if inflectional_string:
                grouped_morphs[group_key].append(inflectional_string)

        # 4. BUILD THE FINAL JSON PAYLOAD
        morph_array = []
        for (word, stem, root, deriv_str), infl_list in grouped_morphs.items():
            entry = {
                'word': word,
                'stem': stem,
                'root': root,
                'inflectional_morphs': infl_list
            }
            if deriv_str:
                entry['derivational_morph'] = deriv_str
                
            morph_array.append(entry)
        
        # 5. Build the final SH-Compliant Dictionary
        # We assume 'Success' since the translation engine successfully generated these tags.
        sh_json = {
            'input': full_input_string.replace('-', ''),
            'status': 'Success',
            'segmentation': segmentation,
            'morph': morph_array,
            'source': 'morph-mapper'
        }

        return sh_json

class SCLAdapter(BaseAdapter):
    def decode(self, raw_string):
        """UPDATED: Now returns a list of (context, tags) tuples with standardized keys."""
        if not raw_string:
            return []
            
        analyses = []
        blocks = raw_string.strip('$').split('/')
        
        for block in blocks:
            if not block:
                continue
            tags = re.findall(r'<([^>]+)>', block)
            if tags:
                # Provide a standardized blank context dictionary
                context = {
                    'full_input': '',
                    'raw_word': '',
                    'clean_word': '',
                    'stem': '',
                    'root': ''
                }
                analyses.append((context, tags))
                
        return analyses

    def encode(self, translated_analyses_list, output_format='json'):
        """UPDATED: Accepts the full payload list."""
        if not translated_analyses_list:
            return []
            
        results = []
        for context, tags_set in translated_analyses_list:
            out_str = "".join(f"<{tag}>" for tag in sorted(tags_set))
            if out_str not in results:
                results.append(out_str)
                
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

    def encode(self, translated_analyses_list, output_format='json'):
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
        """Not strictly needed unless you plan to use Canonical as an input source later."""
        return []

    def encode(self, translated_analyses_list, output_format='json'):
        """Outputs exactly: input, stem, root, and a sorted morph string."""
        if not translated_analyses_list:
            return []
            
        results = []
        for context, tags_set in translated_analyses_list:
            word = context.get('raw_word', '')
            stem = context.get('stem', '')
            root = context.get('root', '')
            
            # Sort alphabetically so evaluations are mathematically consistent
            morph_str = "|".join(sorted(tags_set))
            
            if output_format == 'json':
                out_obj = {
                    "input": word,
                    "stem": stem,
                    "root": root,
                    "morph": morph_str
                }
                if out_obj not in results:
                    results.append(out_obj)
            else:
                # String output: input_stem_root_morph
                word_out = word if word else "_"
                stem_out = stem if stem else "_"
                root_out = root if root else "_"
                out_str = f"{word_out}_{stem_out}_{root_out}_{morph_str}"
                
                if out_str not in results:
                    results.append(out_str)
                    
        return results