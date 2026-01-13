#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub 2025年全年趋势数据收集器
收集2025年全年GitHub热门项目的趋势数据
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import argparse
from datetime import datetime, timedelta
import time
import os
import urllib3
from collections import defaultdict
import re

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GitHub2025DataCollector:
    def __init__(self):
        self.base_url = "https://github.com/trending"
        self.api_url = "https://api.github.com/search/repositories"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 2025年的月份定义
        self.months_2025 = [
            "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
            "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"
        ]
        
        # 主要编程语言列表
        self.target_languages = [
            "python", "javascript", "typescript", "java", "go", "rust", 
            "cpp", "c", "csharp", "php", "ruby", "swift", "kotlin", "scala"
        ]
        
        # 统计数据
        self.stats = {
            'total_projects': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'languages_covered': set(),
            'months_covered': set()
        }

    def collect_yearly_trends(self, output_dir="data_2025"):
        """
        收集2025年全年趋势数据
        
        Args:
            output_dir: 输出目录
        
        Returns:
            收集统计信息
        """
        print("🚀 开始收集2025年GitHub全年趋势数据")
        print("=" * 60)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 收集月度数据
        monthly_data = self._collect_monthly_data(output_dir)
        
        # 收集语言特定数据
        language_data = self._collect_language_data(output_dir)
        
        # 收集热门项目数据
        hot_projects = self._collect_hot_projects(output_dir)
        
        # 生成综合报告
        self._generate_yearly_report(output_dir, monthly_data, language_data, hot_projects)
        
        print("\n" + "=" * 60)
        print("📊 2025年数据收集完成！")
        print(f"   总项目数: {self.stats['total_projects']}")
        print(f"   成功请求: {self.stats['successful_requests']}")
        print(f"   失败请求: {self.stats['failed_requests']}")
        print(f"   覆盖语言: {len(self.stats['languages_covered'])}")
        print(f"   覆盖月份: {len(self.stats['months_covered'])}")
        print(f"   数据保存在: {output_dir}")
        
        return self.stats

    def _collect_monthly_data(self, output_dir):
        """收集每月趋势数据"""
        print("\n📅 收集月度趋势数据...")
        monthly_data = {}
        
        for month in self.months_2025:
            print(f"   正在收集 {month} 的数据...")
            
            # 检查数据文件是否已存在，如果存在则跳过收集
            filename = f"{output_dir}/monthly_trends_{month.replace('-', '')}.json"
            if os.path.exists(filename):
                print(f"     ⏭️  {month}: 数据文件已存在，跳过收集")
                # 读取已存在的数据
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        month_data = json.load(f)
                    monthly_data[month] = month_data
                    self.stats['months_covered'].add(month)
                except Exception as e:
                    print(f"     ⚠️  {month}: 读取已存在数据失败: {e}")
                    continue
                continue
            
            month_data = []
            
            try:
                # 获取月度样本数据
                daily_data = self._get_month_sample_data(month)
                if daily_data:
                    month_data.extend(daily_data)
                    time.sleep(1)  # 礼貌延迟
                else:
                    print(f"     ❌ {month}: 无数据")
                    continue
            except Exception as e:
                print(f"     ❌ {month}: 收集数据失败: {e}")
                continue
            
            if month_data:
                monthly_data[month] = month_data
                self.stats['months_covered'].add(month)
                
                # 保存月度数据
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(month_data, f, indent=2, ensure_ascii=False)
                
                print(f"     ✅ {month}: {len(month_data)} 个项目")
            else:
                print(f"     ❌ {month}: 无数据")
        
        return monthly_data

    def _collect_language_data(self, output_dir):
        """收集各编程语言的热门项目"""
        print("\n💻 收集编程语言数据...")
        language_data = {}
        
        for language in self.target_languages:
            print(f"   正在收集 {language} 语言数据...")
            
            try:
                # 使用GitHub API搜索2025年创建的项目
                language_projects = self._search_language_projects(language, months=12)
                
                if language_projects:
                    language_data[language] = language_projects
                    self.stats['languages_covered'].add(language)
                    self.stats['total_projects'] += len(language_projects)
                    
                    # 保存语言数据
                    filename = f"{output_dir}/language_{language}_2025.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(language_projects, f, indent=2, ensure_ascii=False)
                    
                    print(f"     ✅ {language}: {len(language_projects)} 个项目")
                else:
                    print(f"     ❌ {language}: 无数据")
                
                time.sleep(1)  # 礼貌延迟
                
            except Exception as e:
                print(f"     ❌ {language}: 收集失败 - {e}")
                self.stats['failed_requests'] += 1
        
        return language_data

    def _collect_hot_projects(self, output_dir):
        """收集2025年最热门的项目"""
        print("\n🔥 收集2025年最热门项目...")
        
        try:
            # 搜索2025年最热门的项目
            hot_projects = self._search_hot_projects()
            
            if hot_projects:
                self.stats['total_projects'] += len(hot_projects)
                
                # 保存热门项目数据
                filename = f"{output_dir}/hot_projects_2025.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(hot_projects, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ 收集到 {len(hot_projects)} 个热门项目")
                return hot_projects
            else:
                print(f"   ❌ 无热门项目数据")
                return []
                
        except Exception as e:
            print(f"   ❌ 收集热门项目失败: {e}")
            self.stats['failed_requests'] += 1
            return []

    def _get_month_sample_data(self, month):
        """获取月度样本数据"""
        try:
            # 模拟2025年月度数据
            # 实际实现中应该基于GitHub的搜索API按日期范围搜索
            
            url = self.api_url
            start_date = f"{month}-01"
            end_date = f"{month}-28"  # 使用28号确保月份有效
            
            params = {
                'q': f'created:{start_date}..{end_date}',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 100
            }
            
            response = self.session.get(url, params=params, verify=False, timeout=30)
            
            if response.status_code == 200:
                self.stats['successful_requests'] += 1
                data = response.json()
                projects = []
                
                for item in data.get('items', []):
                    project = {
                        'month': month,
                        'full_name': item['full_name'],
                        'name': item['name'],
                        'author': item['owner']['login'],
                        'description': item.get('description', ''),
                        'language': item.get('language', ''),
                        'stars_count': item['stargazers_count'],
                        'forks_count': item['forks_count'],
                        'created_at': item['created_at'],
                        'updated_at': item['updated_at'],
                        'url': item['html_url'],
                        'topics': item.get('topics', []),
                        'license': item.get('license', {}).get('name', '') if item.get('license') else '',
                        'open_issues': item.get('open_issues_count', 0),
                        'watchers': item.get('watchers_count', 0)
                    }
                    projects.append(project)
                
                return projects
            else:
                self.stats['failed_requests'] += 1
                print(f"     API请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            self.stats['failed_requests'] += 1
            print(f"     获取月度数据失败: {e}")
            return []

    def _search_language_projects(self, language, months=12):
        """搜索特定语言的2025年项目"""
        try:
            url = self.api_url
            
            # 计算2025年的日期范围
            end_date = "2025-12-31"
            start_date = "2025-01-01"
            
            params = {
                'q': f'language:{language} created:{start_date}..{end_date}',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 30
            }
            
            response = self.session.get(url, params=params, verify=False, timeout=30)
            
            if response.status_code == 200:
                self.stats['successful_requests'] += 1
                data = response.json()
                projects = []
                
                for item in data.get('items', []):
                    project = {
                        'language': language,
                        'full_name': item['full_name'],
                        'name': item['name'],
                        'author': item['owner']['login'],
                        'description': item.get('description', ''),
                        'stars_count': item['stargazers_count'],
                        'forks_count': item['forks_count'],
                        'created_at': item['created_at'],
                        'updated_at': item['updated_at'],
                        'url': item['html_url'],
                        'topics': item.get('topics', []),
                        'license': item.get('license', {}).get('name', '') if item.get('license') else '',
                        'open_issues': item.get('open_issues_count', 0),
                        'watchers': item.get('watchers_count', 0)
                    }
                    projects.append(project)
                
                return projects
            else:
                self.stats['failed_requests'] += 1
                return []
                
        except Exception as e:
            self.stats['failed_requests'] += 1
            return []

    def _search_hot_projects(self):
        """搜索2025年最热门的项目"""
        try:
            url = self.api_url
            
            # 搜索2025年最热门的项目（按stars排序）
            params = {
                'q': 'created:2025-01-01..2025-12-31',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 50
            }
            
            response = self.session.get(url, params=params, verify=False, timeout=30)
            
            if response.status_code == 200:
                self.stats['successful_requests'] += 1
                data = response.json()
                projects = []
                
                for item in data.get('items', []):
                    project = {
                        'rank': len(projects) + 1,
                        'full_name': item['full_name'],
                        'name': item['name'],
                        'author': item['owner']['login'],
                        'description': item.get('description', ''),
                        'language': item.get('language', ''),
                        'stars_count': item['stargazers_count'],
                        'forks_count': item['forks_count'],
                        'created_at': item['created_at'],
                        'updated_at': item['updated_at'],
                        'url': item['html_url'],
                        'topics': item.get('topics', []),
                        'license': item.get('license', {}).get('name', '') if item.get('license') else '',
                        'open_issues': item.get('open_issues_count', 0),
                        'watchers': item.get('watchers_count', 0)
                    }
                    projects.append(project)
                
                return projects
            else:
                self.stats['failed_requests'] += 1
                return []
                
        except Exception as e:
            self.stats['failed_requests'] += 1
            return []

    def _generate_yearly_report(self, output_dir, monthly_data, language_data, hot_projects):
        """
        生成2025年年报
        """
        print("\n📋 生成2025年年报...")
        
        # 收集所有项目数据（与图表生成方式一致）
        all_projects = []
        
        # 从月度数据收集
        for month_data in monthly_data.values():
            for project in month_data:
                all_projects.append(project)
        
        # 从语言数据收集
        for lang_projects in language_data.values():
            for project in lang_projects:
                all_projects.append(project)
        
        # 从热门项目数据收集
        for project in hot_projects:
            all_projects.append(project)
        
        # 去重并排序（与图表生成方式一致）
        unique_projects = {}
        for project in all_projects:
            key = project['full_name']
            if key not in unique_projects or project.get('stars_count', 0) > unique_projects[key].get('stars_count', 0):
                unique_projects[key] = project
        
        # 按星标数排序，取前50个项目（与图表生成方式一致）
        top_projects = sorted(unique_projects.values(), key=lambda x: x.get('stars_count', 0), reverse=True)[:50]
        
        # 更新排名
        for i, project in enumerate(top_projects):
            project['rank'] = i + 1
        
        report = {
            'year': 2025,
            'collection_date': datetime.now().isoformat(),
            'summary': {
                'total_projects': len(unique_projects),
                'languages_covered': list(self.stats['languages_covered']),
                'months_covered': list(self.stats['months_covered']),
                'successful_requests': self.stats['successful_requests'],
                'failed_requests': self.stats['failed_requests']
            },
            'monthly_trends': {month: len(projects) for month, projects in monthly_data.items()},
            'language_breakdown': {lang: len(projects) for lang, projects in language_data.items()},
            'top_10_hot_projects': top_projects[:10] if top_projects else [],
            'detailed_data': {
                'monthly': monthly_data,
                'languages': language_data,
                'hot_projects': top_projects
            }
        }
        
        # 保存综合报告
        filename = f"{output_dir}/github_2025_yearly_report.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 生成CSV格式的热门项目列表
        if top_projects:
            csv_filename = f"{output_dir}/github_2025_top_projects.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if top_projects:
                    fieldnames = top_projects[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(top_projects)
        
        print(f"   ✅ 年报已保存: {filename}")
        if hot_projects:
            print(f"   ✅ CSV数据已保存: {csv_filename}")
    
    def collect_missing_months(self, output_dir="data_2025", missing_months=None):
        """
        收集2025年缺失月份的数据
        
        Args:
            output_dir: 输出目录
            missing_months: 要收集的缺失月份列表，默认为["2025-11", "2025-12"]
        
        Returns:
            收集的月度数据
        """
        if missing_months is None:
            missing_months = ["2025-11", "2025-12"]
        
        self.months_2025 = missing_months
        
        print("🚀 开始收集2025年缺失月份数据...")
        print("=" * 60)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 收集月度数据
        monthly_data = {}
        
        for month in missing_months:
            print(f"   正在收集 {month} 的数据...")
            month_data = []
            
            try:
                # 使用GitHub API搜索该月的项目
                daily_data = self._get_month_sample_data(month)
                if daily_data:
                    month_data.extend(daily_data)
                    self.stats['months_covered'].add(month)
                    
                    # 保存月度数据
                    filename = f"{output_dir}/monthly_trends_{month.replace('-', '')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(month_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"     ✅ {month}: {len(month_data)} 个项目")
                    monthly_data[month] = month_data
                else:
                    print(f"     ❌ {month}: 无数据")
                    
                time.sleep(1)  # 礼貌延迟
                
            except Exception as e:
                print(f"     ❌ {month}: 收集失败 - {e}")
                self.stats['failed_requests'] += 1
        
        print("\n" + "=" * 60)
        print("📊 缺失月份数据收集完成！")
        print(f"   收集的月份: {list(monthly_data.keys())}")
        print(f"   数据保存在: {output_dir}")
        
        return monthly_data

def main():
    parser = argparse.ArgumentParser(description='GitHub 2025年全年数据收集器')
    parser.add_argument('--output', '-o', default='data_2025',
                       help='输出目录 (默认: data_2025)')
    parser.add_argument('--languages', '-l', nargs='+',
                       default=['python', 'javascript', 'java', 'go', 'rust'],
                       help='要收集的编程语言列表')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式（不实际发送请求）')
    parser.add_argument('--missing-only', action='store_true',
                       help='仅收集缺失的月份数据（2025-11, 2025-12）')
    parser.add_argument('--months', nargs='+',
                       help='指定要收集的月份列表（格式：YYYY-MM）')
    
    args = parser.parse_args()
    
    collector = GitHub2025DataCollector()
    collector.target_languages = args.languages
    
    if args.dry_run:
        print("🔍 试运行模式 - 将收集以下数据:")
        print(f"   输出目录: {args.output}")
        print(f"   目标语言: {args.languages}")
        print(f"   月份范围: {collector.months_2025}")
        return
    
    try:
        if args.missing_only:
            # 仅收集缺失的月份数据
            monthly_data = collector.collect_missing_months(output_dir=args.output)
        elif args.months:
            # 收集指定月份的数据
            monthly_data = collector.collect_missing_months(output_dir=args.output, missing_months=args.months)
        else:
            # 收集全年数据
            stats = collector.collect_yearly_trends(output_dir=args.output)
        
        print("\n🎉 2025年数据收集任务完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断了数据收集过程")
    except Exception as e:
        print(f"\n❌ 数据收集过程中出现错误: {e}")

if __name__ == "__main__":
    main()