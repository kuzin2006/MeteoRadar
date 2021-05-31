import requests
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin
import pytz

from pydantic import BaseModel

_RADAR = "UKBB2"
_LOCAL_TZ = "Europe/Kiev"

"""
Docs for this
https://www.rainviewer.com/ru/api.html

Sources:
https://data.rainviewer.com/images/
"""


class RainviewerScan(BaseModel):
    timestamp: datetime
    name: str
    size: int
    width: int
    heigth: int


class RainviewerProduct(BaseModel):
    id: str
    name: str
    frequency: int
    lastUpdate: int
    boundingBox: List[float]
    scans: List[RainviewerScan]


class RainViewerAPIResponse (BaseModel):
    id: str
    host: str
    dir: str
    products: List[RainviewerProduct]
    default: str

    @property
    def base_url(self):
        return f"{self.host}{self.dir}/"


class RainViewerClient:
    """
    Obtain data from RainViewer API
    """
    def __init__(self, radar_code):
        self.radar_code = radar_code
        self.api_url = f"https://data.rainviewer.com/images/{radar_code}/0_products.json"
        self.updated_at: str = ""

        self.product: Optional[RainviewerProduct] = None
        self.latest_scan: Optional[RainviewerScan] = None
        self.api_data: Optional[RainViewerAPIResponse] = None

    def update(self):
        try:
            resp = requests.get(self.api_url)
            self.api_data = RainViewerAPIResponse(**resp.json())
            self.product = self.api_data.products.pop()
            self.latest_scan = self.product.scans[-1]

            self.updated_at = self._date_to_str(self.latest_scan.timestamp)

        except Exception:
            return

    @staticmethod
    def _date_to_str(utc_dt: datetime):
        local_tz = pytz.timezone(_LOCAL_TZ)
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)

        return local_tz.normalize(local_dt).strftime("%d.%m.%Y, %H:%M:%S")

    @property
    def jpeg_url(self) -> str:
        file_prefix_data = self.latest_scan.name.split("_")
        jpeg_filename = f"{'_'.join(file_prefix_data[:3])}_0_source.jpg"

        return urljoin(f"{self.api_data.base_url}", jpeg_filename)

    def sensor_data(self) -> dict:
        self.update()
        return {
            "radar": self.radar_code,
            "updated_at": self.updated_at,
            "jpeg_url": self.jpeg_url,
        }


# to create a file:
# jpeg_resp = requests.get(jpeg_url)
# with open("radar.jpg", "wb") as fp:
#     fp.write(jpeg_resp.content)


