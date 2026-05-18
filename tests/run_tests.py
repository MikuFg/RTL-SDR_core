#!/usr/bin/env python3
"""
Test Runner для Radar AI Detection System

Запускает все тесты и генерирует отчеты о покрытии кода.
"""

import unittest
import sys
import os
from pathlib import Path
import time
import argparse
from io import StringIO

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def discover_and_run_tests(test_dir=None, pattern='test_*.py', verbosity=2):
    """
    Обнаруживает и запускает все тесты в указанной директории
    
    Args:
        test_dir: Директория с тестами (по умолчанию tests/)
        pattern: Шаблон для поиска тестовых файлов
        verbosity: Уровень детализации вывода
    
    Returns:
        TestResult: Результат выполнения тестов
    """
    if test_dir is None:
        test_dir = Path(__file__).parent
    
    # Обнаруживаем все тесты
    loader = unittest.TestLoader()
    start_dir = str(test_dir)
    suite = loader.discover(start_dir, pattern=pattern)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        stream=sys.stdout,
        buffer=True  # Буферизируем stdout/stderr во время тестов
    )
    
    print(f"🔍 Поиск тестов в директории: {start_dir}")
    print(f"📋 Шаблон поиска: {pattern}")
    print(f"📊 Количество тестов: {suite.countTestCases()}")
    print("=" * 70)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    print("=" * 70)
    print(f"⏱️ Время выполнения: {end_time - start_time:.2f} секунд")
    
    return result

def run_specific_test_module(module_name, verbosity=2):
    """
    Запускает тесты из конкретного модуля
    
    Args:
        module_name: Имя модуля (например, 'test_signal_processor')
        verbosity: Уровень детализации вывода
    
    Returns:
        TestResult: Результат выполнения тестов
    """
    try:
        suite = unittest.TestLoader().loadTestsFromName(module_name)
        runner = unittest.TextTestRunner(verbosity=verbosity)
        
        print(f"🎯 Запуск тестов из модуля: {module_name}")
        print("=" * 70)
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        print("=" * 70)
        print(f"⏱️ Время выполнения: {end_time - start_time:.2f} секунд")
        
        return result
    except Exception as e:
        print(f"❌ Ошибка при загрузке модуля {module_name}: {e}")
        return None

def generate_test_report(test_result, output_file=None):
    """
    Генерирует отчет о результатах тестирования
    
    Args:
        test_result: Результат выполнения тестов
        output_file: Файл для сохранения отчета (опционально)
    """
    report_lines = []
    report_lines.append("📊 ОТЧЕТ О ТЕСТИРОВАНИИ")
    report_lines.append("=" * 50)
    report_lines.append(f"📅 Дата и время: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"🔢 Всего тестов: {test_result.testsRun}")
    report_lines.append(f"✅ Успешных: {test_result.testsRun - len(test_result.failures) - len(test_result.errors)}")
    report_lines.append(f"❌ Проваленных: {len(test_result.failures)}")
    report_lines.append(f"🚨 Ошибок: {len(test_result.errors)}")
    report_lines.append(f"⏭️ Пропущенных: {len(test_result.skipped) if hasattr(test_result, 'skipped') else 0}")
    
    success_rate = (test_result.testsRun - len(test_result.failures) - len(test_result.errors)) / test_result.testsRun * 100
    report_lines.append(f"📈 Успешность: {success_rate:.1f}%")
    
    report_lines.append("\n" + "=" * 50)
    
    if test_result.failures:
        report_lines.append("\n❌ ПРОВАЛЕННЫЕ ТЕСТЫ:")
        for test, traceback in test_result.failures:
            report_lines.append(f"\n📝 {test}")
            if traceback:
                lines = traceback.split('\n')
                # Берем предпоследнюю строку, если она есть
                error_msg = lines[-2] if len(lines) >= 2 else (lines[0] if lines else "Нет подробной информации")
                report_lines.append("💬 " + error_msg)
            else:
                report_lines.append("💬 Нет подробной информации")
    
    if test_result.errors:
        report_lines.append("\n🚨 ТЕСТЫ С ОШИБКАМИ:")
        for test, traceback in test_result.errors:
            report_lines.append(f"\n📝 {test}")
            if traceback:
                lines = traceback.split('\n')
                # Берем предпоследнюю строку, если она есть
                error_msg = lines[-2] if len(lines) >= 2 else (lines[0] if lines else "Нет подробной информации")
                report_lines.append("💬 " + error_msg)
            else:
                report_lines.append("💬 Нет подробной информации")
    
    report_text = "\n".join(report_lines)
    
    # Выводим отчет в консоль
    print(report_text)
    
    # Сохраняем отчет в файл если указан
    if output_file:
        try:
            import os
            # Получаем путь к корневой директории проекта
            project_root = Path(__file__).parent.parent
            current_dir = os.getcwd()
            full_path = project_root / output_file
            
            print(f"🔍 Текущая директория: {current_dir}")
            print(f"🔍 Корневая директория проекта: {project_root}")
            print(f"🔍 Полный путь к файлу: {full_path}")
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            # Проверяем, что файл создан
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                print(f"\n💾 Отчет сохранен в файл: {output_file} ({file_size} байт)")
            else:
                print(f"\n❌ ОШИБКА: Файл не был создан: {full_path}")
        except Exception as e:
            print(f"\n❌ ОШИБКА при сохранении файла: {e}")
            import traceback
            traceback.print_exc()
    
    return report_text

def check_dependencies():
    """Проверяет наличие всех зависимостей для тестов"""
    required_modules = [
        'unittest', 'numpy', 'torch', 'PIL', 'scipy', 
        'matplotlib', 'pathlib', 'tempfile', 'shutil'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Отсутствуют следующие модули:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n💡 Установите их с помощью: pip install -r requirements.txt")
        return False
    
    print("✅ Все зависимости для тестов установлены")
    return True

def setup_test_environment():
    """Настраивает тестовое окружение"""
    # Создаем директорию для тестовых данных если она не существует
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Генерируем тестовые данные если нужно
    try:
        from test_data_generator import TestDataGenerator
        generator = TestDataGenerator(str(test_data_dir))
        generator.generate_all_test_data()
        print("✅ Тестовые данные сгенерированы")
    except Exception as e:
        print(f"⚠️ Предупреждение при генерации тестовых данных: {e}")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Test Runner для Radar AI Detection System')
    parser.add_argument('--module', '-m', type=str, 
                       help='Запустить тесты из конкретного модуля (например, test_signal_processor)')
    parser.add_argument('--pattern', '-p', type=str, default='test_*.py',
                       help='Шаблон для поиска тестовых файлов (по умолчанию: test_*.py)')
    parser.add_argument('--verbosity', '-v', type=int, default=2, choices=[0, 1, 2],
                       help='Уровень детализации вывода (0=тихий, 1=нормальный, 2=подробный)')
    parser.add_argument('--report', '-r', type=str,
                       help='Сохранить отчет в указанный файл')
    parser.add_argument('--no-setup', action='store_true',
                       help='Пропустить настройку тестового окружения')
    parser.add_argument('--check-deps', action='store_true',
                       help='Только проверить зависимости')
    
    args = parser.parse_args()
    
    print("🚀 Radar AI Detection System - Test Runner")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    if args.check_deps:
        print("✅ Проверка зависимостей завершена")
        sys.exit(0)
    
    # Настраиваем тестовое окружение
    if not args.no_setup:
        print("⚙️ Настройка тестового окружения...")
        setup_test_environment()
        print()
    
    # Запускаем тесты
    try:
        if args.module:
            result = run_specific_test_module(args.module, args.verbosity)
        else:
            result = discover_and_run_tests(pattern=args.pattern, verbosity=args.verbosity)
        
        if result is None:
            print("❌ Не удалось запустить тесты")
            sys.exit(1)
        
        # Генерируем отчет
        print()
        generate_test_report(result, args.report)
        
        # Определяем код выхода
        if result.wasSuccessful():
            print("\n🎉 Все тесты успешно пройдены!")
            sys.exit(0)
        else:
            print(f"\n❌ Тесты не пройдены: {len(result.failures)} провалено, {len(result.errors)} ошибок")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тесты прерваны пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Критическая ошибка при запуске тестов: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
