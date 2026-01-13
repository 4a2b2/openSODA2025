"""
深度分析 - 查看多个指标，找出数据问题
"""
import json
import pandas as pd
import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config import get_external_metrics_path

# 修复中文字符显示问题
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'SimSun', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

def check_data_issue():
    """检查数据问题"""
    print("=" * 60)
    print("检查数据问题")
    print("=" * 60)
    
    base_dir = get_external_metrics_path()
    
    # 查看几个知名项目的完整数据
    test_projects = [
        "microsoft/vscode",
        "facebook/react", 
        "vuejs/vue",
        "tensorflow/tensorflow"
    ]
    
    for project_path in test_projects:
        org, project = project_path.split("/")
        project_dir = base_dir / org / project
        
        if not project_dir.exists():
            print(f"❌ 找不到项目: {project_path}")
            continue
            
        print(f"\n🔍 分析 {project_path}:")
        
        # 查看所有指标文件
        json_files = list(project_dir.glob("*.json"))
        
        # 检查关键指标
        key_files = ["stars.json", "technical_fork.json", "activity.json", "openrank.json"]
        
        for key_file in key_files:
            file_path = project_dir / key_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"\n  📊 {key_file}:")
                    
                    if isinstance(data, dict):
                        print(f"    类型: 时间序列 ({len(data)} 个月)")
                        
                        # 显示完整的时间序列
                        print(f"    完整时间序列:")
                        for date, value in list(data.items())[:5]:  # 前5个月
                            print(f"      {date}: {value}")
                        
                        if len(data) > 5:
                            print(f"      ...")
                            for date, value in list(data.items())[-5:]:  # 后5个月
                                print(f"      {date}: {value}")
                        
                        # 计算增长
                        dates = list(data.keys())
                        if len(dates) >= 2:
                            first = data[dates[0]]
                            last = data[dates[-1]]
                            growth = last - first
                            growth_pct = (growth / first * 100) if first != 0 else 0
                            print(f"    增长: {first} → {last} ({growth:+,}，{growth_pct:+.1f}%)")
                    else:
                        print(f"    类型: 单值")
                        print(f"    值: {data}")
                        
                except Exception as e:
                    print(f"    ❌ 错误: {e}")
            else:
                print(f"  ⚠️  缺少文件: {key_file}")

def analyze_multiple_metrics():
    """分析多个指标"""
    print(f"\n" + "=" * 60)
    print("分析多个指标")
    print("=" * 60)
    
    base_dir = get_external_metrics_path()
    
    # 分析microsoft组织的所有项目
    org = "microsoft"
    org_dir = base_dir / org
    
    if not org_dir.exists():
        print(f"❌ 找不到组织: {org}")
        return
    
    projects_data = []
    
    print(f"📦 分析 {org} 组织的所有指标...")
    
    for project_dir in org_dir.iterdir():
        if not project_dir.is_dir():
            continue
            
        project_name = project_dir.name
        print(f"\n  🔍 项目: {project_name}")
        
        project_info = {"project": f"{org}/{project_name}"}
        
        # 读取多个指标
        metrics_to_read = [
            "stars.json", "technical_fork.json", "activity.json", 
            "openrank.json", "change_requests.json", "issues_new.json"
        ]
        
        for metric_file in metrics_to_read:
            file_path = project_dir / metric_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metric_name = metric_file.replace('.json', '')
                    
                    if isinstance(data, dict) and data:
                        # 对于stars和technical_fork，计算总数（所有月度数据相加）
                        if metric_name in ['stars', 'technical_fork']:
                            # 将所有月度数据相加得到总数
                            total_value = sum(data.values())
                            project_info[f"{metric_name}_latest"] = total_value
                            
                            # 也取最早值和最新值，计算增长趋势
                            dates = list(data.keys())
                            dates.sort()
                            if len(dates) > 1:
                                first_date = dates[0]
                                first_value = data[first_date]
                                last_date = dates[-1]
                                last_value = data[last_date]
                                growth = last_value - first_value
                                project_info[f"{metric_name}_first"] = first_value
                                project_info[f"{metric_name}_growth"] = growth
                        else:
                            # 对于其他指标，取最新值
                            dates = list(data.keys())
                            dates.sort()
                            latest_date = dates[-1]
                            latest_value = data[latest_date]
                            
                            # 也取最早值，计算增长
                            if len(dates) > 1:
                                first_date = dates[0]
                                first_value = data[first_date]
                                growth = latest_value - first_value
                                project_info[f"{metric_name}_latest"] = latest_value
                                project_info[f"{metric_name}_first"] = first_value
                                project_info[f"{metric_name}_growth"] = growth
                            else:
                                project_info[f"{metric_name}_latest"] = latest_value
                    else:
                        project_info[f"{metric_name}_latest"] = data
                        
                except Exception as e:
                    print(f"    ⚠️  读取 {metric_file} 错误: {e}")
        
        projects_data.append(project_info)
    
    # 创建DataFrame
    if projects_data:
        df = pd.DataFrame(projects_data)
        
        # 保存详细数据
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        df.to_csv('output/microsoft_detailed_metrics.csv', index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 已保存详细数据到: output/microsoft_detailed_metrics.csv")
        
        # 显示摘要
        print(f"\n📊 Microsoft组织项目指标摘要:")
        print("-" * 80)
        
        # 显示每个项目的关键指标
        for _, row in df.iterrows():
            print(f"\n{row['project']}:")
            
            # 检查每个指标是否存在
            metrics_display = []
            
            for metric in ['stars', 'technical_fork', 'activity', 'openrank']:
                latest_key = f"{metric}_latest"
                growth_key = f"{metric}_growth"
                
                if latest_key in row and pd.notna(row[latest_key]):
                    if growth_key in row and pd.notna(row[growth_key]):
                        metrics_display.append(f"{metric}: {row[latest_key]:,.0f} (+{row[growth_key]:+,.0f})")
                    else:
                        metrics_display.append(f"{metric}: {row[latest_key]:,.0f}")
            
            if metrics_display:
                print("  " + ", ".join(metrics_display))
        
        return df
    
    return None

def create_comprehensive_chart():
    """创建综合图表"""
    print(f"\n" + "=" * 60)
    print("创建综合图表")
    print("=" * 60)
    
    # 读取刚才保存的数据
    try:
        df = pd.read_csv('output/microsoft_detailed_metrics.csv')
        
        # 创建图表
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Microsoft组织项目指标分析', fontsize=16)
        
        # 1. Star数条形图
        if 'stars_latest' in df.columns:
            ax = axes[0, 0]
            df_sorted = df.sort_values('stars_latest', ascending=False)
            ax.barh(df_sorted['project'].apply(lambda x: x.split('/')[1]), 
                   df_sorted['stars_latest'])
            ax.set_xlabel('Star数量')
            ax.set_title('Star数量')
            ax.invert_yaxis()
        
        # 2. Fork数条形图
        if 'technical_fork_latest' in df.columns:
            ax = axes[0, 1]
            df_sorted = df.sort_values('technical_fork_latest', ascending=False)
            ax.barh(df_sorted['project'].apply(lambda x: x.split('/')[1]), 
                   df_sorted['technical_fork_latest'])
            ax.set_xlabel('Fork数量')
            ax.set_title('Fork数量')
            ax.invert_yaxis()
        
        # 3. Activity活跃度
        if 'activity_latest' in df.columns:
            ax = axes[0, 2]
            df_sorted = df.sort_values('activity_latest', ascending=False)
            ax.barh(df_sorted['project'].apply(lambda x: x.split('/')[1]), 
                   df_sorted['activity_latest'])
            ax.set_xlabel('活跃度')
            ax.set_title('项目活跃度')
            ax.invert_yaxis()
        
        # 4. OpenRank分布
        if 'openrank_latest' in df.columns:
            ax = axes[1, 0]
            df['project_short'] = df['project'].apply(lambda x: x.split('/')[1])
            ax.scatter(df['stars_latest'] if 'stars_latest' in df.columns else range(len(df)), 
                      df['openrank_latest'])
            ax.set_xlabel('Star数量' if 'stars_latest' in df.columns else '项目序号')
            ax.set_ylabel('OpenRank')
            ax.set_title('Star vs OpenRank')
            ax.grid(True, alpha=0.3)
        
        # 5. 月度Stars增长模式变化图
        if 'stars_growth' in df.columns:
            ax = axes[1, 1]
            df_sorted = df.sort_values('stars_growth', ascending=False)
            colors = ['green' if x >= 0 else 'red' for x in df_sorted['stars_growth']]
            ax.barh(df_sorted['project'].apply(lambda x: x.split('/')[1]), 
                   df_sorted['stars_growth'], color=colors)
            ax.set_xlabel('月度Stars增长模式变化')
            ax.set_title('月度Stars增长模式变化')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
            ax.invert_yaxis()
            
            # 添加说明文字
            ax.text(0.5, -0.1, '说明: 正值表示最新月增长超过初期，负值表示最新月增长低于初期', 
                   transform=ax.transAxes, ha='center', va='top', fontsize=8, alpha=0.7)
        
        # 6. 指标相关性
        if 'stars_latest' in df.columns and 'technical_fork_latest' in df.columns:
            ax = axes[1, 2]
            ax.scatter(df['stars_latest'], df['technical_fork_latest'])
            ax.set_xlabel('Star数量')
            ax.set_ylabel('Fork数量')
            ax.set_title('Star vs Fork 相关性')
            ax.grid(True, alpha=0.3)
            
            # 添加趋势线
            import numpy as np
            if len(df) > 1:
                z = np.polyfit(df['stars_latest'], df['technical_fork_latest'], 1)
                p = np.poly1d(z)
                ax.plot(df['stars_latest'], p(df['stars_latest']), "r--", alpha=0.5)
        
        plt.tight_layout()
        
        # 保存图表
        output_dir = Path("output/charts")
        output_dir.mkdir(exist_ok=True)
        plt.savefig('output/charts/microsoft_comprehensive_analysis.png', dpi=150, bbox_inches='tight')
        print(f"📊 综合图表已保存: output/charts/microsoft_comprehensive_analysis.png")
        
        plt.show()
        
    except Exception as e:
        print(f"⚠️  创建图表时出错: {e}")
        print(f"错误详情: {e}")

def analyze_time_series():
    """分析时间序列数据"""
    print(f"\n" + "=" * 60)
    print("分析时间序列趋势")
    print("=" * 60)
    
    base_dir = get_external_metrics_path()
    
    # 分析vscode项目的时间序列
    project_path = "microsoft/vscode"
    org, project = project_path.split("/")
    project_dir = base_dir / org / project
    
    if not project_dir.exists():
        print(f"❌ 找不到项目: {project_path}")
        return
    
    # 读取stars的时间序列数据
    stars_file = project_dir / "stars.json"
    
    if stars_file.exists():
        with open(stars_file, 'r', encoding='utf-8') as f:
            stars_data = json.load(f)
        
        # 转换为DataFrame
        dates = list(stars_data.keys())
        stars = list(stars_data.values())
        
        # 创建时间序列DataFrame
        ts_df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'stars': stars
        })
        
        # 排序
        ts_df = ts_df.sort_values('date')
        
        print(f"\n📈 {project_path} 月度Stars增长趋势:")
        print("-" * 50)
        
        # 计算月度增长
        ts_df['monthly_growth'] = ts_df['stars'].diff()
        ts_df['growth_pct'] = (ts_df['monthly_growth'] / ts_df['stars'].shift(1)) * 100
        
        # 显示关键统计
        print(f"时间范围: {ts_df['date'].min().date()} 到 {ts_df['date'].max().date()}")
        print(f"总增长: {ts_df['stars'].iloc[0]:,} → {ts_df['stars'].iloc[-1]:,} "
              f"(+{ts_df['stars'].iloc[-1] - ts_df['stars'].iloc[0]:+,})")
        print(f"平均月增长: {ts_df['monthly_growth'].mean():.1f}")
        print(f"最大月增长: {ts_df['monthly_growth'].max():.0f} "
              f"(在 {ts_df.loc[ts_df['monthly_growth'].idxmax(), 'date'].date()})")
        
        # 保存时间序列数据
        ts_df.to_csv('output/vscode_stars_timeseries.csv', index=False, encoding='utf-8-sig')
        print(f"\n💾 时间序列数据已保存: output/vscode_stars_timeseries.csv")
        
        # 绘制时间序列图
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        plt.plot(ts_df['date'], ts_df['stars'], marker='o', markersize=3)
        plt.xlabel('日期')
        plt.ylabel('Star数量')
        plt.title(f'{project_path} 月度Stars增长趋势')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.subplot(1, 2, 2)
        plt.bar(ts_df['date'], ts_df['monthly_growth'], alpha=0.7)
        plt.xlabel('日期')
        plt.ylabel('月增长')
        plt.title(f'{project_path} Star月增长')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('output/charts/vscode_stars_timeseries.png', dpi=150, bbox_inches='tight')
        print(f"📊 时间序列图表已保存: output/charts/vscode_stars_timeseries.png")
        
        plt.show()
        
        return ts_df
    
    return None

def main():
    """主函数"""
    print("🚀 开始深度分析 GitHub Top 300 Metrics...")
    
    # 步骤1：检查数据问题
    check_data_issue()
    
    # 步骤2：分析多个指标
    df = analyze_multiple_metrics()
    
    # 步骤3：创建综合图表
    create_comprehensive_chart()
    
    # 步骤4：分析时间序列
    analyze_time_series()
    
    print(f"\n" + "=" * 60)
    print("✅ 深度分析完成！")
    print("=" * 60)
    print("📁 生成的文件:")
    print("  output/microsoft_detailed_metrics.csv - Microsoft详细指标")
    print("  output/vscode_stars_timeseries.csv - VSCode时间序列数据")
    print("  output/charts/microsoft_comprehensive_analysis.png - 综合图表")
    print("  output/charts/vscode_stars_timeseries.png - 时间序列图表")

if __name__ == "__main__":
    main()