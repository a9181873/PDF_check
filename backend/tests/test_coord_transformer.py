from models.diff_models import BBox
from services.coord_transformer import CoordTransformer


def test_coord_round_trip():
    transformer = CoordTransformer(page_width_pt=600.0, page_height_pt=800.0)
    original = BBox(page=1, x0=60.0, y0=100.0, x1=240.0, y1=200.0)

    screen = transformer.to_screen(original, canvas_width=300)
    reconstructed = transformer.to_pdf(screen, canvas_width=300)

    assert abs(reconstructed.x0 - original.x0) < 1e-6
    assert abs(reconstructed.y0 - original.y0) < 1e-6
    assert abs(reconstructed.x1 - original.x1) < 1e-6
    assert abs(reconstructed.y1 - original.y1) < 1e-6
