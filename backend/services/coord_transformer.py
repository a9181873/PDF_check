from pydantic import BaseModel

from models.diff_models import BBox


class ScreenBBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    page: int


class CoordTransformer:
    def __init__(self, page_width_pt: float, page_height_pt: float):
        self.page_width = page_width_pt
        self.page_height = page_height_pt

    def to_screen(self, bbox: BBox, canvas_width: int) -> ScreenBBox:
        scale = canvas_width / self.page_width
        return ScreenBBox(
            x=bbox.x0 * scale,
            y=(self.page_height - bbox.y1) * scale,
            width=(bbox.x1 - bbox.x0) * scale,
            height=(bbox.y1 - bbox.y0) * scale,
            page=bbox.page,
        )

    def to_pdf(self, screen_bbox: ScreenBBox, canvas_width: int) -> BBox:
        scale = canvas_width / self.page_width
        x0 = screen_bbox.x / scale
        x1 = (screen_bbox.x + screen_bbox.width) / scale
        y1 = self.page_height - (screen_bbox.y / scale)
        y0 = self.page_height - ((screen_bbox.y + screen_bbox.height) / scale)
        return BBox(page=screen_bbox.page, x0=x0, y0=y0, x1=x1, y1=y1)
