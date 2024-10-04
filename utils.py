from datetime import datetime, time
from zoneinfo import ZoneInfo

def is_news_time():
    moscow_time = datetime.now(ZoneInfo("Europe/Moscow")).time()
    return moscow_time in (time(13, 0), time(19, 0))
