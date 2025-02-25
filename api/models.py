from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime
from sqlalchemy import JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
class Languages(Base):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_modern = Column(Boolean, nullable=False)
    is_popular = Column(Boolean, nullable=False)
    
class LanguageFeatures(Base):
    __tablename__ = "language_features"
    
    id = Column(Integer, primary_key=True, index=True)
    language_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    
class RecommendationModel(Base):
    __tablename__ = "recommendations"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)  # UUID型のid
    user_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)  # UUID型のuser_id
    recommendation = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)