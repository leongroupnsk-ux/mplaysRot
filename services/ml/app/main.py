"""
ML service — HTTP entrypoint.

Endpoints:
  GET  /health                       liveness / readiness
  GET  /models                       list available model artifacts
  POST /predict/attribution          score (trax_id, order_id) pairs
  POST /predict/conversion           score a click for conversion probability
  POST /train/attribution            trigger attribution model retrain (async)
  POST /train/anomaly                run anomaly detector (async)
"""
import logging
import sys
import os

# Allow sibling-package imports (services/ml/... style)
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="Attribly ML Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


# ── Schemas ───────────────────────────────────────────────────────────────────

class AttributionPair(BaseModel):
    trax_id: str
    order_id: str


class AttributionRequest(BaseModel):
    campaign_id: str
    pairs: list[AttributionPair]


class AttributionResult(BaseModel):
    order_id: str
    trax_id: str
    confidence: float
    method: str


class ConversionRequest(BaseModel):
    ad_platform: str
    device_type: str
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    is_weekend: bool
    platform_hist_rate: float = 0.05
    campaign_cr: float = 0.05
    geo_cr: float = 0.05


class ConversionResult(BaseModel):
    probability: float
    will_convert: bool


class ModelInfo(BaseModel):
    name: str
    exists: bool


class TrainResponse(BaseModel):
    status: str
    message: str


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ml"}


# ── Model list ────────────────────────────────────────────────────────────────

@app.get("/models", response_model=list[ModelInfo])
async def list_models():
    from services.ml.shared.store import model_exists
    return [
        ModelInfo(name="attribution_catboost",    exists=model_exists("attribution_catboost", "pkl")),
        ModelInfo(name="conversion_lr_pipeline",  exists=model_exists("conversion_lr_pipeline", "onnx")),
        ModelInfo(name="lookalike_gb",            exists=model_exists("lookalike_gb", "pkl")),
    ]


# ── Attribution predict ───────────────────────────────────────────────────────

@app.post("/predict/attribution", response_model=list[AttributionResult])
async def predict_attribution(req: AttributionRequest):
    """
    Score candidate (trax_id, order_id) pairs.
    Returns strict (confidence=1.0) or probabilistic attributions.
    Requires the attribution CatBoost model to be trained first.
    """
    try:
        from services.ml.attribution.model import load as load_model
        from services.ml.attribution.features import build_feature_matrix, CandidatePair, FEATURE_COLS
        import numpy as np

        model = load_model()
        results = []

        for pair in req.pairs:
            # Attempt to build features for this pair from ClickHouse
            try:
                candidates = [CandidatePair(
                    trax_id=pair.trax_id,
                    campaign_id=req.campaign_id,
                    ad_platform="",
                    marketplace="",
                    click_at="",
                    order_id=pair.order_id,
                    order_at="",
                    product_id_click="",
                    product_id_order="",
                    region_click="",
                    region_order="",
                )]
                X = build_feature_matrix(candidates)
                if len(X) == 0:
                    confidence = 0.0
                    method = "no_features"
                else:
                    confidence = float(model.predict_proba(X)[0][1])
                    method = "probabilistic"
            except Exception:
                confidence = 0.0
                method = "error"

            results.append(AttributionResult(
                order_id=pair.order_id,
                trax_id=pair.trax_id,
                confidence=confidence,
                method=method,
            ))

        return results

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Attribution model not trained yet. POST /train/attribution first.",
        )
    except Exception as exc:
        log.exception("Attribution prediction failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Conversion predict ────────────────────────────────────────────────────────

@app.post("/predict/conversion", response_model=ConversionResult)
async def predict_conversion(req: ConversionRequest):
    """Score a click event for real-time conversion probability via ONNX runtime."""
    try:
        from services.ml.conversion_predictor.model import predictor

        prob = predictor.score({
            "ad_platform": req.ad_platform,
            "device_type": req.device_type,
            "hour_of_day": req.hour_of_day,
            "day_of_week": req.day_of_week,
            "is_weekend": int(req.is_weekend),
            "platform_hist_rate": req.platform_hist_rate,
            "campaign_cr": req.campaign_cr,
            "geo_cr": req.geo_cr,
        })
        return ConversionResult(probability=prob, will_convert=prob >= 0.5)
    except Exception as exc:
        log.exception("Conversion prediction failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Train endpoints (run in background) ───────────────────────────────────────

def _run_attribution_train():
    try:
        from services.ml.attribution.model import train
        train()
        log.info("Attribution model retrain complete")
    except Exception:
        log.exception("Attribution model retrain failed")


def _run_anomaly_detection():
    try:
        from services.ml.anomaly.detector import detect_anomalies
        anomalies = detect_anomalies()
        log.info("Anomaly detection complete: %d anomalies found", len(anomalies))
    except Exception:
        log.exception("Anomaly detection failed")


@app.post("/train/attribution", response_model=TrainResponse, status_code=status.HTTP_202_ACCEPTED)
async def train_attribution(background_tasks: BackgroundTasks):
    """Trigger attribution model retrain (non-blocking)."""
    background_tasks.add_task(_run_attribution_train)
    return TrainResponse(status="accepted", message="Attribution model retrain queued")


@app.post("/train/anomaly", response_model=TrainResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_anomaly_detection(background_tasks: BackgroundTasks):
    """Run anomaly detector over recent campaign data (non-blocking)."""
    background_tasks.add_task(_run_anomaly_detection)
    return TrainResponse(status="accepted", message="Anomaly detection run queued")
