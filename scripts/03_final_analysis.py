"""
最终分析 - 修复时间序列问题，进行深度分析
"""
import json
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict
# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config import get_external_metrics_path

# 修复中文字符显示问题
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'SimSun', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

def clean_date(date_str):
    """清理日期字符串"""
    if isinstance(date_str, str):
        # 去掉 -raw 后缀
        if '-raw' in date_str:
            date_str = date_str.replace('-raw', '')
        # 确保格式为 YYYY-MM
        if len(date_str) == 7 and '-' in date_str:
            return date_str
    return date_str

def analyze_project_metrics(org, project):
    """分析单个项目的完整指标"""
    base_dir = get_external_metrics_path()
    project_dir = base_dir / org / project
    
    if not project_dir.exists():
        return None
    
    results = {
        'org': org,
        'project': project,
        'full_name': f"{org}/{project}"
    }
    
    # 要分析的指标文件
    metric_files = {
        'stars': 'stars.json',
        'forks': 'technical_fork.json',
        'activity': 'activity.json',
        'openrank': 'openrank.json',
        'issues': 'issues_new.json',
        'prs': 'change_requests.json',
        'contributors': 'new_contributors.json'
    }
    
    for metric_name, filename in metric_files.items():
        file_path = project_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and data:
                    # 清理日期
                    cleaned_data = {}
                    for date_str, value in data.items():
                        clean_dt = clean_date(date_str)
                        if clean_dt:
                            cleaned_data[clean_dt] = value
                    
                    if cleaned_data:
                        # 排序日期
                        sorted_dates = sorted(cleaned_data.keys())
                        
                        # 获取最新值
                        latest_date = sorted_dates[-1]
                        latest_value = cleaned_data[latest_date]
                        
                        # 获取最早值（计算总增长）
                        if len(sorted_dates) > 1:
                            first_date = sorted_dates[0]
                            first_value = cleaned_data[first_date]
                            total_growth = latest_value - first_value
                            
                            results[f'{metric_name}_latest'] = latest_value
                            results[f'{metric_name}_first'] = first_value
                            results[f'{metric_name}_growth'] = total_growth
                            results[f'{metric_name}_start_date'] = first_date
                            results[f'{metric_name}_end_date'] = latest_date
                        else:
                            results[f'{metric_name}_latest'] = latest_value
            except Exception as e:
                print(f"  读取 {filename} 错误: {e}")
    
    return results if len(results) > 3 else None  # 至少除了基本信息外还有数据

def analyze_top_projects_across_orgs():
    """分析所有组织的顶级项目"""
    print("=" * 60)
    print("分析所有组织的顶级项目")
    print("=" * 60)
    
    base_dir = get_external_metrics_path()
    all_projects_data = []
    
    # 只分析一些知名组织（避免太多数据）
    top_orgs_to_analyze = [
        'microsoft', 'google', 'facebook', 'apache',
        'tensorflow', 'kubernetes', 'docker', 'nodejs',
        'python', 'golang', 'rust-lang', 'pytorch'
    ]
    
    org_count = 0
    for org in base_dir.iterdir():
        if not org.is_dir():
            continue
        
        org_name = org.name
        
        # 如果指定了组织列表，只分析这些组织
        if top_orgs_to_analyze and org_name not in top_orgs_to_analyze:
            continue
        
        print(f"\n📦 分析组织: {org_name}")
        
        # 分析组织下的所有项目
        project_count = 0
        for project_dir in org.iterdir():
            if not project_dir.is_dir():
                continue
            
            project_name = project_dir.name
            project_data = analyze_project_metrics(org_name, project_name)
            
            if project_data:
                all_projects_data.append(project_data)
                project_count += 1
        
        print(f"  找到 {project_count} 个项目")
        org_count += 1
        
        # 控制分析的组织数量
        if org_count >= 10 and len(all_projects_data) >= 50:
            print(f"\n已分析 {org_count} 个组织，{len(all_projects_data)} 个项目，停止分析更多")
            break
    
    if all_projects_data:
        # 创建DataFrame
        df = pd.DataFrame(all_projects_data)
        
        # 保存原始数据
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        df.to_csv('output/all_top_projects_metrics.csv', index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 成功分析了 {len(df)} 个项目")
        return df
    else:
        print("❌ 没有收集到项目数据")
        return None

def analyze_project_growth(df):
    """分析项目增长情况"""
    print(f"\n" + "=" * 60)
    print("项目增长分析")
    print("=" * 60)
    
    if df is None or df.empty:
        return
    
    # 计算综合评分
    df = df.copy()
    
    # 确保有足够的数据
    required_cols = ['stars_latest', 'openrank_latest', 'activity_latest']
    available_cols = [col for col in required_cols if col in df.columns]
    
    if len(available_cols) >= 2:
        # 归一化数据
        for col in available_cols:
            if col in df.columns and df[col].max() > df[col].min():
                df[f'{col}_norm'] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
            else:
                df[f'{col}_norm'] = 0
        
        # 计算综合评分（加权平均）
        weights = {'stars_latest_norm': 0.3, 'openrank_latest_norm': 0.4, 'activity_latest_norm': 0.3}
        df['composite_score'] = 0
        
        for col, weight in weights.items():
            if col in df.columns:
                df['composite_score'] += df[col] * weight
    
    # 按OpenRank排序（这是核心指标）
    if 'openrank_latest' in df.columns:
        df_sorted_by_openrank = df.sort_values('openrank_latest', ascending=False)
        
        print(f"\n🏆 Top 20 项目（按OpenRank影响力）:")
        print("-" * 80)
        for i, (idx, row) in enumerate(df_sorted_by_openrank.head(20).iterrows(), 1):
            print(f"{i:2d}. {row['full_name']:45s} "
                  f"📊 {row['openrank_latest']:7.1f} "
                  f"⭐ {row.get('stars_latest', 'N/A'):6,.0f} "
                  f"📈 {row.get('activity_latest', 'N/A'):6,.0f}")
    
    # 按月度Stars增长模式变化排序
    if 'stars_growth' in df.columns:
        df_sorted_by_growth = df.sort_values('stars_growth', ascending=False)
        
        print(f"\n📈 Top 20 项目（按月度Stars增长模式变化）:")
        print("-" * 80)
        print("说明: 正值表示最新月增长超过初期，负值表示最新月增长低于初期")
        for i, (idx, row) in enumerate(df_sorted_by_growth.head(20).iterrows(), 1):
            growth = row['stars_growth']
            growth_str = f"+{growth:,.0f}" if growth >= 0 else f"{growth:,.0f}"
            print(f"{i:2d}. {row['full_name']:45s} {growth_str:>10s}")
    
    # 按综合评分排序
    if 'composite_score' in df.columns:
        df_sorted_by_composite = df.sort_values('composite_score', ascending=False)
        
        print(f"\n🌟 Top 20 项目（按综合评分）:")
        print("-" * 80)
        for i, (idx, row) in enumerate(df_sorted_by_composite.head(20).iterrows(), 1):
            score = row['composite_score']
            print(f"{i:2d}. {row['full_name']:45s} 评分: {score:.3f}")
    
    return df

def create_growth_visualizations(df):
    """创建增长可视化图表"""
    print(f"\n" + "=" * 60)
    print("创建增长可视化图表")
    print("=" * 60)
    
    if df is None or df.empty:
        return
    
    # 创建图表目录
    charts_dir = Path("output/charts")
    charts_dir.mkdir(exist_ok=True)
    
    # 1. OpenRank分布图
    plt.figure(figsize=(14, 10))
    
    if 'openrank_latest' in df.columns:
        # 1.1 Top 20项目OpenRank
        plt.subplot(2, 2, 1)
        top_20_openrank = df.nlargest(20, 'openrank_latest')
        top_20_openrank['short_name'] = top_20_openrank['full_name'].apply(
            lambda x: x.split('/')[-1][:20]
        )
        
        bars = plt.barh(range(len(top_20_openrank)), top_20_openrank['openrank_latest'])
        plt.yticks(range(len(top_20_openrank)), top_20_openrank['short_name'])
        plt.xlabel('OpenRank Score')
        plt.title('Top 20 Projects by OpenRank (Influence)')
        plt.gca().invert_yaxis()
        
        # 添加数值标签
        for bar, value in zip(bars, top_20_openrank['openrank_latest']):
            plt.text(bar.get_width(), bar.get_y() + bar.get_height()/2, 
                    f' {value:.1f}', va='center')
    
    # 1.2 OpenRank vs Stars 散点图
    if 'openrank_latest' in df.columns and 'stars_latest' in df.columns:
        plt.subplot(2, 2, 2)
        
        plt.scatter(df['stars_latest'], df['openrank_latest'], alpha=0.6, s=30)
        plt.xlabel('Monthly New Stars')
        plt.ylabel('OpenRank Score')
        plt.title('OpenRank vs Monthly Stars')
        plt.grid(True, alpha=0.3)
        
        # 添加趋势线
        if len(df) > 1:
            z = np.polyfit(df['stars_latest'], df['openrank_latest'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(df['stars_latest'].min(), df['stars_latest'].max(), 100)
            plt.plot(x_line, p(x_line), 'r--', alpha=0.5, label='Trend line')
            plt.legend()
    
    # 1.3 Activity分布
    if 'activity_latest' in df.columns:
        plt.subplot(2, 2, 3)
        plt.hist(df['activity_latest'], bins=30, alpha=0.7, edgecolor='black')
        plt.xlabel('Activity Score')
        plt.ylabel('Number of Projects')
        plt.title('Activity Distribution')
        plt.grid(True, alpha=0.3)
        
        # 添加统计信息
        mean_activity = df['activity_latest'].mean()
        median_activity = df['activity_latest'].median()
        plt.axvline(mean_activity, color='red', linestyle='--', 
                   label=f'Mean: {mean_activity:.1f}')
        plt.axvline(median_activity, color='green', linestyle='--', 
                   label=f'Median: {median_activity:.1f}')
        plt.legend()
    
    # 1.4 指标相关性热力图
    plt.subplot(2, 2, 4)
    numeric_cols = ['stars_latest', 'forks_latest', 'activity_latest', 
                   'openrank_latest', 'issues_latest', 'prs_latest']
    numeric_cols = [col for col in numeric_cols if col in df.columns]
    
    if len(numeric_cols) >= 3:
        corr_matrix = df[numeric_cols].corr()
        
        # 使用数值显示，避免中文问题
        import seaborn as sns
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
                   square=True, fmt='.2f', cbar_kws={'label': 'Correlation'})
        plt.title('Metrics Correlation Matrix')
    
    plt.suptitle('GitHub Top Projects Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('output/charts/growth_analysis_overview.png', dpi=150, bbox_inches='tight')
    print(f"📊 图表1已保存: output/charts/growth_analysis_overview.png")
    
    # 2. 时间序列分析（选择几个代表性项目）
    print(f"\n📈 时间序列分析（代表性项目）:")
    analyze_time_series_for_selected_projects()
    
    plt.show()

def analyze_time_series_for_selected_projects():
    """分析选定项目的时间序列"""
    base_dir = get_external_metrics_path()
    
    # 选择几个代表性项目
    selected_projects = [
        ("microsoft", "vscode"),
        ("facebook", "react"),
        ("tensorflow", "tensorflow"),
        ("kubernetes", "kubernetes")
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Project Growth Time Series Analysis', fontsize=16, fontweight='bold')
    
    for idx, (org, project) in enumerate(selected_projects):
        ax = axes[idx//2, idx%2]
        
        project_dir = base_dir / org / project
        stars_file = project_dir / "stars.json"
        
        if stars_file.exists():
            try:
                with open(stars_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and data:
                    # 清理数据
                    clean_data = {}
                    for date_str, value in data.items():
                        clean_dt = clean_date(date_str)
                        if clean_dt and '-' in clean_dt:
                            # 只保留标准格式的日期
                            if len(clean_dt) == 7:
                                clean_data[clean_dt] = value
                    
                    if clean_data:
                        # 转换为DataFrame
                        dates = sorted(clean_data.keys())
                        values = [clean_data[d] for d in dates]
                        
                        # 只显示年份-月份，避免太拥挤
                        display_dates = []
                        for i, d in enumerate(dates):
                            if i % 12 == 0 or i == len(dates)-1:  # 每年显示一个标签
                                display_dates.append(d)
                            else:
                                display_dates.append('')
                        
                        # 转换为累计总数（将所有月度新增相加）
                        cumulative_values = []
                        running_total = 0
                        for value in values:
                            running_total += value
                            cumulative_values.append(running_total)
                        
                        # 绘制图表（使用累计数据显示平滑增长）
                        ax.plot(range(len(dates)), cumulative_values, marker='o', markersize=3, linewidth=2)
                        ax.set_title(f'{org}/{project}')
                        ax.set_xlabel('Time (Months)')
                        ax.set_ylabel('Cumulative Total Stars')
                        ax.grid(True, alpha=0.3)
                        
                        # 设置x轴标签
                        ax.set_xticks(range(len(dates)))
                        ax.set_xticklabels(display_dates, rotation=45, ha='right')
                        
                        # 计算和显示增长（使用累计数据）
                        if len(cumulative_values) >= 2:
                            total_stars = cumulative_values[-1]
                            avg_monthly = total_stars / len(cumulative_values)
                            ax.text(0.05, 0.95, 
                                   f'Total Stars: {total_stars:,.0f}\nAvg Monthly: {avg_monthly:.0f}',
                                   transform=ax.transAxes,
                                   verticalalignment='top',
                                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            except Exception as e:
                ax.text(0.5, 0.5, f'Error: {e}', ha='center', va='center')
                ax.set_title(f'{org}/{project} - Error')
        else:
            ax.text(0.5, 0.5, 'Data not found', ha='center', va='center')
            ax.set_title(f'{org}/{project}')
    
    plt.tight_layout()
    plt.savefig('output/charts/time_series_analysis.png', dpi=150, bbox_inches='tight')
    print(f"📊 图表2已保存: output/charts/time_series_analysis.png")

def generate_final_report(df):
    """生成最终分析报告"""
    print(f"\n" + "=" * 60)
    print("生成最终分析报告")
    print("=" * 60)
    
    if df is None or df.empty:
        return
    
    # 生成各种排行榜
    reports_dir = Path("output/reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 1. OpenRank排行榜
    if 'openrank_latest' in df.columns:
        openrank_top = df.nlargest(50, 'openrank_latest')[['full_name', 'openrank_latest', 
                                                          'stars_latest', 'activity_latest']]
        openrank_top.to_csv('output/reports/top_50_by_openrank.csv', index=False, encoding='utf-8-sig')
        print(f"📋 OpenRank排行榜已保存")
    
    # 2. 活跃度排行榜
    if 'activity_latest' in df.columns:
        activity_top = df.nlargest(50, 'activity_latest')[['full_name', 'activity_latest', 
                                                          'openrank_latest', 'stars_latest']]
        activity_top.to_csv('output/reports/top_50_by_activity.csv', index=False, encoding='utf-8-sig')
        print(f"📋 活跃度排行榜已保存")
    
    # 3. 月度Stars增长模式变化排行榜
    if 'stars_growth' in df.columns:
        growth_top = df.nlargest(50, 'stars_growth')[['full_name', 'stars_growth', 
                                                     'stars_latest', 'openrank_latest']]
        growth_top.to_csv('output/reports/top_50_by_star_growth.csv', index=False, encoding='utf-8-sig')
        print(f"📋 月度Stars增长模式变化排行榜已保存")
    
    # 4. 生成文本报告
    with open('output/reports/summary_report.txt', 'w', encoding='utf-8') as f:
        f.write("GitHub Top Projects Analysis Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Total Projects Analyzed: {len(df)}\n")
        f.write(f"Time Range: 2015-2023\n\n")
        
        if 'openrank_latest' in df.columns:
            f.write("Key Statistics:\n")
            f.write(f"- Average OpenRank: {df['openrank_latest'].mean():.1f}\n")
            f.write(f"- Max OpenRank: {df['openrank_latest'].max():.1f}\n")
            f.write(f"- Min OpenRank: {df['openrank_latest'].min():.1f}\n\n")
        
        if 'stars_latest' in df.columns:
            f.write("Monthly New Stars Statistics:\n")
            f.write(f"- Average monthly stars: {df['stars_latest'].mean():.0f}\n")
            f.write(f"- Max monthly stars: {df['stars_latest'].max():.0f}\n")
            f.write(f"- Total analyzed: {df['stars_latest'].sum():,.0f}\n\n")
        
        f.write("Top 10 Projects by OpenRank:\n")
        if 'openrank_latest' in df.columns:
            top_10 = df.nlargest(10, 'openrank_latest')
            for i, (_, row) in enumerate(top_10.iterrows(), 1):
                f.write(f"{i:2d}. {row['full_name']:45s} OpenRank: {row['openrank_latest']:7.1f}\n")
    
    print(f"\n📄 文本报告已保存: output/reports/summary_report.txt")
    print(f"📁 所有报告文件在 output/reports/ 目录中")

def main():
    """主函数"""
    print("🚀 GitHub Top 300 项目深度分析")
    print("=" * 60)
    
    # 步骤1：分析所有顶级项目
    print("1. 收集和分析项目数据...")
    df = analyze_top_projects_across_orgs()
    
    if df is None:
        print("❌ 没有数据可分析")
        return
    
    # 步骤2：分析增长情况
    print("\n2. 分析项目增长情况...")
    df = analyze_project_growth(df)
    
    # 步骤3：创建可视化图表
    print("\n3. 创建可视化图表...")
    create_growth_visualizations(df)
    
    # 步骤4：生成最终报告
    print("\n4. 生成分析报告...")
    generate_final_report(df)
    
    print(f"\n" + "=" * 60)
    print("✅ 分析完成！")
    print("=" * 60)
    print(f"📊 分析了 {len(df)} 个项目")
    print(f"📁 生成的文件:")
    print(f"  output/all_top_projects_metrics.csv - 所有项目数据")
    print(f"  output/charts/growth_analysis_overview.png - 综合分析图表")
    print(f"  output/charts/time_series_analysis.png - 时间序列图表")
    print(f"  output/reports/ - 各种排行榜和报告")

if __name__ == "__main__":
    main()