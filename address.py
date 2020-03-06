from sqlalchemy import Column, Integer, String
from utils import Base


class Address(Base):
    """Represents a postal address.

    :param country: String representing a country.
    :param city: String representing a city.
    :param address_line: String representing the street name, street number, house number or similar.
    :param postal_code: Postal/zip code passed in as a string.
    """
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True)
    country = Column(String(100))
    city = Column(String(100))
    address_line = Column(String(500))
    postal_code = Column(String(20))

    def __init__(self, *, country, city, address_line, postal_code):
        self.country = country
        self.city = city
        self.address_line = address_line
        self.postal_code = postal_code

    def __str__(self):
        return f'{self.address_line}, {self.postal_code}, {self.city}, {self.country}'
