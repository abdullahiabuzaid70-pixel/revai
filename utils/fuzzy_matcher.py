"""
Fuzzy Matching Utility — for vendor name normalization
Handles "Dangote Industries Ltd" vs "Dangote Ind." vs "DANGOTE INDUSTRIES"
"""
from fuzzywuzzy import fuzz
import re


def normalize_vendor_name(name):
    """Normalize vendor name for comparison."""
    if not name or not isinstance(name, str):
        return ""
    
    name = name.strip()
    # Remove common Nigerian business suffixes
    suffixes = [
        " ltd", " limited", " plc", " inc", " llc", 
        " co", " company", " nig", " nigeria", " nig ltd",
        " ent", " enterprises", " ent ltd", " & co", " and co",
        " ltd.", " plc.", " inc."
    ]
    lower_name = name.lower()
    for suffix in suffixes:
        if lower_name.endswith(suffix):
            name = name[:len(name) - len(suffix)].strip()
            lower_name = name.lower()
    
    # Remove special characters
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def get_similarity_score(name1, name2):
    """Get a 0-100 similarity score between two vendor names."""
    norm1 = normalize_vendor_name(name1)
    norm2 = normalize_vendor_name(name2)
    
    if not norm1 or not norm2:
        return 0
    
    # Use token sort ratio — handles word order differences
    score = fuzz.token_sort_ratio(norm1, norm2)
    return score


def are_same_vendor(name1, name2, threshold=85):
    """Check if two vendor names refer to the same entity."""
    return get_similarity_score(name1, name2) >= threshold


def group_vendors(names, threshold=85):
    """
    Group a list of vendor names into clusters of similar names.
    Returns a dict: {canonical_name: [list of original names]}
    """
    groups = {}
    used = set()
    
    for i, name1 in enumerate(names):
        if i in used:
            continue
        group = [name1]
        used.add(i)
        
        for j, name2 in enumerate(names):
            if j in used or i == j:
                continue
            if are_same_vendor(name1, name2, threshold):
                group.append(name2)
                used.add(j)
        
        canonical = normalize_vendor_name(name1)
        groups[canonical] = group
    
    return groups
