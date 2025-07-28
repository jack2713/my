import requests
import os
from collections import defaultdict
import re

# 文件 URL 列表
urls = [
    'https://raw.githubusercontent.com/clion007/livetv/refs/heads/main/m3u/scu.m3u',
    'https://raw.githubusercontent.com/big-mouth-cn/tv/refs/heads/main/iptv-ok.m3u',
    'https://live.hacks.tools/iptv/categories/movies.m3u',
    'https://raw.githubusercontent.com/kilvn/iptv/refs/heads/master/iptv%2B.m3u',
]

# 初始化字典
all_channels_dict = defaultdict(list)

# 遍历 URL 列表并处理每个 m3u 文件
for url in urls:
    try:
        # 发送请求获取文件内容
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'  # 确保正确解码
        m3u_content = response.text

        # 初始化频道信息
        channels = []
        group_title = ""
        channel_name = ""
        tvg_logo = ""
        streaming_url = ""

        # 提取频道信息
        lines = m3u_content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("#EXTINF:"):
                # 重置变量
                group_title = ""
                channel_name = ""
                tvg_logo = ""
                
                # 尝试从EXTINF行提取信息
                # 处理带引号的属性
                attr_matches = re.findall(r'(\S+)=(".*?"|\S+)', line)
                attrs = {k: v.strip('"') for k, v in attr_matches}
                
                if 'group-title' in attrs:
                    group_title = attrs['group-title']
                if 'tvg-logo' in attrs:
                    tvg_logo = attrs['tvg-logo']
                if 'tvg-name' in attrs:
                    channel_name = attrs['tvg-name']
                
                # 如果频道名称为空，尝试从逗号后获取
                if not channel_name:
                    parts = line.split(',')
                    if len(parts) > 1:
                        channel_name = parts[-1].strip()
                
                # 处理下一个行（应该是URL）
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line.startswith(('http', 'rtmp', 'rtsp')):
                        streaming_url = next_line
                        i += 1  # 跳过URL行
                
                if channel_name and streaming_url:
                    # 如果group_title为空，则归类到"其他"
                    if not group_title:
                        group_title = "其他"
                    
                    channels.append({
                        "channel_name": channel_name,
                        "group_title": group_title,
                        "tvg_logo": tvg_logo,
                        "streaming_url": streaming_url,
                        "line_index": i
                    })
            i += 1

        # 将当前文件的频道添加到总字典中
        for channel in channels:
            all_channels_dict[channel["group_title"]].append(channel)
            
    except Exception as e:
        print(f"处理URL {url} 时出错: {e}")
        continue

# 过滤掉含有"成人"字样的分组
filtered_groups = {
    group: channels 
    for group, channels in all_channels_dict.items() 
    if group and "成人" not in group
}

# 输出到文件
output_file_path = "TMP/TMP1.txt"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
with open(output_file_path, "w", encoding="utf-8") as output_file:
    # 先处理"其他"分组
    if "其他" in filtered_groups:
        output_file.write("其他,#genre#\n")
        for channel in sorted(filtered_groups["其他"], key=lambda x: x["line_index"]):
            output_file.write(f"{channel['channel_name']},{channel['streaming_url']}\n")
        output_file.write("\n")
    
    # 处理其他分组（按字母顺序排序）
    for group_title in sorted([g for g in filtered_groups.keys() if g != "其他"]):
        channels_in_group = filtered_groups[group_title]
        if not channels_in_group:
            continue
            
        output_file.write(f"{group_title},#genre#\n")
        for channel in sorted(channels_in_group, key=lambda x: x["line_index"]):
            output_file.write(f"{channel['channel_name']},{channel['streaming_url']}\n")
        output_file.write("\n")

print(f"提取完成,结果已保存到 {output_file_path}")
