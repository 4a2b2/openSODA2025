#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理工具
"""

import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认使用项目根目录的config.json
        """
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # 使用默认配置
            self.config = {
                "data_paths": {
                    "external_metrics": "./top_300_metrics",
                    "project_root": ".",
                    "output_dir": "./output",
                    "final_report_dir": "./final_report",
                    "github_new_trend_dir": "./github_new_trend"
                },
                "analysis": {
                    "time_window": 6,
                    "star_threshold": 5000,
                    "popular_project_definition": "strict"
                },
                "visualization": {
                    "font_size": 10,
                    "figsize": [16, 12],
                    "dpi": 300
                }
            }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔路径（如 "data_paths.external_metrics"）
            default: 默认值
        
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_path(self, key: str, relative_to_project: bool = True) -> Path:
        """
        获取路径配置
        
        Args:
            key: 配置键
            relative_to_project: 是否相对于项目根目录
        
        Returns:
            路径对象
        """
        path_str = self.get(key)
        if not path_str:
            return Path('.')
        
        path = Path(path_str)
        if relative_to_project and not path.is_absolute():
            project_root = self.get_project_root()
            return project_root / path
        
        return path
    
    def get_project_root(self) -> Path:
        """
        获取项目根目录路径
        
        Returns:
            项目根目录路径
        """
        return Path(self.get("data_paths.project_root", ".")).resolve()
    
    def get_external_metrics_path(self) -> Path:
        """
        获取外部指标数据路径
        
        Returns:
            外部指标数据路径
        """
        return self.get_path("data_paths.external_metrics")
    
    def get_output_dir(self) -> Path:
        """
        获取输出目录路径
        
        Returns:
            输出目录路径
        """
        return self.get_path("data_paths.output_dir")
    
    def get_final_report_dir(self) -> Path:
        """
        获取最终报告目录路径
        
        Returns:
            最终报告目录路径
        """
        return self.get_path("data_paths.final_report_dir")

# 全局配置实例
config_manager = ConfigManager()

# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return config_manager.get(key, default)

def get_path(key: str, relative_to_project: bool = True) -> Path:
    """获取路径配置"""
    return config_manager.get_path(key, relative_to_project)

def get_project_root() -> Path:
    """获取项目根目录"""
    return config_manager.get_project_root()

def get_external_metrics_path() -> Path:
    """获取外部指标数据路径"""
    return config_manager.get_external_metrics_path()

def get_output_dir() -> Path:
    """获取输出目录"""
    return config_manager.get_output_dir()

def get_final_report_dir() -> Path:
    """获取最终报告目录"""
    return config_manager.get_final_report_dir()
