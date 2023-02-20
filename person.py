class Person:

    def __init__(self, user_id: int,
                 first_name: str = None,
                 last_name: str = None,
                 location: str = None,
                 aircraft: str = None) -> None:
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.location = location
        self.aircraft = aircraft

    def set_location(self, location: str) -> None:
        self.location = location

    def get_location(self) -> str:
        return str(self.location) if self.location is not None else None

    def set_name(self, first_name: str = None, last_name: str = None):
        self.first_name = first_name
        self.last_name = last_name

    def set_aircraft(self, aircrafts: list) -> None:
        self.aircraft = str(aircrafts)

    def get_aircraft(self) -> list or None:
        if self.aircraft is None:
            return None
        else:
            return self.aircraft

    def __str__(self):
        return str(self.first_name if self.first_name is not None else '') + str(' ' + self.last_name if self.last_name is not None else '')

