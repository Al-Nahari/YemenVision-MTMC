import numpy as np
import pytest

from yemenvision.eval import check_identity_leakage, evaluate_reid


def test_reid_metrics_known_case():
    query = np.asarray([[1.0, 0.0]], dtype=np.float32)
    gallery = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    result = evaluate_reid(query, np.asarray(["v1"]), np.asarray(["cam1"]), gallery,
                           np.asarray(["v1", "v2"]), np.asarray(["cam2", "cam2"]))
    assert result.map == 1.0
    assert result.rank1 == 1.0


def test_identity_leakage_is_rejected():
    with pytest.raises(ValueError):
        check_identity_leakage(["v1"], ["v1"])
