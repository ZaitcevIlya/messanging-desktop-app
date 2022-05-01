import datetime
from pprint import pprint

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class ServerStorage:
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'user'

        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)
        last_login = Column(DateTime)
        password_hash = Column(String)
        pub_key = Column(Text)

        def __init__(self, username, password_hash):
            self.username = username
            self.password_hash = password_hash
            self.pub_key = None
            self.last_login = datetime.datetime.now()

    class LoginHistory(Base):
        __tablename__ = 'login_history'

        id = Column(Integer, primary_key=True)
        user = Column(Integer, ForeignKey('user.id'))
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
        user = Column(Integer, ForeignKey('user.id'))
        ip = Column(String)
        port = Column(Integer)
        last_login = Column(DateTime)

        def __init__(self, user, ip, port, last_login):
            self.user = user
            self.ip = ip
            self.port = port
            self.last_login = last_login

    class UsersContacts(Base):
        __tablename__ = 'users_contacts'

        id = Column(Integer, primary_key=True)
        user = Column(Integer, ForeignKey('user.id'))
        contact = Column(String, ForeignKey('user.id'))

        def __init__(self, user, contact):
            self.user = user
            self.contact = contact

    class UserHistory(Base):
        __tablename__ = 'user_history'

        id = Column(Integer, primary_key=True)
        user = Column(Integer, ForeignKey('user.id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user):
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def user_login(self, username, ip, port, key):
        """Calls during user login, log to db information about it"""
        users = self.session.query(self.User).filter_by(username=username)
        if users.count():
            user = users.first()
            user.last_login = datetime.datetime.now()
            if user.pub_key != key:
                user.pub_key = key
        else:
            raise ValueError('User does not exists')

        new_active_user = self.ActiveUser(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, ip, port, datetime.datetime.now())
        self.session.add(history)

        self.session.commit()

    def add_user(self, username, password_hash):
        """Create a new user to DB"""
        user_row = self.User(username, password_hash)
        self.session.add(user_row)
        self.session.commit()

        history_row = self.UserHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, username):
        """Remove user from DB"""
        user = self.session.query(self.User).filter_by(username=username).first()
        self.session.query(self.ActiveUser).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.UserHistory).filter_by(user=user.id).delete()
        self.session.query(self.User).filter_by(username=username).delete()
        self.session.commit()

    def get_hash(self, username):
        """Get user pass hash."""
        user = self.session.query(self.User).filter_by(username=username).first()
        return user.password_hash

    def get_pubkey(self, username):
        """Get user public key."""
        user = self.session.query(self.User).filter_by(username=username).first()
        return user.pub_key

    def check_user(self, username):
        """Check if user exists."""
        if self.session.query(self.User).filter_by(username=username).count():
            return True
        else:
            return False

    def user_logout(self, username):
        """Log user logout to DB"""
        user = self.session.query(self.User).filter_by(username=username).first()
        self.session.query(self.ActiveUser).filter_by(user=user.id).delete()
        self.session.commit()

    # Process users messages and log it to DB
    def process_message(self, sender, recipient):
        sender = self.session.query(self.User).filter_by(username=sender).first().id
        recipient = self.session.query(self.User).filter_by(username=recipient).first().id

        sender_row = self.session.query(self.UserHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UserHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.User).filter_by(username=user).first()
        contact = self.session.query(self.User).filter_by(username=contact).first()

        if not contact or self.session.query(self.UsersContacts).\
                filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        user = self.session.query(self.User).filter_by(username=user).first()
        contact = self.session.query(self.User).filter_by(username=contact).first()

        if not contact:
            return

        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
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

    def get_contacts(self, username):
        user = self.session.query(self.User).filter_by(username=username).one()

        query = self.session.query(self.UsersContacts, self.User.username).\
            filter_by(user=user.id).\
            join(self.User, self.UsersContacts.contact == self.User.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.User.username,
            self.User.last_login,
            self.UserHistory.sent,
            self.UserHistory.accepted
        ).join(self.User)
        return query.all()


if __name__ == '__main__':
    test_db = ServerStorage('server_base.db3')
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    pprint(test_db.users_list())
    pprint(test_db.active_users_list())
    test_db.user_logout('McG2')
    pprint(test_db.login_history('re'))
    test_db.add_contact('test2', 'test1')
    test_db.add_contact('test1', 'test3')
    test_db.add_contact('test1', 'test6')
    test_db.remove_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    pprint(test_db.message_history())
