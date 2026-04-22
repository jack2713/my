import requests
import os
from concurrent.futures import ThreadPoolExecutor

# 在这里配置URL列表
URL_CONFIG = [
"上海电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E4%B8%8A%E6%B5%B7%E7%94%B5%E4%BF%A1.txt",
"四川电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E5%9B%9B%E5%B7%9D%E7%94%B5%E4%BF%A1.txt",
"安徽电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E5%AE%89%E5%BE%BD%E7%94%B5%E4%BF%A1.txt",
"广东电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E5%B9%BF%E4%B8%9C%E7%94%B5%E4%BF%A1.txt",
"江苏电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E6%B1%9F%E8%8B%8F%E7%94%B5%E4%BF%A1.txt",
"浙江电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E6%B5%99%E6%B1%9F%E7%94%B5%E4%BF%A1.txt",
"湖北电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E6%B9%96%E5%8C%97%E7%94%B5%E4%BF%A1.txt",
"湖南电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E6%B9%96%E5%8D%97%E7%94%B5%E4%BF%A1.txt",
"福建电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E7%A6%8F%E5%BB%BA%E7%94%B5%E4%BF%A1.txt",
"陕西电信,https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/txt/%E9%99%95%E8%A5%BF%E7%94%B5%E4%BF%A1.txt",
]
def fetch_url(url):
    """获取URL内容"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text.strip()
    except:
        return ""

def process_item(item):
    """处理单个配置项"""
    name, url = item.split(',', 1)
    name = name.strip()
    url = url.strip()
    
    content = fetch_url(url)
    if not content:
        return ""
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    return f"{name},#genre#\n" + "\n".join(lines)

def main():
    """主函数"""
    # 创建目录
    os.makedirs("TMP", exist_ok=True)
    
    # 多线程获取内容
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_item, item): item for item in URL_CONFIG}
        
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    # 写入文件
    with open("TMP/new.txt", 'w', encoding='utf-8') as f:
        f.write("\n\n".join(results))
    
    print(f"完成！已保存到 TMP/new.txt")

if __name__ == "__main__":
    main()
