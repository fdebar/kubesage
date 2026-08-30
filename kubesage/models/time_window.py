from datetime import datetime, timedelta

from pydantic import BaseModel

DEFAULT_LOOKBACK = timedelta(minutes=15)
DEFAULT_LOOKAHEAD = timedelta(minutes=5)


class IncidentTimeWindow(BaseModel):
    start: datetime
    end: datetime

    @classmethod
    def from_observed_at(
        cls,
        observed_at: datetime,
        lookback: timedelta,
        lookahead: timedelta,
    ) -> IncidentTimeWindow:
        return cls(
            start=observed_at - lookback,
            end=observed_at + lookahead,
        )
