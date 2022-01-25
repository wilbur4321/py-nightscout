# pylint: disable=missing-module-docstring,missing-function-docstring
from py_nightscout.models import (
    ScheduleEntry,
    AbsoluteScheduleEntry,
    Schedule,
)
from datetime import datetime, timedelta
import pytz


def test_schedule_conversion_to_absolute_time():
    # Schedule should be fixed offset, to match the pump's date math
    schedule_tz = pytz.timezone("Etc/GMT+5")
    schedule = Schedule(
        [
            ScheduleEntry(offset=timedelta(hours=0), value=1),
            ScheduleEntry(offset=timedelta(hours=6), value=0.7),
            ScheduleEntry(offset=timedelta(hours=12), value=0.8),
            ScheduleEntry(offset=timedelta(hours=22), value=0.9),
        ],
        schedule_tz,
    )
    # Queries against the schedule are typically in utc
    items = schedule.between(
        datetime(2017, 7, 7, 20, tzinfo=pytz.utc),
        datetime(2017, 7, 8, 6, tzinfo=pytz.utc),
    )

    expected = [
        AbsoluteScheduleEntry(datetime(2017, 7, 7, 12, tzinfo=schedule_tz), 0.8),
        AbsoluteScheduleEntry(datetime(2017, 7, 7, 22, tzinfo=schedule_tz), 0.9),
        AbsoluteScheduleEntry(datetime(2017, 7, 8, 0, tzinfo=schedule_tz), 1),
    ]

    assert len(items) == len(expected)

    for item, expected_item in zip(items, expected):
        assert item.start_date == expected_item.start_date
        assert item.value == expected_item.value
