from typing import Literal
from pydantic import BaseModel,Field,field_validator
FeedbackType=Literal["answer_usefulness","answer_grounding","source_relevance","confidence_clarity","ethical_note_clarity"]
Rating=Literal["helpful","partially_helpful","not_helpful","relevant","partially_relevant","not_relevant"]
Reason=Literal["missing_context","wrong_source","too_general","too_detailed","unclear","not_actionable","contradicts_profile","unsupported_claim","other"]
class RagAskRequest(BaseModel):query:str=Field(min_length=2,max_length=4000);profile_id:str|None=None;conversation_id:str|None=None
class RagFeedbackRequest(BaseModel):
    feedback_type:FeedbackType="answer_usefulness";rating:Rating;reason_code:Reason|None=None;comment:str|None=Field(default=None,max_length=1000);profile_id:str|None=None
    @field_validator("comment")
    @classmethod
    def clean(cls,value):return " ".join(value.replace("<","").replace(">","").split()) if value else value
