from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture =Column(String(250))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
           'email'        : self.email,
           'picture'      : self.picture,
       }

class Catagory(Base):
    __tablename__ = 'catagory'
   
    # id = Column(Integer, primary_key=True)
    name = Column(String(250), primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name
       }
 
class CatalogItem(Base):
    __tablename__ = 'catalog_item'

    name =Column(String(80), primary_key = True)
    # id = Column(Integer, primary_key = True)
    description = Column(String(500))
    created_date = Column(DateTime, default=func.now())
    catagory_name = Column(String(250),ForeignKey('catagory.name'), primary_key=True)
    catagory = relationship(Catagory)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'description'         : self.description,
           'created_date'         : self.created_date,
           'catagory'         : self.catagory.name,
       }

engine = create_engine('sqlite:///catalogwithusers.db')
 

Base.metadata.create_all(engine)
