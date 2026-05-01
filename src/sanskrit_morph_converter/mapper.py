import os
import pandas as pd

class PivotMapper:
    def __init__(self, norm_path=None, pivot_path=None, out_norm_path=None):
        base_dir = os.path.dirname(__file__)
        self.norm_path = norm_path or os.path.join(base_dir, 'data', 'normalization.tsv')
        self.pivot_path = pivot_path or os.path.join(base_dir, 'data', 'pivot_mapping.tsv')
        self.out_norm_path = out_norm_path or os.path.join(base_dir, 'data', 'output_normalization.tsv')
        
        # self.norms[platform][deprecated] = canonical
        self.norms = {} 
        self.out_norms = {}
        
        # self.encode_map[platform][platform_tag] = set_of_pivot_features
        self.encode_map = {} 
        
        # self.decode_map[platform] = [(required_pivot_features_set, target_platform_tag), ...]
        self.decode_map = {} 

        self._load_data()

    def _load_data(self):
        # 1. Load Normalizations
        df_norm = pd.read_csv(self.norm_path, sep="\t").fillna("")
        for _, row in df_norm.iterrows():
            plat = row['Platform']
            if plat not in self.norms: self.norms[plat] = {}
            self.norms[plat][row['Deprecated_Tag']] = row['Current_Tag']

        if os.path.exists(self.out_norm_path):
            df_out_norm = pd.read_csv(self.out_norm_path, sep="\t").fillna("")
            for _, row in df_out_norm.iterrows():
                plat = row['Platform']
                if plat not in self.out_norms: self.out_norms[plat] = {}
                self.out_norms[plat][row['Deprecated_Tag']] = row['Current_Tag']
        
        # 2. Load Pivot Mappings
        df_pivot = pd.read_csv(self.pivot_path, sep="\t").fillna("")
        for _, row in df_pivot.iterrows():
            plat = row['Platform']
            p_tag = row['Platform_Tag']

            # Split realities by ||, then split features by |
            realities = [frozenset(r.split('|')) for r in row['Pivot_Features'].split('||')]

            if plat not in self.encode_map:
                self.encode_map[plat] = {}
                self.decode_map[plat] = []

            self.encode_map[plat][p_tag] = realities
            for s_feats in realities:
                self.decode_map[plat].append((s_feats, p_tag))

    def normalize(self, platform, tags_list):
        """Replaces deprecated tags with canonical ones."""
        return [self.norms.get(platform, {}).get(tag, tag) for tag in tags_list]
    
    def output_normalize(self, platform, tags_list):
        """Forces target tags to upgrade to their modern equivalents (Compressions AND Aliases)."""
        upgraded = []
        for tag in tags_list:
            # 1. Try to upgrade compressions (N:1) from out_norms
            t1 = self.out_norms.get(platform, {}).get(tag, tag)
            
            # 2. Try to upgrade aliases (1:1) from norms
            t2 = self.norms.get(platform, {}).get(t1, t1)
            
            upgraded.append(t2)
            
        return upgraded

    def to_pivot(self, platform, tags_list):
        """Converts platform tags into a unified pool of Pivot features."""
        # Start with one empty reality
        pivot_pools = [set()]

        for tag in tags_list:
            # 1. Try to find the tag in the platform's standard dictionary
            mapped_realities = self.encode_map.get(platform, {}).get(tag)

            # 2. THE VERSIONING FALLBACK: If ByT5 doesn't know it, check DCS
            if mapped_realities is None and platform == 'ByT5':
                mapped_realities = self.encode_map.get('DCS', {}).get(tag)

            # 3. Default to empty if totally unrecognized by both
            if mapped_realities is None:
                mapped_realities = [set()]
            
            new_pools = []
            for existing_pool in pivot_pools:
                for reality_features in mapped_realities:
                    # Create a branch for every possible interpretation
                    branched_pool = set(existing_pool)
                    branched_pool.update(reality_features)
                    new_pools.append(branched_pool)
            pivot_pools = new_pools
        
        if not pivot_pools:
            return []
        
        # Find the size of the most harmonious (smallest) pool
        min_size = min(len(pool) for pool in pivot_pools)
        
        # Keep ONLY the pools that perfectly overlap with explicit context
        valid_pools = [pool for pool in pivot_pools if len(pool) == min_size]
            
        return valid_pools

    def from_pivot(self, target_platform, pivot_pool):
        """Finds strict matches and specific fan-outs for unmarked defaults."""
        target_rules = self.decode_map.get(target_platform, [])
        
        strict_tags = set()
        covered_features = set()
        
        # 1. MODE A: Find the base exact matches
        for rule_features, tag in target_rules:
            if rule_features and rule_features.issubset(pivot_pool):
                strict_tags.add(tag)
                covered_features.update(rule_features)
        
        tag_sets = []
        if strict_tags:
            tag_sets.append(set(strict_tags))
            
        leftover_features = pivot_pool - covered_features

        # 2. MODE B: Standard Ambiguity (e.g. DCS Generic -> SCL Specific)
        if leftover_features:
            candidate_intersections = []
            max_size = -1
            for rule_features, tag in target_rules:
                if leftover_features.issubset(rule_features):
                    size = len(rule_features.intersection(pivot_pool))
                    candidate_intersections.append((size, tag))
                    if size > max_size: max_size = size

            if candidate_intersections:
                best_candidates = [tag for size, tag in candidate_intersections if size == max_size]
                fan_out_sets = []
                for amb_tag in best_candidates:
                    combined_set = set(strict_tags)
                    combined_set.add(amb_tag)
                    fan_out_sets.append(combined_set)
                return {"match_type": "ambiguous", "tag_sets": fan_out_sets}

        # 3. MODE C (NEW): The Unmarked Default Fan-Out
        # If we had a perfect match, but the target platform has specific supersets of our pool!
        # (e.g. SCL lit -> SH pft. AND per. pft.)
        if not leftover_features and strict_tags:
            for rule_features, tag in target_rules:
                # Find rules that REQUIRE our pool, but have extra specific features
                if pivot_pool.issubset(rule_features) and len(rule_features) > len(pivot_pool):
                    # Create an alternative reality where the specific tag replaces its generic equivalent
                    alt_set = set(strict_tags)
                    for strict_tag in list(strict_tags):
                        s_feats = self.encode_map[target_platform].get(strict_tag, set())
                        if s_feats.issubset(rule_features):
                            alt_set.remove(strict_tag) # Remove 'pft.'
                    alt_set.add(tag) # Add 'per. pft.'
                    tag_sets.append(alt_set)
                    
            return {"match_type": "strict_with_variants", "tag_sets": tag_sets}

        return {"match_type": "partial" if strict_tags else "none", "tag_sets": tag_sets}