from typing import Dict, List, Optional, Tuple
import numpy as np
from sentence_transformers import util

from .dependencies import get_nlp, get_embedder, encode_norm
from .labels import AGREEMENT_LABELS, INDUSTRY_LABELS, COUNTRY_HINTS
from .utils import first_nonempty_line, first_date, norm


class AnalyzerService:
    """Encapsulates all NLP/embedding logic."""

    def __init__(self):
        self._nlp = get_nlp()
        self._embedder = get_embedder()

    # ---- public API ----
    def analyze(self, text: str) -> Dict:
        txt = text or ""
        title = first_nonempty_line(txt) or None
        eff_date = first_date(txt)

        ag_type, ag_conf = self._best_label(txt, AGREEMENT_LABELS)
        ind, ind_conf = self._best_label(txt, INDUSTRY_LABELS)
        govlaw, gov_conf = self._governing_law(txt)
        parties = self._extract_parties(txt)

        return {
            "title": title,
            "effective_date": eff_date,
            "governing_law": govlaw,
            "governing_law_confidence": gov_conf,
            "agreement_type": ag_type,
            "agreement_type_confidence": ag_conf,
            "industry": ind,
            "industry_confidence": ind_conf,
            "parties": parties,
        }

    # ---- internals ----
    def _best_label(
        self, text: str, labels: Dict[str, str]
    ) -> Tuple[Optional[str], float]:
        doc = text[:5000]
        doc_emb = encode_norm(self._embedder, [doc])
        label_texts = [f"{k}: {v}" for k, v in labels.items()]
        lab_embs = encode_norm(self._embedder, label_texts)
        sims = util.cos_sim(doc_emb, lab_embs).cpu().numpy()[0]
        idx = int(np.argmax(sims))
        return list(labels.keys())[idx], float(sims[idx])

    def _governing_law(self, text: str) -> Tuple[Optional[str], float]:
        t = norm(text)

        # Rule-based hints
        for code, hints in COUNTRY_HINTS.items():
            if any(h in t for h in hints):
                return code, 0.70

        # NER fallback
        doc = self._nlp(text[:8000])
        gpes = [ent.text.lower() for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
        if any("united states" in g for g in gpes):
            return "US", 0.65
        if any("germany" in g for g in gpes):
            return "DE", 0.65
        if any("united kingdom" in g or "england" in g for g in gpes):
            return "UK", 0.65
        if any("south africa" in g for g in gpes):
            return "ZA", 0.65
        if any(
            "united arab emirates" in g or "dubai" in g or "abu dhabi" in g
            for g in gpes
        ):
            return "AE", 0.65
        return None, 0.0

    def _extract_parties(self, text: str) -> List[str]:
        doc = self._nlp(text[:8000])
        orgs = [ent.text for ent in doc.ents if ent.label_ in ("ORG", "PERSON")]
        seen, parties = set(), []
        for o in orgs:
            s = o.strip()
            if s and s not in seen:
                seen.add(s)
                parties.append(s)
                if len(parties) >= 4:
                    break
        return parties
