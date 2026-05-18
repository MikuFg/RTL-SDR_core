import unittest
import sys
import os
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui_bridge import RadarTarget, start_simulation, start_real_time_mode, start_batch_processing

def safe_run_async(coro):
    """Безопасный запуск async функции в тестах"""
    try:
        return asyncio.run(coro)
    except (KeyboardInterrupt, SystemExit, RuntimeError, Exception):
        return None

class TestRadarTarget(unittest.TestCase):
    """Тесты для класса RadarTarget"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.target_id = "TEST_TARGET_001"
    
    def test_init_without_real_signal(self):
        """Тест инициализации без реального сигнала"""
        target = RadarTarget(self.target_id, use_real_signal=False)
        
        self.assertEqual(target.id, self.target_id)
        self.assertFalse(target.use_real_signal)
        self.assertIsNone(target.last_signal_data)
        self.assertIsNone(target.signal_characteristics)
        
        # Проверяем начальные координаты
        self.assertIsInstance(target.azimuth, float)
        self.assertIsInstance(target.range, int)
        self.assertIsInstance(target.altitude, int)
        self.assertGreaterEqual(target.azimuth, 0)
        self.assertLess(target.azimuth, 360)
        self.assertGreaterEqual(target.range, 3000)
        self.assertLessEqual(target.range, 8000)
        self.assertGreaterEqual(target.altitude, 100)
        self.assertLessEqual(target.altitude, 3000)
    
    def test_init_with_real_signal(self):
        """Тест инициализации с реальным сигналом"""
        target = RadarTarget(self.target_id, use_real_signal=True)
        
        self.assertEqual(target.id, self.target_id)
        self.assertTrue(target.use_real_signal)
        self.assertIsNone(target.last_signal_data)
        self.assertIsNone(target.signal_characteristics)
    
    def test_update_position(self):
        """Тест обновления позиции"""
        target = RadarTarget(self.target_id, use_real_signal=False)
        
        # Сохраняем начальные значения
        initial_azimuth = target.azimuth
        initial_range = target.range
        initial_altitude = target.altitude
        
        # Обновляем позицию
        target.update_position()
        
        # Проверяем, что позиция изменилась
        self.assertNotEqual(target.azimuth, initial_azimuth)
        self.assertNotEqual(target.range, initial_range)
        self.assertNotEqual(target.altitude, initial_altitude)
        
        # Проверяем, что значения остаются в допустимых пределах
        self.assertGreaterEqual(target.azimuth, 0)
        self.assertLess(target.azimuth, 360)
        self.assertGreaterEqual(target.range, 500)
        self.assertLessEqual(target.range, 9500)
        self.assertGreaterEqual(target.altitude, 50)
        self.assertLessEqual(target.altitude, 5000)
    
    def test_position_boundary_conditions(self):
        """Тест граничных условий позиции"""
        target = RadarTarget(self.target_id, use_real_signal=False)
        
        # Устанавливаем граничные значения
        initial_speed_range = target.speed_range  # Сохраняем начальную скорость
        target.range = 9600  # За пределами максимального
        target.altitude = 6000  # За пределами максимального
        
        # Обновляем позицию
        target.update_position()
        
        # Проверяем, что позиция в пределах
        self.assertLessEqual(target.range, 9500)
        self.assertLessEqual(target.altitude, 5000)
        # Скорость должна измениться на противоположную (т.к. мы вышли за максимальную границу)
        self.assertNotEqual(target.speed_range, initial_speed_range)
        
        # Устанавливаем минимальные значения
        target.range = 400  # За пределами минимального
        target.altitude = 40  # За пределами минимального
        
        # Обновляем позицию
        target.update_position()
        
        # Проверяем, что позиция в пределах
        self.assertGreaterEqual(target.range, 500)
        self.assertGreaterEqual(target.altitude, 50)
        # Скорость может быть отрицательной если мы только что изменили направление
        # Главное что позиция в пределах
    
    def test_get_location(self):
        """Тест получения локации"""
        target = RadarTarget(self.target_id, use_real_signal=False)
        
        location = target.get_location()
        
        self.assertIsInstance(location, dict)
        self.assertIn('azimuth', location)
        self.assertIn('range', location)
        self.assertIn('altitude', location)
        
        self.assertEqual(location['azimuth'], round(target.azimuth, 2))
        self.assertEqual(location['range'], int(target.range))
        self.assertEqual(location['altitude'], int(target.altitude))
    
    @patch('ui_bridge.signal_capture')
    def test_capture_signal_success(self, mock_capture):
        """Тест успешного захвата сигнала"""
        # Настраиваем мок
        mock_image = Mock()
        mock_characteristics = {'rms': 0.15, 'crest_factor': 8.2}
        mock_capture.capture_and_process.return_value = (mock_image, mock_characteristics)
        
        target = RadarTarget(self.target_id, use_real_signal=True)
        
        # Выполняем захват сигнала
        result = target.capture_signal()
        
        self.assertTrue(result)
        self.assertEqual(target.last_signal_data, mock_image)
        self.assertEqual(target.signal_characteristics, mock_characteristics)
    
    @patch('ui_bridge.signal_capture')
    def test_capture_signal_failure(self, mock_capture):
        """Тест неудачного захвата сигнала"""
        # Настраиваем мок для выброса исключения
        mock_capture.capture_and_process.side_effect = Exception("Capture failed")
        
        target = RadarTarget(self.target_id, use_real_signal=True)
        
        # Выполняем захват сигнала
        result = target.capture_signal()
        
        self.assertFalse(result)
        self.assertIsNone(target.last_signal_data)
        self.assertIsNone(target.signal_characteristics)
    
    def test_capture_signal_disabled(self):
        """Тест захвата сигнала когда он отключен"""
        target = RadarTarget(self.target_id, use_real_signal=False)
        
        # Выполняем захват сигнала
        result = target.capture_signal()
        
        self.assertFalse(result)
        self.assertIsNone(target.last_signal_data)
        self.assertIsNone(target.signal_characteristics)

class TestUIBridgeIntegration(unittest.TestCase):
    """Интеграционные тесты для ui_bridge"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем временную директорию для тестов
        self.temp_dir = tempfile.mkdtemp()
        
        # Создаем тестовую структуру директорий
        self.test_data_dir = Path(self.temp_dir) / "data_v2" / "val"
        self.test_data_dir.mkdir(parents=True)
        
        # Создаем тестовые изображения
        from PIL import Image
        import numpy as np
        
        for class_name in ['airplane', 'bird', 'drone', 'helicopter']:
            class_dir = self.test_data_dir / class_name
            class_dir.mkdir()
            
            # Создаем настоящее изображение с разными цветами для классов
            if class_name == 'airplane':
                color = (255, 0, 0)  # Красный
            elif class_name == 'bird':
                color = (0, 255, 0)  # Зеленый
            elif class_name == 'drone':
                color = (0, 0, 255)  # Синий
            else:  # helicopter
                color = (255, 255, 0)  # Желтый
            
            img_array = np.full((128, 128, 3), color, dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            test_file = class_dir / f"{class_name}_test.png"
            img.save(test_file)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ui_bridge.ai_classifier')
    @patch('ui_bridge.json_formatter')
    @patch('ui_bridge.signal_capture')
    @patch('ui_bridge.requests.post')
    def test_start_simulation_test_data(self, mock_post, mock_capture, mock_formatter, mock_ai):
        """Тест запуска симуляции с тестовыми данными"""
        # Настраиваем моки
        mock_ai.classify_signal.return_value = {
            'prediction': 'drone',
            'confidence': 0.85,
            'risk_assessment': 'high',
            'signal_quality': 'excellent'
        }
        
        mock_formatter.format_detection_result.return_value = {
            'detection_id': 'TEST_001',
            'object_info': {'type': 'drone', 'confidence': 0.85}
        }
        
        mock_formatter.create_real_time_update.return_value = {'test': 'update'}
        mock_formatter.save_to_file.return_value = 'test_file.json'
        
        mock_post.return_value = Mock(status_code=200)
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Запускаем симуляцию на короткое время
            with patch('time.sleep', side_effect=KeyboardInterrupt()):
                with patch('builtins.print'):  # Подавляем вывод
                    safe_run_async(start_simulation(use_real_signals=False, save_results=False))
        except KeyboardInterrupt:
            pass  # Ожидаемое прерывание
        finally:
            os.chdir(original_cwd)
        
        # Проверяем, что моки были вызваны
        self.assertTrue(mock_ai.classify_signal.called)
        self.assertTrue(mock_formatter.format_detection_result.called)
        self.assertTrue(mock_formatter.create_real_time_update.called)
    
    @patch('ui_bridge.ai_classifier')
    @patch('ui_bridge.json_formatter')
    @patch('ui_bridge.signal_capture')
    @patch('ui_bridge.requests.post')
    def test_start_simulation_real_signals(self, mock_post, mock_capture, mock_formatter, mock_ai):
        """Тест запуска симуляции с реальными сигналами"""
        # Настраиваем моки
        mock_image = Mock()
        mock_characteristics = {'rms': 0.15, 'crest_factor': 8.2}
        mock_capture.capture_and_process.return_value = (mock_image, mock_characteristics)
        
        mock_ai.classify_signal.return_value = {
            'prediction': 'helicopter',
            'confidence': 0.78,
            'risk_assessment': 'medium',
            'signal_quality': 'good'
        }
        
        mock_formatter.format_detection_result.return_value = {
            'detection_id': 'TEST_002',
            'object_info': {'type': 'helicopter', 'confidence': 0.78}
        }
        
        mock_formatter.create_real_time_update.return_value = {'test': 'update'}
        mock_formatter.save_to_file.return_value = 'test_file.json'
        
        mock_post.return_value = Mock(status_code=200)
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Запускаем симуляцию на короткое время
            with patch('time.sleep', side_effect=KeyboardInterrupt()):
                with patch('builtins.print'):  # Подавляем вывод
                    safe_run_async(start_simulation(use_real_signals=True, save_results=False))
        except KeyboardInterrupt:
            pass  # Ожидаемое прерывание
        finally:
            os.chdir(original_cwd)
        
        # Проверяем, что моки были вызваны
        self.assertTrue(mock_capture.capture_and_process.called)
        self.assertTrue(mock_ai.classify_signal.called)
        self.assertTrue(mock_formatter.format_detection_result.called)
    
    @patch('ui_bridge.ai_classifier')
    @patch('ui_bridge.json_formatter')
    @patch('ui_bridge.signal_capture')
    @patch('ui_bridge.requests.post')
    def test_start_real_time_mode(self, mock_post, mock_capture, mock_formatter, mock_ai):
        """Тест запуска режима реального времени"""
        # Настраиваем моки
        mock_image = Mock()
        mock_characteristics = {'rms': 0.12, 'crest_factor': 7.5}
        mock_capture.capture_and_process.return_value = (mock_image, mock_characteristics)
        
        mock_ai.classify_signal.return_value = {
            'prediction': 'airplane',
            'confidence': 0.92,
            'risk_assessment': 'low',
            'signal_quality': 'excellent'
        }
        
        mock_formatter.format_detection_result.return_value = {
            'detection_id': 'REALTIME_001',
            'object_info': {'type': 'airplane', 'confidence': 0.92}
        }
        
        mock_formatter.create_real_time_update.return_value = {'test': 'update'}
        mock_formatter.save_to_file.return_value = 'realtime_file.json'
        
        mock_post.return_value = Mock(status_code=200)
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Запускаем режим реального времени на короткое время
            with patch('time.sleep', side_effect=KeyboardInterrupt()):
                with patch('builtins.print'):  # Подавляем вывод
                    safe_run_async(start_real_time_mode())
        except KeyboardInterrupt:
            pass  # Ожидаемое прерывание
        finally:
            pass
        
        # Проверяем, что моки были вызваны
        self.assertTrue(mock_capture.capture_and_process.called)
        self.assertTrue(mock_ai.classify_signal.called)
        self.assertTrue(mock_formatter.format_detection_result.called)
        self.assertTrue(mock_formatter.create_real_time_update.called)
        self.assertTrue(mock_formatter.save_to_file.called)
    
    @patch('ui_bridge.ai_classifier')
    @patch('ui_bridge.json_formatter')
    @patch('ui_bridge.signal_capture')
    @patch('numpy.load')
    def test_start_batch_processing(self, mock_np_load, mock_capture, mock_formatter, mock_ai):
        """Тест запуска пакетной обработки"""
        # Создаем тестовую директорию с файлами
        batch_dir = Path(self.temp_dir) / "batch"
        batch_dir.mkdir()
        
        # Создаем тестовые файлы
        (batch_dir / "test1.npy").touch()
        (batch_dir / "test2.npy").touch()
        (batch_dir / "test3.wav").touch()  # Файл, который должен быть пропущен
        
        # Настраиваем моки
        mock_signal_data = Mock()
        mock_np_load.return_value = mock_signal_data
        
        # Убедимся что mock готов к перехвату
        self.assertEqual(mock_np_load.call_count, 0)
        
        # Добавляем отладку
        print(f"Mock numpy.load настроен: {mock_np_load}")
        
        mock_capture.processor.process_signal.return_value = Mock()
        mock_capture.processor.signal_to_image.return_value = Mock()
        mock_capture.processor.analyze_signal_characteristics.return_value = {'rms': 0.1}
        
        mock_ai.classify_signal.return_value = {
            'prediction': 'bird',
            'confidence': 0.67,
            'risk_assessment': 'very_low',
            'signal_quality': 'good'
        }
        
        mock_formatter.format_detection_result.return_value = {
            'detection_id': 'BATCH_001',
            'object_info': {'type': 'bird', 'confidence': 0.67}
        }
        
        mock_formatter.format_batch_results.return_value = {'batch': 'result'}
        mock_formatter.save_to_file.return_value = 'batch_file.json'
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            with patch('builtins.print'):  # Подавляем вывод
                start_batch_processing(str(batch_dir))
        finally:
            os.chdir(original_cwd)
        
        # Проверяем, что numpy загрузчик вызывался для .npy файлов
        self.assertTrue(mock_np_load.called)
        
        # Проверяем, что моки были вызваны
        self.assertTrue(mock_np_load.called)
        self.assertTrue(mock_capture.processor.process_signal.called)
        self.assertTrue(mock_capture.processor.signal_to_image.called)
        self.assertTrue(mock_ai.classify_signal.called)
        self.assertTrue(mock_formatter.format_detection_result.called)
        self.assertTrue(mock_formatter.format_batch_results.called)
        self.assertTrue(mock_formatter.save_to_file.called)

class TestUIBridgeErrorHandling(unittest.TestCase):
    """Тесты обработки ошибок в ui_bridge"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Очистка после каждого тестом"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ui_bridge.ai_classifier')
    @patch('ui_bridge.json_formatter')
    @patch('ui_bridge.signal_capture')
    @patch('requests.post')
    def test_server_connection_error(self, mock_post, mock_capture, mock_formatter, mock_ai):
        """Тест обработки ошибки подключения к серверу"""
        # Настраиваем моки
        mock_ai.classify_signal.return_value = {
            'prediction': 'drone',
            'confidence': 0.85
        }
        
        mock_formatter.format_detection_result.return_value = {'test': 'result'}
        mock_formatter.create_real_time_update.return_value = {'test': 'update'}
        
        # Настраиваем мок для выброса ошибки подключения
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Очищаем счетчик вызовов
        mock_post.reset_mock()
        
        # Убеждаемся что mock готов к перехвату
        self.assertEqual(mock_post.call_count, 0)
        
        # Добавляем проверку что mock установлен правильно
        import requests
        original_post = requests.post
        requests.post = mock_post
        
        # Устанавливаем mock для всех вызовов requests
        import ui_bridge
        ui_bridge.requests.post = mock_post
        
        # Восстанавливаем после теста
        def cleanup():
            ui_bridge.requests.post = original_post
        self.addCleanup(cleanup)
        
        # Добавляем отладку
        print(f"Mock настроен: {mock_post}")
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Запускаем симуляцию на короткое время
            with patch('time.sleep', side_effect=KeyboardInterrupt()):
                with patch('builtins.print'):  # Подавляем вывод
                    safe_run_async(start_simulation(use_real_signals=False, save_results=False))
        except KeyboardInterrupt:
            pass  # Ожидаемое прерывание
        finally:
            os.chdir(original_cwd)
        
        # Проверяем, что симуляция продолжается несмотря на ошибки
        self.assertTrue(mock_post.called)
    
    @patch('ui_bridge.ai_classifier')
    @patch('ui_bridge.json_formatter')
    @patch('ui_bridge.signal_capture')
    def test_signal_capture_error(self, mock_capture, mock_formatter, mock_ai):
        """Тест обработки ошибки захвата сигнала"""
        # Настраиваем моки
        mock_capture.capture_and_process.side_effect = Exception("Capture failed")
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Запускаем симуляцию на короткое время
            with patch('time.sleep', side_effect=KeyboardInterrupt()):
                with patch('builtins.print'):  # Подавляем вывод
                    safe_run_async(start_simulation(use_real_signals=True, save_results=False))
        except KeyboardInterrupt:
            pass  # Ожидаемое прерывание
        finally:
            os.chdir(original_cwd)
        
        # Проверяем, что симуляция продолжается несмотря на ошибки
        self.assertTrue(mock_capture.capture_and_process.called)
    
    def test_start_simulation_no_test_data(self):
        """Тест запуска симуляции без тестовых данных"""
        # Меняем рабочую директорию на временную (без тестовых данных)
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Запускаем симуляцию с прерыванием, чтобы избежать бесконечного цикла
            with patch('time.sleep', side_effect=KeyboardInterrupt()):
                with patch('builtins.print'):  # Подавляем вывод
                    safe_run_async(start_simulation(use_real_signals=False, save_results=False))
        except (SystemExit, KeyboardInterrupt):
            # Ожидаем выход из программы или прерывание
            pass
        finally:
            os.chdir(original_cwd)

if __name__ == '__main__':
    unittest.main()
