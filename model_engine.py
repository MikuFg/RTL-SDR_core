import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io
import numpy as np
from typing import Tuple, Dict, Any

class RadarAI:
    def __init__(self, model_path="radar_model_v2.pth"):
        self.device = torch.device("cpu")
        self.classes = ['airplane', 'bird', 'drone', 'helicopter']
        
        # Инициализация архитектуры
        self.model = models.resnet18()
        self.model.fc = nn.Linear(self.model.fc.in_features, 4)
        
        # Загрузка обученных весов
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def predict_from_image(self, image: Image.Image) -> Tuple[str, float]:
        """Предсказание из объекта PIL Image"""
        img_t = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(img_t)
            prob = torch.nn.functional.softmax(outputs[0], dim=0)
            conf, pred = torch.max(prob, 0)
            
        return self.classes[pred.item()], conf.item()

    def predict(self, image_path):
        """Предсказание из файла изображения (для обратной совместимости)"""
        img = Image.open(image_path).convert('RGB')
        return self.predict_from_image(img)
    
    def predict_with_metadata(self, image: Image.Image, signal_characteristics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Предсказание с дополнительными метаданными"""
        label, confidence = self.predict_from_image(image)
        
        result = {
            'prediction': label,
            'confidence': float(confidence),
            'timestamp': self._get_timestamp(),
            'model_info': {
                'architecture': 'ResNet18',
                'classes': self.classes,
                'input_size': (128, 128, 3)
            }
        }
        
        # Добавление характеристик сигнала (всегда добавляем поле)
        result['signal_analysis'] = signal_characteristics or {}
            
        return result
    
    def _get_timestamp(self) -> str:
        """Получает текущую временную метку"""
        from datetime import datetime
        return datetime.now().isoformat()

class RadarSignalClassifier:
    """Расширенный классификатор для работы с радиосигналами"""
    
    def __init__(self, model_path="radar_model_v2.pth"):
        self.ai_model = RadarAI(model_path)
        self.confidence_threshold = 0.5
        
    def classify_signal(self, image: Image.Image, signal_characteristics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Классифицирует сигнал и возвращает полную информацию"""
        # Базовое предсказание
        result = self.ai_model.predict_with_metadata(image, signal_characteristics)
        
        # Дополнительная обработка на основе характеристик сигнала
        if signal_characteristics:
            result['risk_assessment'] = self._assess_risk(result['prediction'], signal_characteristics)
            result['signal_quality'] = self._assess_signal_quality(signal_characteristics)
        else:
            # Значения по умолчанию когда нет характеристик
            result['risk_assessment'] = 'unknown'
            result['signal_quality'] = 'unknown'
        
        # Флаг достоверности
        result['is_reliable'] = result['confidence'] >= self.confidence_threshold
        
        return result
    
    def _assess_risk(self, prediction: str, signal_characteristics: Dict[str, Any]) -> str:
        """Оценивает уровень риска на основе типа объекта и характеристик сигнала"""
        risk_levels = {
            'drone': 'high',
            'helicopter': 'medium', 
            'airplane': 'low',
            'bird': 'very_low'
        }
        
        base_risk = risk_levels.get(prediction, 'unknown')
        
        # Корректировка риска на основе характеристик
        if signal_characteristics.get('crest_factor', 0) > 10:
            # Высокий пик-фактор может указывать на аномалию
            if base_risk in ['low', 'very_low']:
                base_risk = 'medium'
        
        return base_risk
    
    def _assess_signal_quality(self, signal_characteristics: Dict[str, Any]) -> str:
        """Оценивает качество сигнала"""
        rms = signal_characteristics.get('rms', 0)
        crest_factor = signal_characteristics.get('crest_factor', 0)
        
        if rms > 0.1 and crest_factor < 20:
            return 'excellent'
        elif rms > 0.05 and crest_factor < 30:
            return 'good'
        elif rms > 0.01:
            return 'fair'
        else:
            return 'poor'