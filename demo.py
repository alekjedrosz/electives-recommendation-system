from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, with_polymorphic
from datetime import date
import os

from user import User
from person import Person
from address import Address
from union import StudentUnion
from recommender import Ratings
from student import Student, StudentCourse
from tutor import Tutor, DegreeCategory
from university import UniversityType, University
from utils import Base

# Create a data directory
if not os.path.exists('./data'):
    os.makedirs('./data')

# Define the databse engine
engine = create_engine('sqlite:///data/test.db')

# Generate all database tables
Base.metadata.create_all(engine)

# Start a new session
Session = sessionmaker(bind=engine)
session = Session()

# Create an address
address_1 = Address(country='United Kingdom', city='London', address_line='Houghton Street', postal_code='WC2A 2AE')

# And a university
university_1 = University(name='London School of Economics', category=UniversityType.PUBLIC,
                          abbreviation='LSE', address=address_1, username='uni1', password='pw')

session.add_all([address_1, university_1])

# Add a few students
student_1 = university_1.register_student(name='Name Surname', student_number='nr1', terms_completed=2,
                                          username='st1', password='pw')
student_2 = university_1.register_student(name='Name1 Name2 Surname ', student_number='nr2', terms_completed=7,
                                          username='st2', password='pw')

session.add_all([student_1, student_2])

# Add a few courses
course_1 = university_1.add_course(name='Statistics 1', course_number='ST104a', semester_of_availability=1)
course_2 = university_1.add_course(name='Statistics 2', course_number='ST104b', semester_of_availability=2)
course_3 = university_1.add_course(name='Calculus', course_number='MT1174', semester_of_availability=2)
course_4 = university_1.add_course(name='Linear Algebra', course_number='MT1173', semester_of_availability=5)

session.add_all([course_1, course_2, course_3, course_4])

# Enroll sample students in some courses
enrollment_1 = course_1.add_student(student=student_1, start_date=date(2020, 2, 13))
enrollment_2 = course_3.add_student(student=student_1, start_date=date(2020, 2, 13))
enrollment_3 = course_4.add_student(student=student_2, start_date=date(2020, 2, 13))

# Rate some of the courses
student_1.rate_course(enrollment_1, 9, session)
student_1.rate_course(enrollment_2, 8, session)
student_2.rate_course(enrollment_3, 8, session)

session.add_all([enrollment_1, enrollment_2, enrollment_3])

# Commit these changes
session.commit()

# Train the recommendation model
university_1.recommendation_system.train_model()

# Generate recommendations for each student
recommendations_1 = student_1.generate_recommendations(session)
recommendations_2 = student_2.generate_recommendations(session)

# Rate some recommendations
recommendations_1[0].add_rating(Ratings.HELPFUL, session)
recommendations_2[0].add_rating(Ratings.NOT_HELPFUL, session)