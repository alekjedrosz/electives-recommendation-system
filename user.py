from sqlalchemy import Column, Integer, String, Index

from utils import Base


class User(Base):
    """Class representing a user of the system.

    :param username: Name which the user will use to log into the system.
    :param password: Password which the user will use to log into the system.
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String(20))
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def __init__(self, *, username, password):
        super().__init__()
        self.username = username
        self.password = password

    @classmethod
    def verify_credentials(cls, username, password, session):
        """Verifies the passed in credentials against the user database. Returns the instance of one of :class:'User''s
        subclasses these credentials belong to, or ''None'' if no such credentials exist.

        :param username: A string identification used to log in to the system.
        :param password: A secret string identification used to log in to the system.
        :param session: SQLAlchemy :class:'Session' object allowing to issue queries against the database.
        :return: Instance of the subclass the ''username'' belongs to or ''None'' if such a ''username'' - ''password''
        combination does not exist in the database.
        """
        users = session.query(cls).filter(User.username == username, User.password == password).all()
        assert len(users) <= 1, 'More than one user with such credentials in the database.'
        try:
            return users[0]
        except IndexError:
            return None
