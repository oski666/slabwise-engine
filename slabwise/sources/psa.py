"""PSA Public API cert lookup (free, personal access token).

Docs: https://www.psacard.com/publicapi/documentation
The token is read from the PSA_TOKEN environment variable and never stored in
the repository. Answers are cached on disk so each cert is asked only once.
Untested against the live API from this environment (network restricted):
the field names below follow the public documentation and must be checked on
the first real call.
"""
from __future__ import annotations

import json
import os
import urllib.request

API = "https://api.psacard.com/publicapi/cert/GetByCertNumber/{cert}"


class PSACertLookup:
    def __init__(self, card_resolver, cache_path="data/psa_cache.json", token=None):
        """``card_resolver(psa_cert_dict) -> catalogue card index or -1`` maps PSA's
        description (year, brand, card number, variety) to our catalogue."""
        self.token = token or os.environ.get("PSA_TOKEN")
        self.resolve = card_resolver
        self.cache_path = cache_path
        try:
            self.cache = json.load(open(cache_path))
        except (OSError, ValueError):
            self.cache = {}

    def _fetch(self, cert):
        if cert in self.cache:
            return self.cache[cert]
        if not self.token:
            return None
        req = urllib.request.Request(API.format(cert=cert), headers={"authorization": f"bearer {self.token}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        self.cache[cert] = data
        os.makedirs(os.path.dirname(self.cache_path) or ".", exist_ok=True)
        json.dump(self.cache, open(self.cache_path, "w"))
        return data

    def __call__(self, cert):
        """Return (card, grade) like the simulator's lookup, or None if unknown."""
        data = self._fetch(str(cert))
        if not data or "PSACert" not in data:
            return None
        c = data["PSACert"]
        try:
            grade = int(float(str(c.get("CardGrade", "")).split()[-1]))
        except ValueError:
            return None
        return self.resolve(c), grade
