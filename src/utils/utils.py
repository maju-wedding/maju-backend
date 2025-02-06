from datetime import datetime


def utc_now():
    return datetime.utcnow().replace(tzinfo=tz.tzutc())
