"""
ML модель для классификации критичности дефектов с улучшениями.
Включает: train/test split, метрики, Pipeline, feature engineering, MLflow, кэширование.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.base import BaseEstimator, TransformerMixin

from app.core.config import settings
from app.core.logging_config import logger

# Опциональный импорт mlflow
try:
    import mlflow
    import mlflow.sklearn
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    mlflow = None
    MlflowClient = None
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow не установлен. Функциональность MLflow будет недоступна.")

# Инициализация MLflow (только если доступен)
if MLFLOW_AVAILABLE:
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)


class FeatureEngineeringTransformer(BaseEstimator, TransformerMixin):
    """Кастомный трансформер для feature engineering."""
    
    def __init__(self):
        self.feature_names_ = None
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        """Добавляет новые признаки."""
        if isinstance(X, pd.DataFrame):
            df = X.copy()
        else:
            # Если numpy array, создаем DataFrame (нужно знать имена колонок)
            df = pd.DataFrame(X)
        
        # Временные признаки из даты (если есть)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day_of_year'] = df['date'].dt.dayofyear
            df['is_winter'] = df['month'].isin([12, 1, 2]).astype(int)
            df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
        
        # Взаимодействия признаков
        if 'param1' in df.columns and 'param2' in df.columns:
            df['param1_x_param2'] = df['param1'] * df['param2']
            df['param1_div_param2'] = df['param1'] / (df['param2'] + 1e-6)  # Избегаем деления на 0
            df['param_sum'] = df['param1'] + df['param2']
            df['param_diff'] = abs(df['param1'] - df['param2'])
        
        # Полиномиальные признаки (квадраты)
        if 'param1' in df.columns:
            df['param1_squared'] = df['param1'] ** 2
        if 'param2' in df.columns:
            df['param2_squared'] = df['param2'] ** 2
        
        # Взаимодействие с возрастом объекта
        if 'object_year' in df.columns and 'date' in df.columns:
            df['object_age'] = df['year'] - df['object_year']
            df['object_age_squared'] = df['object_age'] ** 2
        
        # Нормализация параметров относительно метода (если есть)
        if 'method_encoded' in df.columns and 'param1' in df.columns:
            method_means = df.groupby('method_encoded')['param1'].transform('mean')
            df['param1_normalized'] = df['param1'] / (method_means + 1e-6)
        
        return df


class MLModel:
    """Улучшенный класс для ML модели с Pipeline, метриками и MLflow."""
    
    _instance = None
    _model = None
    _pipeline = None
    _feature_transformer = None
    _is_trained = False
    _metrics = {}
    _mlflow_run_id = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация модели."""
        if self._model is None:
            self._create_pipeline()
            self._load_model()
    
    def _create_pipeline(self):
        """Создает Pipeline для предобработки и модели."""
        # Определяем числовые и категориальные признаки
        numeric_features = ['param1', 'param2', 'param3', 'object_year']
        categorical_features = ['method_encoded']
        
        # Трансформеры для числовых признаков
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])
        
        # Трансформеры для категориальных признаков
        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
        ])
        
        # Объединяем трансформеры
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ],
            remainder='passthrough'  # Оставляем остальные признаки как есть
        )
        
        # Полный Pipeline: предобработка + модель
        self._pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=settings.ML_RANDOM_STATE,
                n_jobs=-1,
            ))
        ])
        
        self._feature_transformer = FeatureEngineeringTransformer()
        self._method_encoder = LabelEncoder()
    
    def _load_model(self):
        """Загрузка сохраненной модели (если есть)."""
        model_path = Path(settings.ML_MODEL_PATH)
        if model_path.exists():
            try:
                loaded = joblib.load(model_path)
                self._pipeline = loaded.get("pipeline", self._pipeline)
                self._method_encoder = loaded.get("method_encoder", LabelEncoder())
                self._feature_transformer = loaded.get("feature_transformer", FeatureEngineeringTransformer())
                self._metrics = loaded.get("metrics", {})
                self._mlflow_run_id = loaded.get("mlflow_run_id")
                self._is_trained = True
                logger.info("✅ ML модель загружена из файла")
            except Exception as e:
                logger.error(f"⚠️  Ошибка загрузки модели: {e}")
    
    def _save_model(self):
        """Сохранение модели."""
        model_path = Path(settings.ML_MODEL_PATH)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(
            {
                "pipeline": self._pipeline,
                "method_encoder": self._method_encoder,
                "feature_transformer": self._feature_transformer,
                "metrics": self._metrics,
                "mlflow_run_id": self._mlflow_run_id,
                "saved_at": datetime.now().isoformat(),
            },
            model_path,
        )
        logger.info("✅ ML модель сохранена")
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Подготовка признаков для модели с feature engineering."""
        # Копируем данные
        features_df = df.copy()
        
        # Кодируем метод диагностики
        if "method" in features_df.columns:
            if self._is_trained and hasattr(self._method_encoder, 'classes_'):
                # Используем обученный encoder
                # Обрабатываем неизвестные значения
                known_methods = set(self._method_encoder.classes_)
                features_df['method'] = features_df['method'].apply(
                    lambda x: x if x in known_methods else self._method_encoder.classes_[0]
                )
                features_df["method_encoded"] = self._method_encoder.transform(
                    features_df["method"]
                )
            else:
                # Обучаем encoder на новых данных
                features_df["method_encoded"] = self._method_encoder.fit_transform(
                    features_df["method"]
                )
        elif "method_encoded" not in features_df.columns:
            # Если метода нет, создаем фиктивный
            features_df["method_encoded"] = 0
        
        # Заполняем пропуски
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        features_df[numeric_cols] = features_df[numeric_cols].fillna(0)
        
        # Преобразуем defect_found в int
        if "defect_found" in features_df.columns:
            features_df["defect_found_int"] = features_df["defect_found"].astype(int)
        else:
            features_df["defect_found_int"] = 0
        
        # Добавляем год объекта (если есть)
        if "object_year" not in features_df.columns:
            features_df["object_year"] = 2000
        
        # Применяем feature engineering
        features_df = self._feature_transformer.transform(features_df)
        
        return features_df
    
    def train(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        use_mlflow: bool = True,
        test_size: float = None,
    ) -> Dict:
        """
        Обучение модели с train/test split и метриками.
        
        Args:
            X: DataFrame с признаками
            y: Массив меток
            use_mlflow: Использовать MLflow для логирования
            test_size: Размер тестовой выборки (по умолчанию из settings)
            
        Returns:
            Словарь с метриками обучения
        """
        test_size = test_size or settings.ML_TEST_SIZE
        
        # Подготавливаем признаки
        X_prepared = self.prepare_features(X)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_prepared,
            y,
            test_size=test_size,
            random_state=settings.ML_RANDOM_STATE,
            stratify=y  # Сохраняем пропорции классов
        )
        
        logger.info(f"Разделение данных: train={len(X_train)}, test={len(X_test)}")
        
        # Начинаем MLflow run
        if use_mlflow:
            if MLFLOW_AVAILABLE:
                mlflow.start_run()
                self._mlflow_run_id = mlflow.active_run().info.run_id
            else:
                self._mlflow_run_id = None
        
        try:
            # Обучение модели
            logger.info("Начало обучения модели...")
            self._pipeline.fit(X_train, y_train)
            self._is_trained = True
            
            # Предсказания на тестовой выборке
            y_pred = self._pipeline.predict(X_test)
            y_pred_proba = self._pipeline.predict_proba(X_test)
            
            # Вычисляем метрики
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision_macro': precision_score(y_test, y_pred, average='macro', zero_division=0),
                'recall_macro': recall_score(y_test, y_pred, average='macro', zero_division=0),
                'f1_macro': f1_score(y_test, y_pred, average='macro', zero_division=0),
                'precision_weighted': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                'recall_weighted': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                'f1_weighted': f1_score(y_test, y_pred, average='weighted', zero_division=0),
            }
            
            # Метрики по классам
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            for label in report:
                if label not in ['accuracy', 'macro avg', 'weighted avg']:
                    metrics[f'precision_{label}'] = report[label]['precision']
                    metrics[f'recall_{label}'] = report[label]['recall']
                    metrics[f'f1_{label}'] = report[label]['f1-score']
            
            # Confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            metrics['confusion_matrix'] = cm.tolist()
            
            # Cross-validation на train данных
            cv_scores = cross_val_score(
                self._pipeline,
                X_train,
                y_train,
                cv=5,
                scoring='f1_macro',
                n_jobs=-1
            )
            metrics['cv_f1_mean'] = cv_scores.mean()
            metrics['cv_f1_std'] = cv_scores.std()
            
            self._metrics = metrics
            
            # Логируем в MLflow
            if use_mlflow and MLFLOW_AVAILABLE:
                # Параметры модели
                mlflow.log_params({
                    'n_estimators': self._pipeline.named_steps['classifier'].n_estimators,
                    'max_depth': self._pipeline.named_steps['classifier'].max_depth,
                    'test_size': test_size,
                    'random_state': settings.ML_RANDOM_STATE,
                })
                
                # Метрики
                mlflow.log_metrics(metrics)
                
                # Модель
                mlflow.sklearn.log_model(
                    self._pipeline,
                    "model",
                    registered_model_name="IntegrityOS-Pipeline-Model"
                )
                
                # Confusion matrix как артефакт
                import matplotlib.pyplot as plt
                import seaborn as sns
                
                plt.figure(figsize=(8, 6))
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
                plt.title('Confusion Matrix')
                plt.ylabel('True Label')
                plt.xlabel('Predicted Label')
                plt.tight_layout()
                plt.savefig('confusion_matrix.png')
                mlflow.log_artifact('confusion_matrix.png')
                plt.close()
                
                logger.info(f"✅ MLflow run завершен: {self._mlflow_run_id}")
            
            logger.info(f"✅ ML модель обучена. Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_macro']:.4f}")
            
            # Сохраняем модель
            self._save_model()
            
            return {
                'trained': True,
                'metrics': metrics,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'mlflow_run_id': self._mlflow_run_id,
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обучении модели: {e}", exc_info=True)
            if use_mlflow and MLFLOW_AVAILABLE:
                mlflow.end_run(status="FAILED")
            raise
        finally:
            if use_mlflow and MLFLOW_AVAILABLE:
                mlflow.end_run()
    
    def predict(self, X: pd.DataFrame, return_proba: bool = False) -> List[str]:
        """
        Предсказание меток.
        
        Args:
            X: DataFrame с признаками
            return_proba: Возвращать также вероятности
            
        Returns:
            Список предсказанных меток (и вероятности, если return_proba=True)
        """
        if not self._is_trained:
            # Если модель не обучена, возвращаем "normal" по умолчанию
            default = ["normal"] * len(X)
            if return_proba:
                return default, np.ones((len(X), 3)) / 3
            return default
        
        # Подготавливаем признаки
        X_prepared = self.prepare_features(X)
        
        # Предсказываем
        predictions = self._pipeline.predict(X_prepared)
        predictions = [str(pred) for pred in predictions]
        
        if return_proba:
            probabilities = self._pipeline.predict_proba(X_prepared)
            return predictions, probabilities
        
        return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Предсказание вероятностей."""
        if not self._is_trained:
            # Если модель не обучена, возвращаем равномерное распределение
            return np.ones((len(X), 3)) / 3
        
        X_prepared = self.prepare_features(X)
        return self._pipeline.predict_proba(X_prepared)
    
    def predict_batch(self, X_list: List[pd.DataFrame]) -> List[List[str]]:
        """
        Батчинг предсказаний для эффективной обработки множественных запросов.
        
        Args:
            X_list: Список DataFrame с признаками
            
        Returns:
            Список списков предсказанных меток
        """
        if not X_list:
            return []
        
        # Объединяем все DataFrame
        combined_df = pd.concat(X_list, ignore_index=True)
        
        # Делаем предсказания одним батчем
        predictions = self.predict(combined_df)
        
        # Разделяем обратно по батчам
        result = []
        start_idx = 0
        for df in X_list:
            end_idx = start_idx + len(df)
            result.append(predictions[start_idx:end_idx])
            start_idx = end_idx
        
        return result
    
    @property
    def is_trained(self) -> bool:
        """Проверка, обучена ли модель."""
        return self._is_trained
    
    @property
    def metrics(self) -> Dict:
        """Получить метрики последнего обучения."""
        return self._metrics
    
    @property
    def mlflow_run_id(self) -> Optional[str]:
        """Получить ID последнего MLflow run."""
        return self._mlflow_run_id


# Singleton instance
ml_model = MLModel()
