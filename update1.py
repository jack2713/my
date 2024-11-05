import requests  
import time  
  
def fetch_and_replace(urls):  
    all_processed_lines = []  # 用于存储所有URL处理后的去重行  
    seen_lines = set()        # 用于跟踪已经遇到过的行  
      
    for url in urls:  
        try:  
            # 设置超时时间为5秒  
            start_time = time.time()  
            response = requests.get(url, timeout=15)  
            end_time = time.time()  
              
            # 计算请求耗时  
            elapsed_time = end_time - start_time  
            print(f"Request to {url} took {elapsed_time:.2f} seconds.")  
              
            # 检查响应状态码  
            if response.status_code == 200:  
                content = response.text  
                  
                # 为当前URL创建一个新的集合来跟踪重复行  
                current_url_seen_lines = set()  
                processed_lines = []  
                  
                # 处理每一行  
                for line in content.splitlines():  
                    # 检查行是否包含#genre#并处理（删除下划线）  
                    if '#genre#' in line.lower():  
                        processed_line = line.replace('_', '')  
                    else:  
                        processed_line = line  
                      
                    # 检查处理后的行是否已经在当前URL的集合中  
                    if processed_line not in current_url_seen_lines:  
                        # 如果不在，则添加到当前URL的集合和最终列表中  
                        current_url_seen_lines.add(processed_line)  
                          
                        # 同时检查处理后的行是否已经在所有URL的全局集合中  
                        # 如果不在，则添加到全局列表中（这里我们实际上不需要这个检查，  
                        # 因为每个URL的内容都应该被视为独立的，但保留这个注释以说明思路）  
                        # if processed_line not in seen_lines:  
                        #     seen_lines.add(processed_line)  
                        #     all_processed_lines.append(processed_line)  
                          
                        # 由于我们不需要跨URL去重，只需在当前URL内去重，  
                        # 因此直接添加到最终列表中即可  
                        processed_lines.append(processed_line)  
                  
                # 将当前URL处理后的去重行添加到全局列表中（作为一个整体块）  
                all_processed_lines.extend(processed_lines)  
                # 注意：如果需要在所有URL之间去重，则应该使用上面的注释掉的代码块，  
                # 并相应地调整逻辑，但这通常不是处理多个独立文件时的需求。  
                  
            else:  
                print(f"Failed to retrieve {url} with status code {response.status_code}.")  
          
        except requests.exceptions.Timeout:  
            print(f"Request to {url} timed out.")  
          
        except requests.exceptions.RequestException as e:  
            print(f"An error occurred while requesting {url}: {e}")  
      
    # 保存到新文件（这里为了区分，使用不同的文件名或添加时间戳）  
    timestamp = time.strftime("%Y%m%d_%H%M%S")  
    with open(f'my02.txt', 'w') as file:  
        for line in all_processed_lines:  
            file.write(line + '\n')  # 每个行之间添加一个换行符  
        # 注意：如果需要在不同URL的内容块之间添加分隔符，  
        # 则可以在遍历all_processed_lines之前或之后添加额外的换行符或分隔文本。  
  
if __name__ == "__main__":  
    # 定义多个URL  
    urls = [  
        'https://raw.githubusercontent.com/SSM0415/apptest/main/TVonline.txt',  
        'https://raw.githubusercontent.com/SSM0415/apptest/refs/heads/main/TVbox2livefomi243.txt',
    ]  
      
    fetch_and_replace(urls)
