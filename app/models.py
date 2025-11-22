from pydantic import BaseModel, Field
from typing import List

class FeedbackScore(BaseModel):
    technical_rating: int = Field(..., description="Rating from 1-10 on technical ability")
    communication_rating: int = Field(..., description="Rating from 1-10 on communication skills")
    cultural_fit_rating: int = Field(..., description="Rating from 1-10 on cultural fit")
    summary: str = Field(..., description="A qualitative summary of the candidate")
    decision: str = Field(..., description="HIRE, NO HIRE, or HOLD")

class DetailedEvaluation(BaseModel):
    overall_rating: int = Field(..., description="Overall rating from 1-10")
    technical_rating: int = Field(..., description="Technical skills rating from 1-10")
    communication_rating: int = Field(..., description="Communication skills rating from 1-10")
    problem_solving_rating: int = Field(..., description="Problem solving rating from 1-10")
    strengths: List[str] = Field(..., description="List of candidate's strengths demonstrated in the interview")
    areas_for_improvement: List[str] = Field(..., description="List of areas where candidate could improve")
    recommendations: str = Field(..., description="Detailed recommendations for hiring decision")
    decision: str = Field(..., description="Final decision: HIRE, NO HIRE, or HOLD")