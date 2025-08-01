import requests
import os
import re
from collections import defaultdict

# 文件 URL 列表
urls = [
    'https://raw.githubusercontent.com/clion007/livetv/refs/heads/main/m3u/scu.m3u',
    'https://raw.githubusercontent.com/big-mouth-cn/tv/refs/heads/main/iptv-ok.m3u',
    'https://live.hacks.tools/iptv/categories/movies.m3u',
    'https://raw.githubusercontent.com/kilvn/iptv/refs/heads/master/iptv%2B.m3u',
    #'https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv4.m3u',
]

def extract_channel_name(extinf_line):
    """从EXTINF行提取频道名称"""
    # 首先尝试获取tvg-name
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', extinf_line)
    tvg_name = tvg_name_match.group(1) if tvg_name_match else None
    
    # 如果tvg-name存在且不为null/空，则使用它
    if tvg_name and tvg_name.lower() not in ["null", "none", ""]:
        return tvg_name
    
    # 否则尝试获取最后一个逗号后的内容
    parts = extinf_line.split(',')
    if len(parts) > 1:
        last_part = parts[-1].strip()
        if last_part:
            return last_part
    
    # 如果都失败，返回"未命名频道"
    return "未命名频道"

# 初始化字典
all_channels_dict = defaultdict(list)

for url in urls:
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        m3u_content = response.text

        lines = m3u_content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("#EXTINF:"):
                group_title = ""
                tvg_logo = ""
                streaming_url = ""
                
                # 提取属性
                attr_matches = re.findall(r'(\S+)=(".*?"|\S+)', line)
                attrs = {k: v.strip('"') for k, v in attr_matches}
                
                group_title = attrs.get('group-title', "")
                tvg_logo = attrs.get('tvg-logo', "")
                
                # 获取URL
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line.startswith(('http', 'rtmp', 'rtsp')):
                        streaming_url = next_line
                        i += 1
                
                if streaming_url:
                    channel_name = extract_channel_name(line)
                    
                    # 处理分组
                    if not group_title or group_title.lower() in ["null", "none"]:
                        group_title = "其他"
                    
                    # 过滤内容
                    if "成人" not in group_title and "直播中国" not in group_title:
                        all_channels_dict[group_title].append({
                            "channel_name": channel_name,
                            "tvg_logo": tvg_logo,
                            "streaming_url": streaming_url,
                            "line_index": i
                        })
            i += 1
    except Exception as e:
        print(f"处理URL {url} 时出错: {e}")

# 输出到文件
output_file_path = "TMP/TMP1.txt"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

with open(output_file_path, "w", encoding="utf-8") as output_file:
    # 先处理"其他"分组
    if "其他" in all_channels_dict:
        output_file.write("其他,#genre#\n")
        for channel in sorted(all_channels_dict["其他"], key=lambda x: x["line_index"]):
            output_file.write(f"{channel['channel_name']},{channel['streaming_url']}\n")
        output_file.write("\n")
    
    # 处理其他分组（按字母顺序排序）
    for group_title in sorted([g for g in all_channels_dict.keys() if g != "其他"]):
        channels = all_channels_dict[group_title]
        if channels:
            output_file.write(f"{group_title},#genre#\n")
            for channel in sorted(channels, key=lambda x: x["line_index"]):
                output_file.write(f"{channel['channel_name']},{channel['streaming_url']}\n")
            output_file.write("\n")

print(f"提取完成,结果已保存到 {output_file_path}")
