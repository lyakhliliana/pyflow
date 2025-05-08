import hashlib
from typing import List


def stable_hash_from_hashes(hashes: List[str]) -> str:
    hashes.sort()
    combined = '\n'.join(hashes).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()[0:8]