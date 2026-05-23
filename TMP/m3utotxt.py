import requests
import os
import re
from collections import defaultdict

def fetch_m3u_channels_and_save(urls, output_file_path):
    """最简单直接的版本"""
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
                    
                    # 获取名称
                    name_match = re.search(r'tvg-name="([^"]*)"', line)
                    if name_match:
                        name = name_match.group(1)
                    else:
                        name = line.split(',')[-1].split(' - ')[0].strip()
                    
                    # 获取URL
                    if i + 1 < len(lines) and lines[i+1].startswith(('http://', 'https://')):
                        url = lines[i+1].strip()
                        if name and url:
                            all_channels[group].append((name, url))
                            
        except Exception as e:
            print(f"处理 {url} 时出错: {e}")
    
    # 保存到文件
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    with open(output_file_path, "w", encoding="utf-8") as f:
        for group, channels in all_channels.items():
            if group and channels:
                f.write(f"{group},#genre#\n")
                for name, url in channels:
                    f.write(f"{name},{url}\n")
    
    print(f"完成！保存到: {output_file_path}")

if __name__ == "__main__":
    urls = [
        #'https://raw.githubusercontent.com/judy-gotv/iptv/refs/heads/main/litv.m3u',
        'https://iptv.707626.xyz/sub/K5hMyUOy52A1rzUvV6s5pbADasExbi7x/playlist.m3u',
        "https://cdn.qd.je/live.m3u",
    ]
    
    output_file_path = "TMP/TMP.txt"
    fetch_m3u_channels_and_save(urls, output_file_path)
