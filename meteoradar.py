import json
import requests
from datetime import datetime
from typing import List
from urllib.parse import urljoin

from pydantic import BaseModel

_API_URL = "https://data.rainviewer.com/images/UKBB2/0_products.json"


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


resp = requests.get(_API_URL)

data = RainViewerAPIResponse(**resp.json())

product = data.products.pop()
latest_scan = product.scans[-1]

file_prefix_data = latest_scan.name.split("_")
jpeg_filename = f"{'_'.join(file_prefix_data[:3])}_0_source.jpg"

jpeg_url = urljoin(f"{data.base_url}", jpeg_filename)

jpeg_resp = requests.get(jpeg_url)
with open("radar.jpg", "wb") as fp:
    fp.write(jpeg_resp.content)

print("done")

