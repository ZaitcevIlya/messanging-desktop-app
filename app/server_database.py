import datetime
from pprint import pprint

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class ServerStorage:
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'user'

        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)
        last_login = Column(DateTime)

        def __init__(self, username):
            self.username = username
            self.last_login = datetime.datetime.now()

    class LoginHistory(Base):
        __tablename__ = 'login_history'

        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('user.id'))
        ip = Column(String)
        port = Column(Integer)
        last_login = Column(DateTime)

        def __init__(self, user, ip, port, last_login):
            self.user = user
            self.ip = ip
            self.port = port
            self.last_login = last_login

    class ActiveUser(Base):
        __tablename__ = 'active_user'

        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('user.id'))
        ip = Column(String)
        port = Column(Integer)
        last_login = Column(DateTime)

        def __init__(self, user, ip, port, last_login):
            self.user = user
            self.ip = ip
            self.port = port
            self.last_login = last_login

    def __init__(self):
        self.engine = create_engine('sqlite:///server_base.db3', echo=False, pool_recycle=7200)

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        """Calls during user login, log to db information about it"""
        users = self.session.query(self.User).filter_by(username=username)
        if users.count():
            user = users.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.User(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUser(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, ip, port, datetime.datetime.now())
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        """Log user logout to DB"""
        user = self.session.query(self.User).filter_by(username=username).first()
        self.session.query(self.ActiveUser).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        """Returns all users which are ever were logged in"""
        query = self.session.query(self.User.username, self.User.last_login)
        return query.all()

    def active_users_list(self):
        """Returns active users list"""
        query = self.session.query(
            self.User.username,
            self.ActiveUser.ip,
            self.ActiveUser.port,
            self.ActiveUser.last_login
        ).join(self.User)
        return query.all()

    def login_history(self, username=None):
        """Returns login history by user or all users"""
        query = self.session.query(
            self.User.username,
            self.LoginHistory.ip,
            self.LoginHistory.port,
            self.LoginHistory.last_login
        ).join(self.User)
        
        if username:
            query.filter(self.User.username == username)
        return query.all()


if __name__ == '__main__':
    db = ServerStorage()
    db.user_login('client_1', '192.168.1.4', 8888)
    db.user_login('client_2', '192.168.1.5', 7777)
    pprint(db.active_users_list())
    db.user_logout('client_1')
    pprint(db.users_list())
    pprint(db.active_users_list())
    db.user_logout('client_2')
    pprint(db.users_list())
    pprint(db.active_users_list())
