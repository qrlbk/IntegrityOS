"""
Оптимизация гиперпараметров модели с использованием Optuna.
"""
from typing import Dict, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.metrics import f1_score, make_scorer

try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

from app.core.ml_model import ml_model
from app.core.config import settings
from app.core.logging_config import logger


def optimize_hyperparameters(
    X: pd.DataFrame,
    y: np.ndarray,
    n_trials: int = 50,
    timeout: Optional[int] = None,
) -> Dict:
    """
    Оптимизирует гиперпараметры модели с помощью Optuna.
    
    Args:
        X: DataFrame с признаками
        y: Массив меток
        n_trials: Количество попыток оптимизации
        timeout: Максимальное время оптимизации в секундах
        
    Returns:
        Словарь с лучшими параметрами и метриками
    """
    if not OPTUNA_AVAILABLE:
        logger.warning("Optuna не установлен. Установите: pip install optuna")
        return {
            "optimized": False,
            "message": "Optuna не доступен",
        }
    
    # Подготавливаем признаки
    X_prepared = ml_model.prepare_features(X)
    
    def objective(trial):
        """Целевая функция для оптимизации."""
        # Предлагаем параметры для оптимизации
        n_estimators = trial.suggest_int("n_estimators", 50, 300, step=50)
        max_depth = trial.suggest_int("max_depth", 5, 20)
        min_samples_split = trial.suggest_int("min_samples_split", 2, 10)
        min_samples_leaf = trial.suggest_int("min_samples_leaf", 1, 5)
        max_features = trial.suggest_categorical("max_features", ["sqrt", "log2", None])
        
        # Создаем модель с предложенными параметрами
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.compose import ColumnTransformer
        from sklearn.preprocessing import StandardScaler, OneHotEncoder
        from sklearn.pipeline import Pipeline
        
        numeric_features = ['param1', 'param2', 'param3', 'object_year']
        categorical_features = ['method_encoded']
        
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
        ])
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ],
            remainder='passthrough'
        )
        
        model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                max_features=max_features,
                random_state=settings.ML_RANDOM_STATE,
                n_jobs=-1,
            ))
        ])
        
        # Cross-validation
        cv_scores = cross_val_score(
            model,
            X_prepared,
            y,
            cv=5,
            scoring=make_scorer(f1_score, average='macro', zero_division=0),
            n_jobs=-1
        )
        
        return cv_scores.mean()
    
    try:
        logger.info(f"Начало оптимизации гиперпараметров (n_trials={n_trials})...")
        
        study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=settings.ML_RANDOM_STATE),
        )
        
        study.optimize(
            objective,
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=True,
        )
        
        best_params = study.best_params
        best_value = study.best_value
        
        logger.info(f"✅ Оптимизация завершена. Лучший F1: {best_value:.4f}")
        logger.info(f"Лучшие параметры: {best_params}")
        
        return {
            "optimized": True,
            "best_params": best_params,
            "best_f1_score": best_value,
            "n_trials": len(study.trials),
        }
        
    except Exception as e:
        logger.error(f"Ошибка при оптимизации гиперпараметров: {e}", exc_info=True)
        return {
            "optimized": False,
            "error": str(e),
        }


def train_with_optimized_params(
    X: pd.DataFrame,
    y: np.ndarray,
    optimized_params: Dict,
    use_mlflow: bool = True,
) -> Dict:
    """
    Обучает модель с оптимизированными параметрами.
    
    Args:
        X: DataFrame с признаками
        y: Массив меток
        optimized_params: Словарь с оптимизированными параметрами
        use_mlflow: Использовать MLflow для логирования
        
    Returns:
        Результат обучения
    """
    # Обновляем параметры модели
    if optimized_params:
        classifier = ml_model._pipeline.named_steps['classifier']
        for param, value in optimized_params.items():
            if hasattr(classifier, param):
                setattr(classifier, param, value)
        
        logger.info(f"Параметры модели обновлены: {optimized_params}")
    
    # Обучаем модель
    return ml_model.train(X, y, use_mlflow=use_mlflow)

