import requests
import os
from collections import defaultdict

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
    channels_dict = defaultdict(list)

    # 提取频道信息
    channels = []
    group_title = ""
    for i, line in enumerate(m3u_content.splitlines()):
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # 从 #EXTINF: 行提取频道名称和分组信息
            channel_info = line.split(",", 1)  # 分割成两部分：时长和剩余信息
            if len(channel_info) > 1:
                remaining_info = channel_info[1]
                channel_props = remaining_info.split()  # 按空格分割属性
                
                # 提取频道名称（tvg-name）
                channel_name = next((prop.split("=")[1].strip('"') for prop in channel_props if prop.startswith("tvg-name=")), "")
                
                # 提取分组标题（group-title）
                group_title = next((prop.split("=")[1].strip('"') for prop in channel_props if prop.startswith("group-title=")), "")
        elif line.startswith("http"):
            # 处理流媒体 URL 行
            streaming_url = line
            channels.append({"channel_name": channel_name, "group_title": group_title, "streaming_url": streaming_url, "line_index": i})

    # 按照分组对频道进行分组
    grouped_channels = defaultdict(list)
    for channel in channels:
        grouped_channels[channel["group_title"]].append(channel)

    # 按照行号对每个分组内部的频道进行排序
    sorted_channels = []
    for group_title, channels_in_group in grouped_channels.items():
        sorted_channels.extend(sorted(channels_in_group, key=lambda x: x["line_index"]))

    # 将当前文件的频道添加到总字典中
    for channel in sorted_channels:
        all_channels_dict[channel["group_title"]].append(channel)

# 输出到文件
output_file_path = "TMP/TMP1.txt"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)  # 确保输出目录存在
with open(output_file_path, "w", encoding="utf-8") as output_file:
    prev_group_title = None
    for group_title, channels_in_group in all_channels_dict.items():
        sorted_channels_in_group = sorted(channels_in_group, key=lambda x: x["line_index"])
        if group_title != prev_group_title:
            if prev_group_title:
                output_file.write("\n")
            if group_title:
                output_file.write(f"{group_title},#genre#\n")
            prev_group_title = group_title
        for channel in sorted_channels_in_group:
            channel_name = channel["channel_name"]
            streaming_url = channel["streaming_url"]
            output_file.write(f"{channel_name},{streaming_url}\n")

print(f"提取完成,结果已保存到 {output_file_path}")
