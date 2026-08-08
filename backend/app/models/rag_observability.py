import uuid
from datetime import datetime
from sqlalchemy import Boolean,DateTime,Float,ForeignKey,Integer,String,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import Base

class RagRun(Base):
    __tablename__="rag_runs"
    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()))
    user_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True);profile_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True)
    conversation_id:Mapped[str|None]=mapped_column(String,nullable=True);message_id:Mapped[str|None]=mapped_column(String,nullable=True)
    query:Mapped[str]=mapped_column(Text);query_normalized:Mapped[str|None]=mapped_column(Text,nullable=True);mode:Mapped[str]=mapped_column(String(32),default="knowledge_base")
    run_origin:Mapped[str]=mapped_column(String(20),default="user",nullable=False,index=True)
    retrieval_top_k:Mapped[int]=mapped_column(Integer,default=4);relevance_threshold:Mapped[float]=mapped_column(Float,default=.1);retrieved_count:Mapped[int]=mapped_column(Integer,default=0);used_source_count:Mapped[int]=mapped_column(Integer,default=0)
    highest_similarity_score:Mapped[float|None]=mapped_column(Float,nullable=True);average_similarity_score:Mapped[float|None]=mapped_column(Float,nullable=True)
    retrieval_duration_ms:Mapped[int|None]=mapped_column(Integer,nullable=True);generation_duration_ms:Mapped[int|None]=mapped_column(Integer,nullable=True);total_duration_ms:Mapped[int|None]=mapped_column(Integer,nullable=True)
    embedding_model:Mapped[str|None]=mapped_column(String(120),nullable=True);generation_model:Mapped[str|None]=mapped_column(String(120),nullable=True);provider:Mapped[str|None]=mapped_column(String(40),nullable=True)
    answer:Mapped[str|None]=mapped_column(Text,nullable=True);confidence_note:Mapped[str|None]=mapped_column(Text,nullable=True);ethical_note:Mapped[str|None]=mapped_column(Text,nullable=True);context_quality:Mapped[str]=mapped_column(String(20),default="insufficient")
    fallback_reason:Mapped[str|None]=mapped_column(String(80),nullable=True);insufficient_context:Mapped[bool]=mapped_column(Boolean,default=False);prompt_injection_flag:Mapped[bool]=mapped_column(Boolean,default=False)
    status:Mapped[str]=mapped_column(String(32),default="completed");error_code:Mapped[str|None]=mapped_column(String(80),nullable=True);error_message_safe:Mapped[str|None]=mapped_column(String(300),nullable=True);created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
    sources=relationship("RagRunSource",back_populates="run",cascade="all, delete-orphan");feedback=relationship("RagFeedback",back_populates="run",cascade="all, delete-orphan")

class RagRunSource(Base):
    __tablename__="rag_run_sources"
    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()));rag_run_id:Mapped[str]=mapped_column(ForeignKey("rag_runs.id"),index=True)
    document_id:Mapped[str|None]=mapped_column(String,nullable=True);document_name:Mapped[str]=mapped_column(String(255));chunk_id:Mapped[str]=mapped_column(String(255));section_title:Mapped[str|None]=mapped_column(String(255),nullable=True);chunk_position:Mapped[int|None]=mapped_column(Integer,nullable=True)
    similarity_score:Mapped[float]=mapped_column(Float);rank:Mapped[int]=mapped_column(Integer);was_used_in_context:Mapped[bool]=mapped_column(Boolean,default=False);source_excerpt:Mapped[str]=mapped_column(Text);injection_risk:Mapped[bool]=mapped_column(Boolean,default=False);created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    run=relationship("RagRun",back_populates="sources")

class RagFeedback(Base):
    __tablename__="rag_feedback";__table_args__=(UniqueConstraint("rag_run_id","user_id","feedback_type","source_id",name="uq_rag_feedback_target"),)
    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()));rag_run_id:Mapped[str]=mapped_column(ForeignKey("rag_runs.id"),index=True);user_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True);profile_id:Mapped[str|None]=mapped_column(String,nullable=True)
    feedback_type:Mapped[str]=mapped_column(String(40));rating:Mapped[str]=mapped_column(String(32));reason_code:Mapped[str|None]=mapped_column(String(40),nullable=True);comment:Mapped[str|None]=mapped_column(String(1000),nullable=True);source_id:Mapped[str|None]=mapped_column(String,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow);updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow);run=relationship("RagRun",back_populates="feedback")
