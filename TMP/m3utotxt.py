import requests
import os
import re
from collections import defaultdict

def fetch_m3u_channels_and_save(urls, output_file_path, group_filter_keywords=None, line_filter_keywords=None):
    """
    调整后的版本，支持：
    1. 固定第一行为 mytv,#genre#
    2. 组过滤：过滤掉包含指定关键词的group组
    3. 行过滤：过滤掉包含指定关键词的频道行
    """
    if group_filter_keywords is None:
        group_filter_keywords = []  # 如：["节点", "测试"]
    if line_filter_keywords is None:
        line_filter_keywords = []   # 如：["更新", "测试"]
    
    all_channels = defaultdict(list)
    
    for url in urls:
        try:
            print(f"正在获取: {url}")
            response = requests.get(url, timeout=10)
            response.encoding = 'utf-8'
            content = response.text
            lines = content.splitlines()
            
            for i in range(len(lines)):
                line = lines[i].strip()
                
                if line.startswith('#EXTINF'):
                    # 获取分组
                    group_match = re.search(r'group-title="([^"]*)"', line)
                    group = group_match.group(1) if group_match else "未分组"
                    
                    # 【2】组过滤：检查group是否包含过滤关键词
                    group_filtered = False
                    for keyword in group_filter_keywords:
                        if keyword in group:
                            group_filtered = True
                            break
                    if group_filtered:
                        continue
                    
                    # 获取名称
                    name_match = re.search(r'tvg-name="([^"]*)"', line)
                    if name_match:
                        name = name_match.group(1)
                    else:
                        name = line.split(',')[-1].split(' - ')[0].strip()
                    
                    # 【3】行过滤：检查名称是否包含过滤关键词
                    line_filtered = False
                    for keyword in line_filter_keywords:
                        if keyword in name:
                            line_filtered = True
                            break
                    if line_filtered:
                        continue
                    
                    # 获取URL
                    if i + 1 < len(lines) and lines[i+1].startswith(('http://', 'https://')):
                        channel_url = lines[i+1].strip()
                        if name and channel_url:
                            all_channels[group].append((name, channel_url))
                            
        except Exception as e:
            print(f"处理 {url} 时出错: {e}")
    
    # 保存到文件
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "w", encoding="utf-8") as f:
        # 【1】固定第一行为 mytv,#genre#
        f.write("mytv,#genre#\n")
        
        # 不再输出原来的 #genre# 行，直接输出所有频道
        for group, channels in all_channels.items():
            if channels:
                for name, channel_url in channels:
                    f.write(f"{name},{channel_url}\n")
    
    # 统计信息
    total_channels = sum(len(channels) for channels in all_channels.values())
    print(f"\n完成！")
    print(f"共获取 {len(all_channels)} 个分组，{total_channels} 个频道")
    print(f"保存到: {output_file_path}")
    if group_filter_keywords:
        print(f"组过滤关键词: {group_filter_keywords}")
    if line_filter_keywords:
        print(f"行过滤关键词: {line_filter_keywords}")


if __name__ == "__main__":
    urls = [
        #'https://raw.githubusercontent.com/judy-gotv/iptv/refs/heads/main/litv.m3u',
        'https://iptv.707626.xyz/sub/K5hMyUOy52A1rzUvV6s5pbADasExbi7x/playlist.m3u',
        'https://cdn.qd.je/live.m3u',
        'https://tv123.cc.cd/tv.m3u',
    ]
    
    output_file_path = "TMP/TMP.txt"
    
    # ====== 在这里配置过滤关键词 ======
    # 组过滤：只要group名称包含这些词的组，整个组都被过滤
    GROUP_FILTER_KEYWORDS = ["节点","免費"]
    
    # 行过滤：只要频道名称包含这些词的行，就被过滤
    LINE_FILTER_KEYWORDS = ["更新"]
    
    fetch_m3u_channels_and_save(
        urls, 
        output_file_path,
        group_filter_keywords=GROUP_FILTER_KEYWORDS,
        line_filter_keywords=LINE_FILTER_KEYWORDS
    )
