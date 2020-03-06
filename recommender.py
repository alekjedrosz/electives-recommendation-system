from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, PickleType, Enum, Boolean
from sqlalchemy.orm import relationship

import numpy as np
import pandas as pd
from datetime import date
import enum

from utils import Base, MSE


class RecommendationSystem(Base):
    """Represents the recommendation engine used to make recommendations within the scope of a university.

    :param loss_function: A mathematical function for calculating the cost / loss on training examples (Default = MSE).
    :param student_course_matrix_path: A path to a .csv file containing the ratings of courses (:class:'Course') added
    by students (:class:'Student'). The shape of the resulting matrix is |students| x |courses|. If ''None'' is passed,
    a default value will be set.
    :param model_parameters_path: A path to a .npz file containing the parameters of the model. If ''None'' is passed,
    a default value will be set.
    :param university: The :class:'University' object this recommendation system belongs to.
    """
    __tablename__ = 'recommendation_system'

    id = Column(Integer, primary_key=True)
    loss_function = Column(PickleType)
    student_course_matrix_path = Column(String)
    known_ratings_matrix_path = Column(String)
    model_parameters_path_Q = Column(String)
    model_parameters_path_P = Column(String)
    trained = Column(Boolean)
    university_id = Column(Integer, ForeignKey('university.id'))

    university = relationship('University', back_populates='recommendation_system', foreign_keys=[university_id])

    def __init__(self, *, university, loss_function=MSE, student_course_matrix_path=None,
                 known_ratings_matrix_path=None, model_parameters_path=None):
        super().__init__()
        self.loss_function = loss_function

        if student_course_matrix_path is None:
            self.student_course_matrix_path = f'data/{university.username}_student_course.csv'  # Default value
        else:
            self.student_course_matrix_path = student_course_matrix_path

        if known_ratings_matrix_path is None:
            self.known_ratings_matrix_path = f'data/{university.username}_known_ratings.csv'  # Default value
        else:
            self.known_ratings_matrix_path = known_ratings_matrix_path

        if model_parameters_path is None:
            self.model_parameters_path_Q = f'data/{university.username}_model_parameters_Q.npz'  # Default value
            self.model_parameters_path_P = f'data/{university.username}_model_parameters_P.npz'  # Default value
        else:
            self.model_parameters_path_Q = f'Q_{model_parameters_path}'
            self.model_parameters_path_P = f'P_{model_parameters_path}'

        self.university = university
        self.trained = False
        # Create an empty matrix and save it to a file (recommendation system is created with a university
        # automatically - no ratings to reload yet).
        empty_matrix = pd.DataFrame()
        empty_matrix.to_csv(self.student_course_matrix_path, index=False)
        empty_matrix.to_csv(self.known_ratings_matrix_path, index=False)

    @property
    def student_course_matrix(self):
        try:
            return pd.read_csv(self.student_course_matrix_path, index_col='student_number')\
                .rename_axis('course_number', axis=1)
        except pd.errors.EmptyDataError:
            return None

    @property
    def known_ratings_matrix(self):
        try:
            return pd.read_csv(self.known_ratings_matrix_path, header=None)
        except pd.errors.EmptyDataError:
            return None

    @property
    def parameters(self):
        try:
            Q = pd.read_csv(self.model_parameters_path_Q, index_col='course_number')
            P = pd.read_csv(self.model_parameters_path_P, index_col='student_number')
            return Q, P
        except pd.errors.EmptyDataError:
            return None

    def reload_ratings(self):
        """Retrieves all enrollments in courses offered at the university this recommendation system belongs to,
        converts them to pandas :class:'DataFrame' objects and saves them to .csv files. The matrices can be read
        using the instance attributes ''student_course_matrix'' and ''known_ratings_matrix''.
        """
        # Retrieve all enrollments
        admissions = []
        for course in self.university.courses:
            for admission in course.admissions:
                admissions.append([admission.student.student_number, admission.course.course_number,
                                   admission.course_rating])

        # Extract a ''student_course_matrix'' and a ''known_ratings_matrix'', then save them to appropriate files
        long_df = pd.DataFrame(admissions, columns=['student_number', 'course_number', 'rating'])
        student_course_matrix = long_df.pivot(index='student_number', columns='course_number', values='rating')
        known_ratings_matrix = long_df.dropna()

        student_course_matrix.to_csv(self.student_course_matrix_path, index=True)
        known_ratings_matrix.to_csv(self.known_ratings_matrix_path, index=False, header=False)

    def train_model(self, *, regularization_parameter=0.1, epochs=40, learning_rate=0.015,
                    number_factors=20, thread_errors=None):
        """Trains the model using stochastic gradient descent, by minimizing the L2 regularized sum of squares error
         of known ratings reconstruction. The ratings are reconstructed by ratings matrix factorization into 2 parameter
         matrices.

        :param regularization_parameter: L2 regularization coefficient.
        :param epochs: Number of epochs (iterations) to run SGD for.
        :param learning_rate: SGD learning rate parameter.
        :param number_factors: The number of factors used for ratings matrix factorization (i.e. one of the sizes of the
        factoring matrices).
        :param thread_errors: Saves the errors on each epoch to this mutable parameter. Use only with threading.
        :return: The errors on each learning epoch.
        """
        student_course_matrix = self.student_course_matrix
        number_students, number_courses = student_course_matrix.shape
        student_numbers = student_course_matrix.index
        course_numbers = student_course_matrix.columns

        # Initialize the decomposition matrices to random values in [ 0, sqrt(10/nr_factors) ), and save them as
        # :class:'DataFrame's indexed by student numbers or course numbers (depending on which matrix)
        init_high = np.sqrt(10 / number_factors)
        Q = pd.DataFrame(np.random.uniform(low=0.0, high=init_high, size=(number_courses, number_factors)),
                         index=course_numbers)
        P = pd.DataFrame(np.random.uniform(low=0.0, high=init_high, size=(number_students, number_factors)),
                         index=student_numbers)

        errors = []  # Errors on each iteration

        # -- Training on the known ratings --
        with open(self.known_ratings_matrix_path) as f:
            for epoch in range(epochs):
                # -- Compute and apply SGD updates for each training example --
                for line in f:
                    student_number, course_number, rating = tuple(s for s in line.split(','))
                    rating = float(rating)

                    # Retrieve rows corresponding to the current student-course pair
                    q = Q.loc[course_number]
                    p = P.loc[student_number]

                    # Compute a common error term
                    epsilon = 2 * (rating - np.dot(q, p))

                    # Compute SGD updates
                    q_update = learning_rate * ((epsilon * p) - (2 * regularization_parameter * q))
                    p_update = learning_rate * ((epsilon * q) - (2 * regularization_parameter * p))

                    # Apply SGD updates
                    q = q + q_update
                    p = p + p_update

                    # Update the appropriate rows in decomposition matrices
                    Q.loc[course_number] = q
                    P.loc[student_number] = p

                # -- Compute the training set error on the current iteration --
                E = 0
                # Move file iterator to the first line
                f.seek(0)
                for line in f:
                    student_number, course_number, rating = tuple(s for s in line.split(','))
                    rating = float(rating)

                    # Retrieve rows corresponding to the current student-course pair
                    q = Q.loc[course_number]
                    p = P.loc[student_number]

                    # Compare the predicted rating to the known one, and add this to the error term
                    E += (rating - np.dot(q, p)) ** 2

                # Add the regularization terms
                E += regularization_parameter * sum(Q.apply(lambda row: sum([term ** 2 for term in row])))
                E += regularization_parameter * sum(P.apply(lambda row: sum([term ** 2 for term in row])))
                # Save error on the current iteration
                errors.append(E)
                # Move the file iterator to the first line (before the next epoch)
                f.seek(0)

        # Save the parameters
        Q.to_csv(self.model_parameters_path_Q, index=True)
        P.to_csv(self.model_parameters_path_P, index=True)

        # Set to trained mode to enable generating recommendations
        self.trained = True

        # Save the values in the thread in case of parallel execution
        if thread_errors is not None:
            thread_errors.extend(errors)

        return errors

    def generate_recommendations(self, student, session, number_recommendations=3):
        """Generates recommendations based on the course ratings added by a ''student''.

        :param student: :class:'Student' object for which to generate the recommendations.
        :param session: SQLAlchemy :class:'Session' object allowing to issue queries against the database.
        :param number_recommendations: The maximum number of recommendations to generate. If the number of
        :class:'Course' objects associated with  this system's :class:'University' object is less than the ''number''
        parameter, a recommendation for each course available at this university will be returned.
        :return: A tuple of :class:'Recommendation' objects
        """
        assert number_recommendations in range(1, 4), 'The number of generated recommendations must be within [1, 3]'
        assert self.trained, 'Please train the model at least once before generating a recommendation'

        student_course_matrix = self.student_course_matrix
        courses = student_course_matrix.columns
        enrolled_in_courses = [enrollment.course.course_number for enrollment in student.enrollments]
        not_enrolled_in_courses = [course_number for course_number in courses
                                   if course_number not in enrolled_in_courses]

        # Cap the requested number of recommendations by the number of courses the student is not enrolled in
        number_recommendations = min(number_recommendations, len(not_enrolled_in_courses))

        Q, P = self.parameters
        predicted_ratings = Q @ P.loc[student.student_number].T
        predicted_ratings = predicted_ratings.loc[not_enrolled_in_courses].sort_values(ascending=False)\
            .head(number_recommendations)

        recommendations = [Recommendation(student=student, course=self.university.find_course(course_number, session),
                                          correctness_probability=rating/20)
                           for course_number, rating in predicted_ratings.items()]

        return recommendations


class Recommendation(Base):
    """Represents a recommendation generated by the :class:'RecommendationSystem'.

    :param student: :class:'Student' who adds this recommendation.
    :param course: :class:'Course' object which is recommended.
    :param correctness_probability: Probability of correctness of the recommendation (value in [0, 1]).
    """
    __tablename__ = 'recommendation'

    id = Column(Integer, primary_key=True)
    correctness_probability = Column(Float(2))
    date_generated = Column(Date)
    course_id = Column(Integer, ForeignKey('course.id'))
    student_id = Column(Integer, ForeignKey('student.id'))

    student = relationship('Student', back_populates='recommendations', foreign_keys=[student_id])
    course = relationship('Course', foreign_keys=[course_id])
    rating = relationship('RecommendationRating', uselist=False, back_populates='recommendation')

    def __init__(self, *, student, course, correctness_probability=0.5, date_generated=date.today()):
        super().__init__()
        self.student = student
        self.course = course
        self.correctness_probability = correctness_probability
        self.date_generated = date_generated

    def add_rating(self, rating_value, session, commit=True):
        """Rate this recommendation.

        :param rating_value: One of :class:'Ratings' values.
        :param session: SQLAlchemy session object allowing to issue queries against the database.
        :param commit: If True writes the generated objects to the database.
        """
        assert type(rating_value) is Ratings, 'Please use a valid rating'
        self.rating = RecommendationRating(recommendation=self, rating=rating_value)

        session.add(self.rating)
        if commit:
            session.commit()

    def __str__(self):
        return f'{self.course.course_number}, P={self.correctness_probability}, ' \
               f'Rating={self.rating.rating if self.rating is not None else "None"}, Date={self.date_generated}'


class Ratings(enum.Enum):
    """Represents the possible ratings which can be added as a :class:'RecommendationRating'.
    """
    HELPFUL = 'helpful'
    NOT_HELPFUL = 'not helpful'

    def __str__(self):
        return self.value


class RecommendationRating(Base):
    """Represents the rating of a :class:'Recommendation' instance.

    :param recommendation: :class:'Recommendation' instance which the rating pertains to.
    :param rating: The rating of the :class:'Recommendation' instance.
    """
    __tablename__ = 'recommendation_rating'

    id = Column(Integer, primary_key=True)
    rating = Column(Enum(Ratings))
    date_added = Column(Date)
    recommendation_id = Column(Integer, ForeignKey('recommendation.id'))

    recommendation = relationship('Recommendation', back_populates='rating', foreign_keys=[recommendation_id])

    def __init__(self, recommendation, rating):
        super().__init__()
        self.recommendation = recommendation
        self.rating = rating
        self.date_added = date.today()

