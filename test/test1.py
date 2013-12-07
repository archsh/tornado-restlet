# -*- coding: utf-8 -*-
### slide:: s
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence, MetaData, ForeignKey, Text, SmallInteger, Boolean, Numeric
from sqlalchemy.orm import relationship, backref

### slide::
### title:: Initialize
# Create the Base class with declarative_base()

Base = declarative_base()


### slide::
### title:: Create ORMs
# Create Group, User, Permission

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, Sequence('group_id_seq'), primary_key=True)
    name = Column(String(50))
    users = relationship('User', backref="group")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    fullname = Column(String(50), nullable=True)
    password = Column(String(40), nullable=True)
    key = Column(String(32), nullable=True, doc='Another key')
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)


class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, Sequence('permission_id_seq'), primary_key=True)
    name = Column(String(24), unique=True, nullable=False)
    description = Column(String(128), nullable=True)


### slide::
### title:: Initialize datas...
# Create engine and session ...

from sqlalchemy import create_engine
engine = create_engine('sqlite://')
Base.metadata.create_all(engine)

from sqlalchemy.orm import Session
session = Session(bind=engine)

