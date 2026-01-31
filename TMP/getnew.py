import requests
import os
from concurrent.futures import ThreadPoolExecutor

# 在这里配置URL列表
URL_CONFIG = [
    "上海,https://sh.sohu.blog/list.txt",
    "天津,https://tj.sohu.blog/list.txt",
    "北京,https://bj.sohu.blog/list.txt",
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
