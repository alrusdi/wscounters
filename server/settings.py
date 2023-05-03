import datetime
from pathlib import Path

timezone_offset = 5
tzinfo = datetime.timezone(datetime.timedelta(hours=timezone_offset))
DEFAULT_TIMEZONE = tzinfo  #  YEKT

BASE_DIR = str(Path(__file__).parent.parent)
