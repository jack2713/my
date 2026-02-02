import requests
import os
from concurrent.futures import ThreadPoolExecutor

# 在这里配置URL列表
URL_CONFIG = [
"央视,https://cctv.sohu.blog/list.txt",
"四川,https://sc.sohu.blog/list.txt",
"重庆,https://cq.sohu.blog/list.txt",
"云南,https://yn.sohu.blog/list.txt",
"贵州,https://gz.sohu.blog/list.txt",
"北京,https://bj.sohu.blog/list.txt",
"天津,https://tj.sohu.blog/list.txt",
"河北,https://heb.sohu.blog/list.txt",
"山西,https://sx.sohu.blog/list.txt",
"内蒙古,https://nmg.sohu.blog/list.txt",
"吉林,https://jl.sohu.blog/list.txt",
"黑龙江,https://hlj.sohu.blog/list.txt",
"上海,https://sh.sohu.blog/list.txt",
"江苏,https://js.sohu.blog/list.txt",
"浙江,https://zj.sohu.blog/list.txt",
"安徽,https://ah.sohu.blog/list.txt",
"福建,https://fj.sohu.blog/list.txt",
"江西,https://jx.sohu.blog/list.txt",
"山东,https://sd.sohu.blog/list.txt",
"河南,https://hen.sohu.blog/list.txt",
"湖北,https://hub.sohu.blog/list.txt",
"湖南,https://hun.sohu.blog/list.txt",
"广东,https://gd.sohu.blog/list.txt",
"广西,https://gx.sohu.blog/list.txt",
"海南,https://han.sohu.blog/list.txt",
"西藏,https://xz.sohu.blog/list.txt",
"甘肃,https://gs.sohu.blog/list.txt",
"青海,https://qh.sohu.blog/list.txt",
"宁夏,https://nx.sohu.blog/list.txt",
"新疆,https://xj.sohu.blog/list.txt",
"日本,http://jp.sohu.blog/list.txt",
"韩国,http://kr.sohu.blog/list.txt",
"越南,http://vn.sohu.blog/list.txt",
"泰国,http://th.sohu.blog/list.txt",
"印度尼西亚,http://idn.sohu.blog/list.txt",
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
