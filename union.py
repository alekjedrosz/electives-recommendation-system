from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date

from utils import Base


class ScienceUnion(Base):
    """Represents a union which :class:'Student's may be members of.

    :param name: Name of the union.
    :param date_of_establishment: Date of founding of the union.
    """
    __tablename__ = 'union'

    id = Column(Integer, primary_key=True)
    name = Column(String(300))
    date_of_establishment = Column(Date)

    students = relationship('StudentUnion', back_populates='union')

    def __init__(self, *, name, date_of_establishment=date.today()):
        super().__init__()
        self.name = name
        self.date_of_establishment = date_of_establishment

    def __str__(self):
        return f'{self.name} (founded {self.date_of_establishment})'


class StudentUnion(Base):
    """Represents the membership of a :class:'Student' in a :class:'ScienceUnion'.
    """
    __tablename__ = 'student_union'

    student_id = Column(Integer, ForeignKey('student.id'), primary_key=True)
    course_id = Column(Integer, ForeignKey('union.id'), primary_key=True)
    start_date = Column(Date)

    student = relationship('Student', back_populates='unions')
    union = relationship('ScienceUnion', back_populates='students')

    def __str__(self):
        return f'The membership of {self.student.name} in {self.union.name}; join date={self.start_date}'
