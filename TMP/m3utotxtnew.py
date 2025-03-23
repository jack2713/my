import requests
import os
from collections import defaultdict
import re

# 文件 URL 列表
urls = [
    'https://raw.githubusercontent.com/clion007/livetv/refs/heads/main/m3u/scu.m3u',
    #'https://raw.githubusercontent.com/hujingguang/ChinaIPTV/refs/heads/main/cnTV_AutoUpdate.m3u8',
    'https://raw.githubusercontent.com/big-mouth-cn/tv/refs/heads/main/iptv-ok.m3u',
    #'https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u',
     'https://aktv.space/live.m3u',
    'https://raw.githubusercontent.com/suxuang/myIPTV/main/ipv6.m3u',
    # 'https://qu.ax/kBip.m3u',
    #'https://huangsuming.github.io/iptv/list/tvlist.txt',
    # 'https://raw.githubusercontent.com/mavin521/syiptv/main/live.m3u',
]

# 初始化字典
all_channels_dict = defaultdict(list)

# 遍历 URL 列表并处理每个 m3u 文件
for url in urls:
    # 发送请求获取文件内容
    response = requests.get(url)
    m3u_content = response.text

    # 初始化频道信息
    channels = []
    group_title = ""
    channel_name = ""
    tvg_logo = ""
    streaming_url = ""

    # 提取频道信息
    for i, line in enumerate(m3u_content.splitlines()):
        line = line.strip()
        
        if line.startswith("#EXTINF:"):
            # 使用正则从 #EXTINF 行提取信息
            match = re.match(r'#EXTINF:-1.*?group-title="([^"]+)".*?tvg-name="([^"]*)".*?tvg-logo="([^"]*)"', line)
            if match:
                group_title = match.group(1)  # 提取分组信息
                tvg_name = match.group(2)  # 提取频道名称（可能为空或"null"）
                tvg_logo = match.group(3)  # 提取频道 Logo URL
                
                # 如果 tvg-name 为空或为 "null"，则使用最后一个逗号后的内容作为频道名称
                if not tvg_name or tvg_name.lower() == "null":
                    channel_name = line.split(',')[-1].strip()
                else:
                    channel_name = tvg_name
            else:
                # 如果正则没有匹配，使用备选方案提取信息
                channel_info = line.split(",")
                if len(channel_info) > 1:
                    channel_name = channel_info[1].split(" ")[0].strip()  # 使用第一个逗号后的内容作为频道名称
                group_title_items = [item.split("group-title=")[1].split('"')[1] for item in channel_info if "group-title=" in item]
                group_title = group_title_items[0] if group_title_items else group_title
        elif line.startswith("http"):
            # 处理流媒体 URL 行
            streaming_url = line.strip()
            if channel_name and streaming_url:  # 确保频道名称和 URL 非空
                # 存储频道信息
                channels.append({
                    "channel_name": channel_name,
                    "group_title": group_title,
                    "tvg_logo": tvg_logo,
                    "streaming_url": streaming_url,
                    "line_index": i
                })
            # 清空临时数据以便下一个频道
            channel_name = ""
            group_title = ""
            tvg_logo = ""

    # 将当前文件的频道添加到总字典中
    for channel in channels:
        all_channels_dict[channel["group_title"]].append(channel)

# 输出到文件
output_file_path = "TMP/TMP1.txt"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
with open(output_file_path, "w", encoding="utf-8") as output_file:
    prev_group_title = None
    for group_title, channels_in_group in all_channels_dict.items():
        sorted_channels_in_group = sorted(channels_in_group, key=lambda x: x["line_index"])  # 确保每个分组内的频道也是排序的
        
        # 将 group-title 转换成你要求的格式
        if group_title != prev_group_title:
            if prev_group_title:
                output_file.write("\n")  # 在每个分组后添加一个空行
            if group_title:
                # 修改分组标题的输出格式，例如：将 group-title 输出为 '央视频道,#genre#'
                output_file.write(f"{group_title},#genre#\n")
            prev_group_title = group_title
        
        for channel in sorted_channels_in_group:
            channel_name = channel["channel_name"]
            tvg_logo = channel["tvg_logo"]
            streaming_url = channel["streaming_url"]

            # 输出为一行：频道名称和流媒体 URL，逗号分隔
            output_file.write(f"{channel_name}, {streaming_url}\n")

print(f"提取完成,结果已保存到 {output_file_path}")
