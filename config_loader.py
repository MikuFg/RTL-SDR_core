#!/usr/bin/env python3
"""
Модуль для загрузки конфигурации из YAML файла
"""

import yaml
import os
from typing import Dict, Any, Optional


class ConfigLoader:
    """Класс для загрузки и управления конфигурацией"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Инициализация загрузчика конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = config_path
        self.config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Загружает конфигурацию из YAML файла"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        print(f"✅ Конфигурация загружена из {self.config_path}")
    
    def get(self, *keys, default: Any = None) -> Any:
        """
        Получает значение из конфигурации по вложенным ключам
        
        Args:
            *keys: Ключи для доступа к вложенным значениям
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Значение из конфигурации или default
        """
        if self.config is None:
            return default
        
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_rtl_sdr_config(self, preset: str = "default") -> Dict[str, Any]:
        """
        Получает конфигурацию RTL-SDR
        
        Args:
            preset: Имя предустановки (default, aircraft, weather, radio, drone, custom)
            
        Returns:
            Словарь с параметрами RTL-SDR
        """
        if preset == "default":
            return self.get("rtl_sdr", "default", default={})
        else:
            return self.get("rtl_sdr", "presets", preset, default=self.get("rtl_sdr", "default", default={}))
    
    def get_signal_processing_config(self) -> Dict[str, Any]:
        """Получает конфигурацию обработки сигналов"""
        return self.get("signal_processing", default={})
    
    def get_model_config(self) -> Dict[str, Any]:
        """Получает конфигурацию модели"""
        return self.get("model", default={})
    
    def get_server_config(self) -> Dict[str, Any]:
        """Получает конфигурацию серверов"""
        return self.get("servers", default={})
    
    def get_simulation_config(self) -> Dict[str, Any]:
        """Получает конфигурацию симуляции"""
        return self.get("simulation", default={})
    
    def get_paths_config(self) -> Dict[str, Any]:
        """Получает конфигурацию путей"""
        return self.get("paths", default={})
    
    def get_realtime_config(self) -> Dict[str, Any]:
        """Получает конфигурацию режима реального времени"""
        return self.get("realtime", default={})
    
    def reload(self) -> None:
        """Перезагружает конфигурацию из файла"""
        self._load_config()
    
    def __repr__(self) -> str:
        return f"ConfigLoader(config_path='{self.config_path}')"


# Глобальный экземпляр загрузчика конфигурации
_global_config = None


def get_config(config_path: str = "config.yaml") -> ConfigLoader:
    """
    Получает глобальный экземпляр загрузчика конфигурации
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Экземпляр ConfigLoader
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader(config_path)
    return _global_config


if __name__ == "__main__":
    # Тест загрузки конфигурации
    try:
        config = get_config()
        
        print("\n=== RTL-SDR Configuration ===")
        print(f"Default center_freq: {config.get('rtl_sdr', 'default', 'center_freq')}")
        print(f"Default sample_rate: {config.get('rtl_sdr', 'default', 'sample_rate')}")
        
        print("\n=== Available Presets ===")
        for preset_name in config.get("rtl_sdr", "presets", {}).keys():
            preset = config.get_rtl_sdr_config(preset_name)
            print(f"{preset_name}: {preset.get('description', 'N/A')}")
        
        print("\n=== Signal Processing ===")
        sig_config = config.get_signal_processing_config()
        print(f"Sample rate: {sig_config.get('sample_rate')}")
        print(f"FFT size: {sig_config.get('fft_size')}")
        
        print("\n=== Servers ===")
        server_config = config.get_server_config()
        print(f"Go server URL: {server_config.get('go_server', {}).get('url')}")
        print(f"WebSocket URL: {server_config.get('websocket', {}).get('url')}")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Убедитесь, что файл config.yaml существует в директории проекта")
