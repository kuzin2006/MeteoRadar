import hassapi as hass

import requests
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin
import pytz

from pydantic import BaseModel

# ---- Client ----

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
    def __init__(self, radar_code: str):
        self.radar_code = radar_code
        self.api_url = f"https://data.rainviewer.com/images/{radar_code}/0_products.json"
        self.updated_at: str = ""

        self.product: Optional[RainviewerProduct] = None
        self.latest_scan: Optional[RainviewerScan] = None
        self.api_data: Optional[RainViewerAPIResponse] = None
        
        self.success = False

    def update(self):
        try:
            resp = requests.get(self.api_url)
            self.api_data = RainViewerAPIResponse(**resp.json())
            self.product = self.api_data.products.pop()
            self.latest_scan = self.product.scans[-1]

            self.updated_at = self._date_to_str(self.latest_scan.timestamp)
            
            self.success = True

        except Exception:
            self.success = False
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
            "updated_at": self.updated_at,
            "data": {
                  "radar": self.radar_code,
                  "success": self.success,
                  "jpeg_url": self.jpeg_url,
                },
            }

# ---------


class MeteoRadar(hass.Hass):
    """
    RainViewer Client Meteoradar Sensor
    """
    def initialize(self):        
        self.radar_code = self.args.get('radar', _RADAR)
        
        self.log(
            f"Initializing meteoradar for {self.args['radar']}, timezone: {_LOCAL_TZ}", 
            level='INFO'
            )
        
        self.client = RainViewerClient(radar_code=self.radar_code)
        
        self.update_interval = self.args.get("update_interval", 300)
        self.log(f"Update interval: {self.update_interval}s.", level='INFO')
        self.run_every(self.update_sensor, "now", self.update_interval)
        
    def update_sensor(self, kwargs):
        sensor_data = self.client.sensor_data()  
        self.log(f"{self.radar_code} update success = {sensor_data['data']['success']}", level='INFO')      
        
        sensor_name = f"sensor.rainviewer_meteoradar_{self.radar_code}"

        self.set_state(
          sensor_name, 
          state=sensor_data["updated_at"], 
          attributes=sensor_data["data"], 
          replace=True
        )
        
        
    
        
