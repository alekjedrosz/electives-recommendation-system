from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from utils import Base
from user import User


class Person(User):
    """Class representing a person-user of the system.

    :param names: List of the person's first names.
    :param surname: The person's surname.
    :param username: Name which the person will use to log into the system.
    :param password: Password which the person will use to log into the system.
    """
    __tablename__ = 'person'

    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    surname = Column(String(200))

    names = relationship('Name', back_populates='person')

    __mapper_args__ = {
        'polymorphic_identity': 'person'
    }

    @property
    def name(self):
        return f"{' '.join([name.name for name in self.names])} {self.surname}"

    def __init__(self, *, username, password, names, surname):
        super().__init__(username=username, password=password)
        self.surname = surname
        self.names = [Name(name=name) for name in names]


class Name(Base):
    """Class representing a name of a person. Necessary to represent the ''names'' of a :class:'Person'
    object as rows in a separate table.

    :param name: A string representing the name of the :class:'Person'.
    """
    __tablename__ = 'name'

    id = Column(Integer, primary_key=True)
    name = Column(String(150))
    person_id = Column(Integer, ForeignKey('person.id'))

    person = relationship('Person', back_populates='names')

    def __init__(self, *, name):
        super().__init__()
        self.name = name
