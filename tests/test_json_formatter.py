import unittest
import json
import tempfile
import shutil
import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from json_formatter import RadarJSONFormatter, RadarReportGenerator

class TestRadarJSONFormatter(unittest.TestCase):
    """Тесты для класса RadarJSONFormatter"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем временную директорию для тестов
        self.temp_dir = tempfile.mkdtemp()
        self.formatter = RadarJSONFormatter(output_dir=self.temp_dir)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Удаляем временную директорию
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Тест инициализации"""
        self.assertTrue(self.formatter.output_dir.exists())
        self.assertEqual(self.formatter.output_dir.name, Path(self.temp_dir).name)
    
    def test_format_detection_result(self):
        """Тест форматирования результата обнаружения"""
        # Создаем тестовые данные
        detection_data = {
            'prediction': 'drone',
            'confidence': 0.85,
            'timestamp': '2023-12-01T10:00:00',
            'signal_analysis': {
                'rms': 0.15,
                'crest_factor': 8.2
            },
            'risk_assessment': 'high',
            'signal_quality': 'excellent'
        }
        
        target_id = "TEST_001"
        location = {
            "azimuth": 45.5,
            "range": 5000,
            "altitude": 1500
        }
        
        # Форматируем результат
        result = self.formatter.format_detection_result(
            detection_data, target_id, location
        )
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertEqual(result['detection_id'], target_id)
        self.assertEqual(result['object_info']['type'], 'drone')
        self.assertEqual(result['object_info']['confidence'], 0.85)
        self.assertEqual(result['location'], location)
        self.assertEqual(result['signal_analysis'], detection_data['signal_analysis'])
        self.assertEqual(result['risk_assessment'], 'high')
        self.assertEqual(result['signal_quality'], 'excellent')
    
    def test_format_detection_result_defaults(self):
        """Тест форматирования результата с параметрами по умолчанию"""
        detection_data = {
            'prediction': 'airplane',
            'confidence': 0.92
        }
        
        # Форматируем без target_id и location
        result = self.formatter.format_detection_result(detection_data)
        
        # Проверяем значения по умолчанию
        self.assertIn('detection_id', result)
        self.assertTrue(result['detection_id'].startswith('DET_'))
        self.assertEqual(result['location']['azimuth'], 0.0)
        self.assertEqual(result['location']['range'], 0.0)
        self.assertEqual(result['location']['altitude'], 0.0)
    
    def test_format_batch_results(self):
        """Тест форматирования пакетных результатов"""
        # Создаем тестовые обнаружения
        detections = [
            {
                'detection_id': 'TEST_001',
                'object_info': {'type': 'drone', 'confidence': 0.85, 'is_reliable': True},
                'location': {'azimuth': 45.5, 'range': 5000, 'altitude': 1500}
            },
            {
                'detection_id': 'TEST_002',
                'object_info': {'type': 'airplane', 'confidence': 0.92, 'is_reliable': True},
                'location': {'azimuth': 120.0, 'range': 8000, 'altitude': 10000}
            }
        ]
        
        session_id = "TEST_SESSION_001"
        
        # Форматируем пакетные результаты
        result = self.formatter.format_batch_results(detections, session_id)
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertEqual(result['session_id'], session_id)
        self.assertEqual(result['total_detections'], 2)
        self.assertEqual(len(result['detections']), 2)
        self.assertIn('summary', result)
        
        # Проверяем сводку
        summary = result['summary']
        self.assertIn('object_distribution', summary)
        self.assertIn('average_confidence', summary)
        self.assertIn('reliable_detections', summary)
        self.assertIn('reliability_rate', summary)
        self.assertIn('most_common_object', summary)
    
    def test_format_batch_results_empty(self):
        """Тест форматирования пустых результатов"""
        result = self.formatter.format_batch_results([])
        
        self.assertEqual(result['total_detections'], 0)
        self.assertEqual(len(result['detections']), 0)
        self.assertEqual(result['summary']['message'], 'No detections')
    
    def test_generate_summary(self):
        """Тест генерации сводки"""
        detections = [
            {
                'object_info': {'type': 'drone', 'confidence': 0.85, 'is_reliable': True},
                'location': {'azimuth': 45.5, 'range': 5000, 'altitude': 1500}
            },
            {
                'object_info': {'type': 'drone', 'confidence': 0.75, 'is_reliable': False},
                'location': {'azimuth': 50.0, 'range': 5500, 'altitude': 1600}
            },
            {
                'object_info': {'type': 'airplane', 'confidence': 0.92, 'is_reliable': True},
                'location': {'azimuth': 120.0, 'range': 8000, 'altitude': 10000}
            }
        ]
        
        summary = self.formatter._generate_summary(detections)
        
        # Проверяем распределение объектов
        self.assertEqual(summary['object_distribution']['drone'], 2)
        self.assertEqual(summary['object_distribution']['airplane'], 1)
        
        # Проверяем среднюю уверенность
        expected_avg = (0.85 + 0.75 + 0.92) / 3
        self.assertAlmostEqual(summary['average_confidence'], expected_avg, places=2)
        
        # Проверяем достоверные обнаружения
        self.assertEqual(summary['reliable_detections'], 2)
        self.assertAlmostEqual(summary['reliability_rate'], 2/3, places=2)
        
        # Проверяем самый распространенный объект
        self.assertEqual(summary['most_common_object'], 'drone')
    
    def test_save_to_file(self):
        """Тест сохранения в файл"""
        test_data = {
            'test_key': 'test_value',
            'timestamp': '2023-12-01T10:00:00'
        }
        
        # Сохраняем в файл
        filepath = self.formatter.save_to_file(test_data, "test_file.json")
        
        # Проверяем, что файл создан
        self.assertTrue(os.path.exists(filepath))
        
        # Проверяем содержимое файла
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_save_to_file_auto_filename(self):
        """Тест сохранения с автоматическим именем файла"""
        test_data = {'test': 'data'}
        
        # Сохраняем без указания имени файла
        filepath = self.formatter.save_to_file(test_data)
        
        # Проверяем, что файл создан и имеет правильное имя
        self.assertTrue(os.path.exists(filepath))
        filename = os.path.basename(filepath)
        self.assertTrue(filename.startswith('radar_detection_'))
        self.assertTrue(filename.endswith('.json'))
    
    def test_load_from_file(self):
        """Тест загрузки из файла"""
        test_data = {
            'test_key': 'test_value',
            'number': 42,
            'nested': {'inner': 'value'}
        }
        
        # Сначала сохраняем файл
        filename = "test_load.json"
        self.formatter.save_to_file(test_data, filename)
        
        # Затем загружаем его
        loaded_data = self.formatter.load_from_file(filename)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_create_real_time_update(self):
        """Тест создания обновления в реальном времени"""
        detection_data = {
            'prediction': 'helicopter',
            'confidence': 0.78,
            'risk_assessment': 'medium',
            'signal_quality': 'good'
        }
        
        target_id = "REALTIME_001"
        location = {
            "azimuth": 200.3,
            "range": 3000,
            "altitude": 800
        }
        
        # Создаем обновление
        update = self.formatter.create_real_time_update(
            detection_data, target_id, location
        )
        
        # Проверяем результат
        self.assertEqual(update['type'], 'real_time_update')
        self.assertEqual(update['target_id'], target_id)
        self.assertEqual(update['prediction'], 'helicopter')
        self.assertEqual(update['confidence'], 0.78)
        self.assertEqual(update['location'], location)
        self.assertEqual(update['risk_level'], 'medium')
        self.assertEqual(update['signal_quality'], 'good')
        self.assertIn('timestamp', update)
    
    def test_format_error_report(self):
        """Тест форматирования отчета об ошибке"""
        error_message = "Test error message"
        error_type = "processing_error"
        context = {'module': 'test_module', 'line': 42}
        
        # Форматируем отчет об ошибке
        error_report = self.formatter.format_error_report(
            error_message, error_type, context
        )
        
        # Проверяем результат
        self.assertEqual(error_report['type'], 'error_report')
        self.assertEqual(error_report['error_type'], error_type)
        self.assertEqual(error_report['error_message'], error_message)
        self.assertEqual(error_report['context'], context)
        self.assertIn('timestamp', error_report)
        self.assertIn('system_info', error_report)
    
    def test_get_latest_results(self):
        """Тест получения последних результатов"""
        # Создаем несколько тестовых файлов
        test_files = []
        for i in range(5):
            data = {'test': f'data_{i}', 'index': i}
            filename = f"test_file_{i}.json"
            filepath = self.formatter.save_to_file(data, filename)
            test_files.append(filepath)
        
        # Получаем последние результаты
        latest_files = self.formatter.get_latest_results(limit=3)
        
        # Проверяем результат
        self.assertEqual(len(latest_files), 3)
        
        # Проверяем, что файлы отсортированы по времени (новые первые)
        for filepath in latest_files:
            self.assertTrue(os.path.exists(filepath))
    
    def test_cleanup_old_files(self):
        """Тест очистки старых файлов"""
        # Создаем тестовый файл
        test_data = {'test': 'cleanup_test'}
        filepath = self.formatter.save_to_file(test_data, "old_file.json")
        
        # Проверяем, что файл существует
        self.assertTrue(os.path.exists(filepath))
        
        # Выполняем очистку (для файлов старше 0 дней)
        self.formatter.cleanup_old_files(days_old=0)
        
        # Проверяем, что файл удален
        self.assertFalse(os.path.exists(filepath))

class TestRadarReportGenerator(unittest.TestCase):
    """Тесты для класса RadarReportGenerator"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.formatter = RadarJSONFormatter(output_dir=self.temp_dir)
        self.report_generator = RadarReportGenerator(self.formatter)
    
    def tearDown(self):
        """Очистка после каждым тестом"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Тест инициализации"""
        self.assertIsInstance(self.report_generator.formatter, RadarJSONFormatter)
    
    def test_generate_daily_report(self):
        """Тест генерации дневного отчета"""
        # Создаем тестовые файлы за определенную дату
        test_date = "2023-12-01"
        
        # Создаем несколько сессий
        for i in range(3):
            session_data = {
                'session_id': f'SESSION_{i}',
                'session_start': f'{test_date}T10:{i:02d}:00',
                'total_detections': 2,
                'detections': [
                    {
                        'detection_id': f'DET_{i}_1',
                        'object_info': {'type': 'drone', 'confidence': 0.8, 'is_reliable': True},
                        'location': {'azimuth': 45.0, 'range': 5000, 'altitude': 1500}
                    },
                    {
                        'detection_id': f'DET_{i}_2',
                        'object_info': {'type': 'airplane', 'confidence': 0.9, 'is_reliable': True},
                        'location': {'azimuth': 120.0, 'range': 8000, 'altitude': 10000}
                    }
                ]
            }
            
            filename = f"radar_detection_{test_date.replace('-', '')}_session_{i}.json"
            filepath = self.formatter.save_to_file(session_data, filename)
            # Убедимся что файл создан
            self.assertTrue(os.path.exists(filepath))
            print(f"Создан файл: {filename}")
        
        # Файлы уже сохранены в output_dir через save_to_file
        # Проверяем что они действительно там
        files_in_dir = list(self.formatter.output_dir.glob("radar_detection_20231201_session_*.json"))
        self.assertEqual(len(files_in_dir), 3, f"Найдено файлов: {len(files_in_dir)}, ожидалось: 3")
        
        # Выводим все файлы в директории для отладки
        all_files = list(self.formatter.output_dir.glob("*.json"))
        print(f"Все JSON файлы в директории: {[f.name for f in all_files]}")
        
        # Генерируем дневной отчет
        report = self.report_generator.generate_daily_report(test_date)
        
        # Проверяем результат
        self.assertEqual(report['report_date'], test_date)
        self.assertEqual(report['report_type'], 'daily_summary')
        self.assertEqual(report['total_sessions'], 3)
        self.assertEqual(report['total_detections'], 6)
        self.assertIn('summary', report)
        self.assertIn('generated_at', report)
        
        # Проверяем сводку
        summary = report['summary']
        self.assertIn('object_distribution', summary)
        self.assertEqual(summary['object_distribution']['drone'], 3)
        self.assertEqual(summary['object_distribution']['airplane'], 3)
    
    def test_generate_daily_report_no_data(self):
        """Тест генерации отчета без данных"""
        test_date = "2023-12-01"
        
        report = self.report_generator.generate_daily_report(test_date)
        
        self.assertEqual(report['report_date'], test_date)
        self.assertEqual(report['total_sessions'], 0)
        self.assertEqual(report['total_detections'], 0)
        self.assertIn('summary', report)
    
    def test_export_to_csv(self):
        """Тест экспорта в CSV"""
        # Создаем тестовые данные
        json_data = {
            'detections': [
                {
                    'detection_id': 'TEST_001',
                    'timestamp': '2023-12-01T10:00:00',
                    'object_info': {'type': 'drone', 'confidence': 0.85},
                    'location': {'azimuth': 45.5, 'range': 5000, 'altitude': 1500},
                    'risk_assessment': 'high',
                    'signal_quality': 'excellent'
                },
                {
                    'detection_id': 'TEST_002',
                    'timestamp': '2023-12-01T10:01:00',
                    'object_info': {'type': 'airplane', 'confidence': 0.92},
                    'location': {'azimuth': 120.0, 'range': 8000, 'altitude': 10000},
                    'risk_assessment': 'low',
                    'signal_quality': 'excellent'
                }
            ]
        }
        
        # Экспортируем в CSV
        csv_filepath = self.report_generator.export_to_csv(json_data, "test_export.csv")
        
        # Проверяем, что файл создан
        self.assertTrue(os.path.exists(csv_filepath))
        
        # Проверяем содержимое CSV
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Должна быть как минимум одна строка (заголовок) + данные
        self.assertGreaterEqual(len(lines), 3)  # заголовок + 2 строки данных
        
        # Проверяем заголовок
        header = lines[0].strip()
        expected_columns = ['detection_id', 'timestamp', 'object_type', 'confidence', 
                           'azimuth', 'range', 'altitude', 'risk_assessment', 'signal_quality']
        
        for column in expected_columns:
            self.assertIn(column, header)
    
    def test_export_to_csv_auto_filename(self):
        """Тест экспорта в CSV с автоматическим именем"""
        json_data = {
            'detections': [
                {
                    'detection_id': 'TEST_001',
                    'timestamp': '2023-12-01T10:00:00',
                    'object_info': {'type': 'drone', 'confidence': 0.85},
                    'location': {'azimuth': 45.5, 'range': 5000, 'altitude': 1500},
                    'risk_assessment': 'high',
                    'signal_quality': 'excellent'
                }
            ]
        }
        
        # Экспортируем без указания имени файла
        csv_filepath = self.report_generator.export_to_csv(json_data)
        
        # Проверяем, что файл создан и имеет правильное имя
        self.assertTrue(os.path.exists(csv_filepath))
        filename = os.path.basename(csv_filepath)
        self.assertTrue(filename.startswith('radar_data_'))
        self.assertTrue(filename.endswith('.csv'))
    
    def test_export_to_csv_empty_data(self):
        """Тест экспорта пустых данных в CSV"""
        json_data = {'detections': []}
        
        # Экспортируем пустые данные
        csv_filepath = self.report_generator.export_to_csv(json_data, "empty_export.csv")
        
        # Проверяем, что файл создан
        self.assertTrue(os.path.exists(csv_filepath))

class TestJSONFormatterIntegration(unittest.TestCase):
    """Интеграционные тесты для JSON форматирования"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.formatter = RadarJSONFormatter(output_dir=self.temp_dir)
        self.report_generator = RadarReportGenerator(self.formatter)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """Тест полного рабочего процесса"""
        # 1. Создаем тестовые данные обнаружения
        detection_data = {
            'prediction': 'drone',
            'confidence': 0.85,
            'timestamp': '2023-12-01T10:00:00',
            'signal_analysis': {
                'rms': 0.15,
                'crest_factor': 8.2,
                'dominant_frequency': 1500.0
            },
            'risk_assessment': 'high',
            'signal_quality': 'excellent'
        }
        
        # 2. Форматируем результат
        formatted_result = self.formatter.format_detection_result(
            detection_data, "FULL_TEST_001",
            {"azimuth": 45.5, "range": 5000, "altitude": 1500}
        )
        
        # 3. Создаем пакетный результат
        batch_result = self.formatter.format_batch_results(
            [formatted_result], "FULL_SESSION_001"
        )
        
        # 4. Сохраняем в файл
        json_filepath = self.formatter.save_to_file(batch_result, "full_test.json")
        
        # 5. Загружаем и проверяем
        loaded_data = self.formatter.load_from_file("full_test.json")
        self.assertEqual(loaded_data, batch_result)
        
        # 6. Экспортируем в CSV
        csv_filepath = self.report_generator.export_to_csv(loaded_data, "full_test.csv")
        self.assertTrue(os.path.exists(csv_filepath))
        
        # 7. Проверяем, что файлы существуют и содержат данные
        self.assertTrue(os.path.exists(json_filepath))
        self.assertTrue(os.path.exists(csv_filepath))
        
        # 8. Проверяем получение последних результатов
        latest_files = self.formatter.get_latest_results(limit=5)
        self.assertIn(json_filepath, latest_files)

if __name__ == '__main__':
    unittest.main()
