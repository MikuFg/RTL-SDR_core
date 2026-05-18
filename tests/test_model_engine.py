import unittest
import numpy as np
import torch
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from model_engine import RadarAI, RadarSignalClassifier

class TestRadarAI(unittest.TestCase):
    """Тесты для класса RadarAI"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем мок-модель для тестов
        self.mock_model_path = self._create_mock_model()
        self.ai = RadarAI(model_path=self.mock_model_path)
    
    def _create_mock_model(self):
        """Создает мок-модель для тестов"""
        import torch.nn as nn
        
        # Создаем точно такую же архитектуру как в model_engine.py
        from torchvision import models
        model = models.resnet18()
        model.fc = nn.Linear(model.fc.in_features, 4)  # 4 класса: airplane, bird, drone, helicopter
        
        # Устанавливаем модель в режим eval
        model.eval()
        
        # Сохраняем state_dict
        model_path = "test_mock_model.pth"
        torch.save(model.state_dict(), model_path)
        return model_path
    
    def tearDown(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.mock_model_path):
            os.remove(self.mock_model_path)
    
    def test_init(self):
        """Тест инициализации"""
        self.assertEqual(self.ai.device, torch.device("cpu"))
        self.assertEqual(self.ai.classes, ['airplane', 'bird', 'drone', 'helicopter'])
        self.assertIsNotNone(self.ai.model)
        self.assertIsNotNone(self.ai.transform)
    
    def test_predict_from_image(self):
        """Тест предсказания из изображения"""
        # Создаем тестовое изображение
        image = Image.new('RGB', (128, 128), color='red')
        
        # Получаем предсказание
        label, confidence = self.ai.predict_from_image(image)
        
        # Проверяем результат
        self.assertIn(label, self.ai.classes)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_predict_from_file(self):
        """Тест предсказания из файла изображения"""
        # Создаем временное изображение
        test_image_path = "test_image.png"
        image = Image.new('RGB', (128, 128), color='blue')
        image.save(test_image_path)
        
        try:
            # Получаем предсказание
            label, confidence = self.ai.predict(test_image_path)
            
            # Проверяем результат
            self.assertIn(label, self.ai.classes)
            self.assertIsInstance(confidence, float)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
        finally:
            # Удаляем временный файл
            if os.path.exists(test_image_path):
                os.remove(test_image_path)
    
    def test_predict_with_metadata(self):
        """Тест предсказания с метаданными"""
        # Создаем тестовое изображение
        image = Image.new('RGB', (128, 128), color='green')
        
        # Создаем тестовые характеристики сигнала
        signal_characteristics = {
            'rms': 0.15,
            'crest_factor': 8.2,
            'dominant_frequency': 1500.0
        }
        
        # Получаем предсказание с метаданными
        result = self.ai.predict_with_metadata(image, signal_characteristics)
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('timestamp', result)
        self.assertIn('model_info', result)
        self.assertIn('signal_analysis', result)
        
        # Проверяем содержимое
        self.assertIn(result['prediction'], self.ai.classes)
        self.assertIsInstance(result['confidence'], float)
        self.assertIsInstance(result['timestamp'], str)
        self.assertIsInstance(result['model_info'], dict)
        self.assertEqual(result['signal_analysis'], signal_characteristics)
    
    def test_predict_with_metadata_no_signal(self):
        """Тест предсказания с метаданными без характеристик сигнала"""
        # Создаем тестовое изображение
        image = Image.new('RGB', (128, 128), color='yellow')
        
        # Получаем предсказание без характеристик сигнала
        result = self.ai.predict_with_metadata(image)
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('timestamp', result)
        self.assertIn('model_info', result)
        self.assertIn('signal_analysis', result)
        
        # signal_analysis должно быть пустым
        self.assertEqual(result['signal_analysis'], {})
    
    def test_get_timestamp(self):
        """Тест получения временной метки"""
        timestamp = self.ai._get_timestamp()
        self.assertIsInstance(timestamp, str)
        # Проверяем формат ISO 8601 (простая проверка)
        self.assertIn('T', timestamp)
        self.assertIn(':', timestamp)
    
    def test_model_info_structure(self):
        """Тест структуры информации о модели"""
        image = Image.new('RGB', (128, 128), color='purple')
        result = self.ai.predict_with_metadata(image)
        
        model_info = result['model_info']
        self.assertIn('architecture', model_info)
        self.assertIn('classes', model_info)
        self.assertIn('input_size', model_info)
        
        self.assertEqual(model_info['architecture'], 'ResNet18')
        self.assertEqual(model_info['classes'], self.ai.classes)
        self.assertEqual(model_info['input_size'], (128, 128, 3))

class TestRadarSignalClassifier(unittest.TestCase):
    """Тесты для класса RadarSignalClassifier"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем мок-модель
        self.mock_model_path = self._create_mock_model()
        self.classifier = RadarSignalClassifier(model_path=self.mock_model_path)
    
    def _create_mock_model(self):
        """Создает мок-модель для тестов"""
        import torch.nn as nn
        
        # Создаем точно такую же архитектуру как в model_engine.py
        from torchvision import models
        model = models.resnet18()
        model.fc = nn.Linear(model.fc.in_features, 4)  # 4 класса: airplane, bird, drone, helicopter
        
        # Устанавливаем модель в режим eval
        model.eval()
        
        # Сохраняем state_dict
        model_path = "test_mock_model_classifier.pth"
        torch.save(model.state_dict(), model_path)
        return model_path
    
    def tearDown(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.mock_model_path):
            os.remove(self.mock_model_path)
    
    def test_init(self):
        """Тест инициализации"""
        self.assertIsInstance(self.classifier.ai_model, RadarAI)
        self.assertEqual(self.classifier.confidence_threshold, 0.5)
    
    def test_classify_signal(self):
        """Тест классификации сигнала"""
        # Создаем тестовое изображение
        image = Image.new('RGB', (128, 128), color='red')
        
        # Создаем тестовые характеристики сигнала
        signal_characteristics = {
            'rms': 0.15,
            'crest_factor': 8.2,
            'dominant_frequency': 1500.0
        }
        
        # Классифицируем сигнал
        result = self.classifier.classify_signal(image, signal_characteristics)
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('timestamp', result)
        self.assertIn('model_info', result)
        self.assertIn('signal_analysis', result)
        self.assertIn('risk_assessment', result)
        self.assertIn('signal_quality', result)
        self.assertIn('is_reliable', result)
        
        # Проверяем значения
        self.assertIn(result['prediction'], self.classifier.ai_model.classes)
        self.assertIsInstance(result['confidence'], float)
        self.assertIsInstance(result['is_reliable'], bool)
        self.assertIsInstance(result['risk_assessment'], str)
        self.assertIsInstance(result['signal_quality'], str)
    
    def test_classify_signal_no_characteristics(self):
        """Тест классификации сигнала без характеристик"""
        # Создаем тестовое изображение
        image = Image.new('RGB', (128, 128), color='blue')
        
        # Классифицируем сигнал без характеристик
        result = self.classifier.classify_signal(image)
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('is_reliable', result)
        
        # risk_assessment и signal_quality должны быть 'unknown'
        self.assertEqual(result['risk_assessment'], 'unknown')
        self.assertEqual(result['signal_quality'], 'unknown')
    
    def test_assess_risk(self):
        """Тест оценки риска"""
        test_cases = [
            ('drone', {'crest_factor': 5.0}, 'high'),
            ('helicopter', {'crest_factor': 5.0}, 'medium'),
            ('airplane', {'crest_factor': 5.0}, 'low'),
            ('bird', {'crest_factor': 5.0}, 'very_low'),
            ('airplane', {'crest_factor': 15.0}, 'medium'),  # Высокий crest_factor
            ('bird', {'crest_factor': 15.0}, 'medium'),      # Высокий crest_factor
        ]
        
        for prediction, characteristics, expected_risk in test_cases:
            with self.subTest(prediction=prediction, characteristics=characteristics):
                risk = self.classifier._assess_risk(prediction, characteristics)
                self.assertEqual(risk, expected_risk)
    
    def test_assess_signal_quality(self):
        """Тест оценки качества сигнала"""
        test_cases = [
            ({'rms': 0.15, 'crest_factor': 15.0}, 'excellent'),
            ({'rms': 0.08, 'crest_factor': 25.0}, 'good'),
            ({'rms': 0.03, 'crest_factor': 35.0}, 'fair'),
            ({'rms': 0.005, 'crest_factor': 40.0}, 'poor'),
        ]
        
        for characteristics, expected_quality in test_cases:
            with self.subTest(characteristics=characteristics):
                quality = self.classifier._assess_signal_quality(characteristics)
                self.assertEqual(quality, expected_quality)
    
    def test_is_reliable_threshold(self):
        """Тест порога достоверности"""
        # Создаем изображение
        image = Image.new('RGB', (128, 128), color='green')
        
        # Мокаем predict_with_metadata для возврата разных значений confidence
        with patch.object(self.classifier.ai_model, 'predict_with_metadata') as mock_predict:
            # Тест с высоким confidence
            mock_predict.return_value = {
                'prediction': 'drone',
                'confidence': 0.8,
                'timestamp': '2023-12-01T10:00:00',
                'model_info': {},
                'signal_analysis': {}
            }
            
            result = self.classifier.classify_signal(image)
            self.assertTrue(result['is_reliable'])
            
            # Тест с низким confidence
            mock_predict.return_value = {
                'prediction': 'drone',
                'confidence': 0.3,
                'timestamp': '2023-12-01T10:00:00',
                'model_info': {},
                'signal_analysis': {}
            }
            
            result = self.classifier.classify_signal(image)
            self.assertFalse(result['is_reliable'])

class TestModelEngineIntegration(unittest.TestCase):
    """Интеграционные тесты для model_engine"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.mock_model_path = self._create_mock_model()
        self.ai = RadarAI(model_path=self.mock_model_path)
        self.classifier = RadarSignalClassifier(model_path=self.mock_model_path)
    
    def _create_mock_model(self):
        """Создает мок-модель для тестов"""
        import torch.nn as nn
        
        # Создаем точно такую же архитектуру как в model_engine.py
        from torchvision import models
        model = models.resnet18()
        model.fc = nn.Linear(model.fc.in_features, 4)  # 4 класса: airplane, bird, drone, helicopter
        
        # Устанавливаем модель в режим eval
        model.eval()
        
        # Сохраняем state_dict
        model_path = "test_mock_model_integration.pth"
        torch.save(model.state_dict(), model_path)
        return model_path
    
    def tearDown(self):
        """Очистка после каждого тестом"""
        if os.path.exists(self.mock_model_path):
            os.remove(self.mock_model_path)
    
    def test_full_classification_pipeline(self):
        """Тест полного конвейера классификации"""
        # Создаем тестовое изображение
        image = Image.new('RGB', (128, 128), color='red')
        
        # Создаем характеристики сигнала
        signal_characteristics = {
            'rms': 0.12,
            'crest_factor': 7.5,
            'dominant_frequency': 1200.0
        }
        
        # Выполняем полную классификацию
        result = self.classifier.classify_signal(image, signal_characteristics)
        
        # Проверяем все компоненты результата
        required_keys = [
            'prediction', 'confidence', 'timestamp', 'model_info',
            'signal_analysis', 'risk_assessment', 'signal_quality', 'is_reliable'
        ]
        
        for key in required_keys:
            self.assertIn(key, result)
        
        # Проверяем согласованность данных
        self.assertEqual(result['signal_analysis'], signal_characteristics)
        self.assertIn(result['prediction'], self.ai.classes)
        self.assertIsInstance(result['confidence'], float)
        
        # Проверяем, что risk_assessment и signal_quality соответствуют характеристикам
        self.assertIn(result['risk_assessment'], ['high', 'medium', 'low', 'very_low'])
        self.assertIn(result['signal_quality'], ['excellent', 'good', 'fair', 'poor'])
    
    def test_different_image_sizes(self):
        """Тест классификации изображений разных размеров"""
        test_sizes = [(64, 64), (128, 128), (256, 256), (512, 512)]
        
        for size in test_sizes:
            with self.subTest(size=size):
                image = Image.new('RGB', size, color='blue')
                
                # Должно работать без ошибок
                label, confidence = self.ai.predict_from_image(image)
                
                self.assertIn(label, self.ai.classes)
                self.assertIsInstance(confidence, float)
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)

if __name__ == '__main__':
    unittest.main()
