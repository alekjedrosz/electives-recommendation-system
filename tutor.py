import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from person import Person
from utils import Base


class DegreeCategory(enum.Enum):
    """Represents the possible types of higher education degrees, used as the ''degree_category''
    attribute of :class:'Tutor'.
    """
    ASSOCIATE = 'Associate'
    BACHELOR = 'Bachelor'
    MASTER = 'Master'
    DOCTORATE = 'Doctor'

    def __str__(self):
        return self.value


class Tutor(Person):
    """Represents a tutor at a higher education institution.

    :param names: List of tutor's names.
    :param surname: Tutor's surname.
    :param degree_category: Category of a degree obtained by the tutor, one of :class:'DegreeCategory'
    enumeration values.
    :param degree_extension: The subsequent part of a degree obtained by the tutor.
    :param degree_abbreviation: Abbreviation of the full name of the degree.
    :param username: Name the tutor will use to log into the system.
    :param password: Password the tutor will use to log into the system.
    """
    __tablename__ = 'tutor'

    id = Column(Integer, ForeignKey('person.id'), primary_key=True)
    degree_category = Column(Enum(DegreeCategory))
    degree_extension = Column(String(50))
    degree_abbreviation = Column(String(6))

    employments = relationship('TutorUniversity', back_populates='tutor')
    universities = association_proxy('employments', 'university')

    __mapper_args__ = {
        'polymorphic_identity': 'tutor'
    }

    def __init__(self, *, names, surname, degree_category, degree_extension, degree_abbreviation, username, password):
        super().__init__(username=username, password=password, names=names, surname=surname)
        self.degree_category = degree_category
        self.degree_extension = degree_extension
        self.degree_abbreviation = degree_abbreviation

    @classmethod
    def from_string(cls, *, name, degree_category, degree_extension, degree_abbreviation,
                    username, password, separator=' '):
        """An alternative object constructor. Takes all of tutor's names and
        a surname as a single string, where each name is separated by a
        ''separator''.

        :param name: A single string containing all of tutor's names, separated by ''separator''.
        :param degree_category: Category of a degree obtained by the tutor, one of :class:'DegreeCategory'
        enumeration values.
        :param degree_extension: The subsequent part of a degree obtained by the tutor.
        :param degree_abbreviation: Abbreviation of the full name of the degree.
        :param username: Name the tutor will use to log into the system.
        :param password: Password the tutor will use to log into the system.
        :param separator: A delimiter between each of the names.
        """
        names = name.split(separator)
        instance = cls(names=names[:-1], surname=names[-1], degree_category=degree_category,
                       degree_extension=degree_extension, degree_abbreviation=degree_abbreviation,
                       username=username, password=password)
        return instance

    def __str__(self):
        return f"{' '.join([name.name for name in self.names])} {self.surname}, {self.degree_category} " \
               f"{self.degree_extension} ({self.degree_abbreviation})"


class TutorUniversity(Base):
    """Represents a period of employment of a :class:'Tutor' at a :class:'University'.
    """
    __tablename__ = 'tutor_university'

    tutor_id = Column(Integer, ForeignKey('tutor.id'), primary_key=True)
    university_id = Column(Integer, ForeignKey('university.id'), primary_key=True)
    remuneration = Column(Float(2))
    start_date = Column(Date, primary_key=True)
    end_date = Column(Date, primary_key=True)

    tutor = relationship('Tutor', back_populates='employments')
    university = relationship('University', back_populates='hires')

    def __str__(self):
        return f'The employment of {self.tutor} at {self.university}; remuneration={self.remuneration};' \
               f' start date={self.start_date}; end date={self.end_date}'