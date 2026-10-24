import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "scale", Path(__file__).parents[1] / "scripts/analyse_tidal_scale.py"
)
scale = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scale)


def test_link_normalization_does_not_promote_an_album_to_a_track():
    assert scale.tidal_ref("http://www.tidal.com/browse/track/123") == ("track", "123")
    assert scale.tidal_ref("https://tidal.com/album/123") == ("album", "123")
    assert scale.tidal_ref("https://tidal.com.evil.test/track/123") is None


def test_movement_stems_preserve_versions_and_work_numbers():
    assert scale.stem("Symphony No. 2: IIa. Theme") == "Symphony No. 2"
    assert (
        scale.stem("Sibelius: Symphony No. 2: I. Allegretto")
        == "Sibelius: Symphony No. 2"
    )
    assert (
        scale.stem("Symphony No. 4 (1947 Version): II. Andante")
        == "Symphony No. 4 (1947 Version)"
    )
