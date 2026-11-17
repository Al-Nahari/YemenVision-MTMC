from yemenvision.privacy import NullPlateDetector, check_visual_output


def test_privacy_refuses_visual_output_without_plate_detector():
    decision = check_visual_output(blur_plates=True, allow_unblurred_output=False, plate_detector=NullPlateDetector())
    assert not decision.allowed
    assert decision.warning


def test_privacy_requires_explicit_unblurred_opt_in():
    decision = check_visual_output(blur_plates=True, allow_unblurred_output=True, plate_detector=NullPlateDetector())
    assert decision.allowed
    assert not decision.blurred
    assert decision.warning
