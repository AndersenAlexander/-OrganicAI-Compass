import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Recommendation(Base):
    __tablename__="recommendations"
    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()))
    user_id:Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True,index=True)
    profile_id:Mapped[str]=mapped_column(String,index=True,nullable=False)
    category:Mapped[str]=mapped_column(String(50),index=True,nullable=False)
    title:Mapped[str]=mapped_column(String(255),nullable=False)
    summary:Mapped[str]=mapped_column(Text,nullable=False)
    reason:Mapped[str]=mapped_column(Text,nullable=False)
    profile_signals_json:Mapped[list]=mapped_column(JSON,default=list)
    rag_sources_json:Mapped[list]=mapped_column(JSON,default=list)
    score_components_json:Mapped[dict]=mapped_column(JSON,default=dict)
    retrieval_metadata_json:Mapped[dict]=mapped_column(JSON,default=dict)
    relevance_score:Mapped[float]=mapped_column(Float,default=0)
    confidence:Mapped[float]=mapped_column(Float,default=0)
    effort:Mapped[str]=mapped_column(String(20),default="medium")
    impact:Mapped[str]=mapped_column(String(20),default="medium")
    time_horizon:Mapped[str]=mapped_column(String(30),default="thirty_days")
    estimated_duration:Mapped[str]=mapped_column(String(80),default="2–4 weeks")
    prerequisites_json:Mapped[list]=mapped_column(JSON,default=list)
    first_action:Mapped[str]=mapped_column(Text,nullable=False)
    success_indicator:Mapped[str]=mapped_column(Text,nullable=False)
    ethical_cautions_json:Mapped[list]=mapped_column(JSON,default=list)
    what_to_verify_json:Mapped[list]=mapped_column(JSON,default=list)
    status:Mapped[str]=mapped_column(String(30),default="suggested",index=True)
    user_rating:Mapped[int|None]=mapped_column(Integer,nullable=True)
    user_feedback:Mapped[str|None]=mapped_column(Text,nullable=True)
    generation_version:Mapped[str]=mapped_column(String(30),default="rules-v1")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class RecommendationFeedback(Base):
    __tablename__="recommendation_feedback"
    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()))
    recommendation_id:Mapped[str]=mapped_column(ForeignKey("recommendations.id"),index=True)
    user_id:Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True)
    rating:Mapped[int|None]=mapped_column(Integer,nullable=True)
    relevant:Mapped[bool|None]=mapped_column(Boolean,nullable=True)
    feedback_text:Mapped[str|None]=mapped_column(Text,nullable=True)
    reason_code:Mapped[str|None]=mapped_column(String(50),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class RecommendationEvent(Base):
    __tablename__="recommendation_events"
    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()))
    recommendation_id:Mapped[str]=mapped_column(ForeignKey("recommendations.id"),index=True)
    user_id:Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True)
    event_type:Mapped[str]=mapped_column(String(50),index=True)
    metadata_json:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
