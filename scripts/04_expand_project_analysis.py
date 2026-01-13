#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展项目分析数据源
从多个数据源合并，创建包含更多项目的数据集
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config import get_output_dir, get_project_root

def load_and_merge_data():
    """加载并合并多个数据源"""
    
    # 获取输出目录
    output_dir = get_output_dir()
    
    # 读取现有的完整数据
    complete_df = pd.read_csv(output_dir / 'complete_total_stars_ranking.csv', encoding='utf-8-sig')
    print(f"完整数据源包含 {len(complete_df)} 个项目")
    
    # 读取top100项目数据
    try:
        top100_df = pd.read_csv(output_dir / 'top_100_projects.csv', encoding='utf-8-sig')
        print(f"Top100数据源包含 {len(top100_df)} 个项目")
    except:
        top100_df = pd.DataFrame()
        print("无法读取Top100项目数据")
    
    # 读取详细分析数据
    try:
        improved_df = pd.read_csv(output_dir / 'improved_project_analysis.csv', encoding='utf-8-sig')
        print(f"改进分析数据源包含 {len(improved_df)} 个项目")
    except:
        improved_df = pd.DataFrame()
        print("无法读取改进分析数据")
    
    # 创建新的扩展数据集
    extended_projects = []
    
    # 1. 添加完整数据源中的所有项目
    for _, row in complete_df.iterrows():
        extended_projects.append({
            'rank': row['rank'],
            'org': row['org'],
            'project': row['project'],
            'full_name': row['full_name'],
            'total_stars': row['total_stars'],
            'monthly_stars_latest': row['monthly_stars_latest'],
            'activity_latest': row['activity_latest'],
            'openrank_latest': row['openrank_latest'],
            'source': 'complete_ranking'
        })
    
    # 2. 从top100中添加新项目
    existing_names = {item['full_name'] for item in extended_projects}
    
    if not top100_df.empty:
        for _, row in top100_df.iterrows():
            if row['full_name'] not in existing_names:
                # 尝试从其他数据源找到匹配的指标
                openrank_latest = None
                total_stars = None
                
                # 在改进分析数据中查找
                if not improved_df.empty:
                    match = improved_df[improved_df['full_name'] == row['full_name']]
                    if not match.empty:
                        openrank_latest = match.iloc[0]['openrank_latest']
                
                # 如果找不到，使用默认值或标记为缺失
                if openrank_latest is None:
                    openrank_latest = 0.0  # 标记为缺失
                
                if total_stars is None:
                    total_stars = row['stars']  # 使用stars字段作为备选
                
                extended_projects.append({
                    'rank': len(extended_projects) + 1,
                    'org': row['organization'],
                    'project': row['project'],
                    'full_name': row['full_name'],
                    'total_stars': total_stars,
                    'monthly_stars_latest': row['stars'],  # 使用stars作为最新月度数据
                    'activity_latest': row['activity'],
                    'openrank_latest': openrank_latest,
                    'source': 'top100_only'
                })
    
    # 转换为DataFrame
    extended_df = pd.DataFrame(extended_projects)
    
    # 按openrank_latest降序排序（排除缺失值）
    has_openrank = extended_df['openrank_latest'] > 0
    df_with_openrank = extended_df[has_openrank].sort_values('openrank_latest', ascending=False)
    df_without_openrank = extended_df[~has_openrank].sort_values('total_stars', ascending=False)
    
    # 重新分配排名
    final_df = pd.concat([df_with_openrank, df_without_openrank], ignore_index=True)
    final_df['rank'] = range(1, len(final_df) + 1)
    
    print(f"扩展后数据集包含 {len(final_df)} 个项目")
    print(f"有OpenRank数据的项目: {len(df_with_openrank)}")
    print(f"缺失OpenRank数据的项目: {len(df_without_openrank)}")
    
    return final_df

def enhanced_classify_project_type(project_name):
    """增强的项目分类函数 - 包含更多关键词"""
    project_name_lower = project_name.lower()
    
    # 开发工具和IDE
    if any(keyword in project_name_lower for keyword in ['vscode', 'studio', 'ide', 'editor', 'debugger', 'terminal', 'jupyter']):
        return '开发工具'
    
    # 编程语言和编译器
    elif any(keyword in project_name_lower for keyword in ['typescript', 'python', 'go', 'rust', 'cpp', 'cpython', 'node', 'electron', 'java', 'kotlin', 'swift']):
        return '编程语言'
    
    # 容器和编排
    elif any(keyword in project_name_lower for keyword in ['kubernetes', 'docker', 'container', 'minikube', 'orchestration']):
        return '容器编排'
    
    # 人工智能和机器学习
    elif any(keyword in project_name_lower for keyword in ['pytorch', 'tensorflow', 'ai', 'ml', 'machine', 'learning', 'onnx', 'tvm', 'hudi']):
        return '人工智能'
    
    # 前端框架和UI
    elif any(keyword in project_name_lower for keyword in ['react', 'angular', 'vue', 'ui', 'frontend', 'ant-design', 'fluentui', 'material']):
        return '前端框架'
    
    # 后端框架和服务器
    elif any(keyword in project_name_lower for keyword in ['spring', 'django', 'flask', 'express', 'fastapi', 'server', 'backend', 'framework']):
        return '后端框架'
    
    # 大数据和数据库
    elif any(keyword in project_name_lower for keyword in ['spark', 'flink', 'hadoop', 'kafka', 'database', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'superset', 'doris', 'arrow', 'beam']):
        return '大数据/数据库'
    
    # 云平台和基础设施
    elif any(keyword in project_name_lower for keyword in ['aws', 'azure', 'gcp', 'cloud', 'wsl', 'serverless', 'api', 'gateway', 'apisix', 'pulsar']):
        return '云平台/基础设施'
    
    # DevOps和CI/CD
    elif any(keyword in project_name_lower for keyword in ['ci', 'cd', 'pipeline', 'automation', 'deployment', 'devops', 'jenkins', 'gitlab', 'github-actions']):
        return 'DevOps/CI-CD'
    
    # 实用工具和命令行
    elif any(keyword in project_name_lower for keyword in ['powertoys', 'utility', 'tool', 'cli', 'command', 'script', 'automation', 'cert', 'practice', 'winget']):
        return '实用工具'
    
    # 文档和网站
    elif any(keyword in project_name_lower for keyword in ['docs', 'documentation', 'website', 'blog', 'guide', 'tutorial']):
        return '文档/网站'
    
    # 移动开发
    elif any(keyword in project_name_lower for keyword in ['mobile', 'ios', 'android', 'flutter', 'react-native', 'xamarin']):
        return '移动开发'
    
    # 游戏开发
    elif any(keyword in project_name_lower for keyword in ['game', 'unity', 'unreal', 'gaming', '3d']):
        return '游戏开发'
    
    # 其他
    else:
        return '其他'

def main():
    """主函数"""
    print("=" * 60)
    print("扩展项目分析数据源")
    print("=" * 60)
    
    # 获取输出目录
    output_dir = get_output_dir()
    
    # 创建扩展数据集
    extended_df = load_and_merge_data()
    
    # 应用增强分类
    extended_df['project_type'] = extended_df['project'].apply(enhanced_classify_project_type)
    
    # 保存扩展数据集
    output_path = output_dir / 'extended_project_analysis.csv'
    extended_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"扩展数据集已保存到: {output_path}")
    
    # 分析分类结果
    print("\n项目类型分布:")
    type_counts = extended_df['project_type'].value_counts()
    for project_type, count in type_counts.items():
        percentage = (count / len(extended_df)) * 100
        print(f"  {project_type}: {count} 个项目 ({percentage:.1f}%)")
    
    # 保存分类分析
    type_analysis = extended_df.groupby('project_type').agg({
        'full_name': 'count',
        'openrank_latest': 'mean',
        'total_stars': 'mean'
    }).rename(columns={
        'full_name': 'count',
        'openrank_latest': 'avg_openrank',
        'total_stars': 'avg_total_stars'
    }).round(2)
    
    type_analysis.to_csv(output_dir / 'extended_project_type_analysis.csv', encoding='utf-8-sig')
    print(f"分类分析已保存到: {output_dir / 'extended_project_type_analysis.csv'}")
    
    print(f"\n总计处理了 {len(extended_df)} 个项目")
    print("数据源扩展完成!")

if __name__ == "__main__":
    main()