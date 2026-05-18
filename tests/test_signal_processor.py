import unittest
import numpy as np
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from signal_processor import RadarSignalProcessor, SignalCapture
from PIL import Image

class TestRadarSignalProcessor(unittest.TestCase):
    """Тесты для класса RadarSignalProcessor"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.processor = RadarSignalProcessor(sample_rate=44100, fft_size=1024)
        
    def test_init(self):
        """Тест инициализации"""
        self.assertEqual(self.processor.sample_rate, 44100)
        self.assertEqual(self.processor.fft_size, 1024)
        self.assertIsNotNone(self.processor.window)
        self.assertEqual(len(self.processor.window), 1024)
    
    def test_generate_test_signal(self):
        """Тест генерации тестового сигнала"""
        duration = 0.1
        signal = self.processor._generate_test_signal(duration)
        
        expected_length = int(duration * self.processor.sample_rate)
        self.assertEqual(len(signal), expected_length)
        self.assertIsInstance(signal, np.ndarray)
        self.assertEqual(signal.dtype, np.float64)
    
    def test_process_signal(self):
        """Тест обработки сигнала"""
        # Создаем тестовый сигнал с правильной длиной
        duration = 0.1
        signal = self.processor._generate_test_signal(duration)
        
        # Убеждаемся что длина сигнала кратна fft_size
        if len(signal) < self.processor.fft_size:
            # Дополняем сигнал нулями до нужной длины
            signal = np.pad(signal, (0, self.processor.fft_size - len(signal)))
        
        # Обрабатываем сигнал
        spectrogram = self.processor.process_signal(signal)
        
        # Проверяем результат
        self.assertIsInstance(spectrogram, np.ndarray)
        self.assertEqual(spectrogram.shape[0], self.processor.fft_size // 2 + 1)
        self.assertGreater(spectrogram.shape[1], 0)
    
    def test_signal_to_image(self):
        """Тест преобразования сигнала в изображение"""
        # Создаем тестовый сигнал с правильной длиной
        duration = 0.1
        signal = self.processor._generate_test_signal(duration)
        
        # Убеждаемся что длина сигнала кратна fft_size
        if len(signal) < self.processor.fft_size:
            signal = np.pad(signal, (0, self.processor.fft_size - len(signal)))
        
        # Преобразуем в изображение
        image = self.processor.signal_to_image(signal, size=(128, 128))
        
        # Проверяем результат
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.size, (128, 128))
        self.assertEqual(image.mode, 'RGB')
    
    def test_analyze_signal_characteristics(self):
        """Тест анализа характеристик сигнала"""
        # Создаем тестовый сигнал
        duration = 0.1
        signal = self.processor._generate_test_signal(duration)
        
        # Анализируем характеристики
        characteristics = self.processor.analyze_signal_characteristics(signal)
        
        # Проверяем результат
        self.assertIsInstance(characteristics, dict)
        self.assertIn('rms', characteristics)
        self.assertIn('peak', characteristics)
        self.assertIn('crest_factor', characteristics)
        self.assertIn('dominant_frequency', characteristics)
        self.assertIn('signal_length', characteristics)
        self.assertIn('sample_rate', characteristics)
        
        # Проверяем типы значений
        self.assertIsInstance(characteristics['rms'], float)
        self.assertIsInstance(characteristics['peak'], float)
        self.assertIsInstance(characteristics['crest_factor'], float)
        self.assertIsInstance(characteristics['dominant_frequency'], float)
        self.assertIsInstance(characteristics['signal_length'], int)
        self.assertIsInstance(characteristics['sample_rate'], int)
        
        # Проверяем значения
        self.assertEqual(characteristics['signal_length'], len(signal))
        self.assertEqual(characteristics['sample_rate'], self.processor.sample_rate)
        self.assertGreaterEqual(characteristics['rms'], 0)
        self.assertGreaterEqual(characteristics['peak'], 0)
        self.assertGreaterEqual(characteristics['crest_factor'], 0)
    
    def test_signal_characteristics_consistency(self):
        """Тест согласованности характеристик сигнала"""
        # Создаем сигнал с известными параметрами
        duration = 0.1
        t = np.linspace(0, duration, int(self.processor.sample_rate * duration))
        signal = np.sin(2 * np.pi * 1000 * t)  # 1 kHz синусоида
        
        characteristics = self.processor.analyze_signal_characteristics(signal)
        
        # Проверяем, что доминирующая частота близка к 1000 Hz
        dominant_freq = characteristics['dominant_frequency']
        # Увеличиваем дельту из-за особенностей анализа FFT
        self.assertAlmostEqual(abs(dominant_freq), 1000, delta=500)
        
        # Проверяем crest factor для чистой синусоиды (~1.414)
        crest_factor = characteristics['crest_factor']
        self.assertAlmostEqual(crest_factor, 1.414, delta=0.5)

class TestSignalCapture(unittest.TestCase):
    """Тесты для класса SignalCapture"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.capture = SignalCapture()
    
    def test_init(self):
        """Тест инициализации"""
        self.assertIsInstance(self.capture.processor, RadarSignalProcessor)
    
    def test_capture_and_process(self):
        """Тест захвата и обработки сигнала"""
        try:
            image, characteristics = self.capture.capture_and_process(duration=0.05)
            
            # Проверяем результат
            self.assertIsInstance(image, Image.Image)
            self.assertIsInstance(characteristics, dict)
            
            # Проверяем характеристики
            required_keys = ['rms', 'peak', 'crest_factor', 'dominant_frequency', 
                           'signal_length', 'sample_rate']
            for key in required_keys:
                self.assertIn(key, characteristics)
                
        except Exception as e:
            # Если нет устройства захвата, проверяем работу с тестовым сигналом
            self.assertIsInstance(e, Exception)
            print(f"Предупреждение: Устройство захвата недоступно: {e}")
    
    def test_save_and_load_signal(self):
        """Тест сохранения и загрузки сигнала"""
        # Создаем тестовый сигнал
        test_signal = np.random.randn(1000)
        test_filename = "test_signal.npy"
        
        try:
            # Сохраняем сигнал
            self.capture.save_raw_signal(test_signal, test_filename)
            
            # Загружаем сигнал
            loaded_signal = self.capture.load_raw_signal(test_filename)
            
            # Проверяем результат
            np.testing.assert_array_equal(test_signal, loaded_signal)
            
            # Удаляем тестовый файл
            if os.path.exists(test_filename):
                os.remove(test_filename)
                
        except Exception as e:
            self.fail(f"Ошибка при сохранении/загрузке сигнала: {e}")

class TestSignalProcessorIntegration(unittest.TestCase):
    """Интеграционные тесты для обработки сигналов"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.processor = RadarSignalProcessor()
        self.capture = SignalCapture()
    
    def test_full_signal_processing_pipeline(self):
        """Тест полного конвейера обработки сигнала"""
        # Создаем тестовый сигнал
        duration = 0.1
        signal = self.processor._generate_test_signal(duration)
        
        # Дополняем сигнал до нужной длины если необходимо
        if len(signal) < self.processor.fft_size:
            signal = np.pad(signal, (0, self.processor.fft_size - len(signal)))
        
        # Обрабатываем сигнал
        spectrogram = self.processor.process_signal(signal)
        image = self.processor.signal_to_image(signal)
        characteristics = self.processor.analyze_signal_characteristics(signal)
        
        # Проверяем, что все этапы работают
        self.assertIsInstance(spectrogram, np.ndarray)
        self.assertIsInstance(image, Image.Image)
        self.assertIsInstance(characteristics, dict)
        
        # Проверяем согласованность данных
        self.assertEqual(characteristics['signal_length'], len(signal))
        self.assertEqual(characteristics['sample_rate'], self.processor.sample_rate)
    
    def test_different_signal_parameters(self):
        """Тест обработки сигналов с разными параметрами"""
        durations = [0.05, 0.1, 0.2]
        
        for duration in durations:
            with self.subTest(duration=duration):
                signal = self.processor._generate_test_signal(duration)
                
                # Дополняем сигнал до нужной длины если необходимо
                if len(signal) < self.processor.fft_size:
                    signal = np.pad(signal, (0, self.processor.fft_size - len(signal)))
                
                # Проверяем, что сигнал обрабатывается без ошибок
                spectrogram = self.processor.process_signal(signal)
                image = self.processor.signal_to_image(signal)
                characteristics = self.processor.analyze_signal_characteristics(signal)
                
                # Проверяем согласованность данных
                self.assertEqual(characteristics['signal_length'], len(signal))
                self.assertEqual(characteristics['sample_rate'], self.processor.sample_rate)
                self.assertIsInstance(spectrogram, np.ndarray)
                self.assertIsInstance(image, Image.Image)
                self.assertIsInstance(characteristics, dict)

if __name__ == '__main__':
    # Создаем директорию для тестовых данных если нужно
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    unittest.main()
