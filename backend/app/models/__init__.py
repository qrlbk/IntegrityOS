"""
Импортируем все модели для корректной регистрации в Base.
"""
from app.models.pipeline import Pipeline
from app.models.object import Object
from app.models.diagnostic import Diagnostic
from app.models.ml_prediction_log import MLPredictionLog
from app.models.work_permit import WorkPermit, WorkPermitStatus

__all__ = ["Pipeline", "Object", "Diagnostic", "MLPredictionLog", "WorkPermit", "WorkPermitStatus"]


