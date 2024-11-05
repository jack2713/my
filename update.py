
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
                content = response.text  
  
                # 处理每一行  
                for line in content.splitlines():  
                    # 检查行是否包含#genre#并处理（删除下划线）  
                    if '#genre#' in line.lower():  
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
    timestamp = time.strftime("%Y%m%d_%H%M%S")  
    with open(f'my.txt', 'w') as file:  
        for line in all_processed_lines:  
            file.write(line + '\n')  # 每个行之间添加一个换行符  
  
if __name__ == "__main__":  
    # 定义多个URL  
    urls = [  
        'http://rihou.cc:555/gggg.nzk',  
        'https://mirror.ghproxy.com/raw.githubusercontent.com/suxuang/myIPTV/main/ipv6.m3u',  
    ]  
  
    fetch_and_replace(urls)
