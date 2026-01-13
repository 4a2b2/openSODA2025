#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub流行项目分析器 - 重新定义流行项目的概念
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
import statistics
import argparse

class GitHubPopularProjectsAnalyzer:
    def __init__(self, data_dir="github_new_trend/data_2025"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path("github_new_trend/visualizations")
        self.output_dir.mkdir(exist_ok=True)
        
    def get_stars_count(self, stars):
        """安全地获取项目星数，处理不同数据类型"""
        if stars is None:
            return 0
        if isinstance(stars, str):
            # 移除逗号并尝试转换为整数
            stars = stars.replace(',', '')
            try:
                return int(stars) if stars.isdigit() else 0
            except ValueError:
                return 0
        elif isinstance(stars, (int, float)):
            return int(stars)
        else:
            return 0
    
    def analyze_popular_projects(self, month_data):
        """
        分析月度流行项目
        定义1: 高星数项目 (star >= 1000)
        定义2: 高增长项目 (星数增长率)
        定义3: 多功能项目 (有description且有topics)
        """
        if not month_data:
            return {
                "total_projects": 0,
                "high_star_projects": 0,
                "high_growth_projects": 0,
                "comprehensive_projects": 0,
                "total_stars": 0,
                "avg_stars": 0,
                "top_projects": []
            }
        
        total_projects = len(month_data)
        # 使用安全的方法获取星数
        total_stars = 0
        for p in month_data:
            stars = self.get_stars_count(p.get('stars_count', 0))
            total_stars += stars
        
        avg_stars = total_stars / total_projects if total_projects > 0 else 0
        
        # 定义1: 高星数项目 (>= 1000 stars)
        high_star_projects = []
        for p in month_data:
            stars = self.get_stars_count(p.get('stars_count', 0))
            if stars >= 1000:
                high_star_projects.append(p)
        
        # 适中标准: 星数>=2000, 有描述, 有topics, 有语言 (满足3个条件即可)
        moderate_projects = []
        for p in month_data:
            stars = self.get_stars_count(p.get('stars_count', 0))
            description = p.get('description', '') or ''
            topics = p.get('topics', []) or []
            language = p.get('language', '') or ''
            
            meets_stars = stars >= 2000
            has_description = len(description.strip()) > 20
            has_topics = len(topics) >= 1
            has_language = bool(language and language != 'null' and language.strip())
            
            # 至少满足3个条件
            conditions_met = sum([meets_stars, has_description, has_topics, has_language])
            if conditions_met >= 3:
                moderate_projects.append(p)
        
        # 如果适中标准下项目太少，则使用更宽松的标准
        if len(moderate_projects) < 10:
            basic_projects = []
            for p in month_data:
                stars = self.get_stars_count(p.get('stars_count', 0))
                if stars >= 1000:  # 最基本的标准：1000+ stars
                    basic_projects.append(p)
            popular_projects = basic_projects  # 不限制数量
        else:
            popular_projects = moderate_projects  # 不限制数量
        
        # 获取前10个项目
        top_projects = sorted(month_data, key=lambda p: self.get_stars_count(p.get('stars_count', 0)), reverse=True)[:10]
        
        return {
            "total_projects": total_projects,
            "high_star_projects": len(high_star_projects),
            "popular_projects": len(popular_projects),
            "total_stars": total_stars,
            "avg_stars": round(avg_stars, 1),
            "top_projects": top_projects
        }
    
    def calculate_monthly_popular_trends(self):
        """计算月度流行项目趋势"""
        monthly_trends = {}
        language_stats = defaultdict(list)
        monthly_analysis = {}
        
        # 获取所有月度数据文件
        monthly_files = sorted([f for f in self.data_dir.glob("monthly_trends_*.json")])
        
        for file_path in monthly_files:
            month = file_path.stem.replace("monthly_trends_", "")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    month_data = json.load(f)
                
                # 分析这个月的流行项目
                analysis = self.analyze_popular_projects(month_data)
                monthly_analysis[month] = analysis
                
                # 使用严格标准下的流行项目数量
                monthly_trends[month] = analysis["popular_projects"]
                
                # 收集语言统计
                for project in month_data:
                    lang = project.get('language', 'Unknown')
                    if lang and lang != 'null':
                        stars = self.get_stars_count(project.get('stars_count', 0))
                        language_stats[lang].append(stars)
                        
            except Exception as e:
                import traceback
                print(f"❌ 处理 {month} 数据时出错: {e}")
                print(f"   详细错误: {traceback.format_exc()}")
                continue
        
        return monthly_trends, monthly_analysis, dict(language_stats)
    
    def generate_comprehensive_report(self):
        """生成综合报告"""
        print("📊 分析GitHub 2025年流行项目趋势...")
        
        monthly_trends, monthly_analysis, language_stats = self.calculate_monthly_popular_trends()
        
        if not monthly_trends:
            print("❌ 没有找到有效的月度数据")
            return
        
        # 计算语言统计
        language_summary = {}
        for lang, stars_list in language_stats.items():
            if stars_list:
                language_summary[lang] = {
                    "count": len(stars_list),
                    "avg_stars": round(statistics.mean(stars_list), 1),
                    "total_stars": sum(stars_list)
                }
        
        # 找出最热门的语言
        top_languages = sorted(language_summary.items(), 
                             key=lambda x: x[1]["count"], reverse=True)[:10]
        
        # 生成报告
        report = {
            "year": 2025,
            "analysis_date": "2026-01-05",
            "popular_project_definition": {
                "strict_criteria": "严格标准: >=5000 stars + 详细描述(50+字符) + 技术标签(3+个) + 编程语言",
                "moderate_criteria": "适中标准: >=2000 stars + 描述 + 技术标签 + 编程语言 (满足3个条件)",
                "basic_criteria": "基本标准: >=1000 stars (最多20个项目)",
                "star_thresholds": {
                    "strict": ">= 5000 stars",
                    "moderate": ">= 2000 stars", 
                    "basic": ">= 1000 stars"
                }
            },
            "monthly_popular_projects": monthly_trends,
            "monthly_analysis": monthly_analysis,
            "language_statistics": language_summary,
            "top_languages": top_languages,
            "summary": {
                "total_months_analyzed": len(monthly_trends),
                "total_popular_projects": sum(monthly_trends.values()),
                "avg_popular_projects_per_month": round(statistics.mean(monthly_trends.values()), 1),
                "peak_month": max(monthly_trends.items(), key=lambda x: int(x[1]))[0] if monthly_trends else None,
                "lowest_month": min(monthly_trends.items(), key=lambda x: int(x[1]))[0] if monthly_trends else None
            }
        }
        
        # 保存报告
        report_file = self.data_dir / "popular_projects_analysis_2025.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 流行项目分析完成!")
        print(f"📁 报告保存至: {report_file}")
        print(f"📊 分析了 {len(monthly_trends)} 个月的数据")
        print(f"🎯 每月平均 {report['summary']['avg_popular_projects_per_month']} 个流行项目")
        
        return report

def main():
    parser = argparse.ArgumentParser(description='GitHub流行项目分析器')
    parser.add_argument('--data-dir', default='data_2025', help='数据目录')
    
    args = parser.parse_args()
    
    analyzer = GitHubPopularProjectsAnalyzer(args.data_dir)
    analyzer.generate_comprehensive_report()

if __name__ == "__main__":
    main()