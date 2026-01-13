"""
探索GitHub Top 300 Metrics数据结构
"""
import json
import pandas as pd
import sys
import os
from pathlib import Path
# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config import get_external_metrics_path
import matplotlib.pyplot as plt

# 修复中文字符显示问题
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'SimSun', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

def explore_data_structure():
    """探索数据结构"""
    print("=" * 60)
    print("GitHub Top 300 Metrics 数据结构探索")
    print("=" * 60)
    
    # 1. 定位数据目录
    base_dir = get_external_metrics_path()
    if not base_dir.exists():
        print("❌ 找不到数据目录")
        return None
    
    print(f"📁 数据目录: {base_dir}")
    
    # 2. 统计组织数量
    org_folders = [f for f in base_dir.iterdir() if f.is_dir()]
    print(f"📊 找到 {len(org_folders)} 个组织")
    
    # 3. 查看microsoft组织作为示例
    microsoft_dir = base_dir / "microsoft"
    if microsoft_dir.exists():
        print(f"\n🔍 Microsoft组织下的项目:")
        project_folders = [f for f in microsoft_dir.iterdir() if f.is_dir()]
        for i, project in enumerate(project_folders[:10], 1):
            print(f"  {i:2d}. {project.name}")
        
        if len(project_folders) > 10:
            print(f"  ... 还有 {len(project_folders)-10} 个项目")
    
    # 4. 查看一个项目的数据文件
    print(f"\n📂 查看 vscode 项目的指标文件:")
    vscode_dir = microsoft_dir / "vscode"
    if vscode_dir.exists():
        json_files = list(vscode_dir.glob("*.json"))
        print(f"  vscode 项目有 {len(json_files)} 个指标文件:")
        for i, f in enumerate(json_files[:8], 1):
            print(f"  {i:2d}. {f.name}")
        
        if len(json_files) > 8:
            print(f"  ... 还有 {len(json_files)-8} 个文件")
        
        # 查看一个文件的内容
        if json_files:
            first_file = json_files[0]
            print(f"\n📄 查看 {first_file.name} 的结构:")
            try:
                with open(first_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"  数据类型: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"  键数量: {len(data)}")
                    first_key = list(data.keys())[0] if data else None
                    first_value = data[first_key] if first_key else None
                    print(f"  第一个键: {first_key}")
                    print(f"  值类型: {type(first_value)}")
            except Exception as e:
                print(f"  读取出错: {e}")
    
    return base_dir, org_folders

def collect_project_info(base_dir, max_orgs=None):
    """收集项目信息"""
    print(f"\n" + "=" * 60)
    print("收集项目信息")
    print("=" * 60)
    
    projects_info = []
    
    # 获取所有组织
    org_folders = [f for f in base_dir.iterdir() if f.is_dir()]
    
    # 如果指定了最大组织数，则只处理前几个
    if max_orgs:
        org_folders = org_folders[:max_orgs]
        print(f"⚠️  为了测试，只处理前 {max_orgs} 个组织")
    else:
        print(f"📊 处理所有 {len(org_folders)} 个组织")
    
    for org_idx, org_folder in enumerate(org_folders):
        # 显示进度信息
        if max_orgs:
            progress_info = f"{org_idx+1}/{min(len(org_folders), max_orgs)}"
        else:
            progress_info = f"{org_idx+1}/{len(org_folders)}"
        print(f"\n📦 处理组织: {org_folder.name} ({progress_info})")
        
        # 获取组织下的所有项目文件夹
        project_folders = [f for f in org_folder.iterdir() if f.is_dir()]
        
        for project_folder in project_folders:
            # 检查是否有stars.json文件
            stars_file = project_folder / "stars.json"
            if stars_file.exists():
                try:
                    with open(stars_file, 'r', encoding='utf-8') as f:
                        stars_data = json.load(f)
                    
                    # 计算总star数（将所有月度新增相加）
                    if isinstance(stars_data, dict) and stars_data:
                        # 将所有月度star数相加得到总star数
                        total_stars = sum(stars_data.values())
                        latest_stars = total_stars
                    else:
                        latest_stars = stars_data if isinstance(stars_data, (int, float)) else 0
                    
                    # 获取其他指标
                    activity_file = project_folder / "activity.json"
                    activity_value = 0
                    if activity_file.exists():
                        try:
                            with open(activity_file, 'r', encoding='utf-8') as f:
                                activity_data = json.load(f)
                            if isinstance(activity_data, dict) and activity_data:
                                latest_activity = sorted(activity_data.keys())[-1]
                                activity_value = activity_data[latest_activity]
                        except:
                            pass
                    
                    projects_info.append({
                        'organization': org_folder.name,
                        'project': project_folder.name,
                        'full_name': f"{org_folder.name}/{project_folder.name}",
                        'stars': latest_stars,
                        'activity': activity_value
                    })
                    
                except Exception as e:
                    print(f"  ⚠️  处理 {project_folder.name} 时出错: {e}")
    
    # 创建DataFrame
    if projects_info:
        df = pd.DataFrame(projects_info)
        print(f"\n✅ 成功收集了 {len(df)} 个项目的信息")
        return df
    else:
        print("❌ 没有收集到项目信息")
        return None

def analyze_top_projects(df):
    """分析Top项目"""
    print(f"\n" + "=" * 60)
    print("分析Top项目")
    print("=" * 60)
    
    if df is None or df.empty:
        print("❌ 没有数据可分析")
        return
    
    # 按star数排序
    df_sorted = df.sort_values('stars', ascending=False)
    
    print(f"\n🏆 Top 20 项目（按Star数）:")
    print("-" * 80)
    for i, (idx, row) in enumerate(df_sorted.head(20).iterrows(), 1):
        print(f"{i:2d}. {row['full_name']:50s} ⭐ {row['stars']:8,d}")
    
    # 按组织统计
    print(f"\n📊 按组织统计（前10个组织）:")
    org_stats = df.groupby('organization').agg({
        'project': 'count',
        'stars': 'sum'
    }).sort_values('stars', ascending=False)
    
    for i, (org, row) in enumerate(org_stats.head(10).iterrows(), 1):
        print(f"{i:2d}. {org:30s} 项目数: {row['project']:3d} 总Star数: {row['stars']:10,d}")
    
    return df_sorted

def save_results(df_sorted):
    """保存结果"""
    print(f"\n" + "=" * 60)
    print("保存结果")
    print("=" * 60)
    
    if df_sorted is None:
        return
    
    # 保存完整数据
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 1. 保存Top 100项目
    top_100 = df_sorted.head(100)
    top_100.to_csv('output/top_100_projects.csv', index=False, encoding='utf-8-sig')
    print(f"💾 已保存: output/top_100_projects.csv")
    
    # 2. 按组织汇总
    org_summary = df_sorted.groupby('organization').agg({
        'project': 'count',
        'stars': ['sum', 'mean', 'max']
    }).round(1)
    
    # 简化列名
    org_summary.columns = ['project_count', 'stars_total', 'stars_avg', 'stars_max']
    org_summary = org_summary.sort_values('stars_total', ascending=False)
    org_summary.to_csv('output/organization_summary.csv', encoding='utf-8-sig')
    print(f"💾 已保存: output/organization_summary.csv")
    
    # 3. 创建简单图表
    create_simple_charts(top_100.head(20), org_summary.head(10))
    
    return top_100, org_summary

def create_simple_charts(top_projects, org_summary):
    """创建简单图表"""
    try:
        plt.figure(figsize=(15, 10))
        
        # 1. Top 20项目柱状图
        plt.subplot(2, 2, 1)
        top_20 = top_projects.head(20)
        # 简化项目名
        top_20['short_name'] = top_20['full_name'].apply(
            lambda x: x.split('/')[-1] if '/' in x else (x[:20] + '...' if len(x) > 20 else x)
        )
        
        plt.barh(range(len(top_20)), top_20['stars'])
        plt.yticks(range(len(top_20)), top_20['short_name'])
        plt.xlabel('Star数量')
        plt.title('Top 20 GitHub项目')
        plt.gca().invert_yaxis()  # 让最大的在最上面
        
        # 2. Star分布直方图
        plt.subplot(2, 2, 2)
        plt.hist(top_projects['stars'], bins=30, alpha=0.7, edgecolor='black')
        plt.xlabel('Star数量')
        plt.ylabel('项目数量')
        plt.title('Star数量分布')
        plt.grid(alpha=0.3)
        
        # 3. Top 10组织（按项目数）
        plt.subplot(2, 2, 3)
        top_orgs_by_count = org_summary.sort_values('project_count', ascending=False).head(10)
        plt.barh(range(len(top_orgs_by_count)), top_orgs_by_count['project_count'])
        plt.yticks(range(len(top_orgs_by_count)), top_orgs_by_count.index)
        plt.xlabel('项目数量')
        plt.title('Top 10组织（按项目数）')
        plt.gca().invert_yaxis()
        
        # 4. Top 10组织（按总Star数）
        plt.subplot(2, 2, 4)
        top_orgs_by_stars = org_summary.head(10)
        plt.barh(range(len(top_orgs_by_stars)), top_orgs_by_stars['stars_total'])
        plt.yticks(range(len(top_orgs_by_stars)), top_orgs_by_stars.index)
        plt.xlabel('总Star数')
        plt.title('Top 10组织（按总Star数）')
        plt.gca().invert_yaxis()
        
        plt.suptitle('GitHub Top 300 项目分析', fontsize=16)
        plt.tight_layout()
        
        # 保存图表
        charts_dir = Path("output/charts")
        charts_dir.mkdir(exist_ok=True)
        plt.savefig('output/charts/projects_analysis.png', dpi=150, bbox_inches='tight')
        print(f"📊 图表已保存: output/charts/projects_analysis.png")
        
        # 显示图表
        plt.show()
        
    except Exception as e:
        print(f"⚠️  创建图表时出错: {e}")

def main():
    """主函数"""
    print("🚀 开始分析 GitHub Top 300 Metrics...")
    
    # 步骤1：探索数据结构
    result = explore_data_structure()
    if result is None:
        return
    
    base_dir, org_folders = result
    
    # 步骤2：收集项目信息
    df = collect_project_info(base_dir)  # 处理所有组织
    
    # 步骤3：分析Top项目
    if df is not None:
        df_sorted = analyze_top_projects(df)
        
        # 步骤4：保存结果
        save_results(df_sorted)
        
        print(f"\n" + "=" * 60)
        print("✅ 分析完成！")
        print("=" * 60)
        print(f"📊 分析了 {len(df)} 个项目")
        print(f"📁 生成的文件在 output/ 文件夹中")
    else:
        print("❌ 没有收集到数据，分析失败")

if __name__ == "__main__":
    main()