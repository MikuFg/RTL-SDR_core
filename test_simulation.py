#!/usr/bin/env python3
"""
Тестовый скрипт для запуска симуляции и генерации JSON файлов
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui_bridge import start_simulation

async def main():
    print("🚀 Запуск тестовой симуляции для генерации JSON файлов...")
    print("⏱️ Будет выполнено 10 циклов для демонстрации")
    
    # Запускаем симуляцию с тестовыми данными
    # Изменим количество циклов для быстрой демонстрации
    try:
        # Создадим измененную версию для короткого теста
        await run_short_simulation()
    except KeyboardInterrupt:
        print("\n✅ Тест завершен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def run_short_simulation():
    """Короткая симуляция для демонстрации"""
    from ui_bridge import RadarTarget, ws_manager, ai_classifier, json_formatter
    import random
    import os
    from PIL import Image
    
    print("🔧 Подключаем WebSocket...")
    await ws_manager.connect()
    
    # Создаем тестовые цели
    active_targets = []
    test_dir = "data_v2/val"
    classes = os.listdir(test_dir)
    
    # Создаем 3 цели для демонстрации
    for i in range(3):
        t_class = random.choice(classes)
        class_path = os.path.join(test_dir, t_class)
        t_file = random.choice(os.listdir(class_path))
        
        new_target = RadarTarget(target_id=f"TEST-{100 + i}", use_real_signal=False)
        new_target.file_path = os.path.join(class_path, t_file)
        active_targets.append(new_target)
        print(f"📡 Создана цель {new_target.id} (Класс: {t_class})")
    
    print("\n🎯 Начинаем симуляцию (10 циклов)...")
    
    try:
        for cycle in range(10):
            print(f"\n--- Цикл {cycle + 1}/10 ---")
            
            for target in active_targets:
                # Обновляем позицию
                target.update_position()
                
                # Классификация
                try:
                    image = Image.open(target.file_path).convert('RGB')
                    detection_result = ai_classifier.classify_signal(image)
                    
                    # Форматирование результата
                    location = target.get_location()
                    formatted_result = json_formatter.format_detection_result(
                        detection_result, 
                        target.id, 
                        location
                    )
                    
                    # Сохранение в файл
                    filename = json_formatter.save_to_file(formatted_result, f"test_{target.id}_cycle_{cycle+1}.json")
                    print(f"✓ {target.id}: {detection_result.get('prediction', 'unknown')} "
                          f"(confidence: {detection_result.get('confidence', 0):.3f}) -> {filename}")
                    
                except Exception as e:
                    print(f"❌ Ошибка обработки {target.id}: {e}")
            
            # Небольшая пауза
            await asyncio.sleep(0.5)
            
    finally:
        await ws_manager.disconnect()
        print("\n✅ Симуляция завершена!")

if __name__ == "__main__":
    asyncio.run(main())
