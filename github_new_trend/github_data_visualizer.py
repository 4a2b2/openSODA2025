#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub数据可视化工具
生成2025年GitHub项目趋势的各种统计图表
"""

import json
import os
import glob
from datetime import datetime
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")

# 动态设置中文字体
try:
    # 尝试设置支持中文的字体
    import matplotlib.font_manager as fm
    font_list = [f.name for f in fm.fontManager.ttflist]
    chinese_fonts = ['DejaVu Sans', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'Noto Sans CJK SC']
    
    selected_font = 'DejaVu Sans'  # 默认使用
    for font in chinese_fonts:
        if font in font_list:
            selected_font = font
            break
    
    plt.rcParams['font.sans-serif'] = [selected_font]
    print(f"✅ 使用字体: {selected_font}")
except:
    print("⚠️ 字体设置失败，使用默认字体")

class GitHubDataVisualizer:
    def __init__(self, data_dir="data_2025", output_dir="visualizations"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 颜色配置
        self.colors = {
            'python': '#3776ab',
            'javascript': '#f7df1e',
            'typescript': '#3178c6',
            'java': '#ed8b00',
            'go': '#00add8',
            'rust': '#ce422b',
            'cpp': '#00599c',
            'c': '#a8b9cc',
            'csharp': '#239120',
            'shell': '#89e051',
            'other': '#8b949e'
        }
        
        # 加载数据
        yearly_loaded = self._load_yearly_data()
        if not yearly_loaded:
            print("❌ Failed to load yearly data")
        self.monthly_data = self._load_monthly_data()
        self.current_trending = self._load_current_trending()

    def _load_yearly_data(self):
        """Load yearly data from the report file"""
        # 优先使用流行项目分析数据
        popular_report_file = self.data_dir / "popular_projects_analysis_2025.json"
        yearly_report_file = self.data_dir / "github_2025_yearly_report.json"
        
        if popular_report_file.exists():
            print("📊 Loading popular projects analysis data...")
            try:
                with open(popular_report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 将流行项目分析数据转换为可视化脚本需要的格式
                self.yearly_data = {
                    "year": data["year"],
                    "collection_date": data["analysis_date"],
                    "summary": {
                        "total_projects": sum(data["monthly_analysis"][month]["total_projects"] for month in data["monthly_analysis"]),
                        "languages_covered": list(data["language_statistics"].keys())[:10],
                        "months_covered": list(data["monthly_popular_projects"].keys()),
                        "successful_requests": len(data["monthly_popular_projects"]),
                        "failed_requests": 0
                    },
                    "monthly_trends": data["monthly_popular_projects"],
                    "language_breakdown": data["language_statistics"],
                    "top_10_hot_projects": [],
                    "detailed_data": {
                        "monthly": data["monthly_analysis"]
                    },
                    "popular_project_definition": data["popular_project_definition"]
                }
                return True
            except Exception as e:
                print(f"❌ Error loading popular projects data: {e}")
        
        # 备用：使用原始年度数据
        if yearly_report_file.exists():
            print("📊 Loading original yearly data...")
            try:
                with open(yearly_report_file, 'r', encoding='utf-8') as f:
                    self.yearly_data = json.load(f)
                return True
            except Exception as e:
                print(f"❌ Error loading yearly data: {e}")
                return False
                
        print(f"❌ No report files found")
        return False

    def _load_monthly_data(self):
        """加载月度数据"""
        monthly_files = glob.glob(str(self.data_dir / "monthly_trends_*.json"))
        monthly_data = {}
        
        for file_path in monthly_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:
                        # 从文件名提取月份
                        month = Path(file_path).stem.replace("monthly_trends_", "20")
                        monthly_data[month] = data
            except Exception as e:
                print(f"警告: 无法加载 {file_path}: {e}")
        
        return monthly_data

    def _load_current_trending(self):
        """加载当前趋势数据"""
        trending_files = glob.glob("github_trending_*_*.json")
        if trending_files:
            # 获取最新的趋势文件
            latest_file = max(trending_files, key=os.path.getctime)
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告: 无法加载趋势数据 {latest_file}: {e}")
        return []

    def generate_monthly_trends_chart(self):
        """Generate Monthly Trends Chart"""
        print("📊 Generating monthly trends chart...")
        
        if not self.yearly_data.get('monthly_trends'):
            print("❌ No monthly trends data available")
            return
        
        # 处理月度趋势数据 - 转换键格式
        monthly_trends = self.yearly_data['monthly_trends']
        formatted_trends = {}
        
        for month_key, count in monthly_trends.items():
            # 将"202501"格式转换为"2025-01"格式
            if len(month_key) == 6 and month_key.isdigit():
                formatted_month = f"{month_key[:4]}-{month_key[4:]}"
                formatted_trends[formatted_month] = count
            else:
                formatted_trends[month_key] = count
        
        months = list(formatted_trends.keys())
        counts = list(formatted_trends.values())
        
        # Sort by month order
        month_order = ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06',
                      '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12']
        
        sorted_months = []
        sorted_counts = []
        for month in month_order:
            if month in months:
                sorted_months.append(month)
                sorted_counts.append(formatted_trends[month])
        
        plt.figure(figsize=(12, 6))
        
        # Bar chart
        bars = plt.bar(range(len(sorted_months)), sorted_counts, 
                      color='skyblue', alpha=0.8, edgecolor='navy', linewidth=1)
        
        # Line chart
        plt.plot(range(len(sorted_months)), sorted_counts, 
                color='red', marker='o', linewidth=2, markersize=8, label='Trend Line')
        
        plt.title('GitHub 2025 Monthly Popular Project Count Trends', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Number of Projects', fontsize=12)
        plt.xticks(range(len(sorted_months)), 
                  [month.split('-')[1] for month in sorted_months], 
                  rotation=45)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, sorted_counts)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'monthly_trends_2025.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Monthly trends chart saved")

    def generate_language_distribution_chart(self):
        """生成编程语言分布图表"""
        print("💻 生成编程语言分布图表...")
        
        # 收集所有项目的语言信息
        language_stats = Counter()
        
        # 从月度数据收集
        for month_data in self.monthly_data.values():
            for project in month_data:
                lang = project.get('language') or 'Unknown'
                if lang and lang != 'null':
                    language_stats[lang] += 1
        
        # 从当前趋势数据收集
        for project in self.current_trending:
            lang = project.get('language') or 'Unknown'
            if lang and lang != 'null':
                language_stats[lang] += 1
        
        if not language_stats:
            print("❌ 没有编程语言数据")
            return
        
        # 取前10种语言
        top_languages = language_stats.most_common(10)
        languages = [item[0] for item in top_languages]
        counts = [item[1] for item in top_languages]
        
        # 创建饼图
        plt.figure(figsize=(10, 8))
        
        # 为每种语言分配颜色
        colors = []
        for lang in languages:
            if lang.lower() in self.colors:
                colors.append(self.colors[lang.lower()])
            else:
                colors.append(self.colors['other'])
        
        wedges, texts, autotexts = plt.pie(counts, labels=languages, autopct='%1.1f%%',
                                          colors=colors, startangle=90, 
                                          explode=[0.05 if i < 3 else 0 for i in range(len(languages))])
        
        plt.title('GitHub Programming Language Distribution (2025)', fontsize=16, fontweight='bold', pad=20)
        
        # 美化文本
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
        
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'language_distribution_2025.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 生成横向条形图
        plt.figure(figsize=(12, 8))
        
        bars = plt.barh(range(len(languages)), counts, color=colors, alpha=0.8)
        plt.yticks(range(len(languages)), languages)
        plt.xlabel('Number of Projects', fontsize=12)
        plt.title('GitHub Programming Language Distribution (Horizontal Bar Chart)', fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for i, (bar, count) in enumerate(zip(bars, counts)):
            plt.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(count), ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'language_distribution_bar_2025.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Programming language distribution charts saved")

    def generate_top_projects_chart(self):
        """Generate Top Projects Chart"""
        print("🏆 Generating top projects chart...")
        
        # 收集所有项目数据
        all_projects = []
        
        # 从月度数据收集
        for month_data in self.monthly_data.values():
            for project in month_data:
                stars = project.get('stars_count', 0)
                if isinstance(stars, str):
                    stars = int(stars.replace(',', '')) if stars.replace(',', '').isdigit() else 0
                
                all_projects.append({
                    'name': project.get('name', 'Unknown'),
                    'full_name': project.get('full_name', 'Unknown'),
                    'author': project.get('author', 'Unknown'),
                    'stars': stars,
                    'language': project.get('language', 'Unknown'),
                    'description': project.get('description', '')
                })
        
        # 从当前趋势数据收集
        for project in self.current_trending:
            stars_str = project.get('stars', '0')
            stars = int(stars_str.replace(',', '')) if isinstance(stars_str, str) and stars_str.replace(',', '').isdigit() else 0
            
            all_projects.append({
                'name': project.get('name', 'Unknown'),
                'full_name': project.get('full_name', 'Unknown'),
                'author': project.get('author', 'Unknown'),
                'stars': stars,
                'language': project.get('language', 'Unknown'),
                'description': project.get('description', '')
            })
        
        if not all_projects:
            print("❌ 没有项目数据")
            return
        
        # 去重并排序
        unique_projects = {}
        for project in all_projects:
            key = project['full_name']
            if key not in unique_projects or project['stars'] > unique_projects[key]['stars']:
                unique_projects[key] = project
        
        # 按星标数排序，取前20
        top_projects = sorted(unique_projects.values(), key=lambda x: x['stars'], reverse=True)[:20]
        
        # 创建排行榜
        plt.figure(figsize=(18, 14))  # 增加图表宽度和高度
        
        names = [p['name'] for p in top_projects]
        stars = [p['stars'] for p in top_projects]
        languages = [p['language'] for p in top_projects]
        
        # 为每种语言分配颜色
        colors = []
        for lang in languages:
            colors.append(self.colors.get(lang.lower(), self.colors['other']) if lang else self.colors['other'])
        
        bars = plt.barh(range(len(names)), stars, color=colors, alpha=0.8, height=0.8)
        
        # 处理长项目名称，自动换行
        wrapped_names = []
        for name in names:
            if len(name) > 30:
                # 尝试在连字符处换行
                if '-' in name:
                    parts = name.split('-')
                    # 找到合适的换行位置
                    for i in range(1, len(parts)):
                        first_part = '-'.join(parts[:i])
                        second_part = '-'.join(parts[i:])
                        if len(first_part) > 15 and len(second_part) > 10:
                            wrapped_names.append(f"{first_part}\
{second_part}")
                            break
                    else:
                        # 如果没有合适的连字符位置，直接截断
                        wrapped_names.append(name[:35] + '...')
                else:
                    # 没有连字符，直接截断
                    wrapped_names.append(name[:35] + '...')
            else:
                wrapped_names.append(name)
        
        plt.yticks(range(len(names)), wrapped_names, fontsize=10, linespacing=1.5)
        plt.xlabel('Stars Count', fontsize=12)
        plt.title('GitHub 2025 Most Popular Projects Ranking (Top 20)', fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for i, (bar, star_count) in enumerate(zip(bars, stars)):
            plt.text(bar.get_width() + max(stars) * 0.01, bar.get_y() + bar.get_height()/2,
                    f'{star_count:,}', ha='left', va='center', fontweight='bold', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'top_projects_2025.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Top projects ranking chart saved")

    def generate_language_stars_chart(self):
        """Generate Language Average Stars Chart"""
        print("⭐ Generating language average stars chart...")
        
        # 收集语言和星标数据
        language_stats = defaultdict(list)
        
        # 从月度数据收集
        for month_data in self.monthly_data.values():
            for project in month_data:
                lang = project.get('language') or 'Unknown'
                stars = project.get('stars_count', 0)
                if isinstance(stars, str):
                    stars = int(stars.replace(',', '')) if stars.replace(',', '').isdigit() else 0
                
                if lang and lang != 'null' and stars > 0:
                    language_stats[lang].append(stars)
        
        # 从当前趋势数据收集
        for project in self.current_trending:
            lang = project.get('language') or 'Unknown'
            stars_str = project.get('stars', '0')
            stars = int(stars_str.replace(',', '')) if isinstance(stars_str, str) and stars_str.replace(',', '').isdigit() else 0
            
            if lang and lang != 'null' and stars > 0:
                language_stats[lang].append(stars)
        
        # 计算平均星标数
        avg_stars = {}
        for lang, stars_list in language_stats.items():
            if len(stars_list) >= 2:  # 至少2个项目
                avg_stars[lang] = sum(stars_list) / len(stars_list)
        
        if not avg_stars:
            print("❌ 没有足够的语言数据")
            return
        
        # 取前10种语言
        top_languages = sorted(avg_stars.items(), key=lambda x: x[1], reverse=True)[:10]
        languages = [item[0] for item in top_languages]
        avg_star_counts = [item[1] for item in top_languages]
        
        plt.figure(figsize=(12, 8))
        
        colors = []
        for lang in languages:
            if lang.lower() in self.colors:
                colors.append(self.colors[lang.lower()])
            else:
                colors.append(self.colors['other'])
        
        bars = plt.bar(range(len(languages)), avg_star_counts, color=colors, alpha=0.8)
        plt.xticks(range(len(languages)), languages, rotation=45, ha='right')
        plt.ylabel('Average Stars Count', fontsize=12)
        plt.title('Average Stars Count by Programming Language (2025)', fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, avg_count in zip(bars, avg_star_counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_star_counts) * 0.01,
                    f'{avg_count:.0f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'language_avg_stars_2025.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Language average stars chart saved")

    def generate_comprehensive_dashboard(self):
        """Generate Comprehensive Dashboard"""
        print("📊 Generating comprehensive dashboard...")
        
        # 创建2x2的子图布局
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('GitHub 2025 Project Trends Analysis Dashboard', fontsize=20, fontweight='bold', y=0.98)
        
        # 1. 月度趋势图
        if self.yearly_data.get('monthly_trends'):
            monthly_trends = self.yearly_data['monthly_trends']
            
            # 处理月度趋势数据 - 转换键格式
            formatted_trends = {}
            for month_key, count in monthly_trends.items():
                # 将"202501"格式转换为"2025-01"格式
                if len(month_key) == 6 and month_key.isdigit():
                    formatted_month = f"{month_key[:4]}-{month_key[4:]}"
                    formatted_trends[formatted_month] = count
                else:
                    formatted_trends[month_key] = count
            
            months = list(formatted_trends.keys())
            counts = list(formatted_trends.values())
            
            month_order = ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06',
                          '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12']
            
            sorted_months = []
            sorted_counts = []
            for month in month_order:
                if month in months:
                    sorted_months.append(month.split('-')[1])
                    sorted_counts.append(formatted_trends[month])
            
            ax1.bar(sorted_months, sorted_counts, color='skyblue', alpha=0.8)
            ax1.set_title('Monthly Project Trends', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Number of Projects')
            ax1.grid(True, alpha=0.3)
        
        # 2. 编程语言分布饼图
        language_stats = Counter()
        for month_data in self.monthly_data.values():
            for project in month_data:
                lang = project.get('language') or 'Unknown'
                if lang and lang != 'null':
                    language_stats[lang] += 1
        
        if language_stats:
            top_languages = language_stats.most_common(8)
            languages = [item[0] for item in top_languages]
            counts = [item[1] for item in top_languages]
            
            colors = []
            for lang in languages:
                if lang.lower() in self.colors:
                    colors.append(self.colors[lang.lower()])
                else:
                    colors.append(self.colors['other'])
            
            ax2.pie(counts, labels=languages, autopct='%1.1f%%', colors=colors, startangle=90)
            ax2.set_title('Programming Language Distribution', fontsize=14, fontweight='bold')
        
        # 3. 顶级项目横向条形图
        all_projects = []
        for month_data in self.monthly_data.values():
            for project in month_data:
                stars = project.get('stars_count', 0)
                if isinstance(stars, str):
                    stars = int(stars.replace(',', '')) if stars.replace(',', '').isdigit() else 0
                
                all_projects.append({
                    'name': project.get('name', 'Unknown'),
                    'stars': stars
                })
        
        if all_projects:
            top_projects = sorted(all_projects, key=lambda x: x['stars'], reverse=True)[:10]
            # 增加截断长度，确保长项目名也能完整显示
            names = [p['name'][:30] + '...' if len(p['name']) > 30 else p['name'] for p in top_projects]
            stars = [p['stars'] for p in top_projects]
            
            bars = ax3.barh(range(len(names)), stars, color='lightcoral', alpha=0.8)
            ax3.set_yticks(range(len(names)))
            ax3.set_yticklabels(names, fontsize=10)
            ax3.set_title('Top 10 Popular Projects', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Stars Count')
            ax3.grid(True, alpha=0.3, axis='x')
        
        # 4. 统计信息文本
        stats_text = self._generate_stats_text()
        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('Statistics Summary', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comprehensive_dashboard_2025.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Comprehensive dashboard saved")

    def _generate_stats_text(self):
        """生成统计信息文本"""
        total_projects = 0
        total_stars = 0
        languages_set = set()
        
        for month_data in self.monthly_data.values():
            for project in month_data:
                total_projects += 1
                stars = project.get('stars_count', 0)
                if isinstance(stars, str):
                    stars = int(stars.replace(',', '')) if stars.replace(',', '').isdigit() else 0
                total_stars += stars
                
                lang = project.get('language')
                if lang and lang != 'null':
                    languages_set.add(lang)
        
        # 添加当前趋势数据
        for project in self.current_trending:
            total_projects += 1
            stars_str = project.get('stars', '0')
            stars = int(stars_str.replace(',', '')) if isinstance(stars_str, str) and stars_str.replace(',', '').isdigit() else 0
            total_stars += stars
            
            lang = project.get('language')
            if lang and lang != 'null':
                languages_set.add(lang)
        
        # 动态查找最高星项目
        highest_star_project = None
        max_stars = 0
        
        # 遍历所有月度数据查找最高星项目
        all_projects = []
        for month_data in self.monthly_data.values():
            all_projects.extend(month_data)
        all_projects.extend(self.current_trending)
        
        for project in all_projects:
            stars = project.get('stars_count', 0)
            if isinstance(stars, str):
                stars = int(stars.replace(',', '')) if stars.replace(',', '').isdigit() else 0
            elif not isinstance(stars, (int, float)):
                stars = 0
            
            if stars > max_stars:
                max_stars = stars
                highest_star_project = project
        
        # 获取最高星项目信息
        highest_project_name = highest_star_project.get('name', 'Unknown') if highest_star_project else 'Unknown'
        
        stats = f"""Data Collection Statistics:
━━━━━━━━━━━━━━━━━━━━

Total Projects: {total_projects:,}
Total Stars: {total_stars:,}
Programming Languages: {len(languages_set)}
Covered Months: {len(self.monthly_data)}

Highest Starred Project:
   {highest_project_name}: {max_stars:,} stars
   
Data Time Range:
   Jan 2025 - Dec 2025
   + Jan 2026 Latest Trends

Data Collection Success Rate:
   {self.yearly_data.get('summary', {}).get('successful_requests', 0)} Success
   {self.yearly_data.get('summary', {}).get('failed_requests', 0)} Failed"""
        
        return stats

    def generate_all_charts(self):
        """生成所有图表"""
        print("🚀 开始生成所有可视化图表...")
        print("=" * 50)
        
        # 生成各种图表
        self.generate_monthly_trends_chart()
        self.generate_language_distribution_chart()
        self.generate_top_projects_chart()
        self.generate_language_stars_chart()
        self.generate_comprehensive_dashboard()
        
        print("=" * 50)
        print("🎉 All charts generated successfully!")
        print(f"📁 图表保存在: {self.output_dir.absolute()}")
        print(f"🖼️ 生成的文件:")
        
        for file in self.output_dir.glob("*.png"):
            print(f"   - {file.name}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub数据可视化工具')
    parser.add_argument('--data-dir', '-d', default='data_2025',
                       help='数据目录 (默认: data_2025)')
    parser.add_argument('--output-dir', '-o', default='visualizations',
                       help='输出目录 (默认: visualizations)')
    parser.add_argument('--chart-type', '-c', 
                       choices=['all', 'monthly', 'language', 'projects', 'dashboard'],
                       default='all',
                       help='图表类型: all(全部), monthly(月度), language(语言), projects(项目), dashboard(仪表板)')
    
    args = parser.parse_args()
    
    visualizer = GitHubDataVisualizer(data_dir=args.data_dir, output_dir=args.output_dir)
    
    if args.chart_type == 'all':
        visualizer.generate_all_charts()
    elif args.chart_type == 'monthly':
        visualizer.generate_monthly_trends_chart()
    elif args.chart_type == 'language':
        visualizer.generate_language_distribution_chart()
    elif args.chart_type == 'projects':
        visualizer.generate_top_projects_chart()
    elif args.chart_type == 'dashboard':
        visualizer.generate_comprehensive_dashboard()

if __name__ == "__main__":
    main()