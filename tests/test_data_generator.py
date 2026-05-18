import numpy as np
import os
from pathlib import Path
import json
from datetime import datetime

class TestDataGenerator:
    """Генератор тестовых данных для системы распознавания"""
    
    def __init__(self, output_dir="test_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.signals_dir = self.output_dir / "signals"
        self.images_dir = self.output_dir / "images"
        self.json_dir = self.output_dir / "json"
        
        for dir_path in [self.signals_dir, self.images_dir, self.json_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def generate_test_signals(self):
        """Генерирует тестовые радиосигналы для каждого класса"""
        sample_rate = 44100
        duration = 0.1
        
        # Характеристики сигналов для разных классов
        signal_params = {
            'airplane': {
                'frequencies': [800, 1200, 1600],
                'amplitudes': [0.8, 0.6, 0.4],
                'noise_level': 0.05
            },
            'bird': {
                'frequencies': [2000, 2500],
                'amplitudes': [0.3, 0.2],
                'noise_level': 0.15
            },
            'drone': {
                'frequencies': [500, 1000, 3000],
                'amplitudes': [0.9, 0.7, 0.5],
                'noise_level': 0.03
            },
            'helicopter': {
                'frequencies': [150, 300, 600],
                'amplitudes': [1.0, 0.8, 0.6],
                'noise_level': 0.08
            }
        }
        
        generated_files = {}
        
        for class_name, params in signal_params.items():
            class_dir = self.signals_dir / class_name
            class_dir.mkdir(exist_ok=True)
            
            for i in range(5):  # 5 сигналов на класс
                signal_data = self._generate_signal(
                    sample_rate, duration, 
                    params['frequencies'], 
                    params['amplitudes'],
                    params['noise_level']
                )
                
                filename = f"{class_name}_{i+1}.npy"
                filepath = class_dir / filename
                np.save(filepath, signal_data)
                
                if class_name not in generated_files:
                    generated_files[class_name] = []
                generated_files[class_name].append(str(filepath))
        
        return generated_files
    
    def _generate_signal(self, sample_rate, duration, frequencies, amplitudes, noise_level):
        """Генерирует синтетический сигнал"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        signal = np.zeros_like(t)
        
        # Добавляем синусоидальные компоненты
        for freq, amp in zip(frequencies, amplitudes):
            signal += amp * np.sin(2 * np.pi * freq * t)
        
        # Добавляем шум
        noise = np.random.normal(0, noise_level, len(t))
        signal += noise
        
        return signal
    
    def generate_test_images(self):
        """Генерирует тестовые изображения (заглушки)"""
        from PIL import Image
        
        image_classes = ['airplane', 'bird', 'drone', 'helicopter']
        generated_files = {}
        
        for class_name in image_classes:
            class_dir = self.images_dir / class_name
            class_dir.mkdir(exist_ok=True)
            
            for i in range(3):  # 3 изображения на класс
                # Создаем простое тестовое изображение с разными цветами для классов
                if class_name == 'airplane':
                    color = (255, 0, 0)  # Красный
                elif class_name == 'bird':
                    color = (0, 255, 0)  # Зеленый
                elif class_name == 'drone':
                    color = (0, 0, 255)  # Синий
                else:  # helicopter
                    color = (255, 255, 0)  # Желтый
                
                img_array = np.full((128, 128, 3), color, dtype=np.uint8)
                # Добавляем немного шума для разнообразия
                noise = np.random.randint(-20, 20, (128, 128, 3), dtype=np.int16)
                img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                
                img = Image.fromarray(img_array)
                
                filename = f"{class_name}_{i+1}.png"
                filepath = class_dir / filename
                img.save(filepath)
                
                if class_name not in generated_files:
                    generated_files[class_name] = []
                generated_files[class_name].append(str(filepath))
        
        return generated_files
    
    def generate_test_json_results(self):
        """Генерирует тестовые JSON результаты"""
        test_results = []
        
        # Примеры результатов для каждого класса
        test_cases = [
            {
                "detection_id": "TEST_001",
                "timestamp": "2023-12-01T10:00:00",
                "object_info": {
                    "type": "drone",
                    "confidence": 0.85,
                    "is_reliable": True
                },
                "location": {
                    "azimuth": 45.5,
                    "range": 5000,
                    "altitude": 1500
                },
                "signal_analysis": {
                    "rms": 0.15,
                    "crest_factor": 8.2,
                    "dominant_frequency": 1500.0
                },
                "risk_assessment": "high",
                "signal_quality": "excellent"
            },
            {
                "detection_id": "TEST_002",
                "timestamp": "2023-12-01T10:01:00",
                "object_info": {
                    "type": "airplane",
                    "confidence": 0.92,
                    "is_reliable": True
                },
                "location": {
                    "azimuth": 120.0,
                    "range": 8000,
                    "altitude": 10000
                },
                "signal_analysis": {
                    "rms": 0.25,
                    "crest_factor": 6.5,
                    "dominant_frequency": 1200.0
                },
                "risk_assessment": "low",
                "signal_quality": "excellent"
            },
            {
                "detection_id": "TEST_003",
                "timestamp": "2023-12-01T10:02:00",
                "object_info": {
                    "type": "bird",
                    "confidence": 0.67,
                    "is_reliable": True
                },
                "location": {
                    "azimuth": 200.3,
                    "range": 1500,
                    "altitude": 300
                },
                "signal_analysis": {
                    "rms": 0.08,
                    "crest_factor": 12.0,
                    "dominant_frequency": 2500.0
                },
                "risk_assessment": "very_low",
                "signal_quality": "good"
            }
        ]
        
        # Сохраняем отдельные результаты
        for i, result in enumerate(test_cases):
            filename = f"test_result_{i+1}.json"
            filepath = self.json_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            test_results.append(str(filepath))
        
        # Сохраняем пакетный результат
        batch_data = {
            "session_id": "TEST_SESSION_001",
            "session_start": "2023-12-01T10:00:00",
            "total_detections": len(test_cases),
            "detections": test_cases,
            "summary": {
                "object_distribution": {
                    "drone": 1,
                    "airplane": 1,
                    "bird": 1
                },
                "average_confidence": 0.813,
                "reliable_detections": 3,
                "reliability_rate": 1.0,
                "most_common_object": "drone"
            }
        }
        
        batch_filename = "test_batch_result.json"
        batch_filepath = self.json_dir / batch_filename
        with open(batch_filepath, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        test_results.append(str(batch_filepath))
        
        return test_results
    
    def create_mock_model(self):
        """Создает мок-модель для тестов"""
        import torch
        import torch.nn as nn
        
        # Создаем простую модель
        class MockModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc = nn.Linear(512, 4)  # 4 класса
            
            def forward(self, x):
                batch_size = x.size(0)
                # Возвращаем случайные логиты
                return torch.randn(batch_size, 4)
        
        model = MockModel()
        model_path = self.output_dir / "mock_model.pth"
        torch.save(model.state_dict(), model_path)
        
        return str(model_path)
    
    def generate_all_test_data(self):
        """Генерирует все тестовые данные"""
        print("🔄 Генерация тестовых данных...")
        
        print("  📡 Генерация тестовых сигналов...")
        signal_files = self.generate_test_signals()
        
        print("  🖼️ Генерация тестовых изображений...")
        image_files = self.generate_test_images()
        
        print("  📄 Генерация тестовых JSON...")
        json_files = self.generate_test_json_results()
        
        print("  🤖 Создание мок-модели...")
        model_file = self.create_mock_model()
        
        print("✅ Тестовые данные сгенерированы!")
        return {
            'signals': signal_files,
            'images': image_files,
            'json': json_files,
            'model': model_file,
            'base_dir': str(self.output_dir)
        }

if __name__ == "__main__":
    generator = TestDataGenerator()
    test_data = generator.generate_all_test_data()
    print(f"\n📁 Тестовые данные созданы в: {test_data['base_dir']}")
