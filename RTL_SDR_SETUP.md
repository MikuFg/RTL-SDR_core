# RTL-SDR Настройка и использование

## 📡 Что нужно для работы с реальными радиосигналами

### Оборудование:
1. **RTL-SDR приемник** (RTL2832U) - $10-30
   - Поиск: "RTL-SDR dongle" или "RTL2832U"
   - Популярные модели: Nooelec NESDR, Generic RTL-SDR

2. **Антенна** (в зависимости от частот):
   - **433 МГц**: Дипольная или монопольная антенна
   - **1090 МГц**: Специализированная ADS-B антенна
   - **88-108 МГц**: FM радио антенна
   - **Универсальная**: телескопическая антенна

3. **USB кабель** для подключения к ПК

### Программное обеспечение:

#### Установка драйверов (Windows):
1. Скачайте **Zadig**: https://zadig.akeo.ie/
2. Подключите RTL-SDR к USB
3. Запустите Zadig от имени администратора
4. Выберите "Options" → "List All Devices"
5. Найдите "RTL2832U" или "Bulk-In, Interface (Interface 0)"
6. Выберите драйвер "WinUSB" и нажмите "Install Driver"

#### Установка Python библиотек:
```bash
pip install rtlsdr pyrtlsdr
```

## 🎯 Использование в проекте

### 1. Установка зависимостей:
```bash
pip install -r requirements.txt
```

### 2. Запуск с RTL-SDR:
```python
# В ui_bridge.py или test_simulation.py
from signal_processor import RadarSignalProcessor

# Использование RTL-SDR вместо микрофона
processor = RadarSignalProcessor(use_rtl_sdr=True)
```

### 3. Тестирование RTL-SDR:
```bash
python rtl_sdr_capture.py
```

## 📡 Частоты и предустановки

### Доступные предустановки:
- **aircraft**: 1090 МГц - ADS-B трансмиттеры самолетов
- **weather**: 1660 МГц - метеорологические спутники
- **radio**: 88 МГц - FM радио станции
- **drone**: 433.92 МГц - дроны и пульты управления
- **custom**: настраиваемая частота

### Настройка частоты:
```python
from rtl_sdr_capture import RTLSdrCapture

# Для дронов
sdr = RTLSdrCapture(center_freq=433.92e6)

# Для самолетов
sdr = RTLSdrCapture(center_freq=1090e6)

# Для радио
sdr = RTLSdrCapture(center_freq=88e6)
```

## 🔧 Поиск и устранение проблем

### Проблема: "RTL-SDR не найден"
**Решение:**
1. Проверьте подключение USB
2. Убедитесь, что драйверы Zadig установлены
3. Перезагрузите компьютер
4. Проверьте в Диспетчере устройств, что RTL-SDR определен как "USB Serial Device"

### Проблема: "Устройство занято"
**Решение:**
1. Закройте другие программы SDR (SDR#, CubicSDR)
2. Отключите и подключите RTL-SDR снова
3. Перезагрузите компьютер

### Проблема: "Слабый сигнал"
**Решение:**
1. Улучшите антенну
2. Настройте усиление: `gain='auto'` или конкретное значение
3. Используйте внешнюю антенну для нужных частот
4. Проверьте экранирование от помех

### Проблема: "Много шумов"
**Решение:**
1. Уменьшите усиление
2. Используйте фильтр
3. Уберите источники помех
4. Используйте качественную антенну

## 🎯 Примеры использования

### Мониторинг дронов:
```python
from signal_processor import RadarSignalProcessor
from ui_bridge import start_real_time_mode

# Создаем процессор с RTL-SDR для частоты дронов
processor = RadarSignalProcessor(use_rtl_sdr=True)
if processor.use_rtl_sdr:
    processor.rtl_sdr.center_freq = 433.92e6  # 433.92 МГц
    print("🚁 Мониторинг частоты дронов активен")
    
# Запускаем режим реального времени
start_real_time_mode()
```

### Сканирование диапазона:
```python
from rtl_sdr_capture import RTLSdrCapture

with RTLSdrCapture() as sdr:
    if sdr.is_connected:
        # Сканируем диапазон 430-440 МГц
        results = sdr.scan_frequency_range(430e6, 440e6, 1e6)
        
        # Находим самую сильную частоту
        if results:
            best_freq = max(results, key=results.get)
            print(f"📡 Самый сильный сигнал: {best_freq/1e6:.2f} МГц = {results[best_freq]:.1f} дБ")
```

## ⚠️ Важные замечания

1. **Законность**: Убедитесь, что вы имеете право мониторить выбранные частоты
2. **Помехи**: RTL-SDR чувствителен к помехам от других устройств
3. **Питание**: Используйте качественный USB порт или внешнее питание
4. **Антенна**: Качество антенны сильно влияет на прием сигналов
5. **Температура**: RTL-SDR может нагреваться при длительной работе

## 📚 Дополнительные ресурсы

- **RTL-SDR.com**: https://www.rtl-sdr.com/
- **GreatScott Gadgets**: https://greatscottgadgets.com/sdr/
- **Reddit r/rtlsdr**: https://www.reddit.com/r/rtlsdr/

## 🎯 Быстрый старт

1. Купите RTL-SDR приемник ($10-30)
2. Установите драйверы Zadig
3. Установите библиотеки: `pip install rtlsdr pyrtlsdr`
4. Подключите антенну
5. Запустите тест: `python rtl_sdr_capture.py`
6. Наслаждайтесь реальными радиосигналами! 📡
