"""
RTL-SDR модуль для захвата реальных радиосигналов
"""

import numpy as np
from rtlsdr import RtlSdr
import warnings
from typing import Tuple, Optional

class RTLSdrCapture:
    """Класс для захвата радиосигналов через RTL-SDR приемник"""
    
    def __init__(self, 
                 center_freq: float = 433.92e6,  # Частота по умолчанию 433.92 МГц
                 sample_rate: float = 2.048e6,   # Частота дискретизации 2.048 МГц
                 gain: str = 'auto'):            # Усиление (auto или число)
        """
        Инициализация RTL-SDR приемника
        
        Args:
            center_freq: Центральная частота в Гц
            sample_rate: Частота дискретизации в Гц  
            gain: Усиление ('auto' или число от 0 до 50)
        """
        self.center_freq = center_freq
        self.sample_rate = sample_rate
        self.gain = gain
        self.sdr = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """Подключение к RTL-SDR приемнику"""
        try:
            self.sdr = RtlSdr()
            
            # Настройка параметров
            self.sdr.center_freq = self.center_freq
            self.sdr.sample_rate = self.sample_rate
            self.sdr.gain = self.gain
            
            # Настройка фильтра
            self.sdr.bandwidth = self.sample_rate * 0.95
            
            self.is_connected = True
            print(f"✅ RTL-SDR подключен:")
            print(f"   Частота: {self.center_freq/1e6:.2f} МГц")
            print(f"   Частота дискретизации: {self.sample_rate/1e6:.2f} МГц")
            print(f"   Усиление: {self.sdr.gain} dB")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения RTL-SDR: {e}")
            self.is_connected = False
            return False
    
    def capture_samples(self, num_samples: int = 1024) -> Optional[np.ndarray]:
        """
        Захватывает сэмплы с RTL-SDR
        
        Args:
            num_samples: Количество сэмплов для захвата
            
        Returns:
            np.ndarray: Комплексные сэмплы или None при ошибке
        """
        if not self.is_connected or self.sdr is None:
            print("❌ RTL-SDR не подключен")
            return None
            
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                samples = self.sdr.read_samples(num_samples)
            
            return samples
            
        except Exception as e:
            print(f"❌ Ошибка захвата сэмплов: {e}")
            return None
    
    def capture_block(self, duration: float = 0.1) -> Optional[np.ndarray]:
        """
        Захватывает блок данных на указанную длительность
        
        Args:
            duration: Длительность захвата в секундах
            
        Returns:
            np.ndarray: Комплексные сэмплы или None при ошибке
        """
        num_samples = int(duration * self.sample_rate)
        return self.capture_samples(num_samples)
    
    def get_signal_strength(self) -> Optional[float]:
        """
        Измеряет силу сигнала в дБ
        
        Returns:
            float: Сила сигнала в дБ или None при ошибке
        """
        if not self.is_connected or self.sdr is None:
            return None
            
        try:
            # Захватываем небольшой блок для измерения
            samples = self.capture_samples(4096)
            if samples is None:
                return None
                
            # Вычисляем мощность сигнала
            power_db = 10 * np.log10(np.mean(np.abs(samples)**2))
            return power_db
            
        except Exception as e:
            print(f"❌ Ошибка измерения силы сигнала: {e}")
            return None
    
    def scan_frequency_range(self, 
                           start_freq: float, 
                           end_freq: float, 
                           step: float = 1e6) -> dict:
        """
        Сканирует диапазон частот
        
        Args:
            start_freq: Начальная частота в Гц
            end_freq: Конечная частота в Гц
            step: Шаг сканирования в Гц
            
        Returns:
            dict: Результаты сканирования {частота: сила_сигнала_дБ}
        """
        if not self.is_connected:
            return {}
            
        results = {}
        original_freq = self.center_freq
        
        try:
            freq = start_freq
            while freq <= end_freq:
                self.sdr.center_freq = freq
                # Небольшая задержка для стабилизации
                import time
                time.sleep(0.1)
                
                strength = self.get_signal_strength()
                if strength is not None:
                    results[freq] = strength
                    print(f"📡 {freq/1e6:.2f} МГц: {strength:.1f} дБ")
                
                freq += step
                
        except Exception as e:
            print(f"❌ Ошибка сканирования: {e}")
        finally:
            # Возвращаем исходную частоту
            if self.sdr is not None:
                self.sdr.center_freq = original_freq
                
        return results
    
    def disconnect(self):
        """Отключение от RTL-SDR"""
        if self.sdr is not None:
            try:
                self.sdr.close()
                print("✅ RTL-SDR отключен")
            except:
                pass
            finally:
                self.sdr = None
                self.is_connected = False
    
    def __enter__(self):
        """Контекстный менеджер - подключение"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - отключение"""
        self.disconnect()

# Предустановленные конфигурации для разных частот
RTL_SDR_PRESETS = {
    'aircraft': {
        'center_freq': 1090e6,    # 1090 МГц - ADS-B (самолеты)
        'sample_rate': 2.0e6,
        'gain': 'auto',
        'description': 'Мониторинг самолетов (ADS-B)'
    },
    'weather': {
        'center_freq': 1660e6,    # 1660 МГц - метеорологические спутники
        'sample_rate': 2.4e6,
        'gain': 'auto',
        'description': 'Метеорологические спутники'
    },
    'radio': {
        'center_freq': 88e6,      # 88 МГц - FM радио
        'sample_rate': 2.048e6,
        'gain': 'auto',
        'description': 'FM радио станции'
    },
    'drone': {
        'center_freq': 433.92e6,  # 433.92 МГц - дроны/пульты
        'sample_rate': 2.048e6,
        'gain': 'auto',
        'description': 'Дроны и пульты управления'
    },
    'custom': {
        'center_freq': 100e6,     # 100 МГц - настраиваемый
        'sample_rate': 2.048e6,
        'gain': 'auto',
        'description': 'Настраиваемая частота'
    }
}

def get_rtl_sdr_preset(preset_name: str) -> dict:
    """Возвращает предустановку по имени"""
    return RTL_SDR_PRESETS.get(preset_name, RTL_SDR_PRESETS['custom'])

def list_available_presets():
    """Выводит список доступных предустановок"""
    print("📡 Доступные предустановки RTL-SDR:")
    for name, config in RTL_SDR_PRESETS.items():
        print(f"  {name}: {config['description']}")
        print(f"    Частота: {config['center_freq']/1e6:.2f} МГц")
        print(f"    Частота дискретизации: {config['sample_rate']/1e6:.2f} МГц")
        print()

if __name__ == "__main__":
    # Демонстрация работы
    print("📡 Тестирование RTL-SDR модуля")
    list_available_presets()
    
    # Попытка подключения с предустановкой для дронов
    preset = get_rtl_sdr_preset('drone')
    
    with RTLSdrCapture(
        center_freq=preset['center_freq'],
        sample_rate=preset['sample_rate'],
        gain=preset['gain']
    ) as sdr:
        if sdr.is_connected:
            # Измерение силы сигнала
            strength = sdr.get_signal_strength()
            if strength is not None:
                print(f"📊 Текущая сила сигнала: {strength:.1f} дБ")
            
            # Захват сэмплов
            samples = sdr.capture_block(duration=0.1)
            if samples is not None:
                print(f"📈 Захвачено {len(samples)} сэмплов")
                print(f"📊 Средняя амплитуда: {np.mean(np.abs(samples)):.4f}")
        else:
            print("❌ Не удалось подключиться к RTL-SDR")
            print("💡 Убедитесь, что:")
            print("   1. RTL-SDR приемник подключен к USB")
            print("   2. Драйверы Zadig установлены")
            print("   3. Устройство не используется другими программами")
