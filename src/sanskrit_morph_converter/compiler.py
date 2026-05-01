import pandas as pd
import os
import re
import csv
from collections import defaultdict

# # OLD
# DEFAULT_SHEET_ID = "1a_CaU9JBnHhg6PkHZ1TNRPtnu3RIdG6HNnCFO-ngzz8"
# DEFAULT_GID = "214029579"

# NEW
DEFAULT_SHEET_ID = "1dWyPWj-OKuikfyutYC4SYnESn712SUSir-VZ_eyigpA"
DEFAULT_GID = "214029579"

def download_google_sheet(sheet_id, gid=DEFAULT_GID):
    if "docs.google.com" in sheet_id:
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_id)
        if match:
            sheet_id = match.group(1)
    
    sheet_id = sheet_id.strip()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=tsv&gid={gid}"
    print(f"Downloading from: {url}")
    
    try:
        df = pd.read_csv(url, sep='\t', dtype=str).fillna("")
        return df.to_dict('records')
    except Exception as e:
        print(f"Download failed! Error: {e}")
        return []

def compile_mappings(sheet_id=DEFAULT_SHEET_ID, local_tsv_path=None):
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    norm_tsv = os.path.join(data_dir, 'normalization.tsv')
    out_norm_tsv = os.path.join(data_dir, 'output_normalization.tsv')
    pivot_tsv = os.path.join(data_dir, 'pivot_mapping.tsv')
    reference_tsv = os.path.join(data_dir, 'reference.tsv')

    if local_tsv_path:
        df = pd.read_csv(local_tsv_path, sep='\t', dtype=str).fillna("")
        records = df.to_dict('records')
    else:
        records = download_google_sheet(sheet_id)
        if not records: return

    normalizations = []
    output_normalizations = []
    convergences = {'DCS': defaultdict(set), 'ByT5': defaultdict(set)}
    
    tag_mappings = {
        'SCL': defaultdict(set), 'SH': defaultdict(set), 
        'ByT5': defaultdict(set), 'DCS': defaultdict(set),
        'Svarupa': defaultdict(set), 'Canonical': defaultdict(set)
    }
    reference_data = {}
    
    current_scl, current_sh, current_byt5, current_svarupa = None, None, None, None

    for row in records:
        if not any(str(val).strip() for val in row.values()): 
            continue

        # 1. READ COLUMNS EXACTLY AS THEY ARE
        scl_val = str(row.get('SCL', '')).strip()
        sh_val = str(row.get('SH', '')).strip()
        byt5_val = str(row.get('ByT5', '')).strip()
        byt5_new_val = str(row.get('ByT5_new', '')).strip()
        dcs_val = str(row.get('DCS', '')).strip()
        dcs_new_val = str(row.get('DCS_new', '')).strip()
        svarupa_val = str(row.get('Svarupa', '')).strip()
        canonical_val = str(row.get('Canonical', '')).strip()

        sh_internal = sh_val
        for i in range(1, 8):
            sh_internal = sh_internal.replace(f"aor. [{i}]", f"aor_{i}")
        for i in range(1, 4):
            sh_internal = sh_internal.replace(f"pfp. [{i}]", f"pfp_{i}")

        eng_ref = str(row.get('English', '')).strip()
        san_ref = str(row.get('Sanskrit', '')).strip()
        
        # 2. THE UNIVERSAL PIVOT FEATURE
        pivot_val = str(row.get('pivot_grammar', '')).strip()
        
        # Determine the "Expanded_Features" for the reference sheet (No trackers used!)
        expanded_kv = canonical_val if canonical_val else (scl_val if scl_val else sh_internal)

        if pivot_val:
            pivot_feature = pivot_val

            if pivot_feature not in reference_data:
                reference_data[pivot_feature] = {
                    'pivot_grammar': pivot_feature,
                    'Expanded_Features': expanded_kv,
                    'English': eng_ref,
                    'Sanskrit': san_ref
                }
            else:
                if not reference_data[pivot_feature]['English'] and eng_ref:
                    reference_data[pivot_feature]['English'] = eng_ref
                if not reference_data[pivot_feature]['Sanskrit'] and san_ref:
                    reference_data[pivot_feature]['Sanskrit'] = san_ref
        else:
            pivot_feature = expanded_kv
            if not pivot_feature: 
                continue

        # 3. NORMALIZATION (Aliases)
        if dcs_val and dcs_new_val and dcs_new_val != dcs_val:
            convergences['DCS'][dcs_new_val].add(dcs_val)
        
        if byt5_val and byt5_new_val and byt5_new_val != byt5_val:
            convergences['ByT5'][byt5_new_val].add(byt5_val)

        # 4. MAP PLATFORMS STRICTLY TO THIS ROW
        # If the cell is blank, the platform gets NOTHING for this row.
        if scl_val: tag_mappings['SCL'][scl_val].add(pivot_feature)
        if sh_internal: tag_mappings['SH'][sh_internal].add(pivot_feature)
        if byt5_val: tag_mappings['ByT5'][byt5_val].add(pivot_feature)
        if byt5_new_val: tag_mappings['ByT5'][byt5_new_val].add(pivot_feature)
        if dcs_val: tag_mappings['DCS'][dcs_val].add(pivot_feature)
        if dcs_new_val: tag_mappings['DCS'][dcs_new_val].add(pivot_feature)
        if svarupa_val: tag_mappings['Svarupa'][svarupa_val].add(pivot_feature)
        if canonical_val: tag_mappings['Canonical'][canonical_val].add(pivot_feature)

    # ==========================================
    # AUTOMATIC ALIAS VS COMPRESSION ROUTING
    # ==========================================
    # Run this AFTER the loop finishes, right before you write the files!
    
    for platform in ['DCS', 'ByT5']:
        for new_tag, old_tags in convergences[platform].items():
            if len(old_tags) == 1:
                # ALIAS (1:1) -> Safe for Input Normalization
                old_tag = list(old_tags)[0]
                if old_tag != new_tag:
                    normalizations.append({
                        'Platform': platform, 
                        'Deprecated_Tag': old_tag, 
                        'Current_Tag': new_tag
                    })
            else:
                # COMPRESSION (N:1) -> Must use Output Normalization to prevent data loss!
                for old_tag in old_tags:
                    if old_tag != new_tag:
                        output_normalizations.append({
                            'Platform': platform, 
                            'Deprecated_Tag': old_tag, 
                            'Current_Tag': new_tag
                        })
    
    
    # ==========================================
    # WRITE OUTPUTS
    # ==========================================
    with open(norm_tsv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Platform', 'Deprecated_Tag', 'Current_Tag'], delimiter='\t')
        writer.writeheader()
        writer.writerow({'Platform': 'SH', 'Deprecated_Tag': 'md.', 'Current_Tag': 'mo.'})
        for norm in normalizations: writer.writerow(norm)

    with open(out_norm_tsv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Platform', 'Deprecated_Tag', 'Current_Tag'], delimiter='\t')
        writer.writeheader()
        for norm in output_normalizations: writer.writerow(norm)

    with open(pivot_tsv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['Platform', 'Platform_Tag', 'Pivot_Features'])
        for platform, mappings in tag_mappings.items():
            for p_tag, pivot_set in mappings.items():
                if p_tag and pivot_set:
                    writer.writerow([platform, p_tag, "||".join(sorted(pivot_set))])
    
    with open(reference_tsv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pivot_grammar', 'Expanded_Features', 'English', 'Sanskrit'], delimiter='\t')
        writer.writeheader()
        for ref_data in reference_data.values():
            writer.writerow(ref_data)

    print(f"Success! Compiled tags saved to {data_dir}")

def cli_entry():
    import argparse
    parser = argparse.ArgumentParser(description="Compile Morphological Mappings.")
    parser.add_argument('--sheet-id', type=str, default=DEFAULT_SHEET_ID, help="Google Sheet ID.")
    parser.add_argument('--local-file', type=str, help="Path to local TSV")
    args = parser.parse_args()
    
    if args.local_file: compile_mappings(local_tsv_path=args.local_file)
    else: compile_mappings(sheet_id=args.sheet_id)

if __name__ == "__main__":
    cli_entry()