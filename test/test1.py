# -*- coding: utf-8 -*-
### slide:: s
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, Column, Integer, String, Sequence, MetaData, DateTime, func,
                        ForeignKey, Text, SmallInteger, Boolean, Numeric)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr


class _Base(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()+'s'

    id = Column(Integer, primary_key=True)

    def __repr__(self):
        return '<%s: %d>' % (self.__class__.__name__, self.id)

### slide::
### title:: Initialize
# Create the Base class with declarative_base()

Base = declarative_base(cls=_Base)


### slide::
### title:: Create ORMs
# Create Group, User, Permission

group2permission_table = Table('groups2permissions', Base.metadata,
                               Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
                               Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True))


class Group(Base):
    #__tablename__ = 'groups'
    #id = Column(Integer, Sequence('group_id_seq'), primary_key=True)
    name = Column(String(50))
    users = relationship('User', backref="group")
    permissions = relationship('Permission', secondary=group2permission_table)


class User(Base):
    #__tablename__ = 'users'
    #id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    fullname = Column(String(50), nullable=True)
    password = Column(String(40), nullable=True)
    key = Column(String(32), nullable=True, doc='Another key')
    created = Column(DateTime, default=func.NOW())
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)


class Permission(Base):
    #__tablename__ = 'permissions'
    #id = Column(Integer, Sequence('permission_id_seq'), primary_key=True)
    name = Column(String(24), unique=True, nullable=False)
    description = Column(String(128), nullable=True)


### slide:: pi
### title:: Initialize datas...
# Create engine and session ...

from sqlalchemy import create_engine
engine = create_engine('sqlite://', echo=True)
#create_engine('postgresql://postgres:postgres@localhost/test', echo=True)
Base.metadata.create_all(engine)

from sqlalchemy.orm import Session
session = Session(bind=engine)


### slide:: pi
### title:: Create users

u1 = User(name='fangze', fullname='Fangze SHEN', password='123456', key='123')
u2 = User(name='fangyi', fullname='Fangyi SHEN', password='234567', key='234')
session.add_all([u1, u2])
session.flush()

### slide:: pi
### title:: Create groups

g1 = Group(name='Admin')
g2 = Group(name='Manager')
g3 = Group(name='Guest')

g1.users = [u1, u2]

session.add_all([g1, g2, g3])
session.flush()

### slide:: pi
### title:: Create Permissions
p0 = Permission(name='Read')
p1 = Permission(name='Create')
p2 = Permission(name='Update')
p3 = Permission(name='Delete')

session.add_all([p0, p1, p2, p3])

g1.permissions = [p0, p1, p2, p3]
g2.permissions = [p0, p1, p2]
g3.permissions = [p0]

session.flush()


### slide:: pi
### title:: Query the user in groups with permission(4)

q = session.query(User).join(User.group).join(Group.permissions).filter(Permission.id == 4)
q.all()

### slide::
### title:: A little bit inside...

Group.__mapper__.relationships.permissions.mapper.class_
Group.__mapper__.relationships.permissions.direction
User.__mapper__.relationships.group.direction
Group.__mapper__.relationships.users.direction

### slide::