"""
Models router - model management and training
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class ModelStatus(BaseModel):
    model_name: str
    version: str
    marketplace: str  # wildberries, amazon
    trained_at: datetime
    accuracy: float
    auc_score: float
    feature_count: int
    last_retrain: datetime
    status: str  # active, training, failed


@router.get("/status")
async def get_model_status(marketplace: str = "wildberries") -> ModelStatus:
    """
    Get current status of attribution model for a marketplace
    """
    # TODO: Implement status retrieval
    pass


@router.post("/retrain")
async def trigger_retrain(marketplace: str = "wildberries"):
    """
    Manually trigger model retraining
    
    Uses data from verified attributions since last training
    """
    # TODO: Implement manual retrain
    pass


@router.get("/features")
async def get_model_features(marketplace: str = "wildberries") -> dict:
    """
    Get feature importance for the current model
    
    Helps understand which factors drive attribution decisions
    """
    # TODO: Implement feature importance retrieval
    pass


@router.post("/export")
async def export_model(marketplace: str = "wildberries", format: str = "onnx"):
    """
    Export model in specified format
    
    Supported formats: onnx, pickle, joblib
    """
    # TODO: Implement model export
    pass
