import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

class RadarJSONFormatter:
    """Класс для форматирования результатов распознавания в JSON"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def format_detection_result(self, 
                              detection_data: Dict[str, Any],
                              target_id: str = None,
                              location: Dict[str, float] = None) -> Dict[str, Any]:
        """Форматирует результат обнаружения объекта"""
        
        result = {
            "detection_id": target_id or f"DET_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": detection_data.get('timestamp', datetime.now().isoformat()),
            "object_info": {
                "type": detection_data.get('prediction', 'unknown'),
                "confidence": detection_data.get('confidence', 0.0),
                "is_reliable": detection_data.get('is_reliable', False)
            },
            "location": location or {
                "azimuth": 0.0,
                "range": 0.0,
                "altitude": 0.0
            },
            "signal_analysis": detection_data.get('signal_analysis', {}),
            "risk_assessment": detection_data.get('risk_assessment', 'unknown'),
            "signal_quality": detection_data.get('signal_quality', 'unknown'),
            "model_info": detection_data.get('model_info', {})
        }
        
        return result
    
    def format_batch_results(self, 
                           detections: List[Dict[str, Any]], 
                           session_id: str = None) -> Dict[str, Any]:
        """Форматирует пакет результатов обнаружения"""
        
        session_id = session_id or f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        batch_result = {
            "session_id": session_id,
            "session_start": datetime.now().isoformat(),
            "total_detections": len(detections),
            "detections": detections,
            "summary": self._generate_summary(detections)
        }
        
        return batch_result
    
    def _generate_summary(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Генерирует сводку по обнаружениям"""
        
        if not detections:
            return {"message": "No detections"}
        
        # Статистика по типам объектов
        object_counts = {}
        confidence_sum = 0
        reliable_count = 0
        
        for detection in detections:
            obj_type = detection.get('object_info', {}).get('type', 'unknown')
            object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
            
            confidence = detection.get('object_info', {}).get('confidence', 0)
            confidence_sum += confidence
            
            if detection.get('object_info', {}).get('is_reliable', False):
                reliable_count += 1
        
        return {
            "object_distribution": object_counts,
            "average_confidence": confidence_sum / len(detections),
            "reliable_detections": reliable_count,
            "reliability_rate": reliable_count / len(detections),
            "most_common_object": max(object_counts, key=object_counts.get) if object_counts else "unknown"
        }
    
    def save_to_file(self, data: Dict[str, Any], filename: str = None) -> str:
        """Сохраняет данные в JSON файл"""
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"radar_detection_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def load_from_file(self, filename: str) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_real_time_update(self, 
                              detection_data: Dict[str, Any],
                              target_id: str,
                              location: Dict[str, float]) -> Dict[str, Any]:
        """Создает JSON для обновления в реальном времени"""
        
        return {
            "type": "real_time_update",
            "timestamp": datetime.now().isoformat(),
            "target_id": target_id,
            "prediction": detection_data.get('prediction', 'unknown'),
            "confidence": detection_data.get('confidence', 0.0),
            "location": location,
            "risk_level": detection_data.get('risk_assessment', 'unknown'),
            "signal_quality": detection_data.get('signal_quality', 'unknown')
        }
    
    def format_error_report(self, 
                          error_message: str,
                          error_type: str = "processing_error",
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Форматирует отчет об ошибке"""
        
        return {
            "type": "error_report",
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "system_info": {
                "python_version": "3.x",
                "platform": "windows"
            }
        }
    
    def get_latest_results(self, limit: int = 10) -> List[str]:
        """Получает список последних файлов с результатами"""
        
        json_files = list(self.output_dir.glob("*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return [str(f) for f in json_files[:limit]]
    
    def cleanup_old_files(self, days_old: int = 7):
        """Удаляет старые файлы результатов"""
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        
        for filepath in self.output_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff_time:
                filepath.unlink()
                print(f"Удален старый файл: {filepath}")

class RadarReportGenerator:
    """Генератор отчетов по результатам работы радара"""
    
    def __init__(self, formatter: RadarJSONFormatter):
        self.formatter = formatter
    
    def generate_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Генерирует дневной отчет"""
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Загрузка всех файлов за день
        daily_data = []
        date_formatted = date.replace('-', '')  # Конвертируем 2023-12-01 в 20231201
        for filename in os.listdir(self.formatter.output_dir):
            if date_formatted in filename and filename.endswith('.json'):
                try:
                    data = self.formatter.load_from_file(filename)
                    daily_data.append(data)
                except Exception as e:
                    print(f"Ошибка загрузки файла {filename}: {e}")
        
        # Генерация отчета
        report = {
            "report_date": date,
            "report_type": "daily_summary",
            "total_sessions": len(daily_data),
            "total_detections": sum(len(d.get('detections', [])) for d in daily_data),
            "generated_at": datetime.now().isoformat()
        }
        
        if daily_data:
            all_detections = []
            for session in daily_data:
                all_detections.extend(session.get('detections', []))
            
            report['summary'] = self.formatter._generate_summary(all_detections)
        else:
            # Добавляем пустой summary когда нет данных
            report['summary'] = {
                'total_detections': 0,
                'object_types': {},
                'average_confidence': 0.0,
                'risk_distribution': {}
            }
        
        return report
    
    def export_to_csv(self, json_data: Dict[str, Any], csv_filename: str = None) -> str:
        """Экспортирует данные в CSV формат"""
        
        import csv
        
        if not csv_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"radar_data_{timestamp}.csv"
        
        csv_path = self.formatter.output_dir / csv_filename
        
        detections = json_data.get('detections', [])
        
        if not detections:
            # Создаем пустой CSV файл с заголовками
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['detection_id', 'timestamp', 'object_type', 'confidence', 
                             'azimuth', 'range', 'altitude', 'risk_assessment', 'signal_quality']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            return str(csv_path)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['detection_id', 'timestamp', 'object_type', 'confidence', 
                         'azimuth', 'range', 'altitude', 'risk_assessment', 'signal_quality']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for detection in detections:
                writer.writerow({
                    'detection_id': detection.get('detection_id', ''),
                    'timestamp': detection.get('timestamp', ''),
                    'object_type': detection.get('object_info', {}).get('type', ''),
                    'confidence': detection.get('object_info', {}).get('confidence', 0),
                    'azimuth': detection.get('location', {}).get('azimuth', 0),
                    'range': detection.get('location', {}).get('range', 0),
                    'altitude': detection.get('location', {}).get('altitude', 0),
                    'risk_assessment': detection.get('risk_assessment', ''),
                    'signal_quality': detection.get('signal_quality', '')
                })
        
        return str(csv_path)
