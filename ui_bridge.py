import time
import requests
import random
import os
import asyncio
import websockets
import json
import numpy as np
from model_engine import RadarSignalClassifier
from signal_processor import SignalCapture
from json_formatter import RadarJSONFormatter, RadarReportGenerator

# Настройки связи
GO_SERVER_URL = "http://localhost:8080/update"
WEBSOCKET_URL = "ws://localhost:8080/ws"

# WebSocket менеджер
class WebSocketManager:
    def __init__(self, uri=WEBSOCKET_URL):
        self.uri = uri
        self.websocket = None
        self.is_connected = False
        
    async def connect(self):
        """Устанавливает WebSocket соединение"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            print(f"✓ WebSocket соединение установлено: {self.uri}")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения WebSocket: {e}")
            self.is_connected = False
            return False
    
    async def send_json(self, data):
        """Отправляет JSON данные через WebSocket"""
        if not self.is_connected or self.websocket is None:
            return False
        
        try:
            await self.websocket.send(json.dumps(data))
            return True
        except Exception as e:
            print(f"✗ Ошибка отправки WebSocket: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Закрывает WebSocket соединение"""
        if self.websocket:
            try:
                await self.websocket.close()
                print("✓ WebSocket соединение закрыто")
            except:
                pass
            finally:
                self.is_connected = False
                self.websocket = None

# Глобальный WebSocket менеджер
ws_manager = WebSocketManager()

# Инициализация компонентов
try:
    ai_classifier = RadarSignalClassifier("radar_model_v2.pth")
    signal_capture = SignalCapture()
    json_formatter = RadarJSONFormatter()
    report_generator = RadarReportGenerator(json_formatter)
    print("Все компоненты успешно загружены.")
except Exception as e:
    print(f"Ошибка загрузки компонентов: {e}")
    exit()

class RadarTarget:
    """Класс, описывающий физическое поведение цели на радаре"""
    def __init__(self, target_id, use_real_signal=False):
        self.id = target_id
        self.use_real_signal = use_real_signal
        
        # Начальные координаты (случайные)
        self.azimuth = random.uniform(0, 360)
        self.range = random.randint(3000, 8000)
        self.altitude = random.randint(100, 3000)
        
        # Вектор движения (маленькие значения для плавности)
        self.speed_az = random.uniform(-0.8, 0.8)
        self.speed_range = random.uniform(-20, 20)
        self.speed_altitude = random.uniform(-5, 5)
        
        # Для реальных сигналов
        self.last_signal_data = None
        self.signal_characteristics = None

    def update_position(self):
        """Расчет координат на следующем шаге"""
        # Если цель улетает слишком далеко или близко - разворачиваем её
        if self.range > 9500 or self.range < 500:
            self.speed_range *= -1
        if self.altitude > 5000 or self.altitude < 50:
            self.speed_altitude *= -1
        
        # Обновляем позицию с учетом новой скорости
        self.azimuth = (self.azimuth + self.speed_az) % 360
        self.range += self.speed_range
        self.altitude += self.speed_altitude
        
        # Ограничиваем позицию в допустимых пределах
        self.range = max(500, min(9500, self.range))
        self.altitude = max(50, min(5000, self.altitude))
    
    def capture_signal(self):
        """Захватывает реальный сигнал если это необходимо"""
        if self.use_real_signal:
            try:
                image, characteristics = signal_capture.capture_and_process(duration=0.1)
                self.last_signal_data = image
                self.signal_characteristics = characteristics
                return True
            except Exception as e:
                print(f"Ошибка захвата сигнала для цели {self.id}: {e}")
                return False
        return False
    
    def get_location(self):
        """Возвращает текущие координаты цели"""
        return {
            "azimuth": round(self.azimuth, 2),
            "range": int(self.range),
            "altitude": int(self.altitude)
        }

async def start_simulation(use_real_signals=False, save_results=True):
    """Запускает симуляцию с возможностью использования реальных сигналов"""
    mode = "реальных сигналов" if use_real_signals else "тестовых данных"
    print(f"Запуск многоцелевой симуляции в режиме {mode}...")
    
    # Подключаем WebSocket
    await ws_manager.connect()
    
    # Создаем список активных целей
    active_targets = []
    num_targets = 5
    
    if not use_real_signals and os.path.exists("data_v2/val"):
        # Режим с тестовыми изображениями
        test_dir = "data_v2/val"
        classes = os.listdir(test_dir)
        
        for i in range(num_targets):
            t_class = random.choice(classes)
            class_path = os.path.join(test_dir, t_class)
            t_file = random.choice(os.listdir(class_path))
            
            new_target = RadarTarget(target_id=f"TGT-{100 + i}", use_real_signal=False)
            new_target.file_path = os.path.join(class_path, t_file)
            active_targets.append(new_target)
            print(f"Создана цель {new_target.id} (Класс: {t_class})")
    else:
        # Режим с реальными сигналами
        for i in range(num_targets):
            new_target = RadarTarget(target_id=f"TGT-{200 + i}", use_real_signal=True)
            active_targets.append(new_target)
            print(f"Создана цель {new_target.id} (Реальный сигнал)")
    
    # Основной цикл симуляции
    session_detections = []
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"Цикл {cycle_count}")
            
            for target in active_targets:
                # Обновляем позицию цели
                target.update_position()
                
                # Получаем данные для распознавания
                detection_result = None
                
                if target.use_real_signal:
                    # Захватываем реальный сигнал
                    if target.capture_signal():
                        detection_result = ai_classifier.classify_signal(
                            target.last_signal_data, 
                            target.signal_characteristics
                        )
                    else:
                        continue
                else:
                    # Используем тестовое изображение
                    from PIL import Image
                    image = Image.open(target.file_path).convert('RGB')
                    detection_result = ai_classifier.classify_signal(image)
                
                # Формируем полный результат
                location = target.get_location()
                formatted_result = json_formatter.format_detection_result(
                    detection_result, 
                    target.id, 
                    location
                )
                
                session_detections.append(formatted_result)
                
# Отправка в Go-сервер через WebSocket
                payload = json_formatter.create_real_time_update(
                    detection_result,
                    target.id,
                    location
                )
                
                # Отправляем через WebSocket
                ws_success = await ws_manager.send_json(payload)
                if ws_success:
                    print(f"✓ {target.id}: {detection_result.get('prediction', 'unknown')} "
                          f"(confidence: {detection_result.get('confidence', 0):.3f}) [WS]")
                else:
                    print(f"⚠ {target.id}: WebSocket не доступен, пробуем HTTP...")
                    # Fallback на HTTP если WebSocket не работает
                    try:
                        response = requests.post(GO_SERVER_URL, json=payload, timeout=0.1)
                        if response.status_code == 200:
                            print(f"✓ {target.id}: {detection_result.get('prediction', 'unknown')} "
                                  f"(confidence: {detection_result.get('confidence', 0):.3f}) [HTTP]")
                    except:
                        print(f"✗ Ошибка отправки для {target.id}: оба метода недоступны")
                try:
                    response = requests.post(GO_SERVER_URL, json=payload, timeout=0.1)
                    if response.status_code == 200:
                        print(f"✓ {target.id}: {detection_result.get('prediction', 'unknown')} "
                              f"(confidence: {detection_result.get('confidence', 0):.3f})")
                except requests.exceptions.ConnectionError:
                    print("⚠ Go-сервер не отвечает, продолжаем работу...")
                except Exception as e:
                    print(f"✗ Ошибка отправки для {target.id}: {e}")
            
            # Сохраняем результаты каждые 50 циклов
            if save_results and cycle_count % 50 == 0:
                save_session_results(session_detections, cycle_count)
            
            # Пауза между циклами
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nСимуляция остановлена пользователем")
        if save_results and session_detections:
            save_session_results(session_detections, cycle_count, final=True)
    finally:
        # Закрываем WebSocket соединение
        await ws_manager.disconnect()

def save_session_results(detections, cycle_count, final=False):
    """Сохраняет результаты сессии"""
    suffix = "_final" if final else f"_cycle_{cycle_count}"
    session_data = json_formatter.format_batch_results(
        detections, 
        f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
    )
    
    filename = json_formatter.save_to_file(session_data)
    print(f"💾 Результаты сохранены: {filename}")

async def start_real_time_mode():
    """Запускает режим обработки реальных сигналов в реальном времени"""
    print("🎯 Запуск режима реального времени...")
    print("Нажмите Ctrl+C для остановки")
    
    # Подключаем WebSocket
    await ws_manager.connect()
    
    detection_count = 0
    
    try:
        while True:
            print(f"\n--- Обработка сигнала #{detection_count + 1} ---")
            
            # Захват и обработка сигнала
            image, characteristics = signal_capture.capture_and_process(duration=0.2)
            
            # Классификация
            result = ai_classifier.classify_signal(image, characteristics)
            
            # Форматирование результата
            location = {
                "azimuth": random.uniform(0, 360),
                "range": random.randint(1000, 10000),
                "altitude": random.randint(100, 3000)
            }
            
            formatted_result = json_formatter.format_detection_result(
                result, 
                f"REALTIME_{detection_count + 1}", 
                location
            )
            
            # Вывод результата
            print(f"🔍 Обнаружен объект: {result.get('prediction', 'unknown')}")
            print(f"📊 Уверенность: {result.get('confidence', 0):.3f}")
            print(f"⚠️ Уровень риска: {result.get('risk_assessment', 'unknown')}")
            print(f"📡 Качество сигнала: {result.get('signal_quality', 'unknown')}")
            
            # Отправка на сервер через WebSocket
            # Отправка на сервер
            payload = json_formatter.create_real_time_update(
                result,
                f"REALTIME_{detection_count + 1}",
                location
            )
            
            # Отправляем через WebSocket
            ws_success = await ws_manager.send_json(payload)
            if ws_success:
                print("📡 Данные отправлены на сервер [WS]")
            else:
                print("⚠️ WebSocket не доступен, пробуем HTTP...")
                try:
                    requests.post(GO_SERVER_URL, json=payload, timeout=0.1)
                    print("📡 Данные отправлены на сервер [HTTP]")
                except:
                    print("⚠️ Ошибка отправки на сервер")
            try:
                requests.post(GO_SERVER_URL, json=payload, timeout=0.1)
                print("📡 Данные отправлены на сервер")
            except:
                print("⚠️ Ошибка отправки на сервер")
            
            # Сохранение результата
            json_formatter.save_to_file(formatted_result, f"realtime_detection_{detection_count + 1}.json")
            
            detection_count += 1
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print(f"\nРежим реального времени остановлен. Обработано сигналов: {detection_count}")
    finally:
        # Закрываем WebSocket соединение
        await ws_manager.disconnect()

def start_batch_processing(signal_files_dir):
    """Запускает пакетную обработку сигналов из файлов"""
    print(f"📁 Запуск пакетной обработки из директории: {signal_files_dir}")
    
    if not os.path.exists(signal_files_dir):
        print(f"❌ Директория {signal_files_dir} не найдена!")
        return
    
    signal_files = [f for f in os.listdir(signal_files_dir) if f.endswith(('.npy', '.wav'))]
    if not signal_files:
        print("❌ Файлы сигналов не найдены!")
        return
    
    results = []
    
    for i, filename in enumerate(signal_files):
        filepath = os.path.join(signal_files_dir, filename)
        print(f"🔄 Обработка файла {i+1}/{len(signal_files)}: {filename}")
        
        try:
            # Загрузка сигнала
            if filename.endswith('.npy'):
                signal_data = np.load(filepath)
            else:
                # Для .wav файлов нужна дополнительная обработка
                print(f"⚠️ Формат .wav требует дополнительной обработки")
                continue
            
            # Обработка сигнала
            processed_signal = signal_capture.processor.process_signal(signal_data)
            image = signal_capture.processor.signal_to_image(signal_data)
            characteristics = signal_capture.processor.analyze_signal_characteristics(signal_data)
            
            # Классификация
            result = ai_classifier.classify_signal(image, characteristics)
            
            # Сохранение результата
            formatted_result = json_formatter.format_detection_result(
                result,
                f"BATCH_{i+1}_{filename.split('.')[0]}",
                {"azimuth": 0, "range": 0, "altitude": 0}
            )
            
            results.append(formatted_result)
            print(f"✓ {filename}: {result.get('prediction', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Ошибка обработки {filename}: {e}")
    
    # Сохранение всех результатов
    if results:
        batch_data = json_formatter.format_batch_results(results, f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        json_formatter.save_to_file(batch_data)
        print(f"✅ Пакетная обработка завершена. Обработано файлов: {len(results)}")
    else:
        print("❌ Ни один файл не был обработан")

if __name__ == "__main__":
    import sys
    
    print("🎯 Radar AI System - Выбор режима работы")
    print("1. Симуляция с тестовыми данными")
    print("2. Симуляция с реальными сигналами")
    print("3. Режим реального времени")
    print("4. Пакетная обработка файлов")
    
    async def run_chosen_mode():
        try:
            choice = input("Выберите режим (1-4): ").strip()
            
            if choice == "1":
                await start_simulation(use_real_signals=False)
            elif choice == "2":
                await start_simulation(use_real_signals=True)
            elif choice == "3":
                await start_real_time_mode()
            elif choice == "4":
                signal_dir = input("Укажите директорию с файлами сигналов: ").strip()
                start_batch_processing(signal_dir)
            else:
                print("Неверный выбор. Запуск стандартной симуляции...")
                await start_simulation()
                
        except KeyboardInterrupt:
            print("\nПрограмма завершена")
        except Exception as e:
            print(f"Ошибка: {e}")
            print("Запуск стандартной симуляции...")
            await start_simulation()
    
    # Запускаем async функцию
    asyncio.run(run_chosen_mode())
    try:
        choice = input("Выберите режим (1-4): ").strip()
        
        if choice == "1":
            start_simulation(use_real_signals=False)
        elif choice == "2":
            start_simulation(use_real_signals=True)
        elif choice == "3":
            start_real_time_mode()
        elif choice == "4":
            signal_dir = input("Укажите директорию с файлами сигналов: ").strip()
            start_batch_processing(signal_dir)
        else:
            print("Неверный выбор. Запуск стандартной симуляции...")
            start_simulation()
            
    except KeyboardInterrupt:
        print("\nПрограмма завершена")
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Запуск стандартной симуляции...")
        start_simulation()
