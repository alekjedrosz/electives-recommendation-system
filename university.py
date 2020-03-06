from sqlalchemy import UniqueConstraint, Index
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

import enum
from datetime import date

from user import User
from student import Student, StudentCourse
from tutor import TutorUniversity
from recommender import RecommendationSystem
from utils import Base, MSE


class UniversityType(enum.Enum):
    """Represents the possible types of universities, used as a the ''category''
    attribute of the :class:'University'.
    """
    PRIVATE = 'private'
    PUBLIC = 'public'
    COMMUNITY = 'community college'
    LIBERAL_ARTS = 'liberal arts'

    def __str__(self):
        return self.value


class University(User):
    """Represents a higher education institution.

    :param name: Name of the university.
    :param category: Type of the university, one of the :class:'UniversityType'
    enumeration values.
    :param abbreviation: Short form of the ''name'' of the university.
    :param username: Name which the university will use to log into the system.
    :param password: Password which the university will use to log into the system.
    :param address: Postal address given as a :class:'Address' object.
    """
    __tablename__ = 'university'

    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    name = Column(String(100))
    abbreviation = Column(String(6))
    category = Column(Enum(UniversityType))
    address_id = Column(Integer, ForeignKey('address.id'))

    recommendation_system = relationship('RecommendationSystem', uselist=False, back_populates='university')
    address = relationship('Address')
    students = relationship('Student', back_populates='university', foreign_keys='Student.university_id',
                            order_by='Student.student_number')
    hires = relationship('TutorUniversity', back_populates='university')
    tutors = association_proxy('hires', 'tutor')
    courses = relationship('Course', back_populates='university')

    __table_args__ = (Index('index_university', id.asc()), )
    __mapper_args__ = {
        'polymorphic_identity': 'university'
    }

    def __init__(self, *, name, abbreviation, category, address, username, password,
                 initialize_recommendation_system=True):
        super().__init__(username=username, password=password)
        self.name = name
        self.abbreviation = abbreviation
        self.category = category
        self.address = address
        if initialize_recommendation_system:
            self.initialize_recommendation_system()

    def find_student(self, student_number, session):
        """Finds and returns the instance of :class:'Student' corresponding to the ''student_number''

        :param student_number: Number of the student to find (unique within the scope of the university).
        :param session: SQLAlchemy :class:'Session' object allowing to issue queries against the database.
        :return: An object of the :class:'Student' corresponding to the passed in ''student_number'' or ''None''
        if no student with such a ''student_number'' exists.
        """
        student = session.query(Student).filter(Student.student_number == student_number,
                                                Student.university_id == self.id)

        try:
            return student[0]
        except IndexError:
            return None

    def find_course(self, course_number, session):
        """Finds and returns the instance of :class:'Course' corresponding to the ''course_number''

        :param course_number: Number of the course to find (unique within the scope of the university).
        :param session: SQLAlchemy :class:'Session' object allowing to issue queries against the database.
        :return: An object of the :class:'Course' corresponding to the passed in ''course_number'' or ''None''
        if no course with such a ''course_number'' exists.
        """
        course = session.query(Course).filter(Course.course_number == course_number,
                                              Course.university_id == self.id)
        try:
            return course[0]
        except IndexError:
            return None

    def register_student(self, *, name, student_number, terms_completed, username, password, separator=' '):
        """Creates and registers a new student (who has not been previously registered by any university).

        :param name: String representing the names and the surname of the student.
        :param student_number: A unique identifier of the student within the university.
        :param terms_completed: Number of academic terms completed (might vary from 0 due to accreditation of previous
        work).
        :param username: Name which the student will use to log into the system.
        :param password: Password which the student will use to log into the system.
        :param separator: A delimiter between each of the names.
        :return: New student object.
        """
        student = Student.from_string(name=name, university=self, student_number=student_number,
                                      terms_completed=terms_completed, username=username,
                                      password=password, separator=separator)
        return student

    def delete_student(self, student, session, commit=True):
        """Deletes the :class:'Student' object from this university, hence removing it from the system entirely. All
        associated :class:'StudentCourse' objects are also deleted.

        :param student: :class:'Student' object to remove.
        :param session: SQLAlchemy session allowing to issue queries against the database.
        :param commit: If True writes the changes to the database.
        """
        assert student.university is self, 'Cannot delete a student who does not study at this university'
        session.delete(student)
        if commit:
            session.commit()

    def delete_course(self, course, session, commit=True):
        """Deletes the :class:'Course' object from this university, hence removing it from the system entirely.

        :param course: :class:'Student' object to remove.
        :param session: SQLAlchemy session allowing to issue queries against the database.
        :param commit: If True writes the changes to the database.
        """
        assert course.university is self, 'Cannot delete a course which is not offered at this university'
        session.delete(course)
        if commit:
            session.commit()

    def add_tutor(self, *, tutor, remuneration, end_date, start_date=date.today()):
        """Hires a tutor at the calling :class:'University' object.

        :param tutor: :class:'Tutor' object representing the tutor to hire.
        :param remuneration: Monthly pay for the period of employment.
        :param end_date: End date of the period of employment.
        :param start_date: Start date of the period of employment (default=today).
        """
        employment = TutorUniversity(remuneration=remuneration, start_date=start_date, end_date=end_date)
        employment.university = self
        employment.tutor = tutor
        return employment

    def terminate_employment(self, employment, session, commit=True):
        """Removes the :class:'Employment' object from the system, therefore terminating the contract between the
        :class:'Tutor' object associated with this employment and this university. Does not remove the :class:'Tutor'
        object from the system entirely.

        :param employment: :class:'Employment' object to terminate.
        :param session: SQLAlchemy session allowing to issue queries against the database.
        :param commit: If True writes the changes to the database.
        """
        assert employment.university is self, 'Cannot delete a tutor which does not teach at this university'
        session.delete(employment)
        if commit:
            session.commit()

    def add_course(self, *, name, course_number, semester_of_availability,
                   abbreviation=None, description=None, is_elective=True):
        """Adds a course offered at the calling :class:''University'' object.

        :param name: Name of the course.
        :param course_number: An identifier of the course, unique within the scope of the university.
        :param abbreviation: Abbreviation of the name of the course. If ''None'' set to the same
         value as ''course_number''.
        :param semester_of_availability: Semester during which this course is available.
        :param description: Description of the course.
        :param is_elective: Whether the course is elective or compulsory.
        :return: :class:'Course' object representing the course.
        """
        if abbreviation is None:
            abbreviation = course_number
        return Course(university=self, name=name, course_number=course_number, abbreviation=abbreviation,
                      semester_of_availability=semester_of_availability,
                      description=description, is_elective=is_elective)

    def initialize_recommendation_system(self, loss_function=MSE,
                                         student_course_matrix_path=None, model_parameters_path=None):
        """Initializes the :class:'RecommendationSystem'.

        :param loss_function: A mathematical function for calculating the cost / loss on training examples
        (Default = MSE).
        :param student_course_matrix_path: A path to a .csv file containing the ratings of courses (:class:'Course')
        added by students (:class:'Student'). If ''None'' is passed, a default value will be set.
        :param model_parameters_path: A path to a .bin file containing the parameters of the model. If ''None'' is
        passed, a default value will be set.
        """
        RecommendationSystem(university=self, loss_function=loss_function,
                             student_course_matrix_path=student_course_matrix_path,
                             model_parameters_path=model_parameters_path)

    def __str__(self):
        return f'{self.name}{f" ({self.abbreviation})" if self.abbreviation is not None else ""}'


class Course(Base):
    """Represents a course offered at a university.

    :param university: :class:'University' object representing the university the course is offered at.
    :param name: Name of the course.
    :param course_number: An identifier of the course, unique within the scope of the university.
    :param abbreviation: Abbreviation of the name of the course. If ''None'' set to the same value as ''course_number''.
    :param semester_of_availability: Semester during which this course is available.
    :param description: Description of the course (default ''None'').
    :param is_elective: Whether the course is elective or compulsory (default ''False'').
    """
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    name = Column(String(300))
    course_number = Column(String(10), nullable=False)
    abbreviation = Column(String(20))
    semester_of_availability = Column(Integer)
    description = Column(String(1000), nullable=True)
    is_elective = Column(Boolean, default=False)
    university_id = Column(Integer, ForeignKey('university.id'))

    university = relationship('University', back_populates='courses', foreign_keys=[university_id])
    admissions = relationship('StudentCourse', back_populates='course', cascade='all, delete-orphan')
    students = association_proxy('admissions', 'student')

    __table_args__ = (UniqueConstraint('course_number', 'university_id'),)

    def __init__(self, *, university, name, course_number, semester_of_availability, abbreviation=None,
                 description=None, is_elective=True):
        self.university = university
        self.name = name
        self.course_number = course_number
        if abbreviation is None:
            self.abbreviation = course_number
        else:
            self.abbreviation = abbreviation
        self.semester_of_availability = semester_of_availability
        self.description = description
        self.is_elective = is_elective

    def add_student(self, student, start_date):
        """Enrols a student in the calling :class:'Course' object.

        :param student: :class:'Student' object to enrol in the calling :class:'Course' object.
        :param start_date: Starting date of the course.
        :returns: An instance of :class:'StudentCourse' representing the student's enrollment in the course.
        """
        assert student.university is self.university, \
            f'Cannot enrol a student who studies at university \"{student.university}\"' \
            f' in a course offered at \"{self.university}\".'

        enrolment = StudentCourse(start_date=start_date)
        enrolment.student = student
        enrolment.course = self
        return enrolment

    def __str__(self):
        return f'{self.name} ({self.abbreviation})'

