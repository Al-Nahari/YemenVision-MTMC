from dataclasses import dataclass
@dataclass(frozen=True)
class ReIDSample:
 image: str; identity_id: str; camera_id: str; split: str
 vehicle_type: str='unknown'; color: str='unknown'; body_style: str='unknown'; viewpoint: str='unknown'; quality: str='unknown'
@dataclass(frozen=True)
class MatchDecision:
 label: str # likely_match|ambiguous|unknown|insufficient_visual_evidence
 calibrated_probability: float|None
 cosine_similarity: float
 reason: str
