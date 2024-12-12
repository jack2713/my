import requests
import os
from collections import defaultdict
import re

# 文件 URL 列表
urls = [
    'https://live.fanmingming.com/tv/m3u/ipv6.m3u',
    'https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u',
    'https://raw.githubusercontent.com/suxuang/myIPTV/main/ipv6.m3u',
    'https://qu.ax/kBip.m3u',
    'https://huangsuming.github.io/iptv/list/tvlist.txt',
    'https://www.mytvsuper.com.mp/m3u/Live.m3u',
]

# 初始化字典
all_channels_dict = defaultdict(list)

# 遍历 URL 列表并处理每个 m3u 文件
for url in urls:
    # 发送请求获取文件内容
    response = requests.get(url)
    m3u_content = response.text

    # 初始化字典
    channels = []
    group_title = ""
    channel_name = ""
    tvg_logo = ""
    tvg_id = ""

    # 提取频道信息
    for i, line in enumerate(m3u_content.splitlines()):
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # 使用正则从 #EXTINF 行提取信息
            match = re.match(r'#EXTINF:-1.*?group-title="([^"]+)".*?tvg-name="([^"]+)".*?tvg-logo="([^"]+)"', line)
            if match:
                group_title = match.group(1)  # 提取分组信息
                channel_name = match.group(2)  # 提取频道名称
                tvg_logo = match.group(3)     # 提取频道 Logo URL
        elif line.startswith("http"):
            # 处理流媒体 URL 行
            streaming_url = line
            if channel_name:  # 确保频道名称非空
                # 存储频道信息
                channels.append({
                    "channel_name": channel_name,
                    "group_title": group_title,
                    "tvg_logo": tvg_logo,
                    "streaming_url": streaming_url,
                    "line_index": i
                })

    # 将当前文件的频道添加到总字典中
    for channel in channels:
        all_channels_dict[channel["group_title"]].append(channel)

# 输出到文件
output_file_path = "TMP/TMP1.txt"
with open(output_file_path, "w", encoding="utf-8") as output_file:
    prev_group_title = None
    for group_title, channels_in_group in all_channels_dict.items():
        sorted_channels_in_group = sorted(channels_in_group, key=lambda x: x["line_index"])  # 确保每个分组内的频道也是排序的
        if group_title != prev_group_title:
            if prev_group_title:
                output_file.write("\n")  # 在每个分组后添加一个空行
            if group_title:
                output_file.write(f"group-title: {group_title}\n")
            prev_group_title = group_title
        for channel in sorted_channels_in_group:
            channel_name = channel["channel_name"]
            tvg_logo = channel["tvg_logo"]
            streaming_url = channel["streaming_url"]
            output_file.write(f"channel-name: {channel_name}\n")
            output_file.write(f"tvg-logo: {tvg_logo}\n")
            output_file.write(f"streaming-url: {streaming_url}\n")
            output_file.write("\n")  # 每个频道后空一行

print(f"提取完成,结果已保存到 {output_file_path}")
