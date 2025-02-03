from dataclasses import dataclass, field
from datetime import datetime
from agents.flight_team.crawl.utils.airport_codes import get_city_name


@dataclass
class Flight:
    airline: str
    departure_datetime: datetime
    flight_number: str
    origin_city: str
    origin_code: str
    dest_city: str
    dest_code: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "airline": self.airline,
            "departure_datetime": self.departure_datetime.isoformat(),
            "flight_number": self.flight_number,
            "origin_city": self.origin_city,
            "origin_code": self.origin_code,
            "dest_city": self.dest_city,
            "dest_code": self.dest_code,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            airline=data["airline"],
            departure_datetime=datetime.fromisoformat(data["departure_datetime"])
            if isinstance(data["departure_datetime"], str)
            else data["departure_datetime"],
            flight_number=data["flight_number"],
            origin_city=get_city_name(data["origin_code"]),
            origin_code=data["origin_code"],
            dest_city=get_city_name(data["dest_code"]),
            dest_code=data["dest_code"],
            created_at=datetime.now(),
        )
