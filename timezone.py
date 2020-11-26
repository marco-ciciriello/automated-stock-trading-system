import pytz

from datetime import datetime


def is_dst():
    """ Determine whether Daylight Savings Time is currently in effect. """

    x = datetime(datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('Europe/London'))  # Timezone as of Jan 1st of this year
    y = datetime.now(pytz.timezone('Europe/London'))  # Timezone as of now

    # If DST is in effect, x and y offsets will be different
    return not(y.utcoffset() == x.utcoffset())
