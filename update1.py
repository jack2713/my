

import requests  
import time  
  
def fetch_and_replace(urls):  
    all_processed_lines = []  # 用于存储所有URL处理后的去重行  
    seen_lines = set()        # 用于跟踪已经遇到过的行（全局去重）  
  
    for url in urls:  
        try:  
            # 设置超时时间为15秒（原代码中设置为15秒，但打印信息中写的是5秒，这里保持一致）  
            start_time = time.time()  
            response = requests.get(url, timeout=15)  
            end_time = time.time()  
  
            # 计算请求耗时  
            elapsed_time = end_time - start_time  
            print(f"Request to {url} took {elapsed_time:.2f} seconds.")  
  
            # 检查响应状态码  
            if response.status_code == 200:
                response.encoding = 'utf-8'
                content = response.text  
  
                # 处理每一行  
                for line in content.splitlines():  
                    if '更新时间' in line or time.strftime("%Y%m%d")  in line or '关于' in line or '#EXTINF' in line or '公众号' in line or '软件库' in line:
                        continue
                    # 检查行是否包含#genre#并处理（删除下划线）  
                    if '#genre#' in line.lower() or '更新时间' not in line:  
                        processed_line = line.replace('_', '')  
                    else:  
                        processed_line = line  
  
                    # 检查处理后的行是否已经在全局集合中  
                    if processed_line not in seen_lines:  
                        # 如果不在，则添加到全局集合和最终列表中  
                        seen_lines.add(processed_line)  
                        all_processed_lines.append(processed_line)  
  
            else:  
                print(f"Failed to retrieve {url} with status code {response.status_code}.")  
  
        except requests.exceptions.Timeout:  
            print(f"Request to {url} timed out.")  
  
        except requests.exceptions.RequestException as e:  
            print(f"An error occurred while requesting {url}: {e}")  
  
    # 保存到新文件（使用不同的文件名或添加时间戳）  
    timestamp = time.strftime("%Y%m%d%H%M%S") 
    # 在文件最前面添加注意事项
    notice = "注意事项,#genre#\n"+timestamp+"仅供测试自用如有侵权请通知,http://rihou.cc:555/mp4?id=lndjll.mp4\n" 
    with open(f'my02.txt', 'w', encoding='UTF-8') as file:
        file.write(notice)  # 首先写入注意事项
        for line in all_processed_lines:  
            file.write(line + '\n')  # 每个行之间添加一个换行符  
  
if __name__ == "__main__":  
    # 定义多个URL  
    urls = [
        #'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/temp1.txt',
         'https://raw.githubusercontent.com/zyxusan/IPTV/refs/heads/main/%E5%BD%A9%E8%99%B9%E9%9B%BB%E5%BD%B1.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP.txt',
        'https://raw.githubusercontent.com/dlgt7/TVbox-interface/ddd11b8e92de6c5e162498c8dbad3d7f46e57974/1234.txt',
        'https://raw.githubusercontent.com/dlgt7/TVbox-interface/refs/heads/main/%E5%A6%82%E6%AD%A4%E8%82%BE%E5%A5%BD.txt',
        'https://raw.githubusercontent.com/Gsl201600/Live/refs/heads/main/Mix.txt',
        #'https://qu.ax/HtMB.txt',
        #'https://raw.githubusercontent.com/SSM0415/apptest/main/TVonline.txt',  
        #'https://raw.githubusercontent.com/SSM0415/apptest/refs/heads/main/TVbox2livefomi243.txt',
        #'https://raw.githubusercontent.com/alenin-zhang/IPTV/4e8e4812168164ea11acc0617b814a7948b632f5/av',
        #'https://raw.githubusercontent.com/fish2018/lib/refs/heads/main/txt/%E7%8F%8D%E8%97%8F.m3u',
        #'https://raw.githubusercontent.com/fish2018/lib/refs/heads/main/txt/18%2B.txt',
    ]  
  
    fetch_and_replace(urls)
