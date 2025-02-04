from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
class Language(Base):
    __tablename__ = "language"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_modern = Column(Boolean, nullable=False)
    is_popular = Column(Boolean, nullable=False)