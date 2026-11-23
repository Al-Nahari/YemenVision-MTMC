import sys
from dataclasses import replace
from urllib.parse import parse_qs, urlparse

import numpy as np
import pytest
from app.config import Settings, settings
from app.media import media_url, verify_media_request
from app.privacy import redact_frame


class _FakeCv2:
    @staticmethod
    def GaussianBlur(region, _ksize, _sigma):
        return np.zeros_like(region)


def test_settings_reject_unblurred_output_without_opt_in():
    with pytest.raises(ValueError, match='blur_mode is off'):
        Settings(blur_plates=True, allow_unblurred_output=False, blur_mode='off')


def test_media_signature_is_short_lived_and_tamper_evident():
    url = media_url('clip.mp4', ttl_seconds=60)
    query = parse_qs(urlparse(url).query)
    expires = int(query['exp'][0])
    signature = query['sig'][0]

    assert verify_media_request('clip.mp4', expires, signature)
    assert not verify_media_request('other.mp4', expires, signature)
    assert not verify_media_request('clip.mp4', expires, 'bad-signature')
    assert not verify_media_request('clip.mp4', 1, signature)


def _enable_blur(monkeypatch):
    monkeypatch.setattr(
        'app.privacy.settings',
        replace(settings, blur_plates=True, blur_mode='plate_region'),
    )


def test_unblurred_output_is_the_documented_default():
    assert settings.blur_plates is False
    assert settings.allow_unblurred_output is True
    assert settings.plate_ocr_enabled is True


def test_redact_frame_fails_closed_when_no_vehicle_was_detected(monkeypatch):
    _enable_blur(monkeypatch)
    monkeypatch.setitem(sys.modules, 'cv2', _FakeCv2)
    frame = np.full((16, 16, 3), 255, dtype=np.uint8)

    redact_frame(frame, [])

    assert int(frame.max()) == 0


def test_redact_frame_blurs_only_the_vehicle_region(monkeypatch):
    _enable_blur(monkeypatch)
    monkeypatch.setitem(sys.modules, 'cv2', _FakeCv2)
    frame = np.full((20, 20, 3), 255, dtype=np.uint8)

    redact_frame(frame, [[2, 2, 18, 18]])

    assert int(frame[0, 0, 0]) == 255
    assert int(frame[15, 15, 0]) == 0
