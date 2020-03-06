from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from utils import Base
from person import Person


class Student(Person):
    """Represents a student, who studies at a university.
    :param names: List of student's names.
    :param surname: Student's surname.
    :param university: :class:'University' object at which the student is registered.
    :param student_number: A unique identifier of the student within the scope of the system.
    :param terms_completed: Number of academic terms already completed.
    :param username: Name which the student will use to log into the system.
    :param password: Password which the student will use to log into the system.
    """
    __tablename__ = 'student'

    id = Column(Integer, ForeignKey('person.id'), primary_key=True)
    terms_completed = Column(Integer)
    student_number = Column(String(10), nullable=False, index=True)
    university_id = Column(Integer, ForeignKey('university.id'), index=True)

    university = relationship('University', back_populates='students', foreign_keys=[university_id])
    enrollments = relationship('StudentCourse', back_populates='student', cascade='all, delete-orphan')
    unions = relationship('StudentUnion', back_populates='student')
    courses = association_proxy('enrollments', 'course')
    recommendations = relationship('Recommendation', back_populates='student')

    __table_args__ = (UniqueConstraint('student_number', 'university_id'),)

    __mapper_args__ = {
        'polymorphic_identity': 'student'
    }

    def __init__(self, *, names, surname, university, student_number, terms_completed, username, password):
        super().__init__(names=names, surname=surname, username=username, password=password)
        self.university = university
        self.student_number = student_number
        self.terms_completed = terms_completed

    @classmethod
    def from_string(cls, *, name, university, student_number, terms_completed, username, password, separator=' '):
        """An alternative object constructor. Takes all of student's names and
        a surname as a single string, where each name is separated by a
        ''separator''.

        :param name: A single string containing all of student's names, separated by ''separator''.
        :param university: :class:'University' object at which the student is registered.
        :param student_number: A unique identifier of the student within the university.
        :param terms_completed: Number of academic terms already completed.
        :param username: Name which the student will use to log into the system.
        :param password: Password which the student will use to log into the system.
        :param separator: A delimiter between each of the names.
        :return: New student object.
        """
        names = name.split(separator)
        return cls(names=names[:-1], surname=names[-1], university=university, student_number=student_number,
                   terms_completed=terms_completed, username=username, password=password)

    @classmethod
    def extent(cls, session):
        """Retrieves and returns the extent of the :class:'Student', ordered by the ''university_id'' column.

        :param session: SQLAlchemy session object, used to issue queries against the database.
        :return: List of :class:'Student' objects, ordered by their ''university_id'' attributes.
        """
        return session.query(cls).order_by(cls.university_id.asc()).all()

    @property
    def years_completed(self):
        """Attribute returning the number of years the student has completed, based on the
        ''terms_completed'' attribute.
        """
        return int(self.terms_completed / 2)

    def rate_course(self, enrollment, rating, session, commit=True, reload_ratings=True):
        """Allows to set the rating of a course the :class:'Student' object ''self'' is enrolled in. The modification
        is done in-place.

        :param enrollment: :class:'StudentCourse' object representing the enrollment of this student in a course.
        :param rating: The rating of the course to be set.
        :param session: SQLAlchemy :class:'Session' object allowing to issue queries against the database.
        :param commit: If True writes the generated objects to the database.
        :param reload_ratings: Whether to reload the student-course matrix in the :class:'RecommendationSystem' instance
        corresponding to the :class:'University' instance this student studies at, so as to include the new added
        rating. For efficiency reasons, it is best to add multiple ratings in a batch and only then reload the matrix
        by calling :class:'RecommendationSystem'.''reload_ratings'' (default: True).

        """
        assert rating in range(1, 11), 'Rating must be an integer in range [1, 10].'
        assert enrollment.student is self, 'Cannot rate a course this student is not enrolled in.'
        enrollment.course_rating = rating
        if commit:
            session.commit()
        if reload_ratings:
            self.university.recommendation_system.reload_ratings()

    def generate_recommendations(self, session, number_recommendations=3, commit=True):
        """Generates recommendations for this :class:'Student' object.

        :param session: SQLAlchemy :class:'Session' object allowing to issue queries against the database.
        :param number_recommendations: Number fo recommendations to generate.
        :param commit: If True writes the generated objects to the database.
        :return: A tuple of :class:'Recommendation' objects.
        """
        recommendations = self.university. \
            recommendation_system. \
            generate_recommendations(student=self, session=session, number_recommendations=number_recommendations)

        session.add_all(recommendations)
        if commit:
            session.commit()
        return recommendations

    def __str__(self):
        return f"{' '.join([name.name for name in self.names])} {self.surname} ({self.student_number}) " \
               f"Term: {self.terms_completed}"


class StudentCourse(Base):
    """Represents enrolment of a :class:'Student' in a :class:'Course'.
    """
    __tablename__ = 'student_course'

    student_id = Column(Integer, ForeignKey('student.id'), primary_key=True)
    course_id = Column(Integer, ForeignKey('course.id'), primary_key=True)
    course_rating = Column(Integer, nullable=True)
    start_date = Column(Date, primary_key=True)

    student = relationship('Student', back_populates='enrollments')
    course = relationship('Course', back_populates='admissions')

    __tableargs__ = (CheckConstraint('course_rating BETWEEN 1 AND 10'),)

    def __str__(self):
        return f'The enrollment of {self.student.name} in {self.course.name} ({self.course.abbreviation}); ' \
               f'start date={self.start_date}; course rating={self.course_rating}'
