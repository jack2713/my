import requests
import os
import re
from collections import defaultdict, OrderedDict

# 文件 URL 列表
urls = [
    'https://raw.githubusercontent.com/Drewski2423/DrewLive/main/MergedPlaylist.m3u8',
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

def normalize_url(url):
    """标准化URL，用于去重比较"""
    # 移除URL末尾的斜杠和常见参数
    url = url.strip()
    # 可以在这里添加更多的URL标准化规则
    return url

def is_duplicate_channel(existing_channels, new_channel):
    """检查是否为重复频道"""
    new_url = normalize_url(new_channel['streaming_url'])
    new_name = new_channel['channel_name'].strip().lower()
    
    for existing_channel in existing_channels:
        existing_url = normalize_url(existing_channel['streaming_url'])
        existing_name = existing_channel['channel_name'].strip().lower()
        
        # 如果URL相同，认为是重复频道
        if new_url == existing_url:
            return True
        
        # 如果频道名称非常相似且分组相同，也认为是重复
        if (new_name == existing_name and 
            new_channel.get('group_title', '').lower() == existing_channel.get('group_title', '').lower()):
            return True
    
    return False

# 使用OrderedDict保持分组顺序
all_channels_dict = OrderedDict()
group_order = []
processed_urls = set()  # 用于记录已处理的URL，实现URL级别的去重

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
                    # URL级别的去重
                    normalized_url = normalize_url(streaming_url)
                    if normalized_url in processed_urls:
                        i += 1
                        continue
                    processed_urls.add(normalized_url)
                    
                    channel_name = extract_channel_name(line)
                    
                    # 处理分组
                    if not group_title or group_title.lower() in ["null", "none"]:
                        group_title = "其他"
                    
                    # 如果URL包含联通标识，则在分组名称后添加"-联通"
                    if "http://sc.rrs.169ol.com" in streaming_url:
                        group_title = f"{group_title}-联通"
                    
                    # 过滤内容
                    if ("成人" not in group_title and 
                        "直播中国" not in group_title and 
                        "列表更新" not in group_title):
                        
                        # 记录分组出现的顺序
                        if group_title not in all_channels_dict:
                            all_channels_dict[group_title] = []
                            group_order.append(group_title)
                        
                        channel_data = {
                            "channel_name": channel_name,
                            "tvg_logo": tvg_logo,
                            "streaming_url": streaming_url,
                            "line_index": i,
                            "source_url": url,  # 记录来源URL
                            "group_title": group_title  # 添加分组信息用于去重比较
                        }
                        
                        # 频道级别的去重（在同一分组内）
                        if not is_duplicate_channel(all_channels_dict[group_title], channel_data):
                            all_channels_dict[group_title].append(channel_data)
            i += 1
    except Exception as e:
        print(f"处理URL {url} 时出错: {e}")

# 统计信息
total_channels = 0
for group_title, channels in all_channels_dict.items():
    total_channels += len(channels)
    print(f"分组 '{group_title}' 有 {len(channels)} 个频道")

print(f"总共处理了 {total_channels} 个频道")

# 输出到文件
output_file_path = "TMP/1699.txt"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

with open(output_file_path, "w", encoding="utf-8") as output_file:
    # 按照分组在源文件中出现的顺序输出
    for group_title in group_order:
        if group_title in all_channels_dict:
            channels = all_channels_dict[group_title]
            if channels:
                output_file.write(f"{group_title},#genre#\n")
                # 按照频道在源文件中的顺序输出
                for channel in sorted(channels, key=lambda x: (x['source_url'], x['line_index'])):
                    output_file.write(f"{channel['channel_name']},{channel['streaming_url']}\n")
                output_file.write("\n")

print(f"提取完成,结果已保存到 {output_file_path}")
print(f"最终保留了 {total_channels} 个不重复的频道")
