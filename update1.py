import requests  
import time  
  
def fetch_and_replace(urls):  
    processed_contents = []  
      
    for url in urls:  
        try:  
            # 设置超时时间为5秒  
            start_time = time.time()  
            response = requests.get(url, timeout=5)  
            end_time = time.time()  
              
            # 计算请求耗时  
            elapsed_time = end_time - start_time  
            print(f"Request to {url} took {elapsed_time:.2f} seconds.")  
              
            # 检查响应状态码  
            if response.status_code == 200:  
                content = response.text  
                  
                # 处理每一行，如果包含#genre#，则删除其中的_字符  
                processed_lines = []  
                for line in content.splitlines():  
                    if '#genre#' in line.lower():  
                        processed_line = line.replace('_', '')  
                    else:  
                        processed_line = line  
                    processed_lines.append(processed_line)  
                  
                # 将处理后的内容添加到列表中  
                processed_contents.append('\n'.join(processed_lines))  
            else:  
                print(f"Failed to retrieve {url} with status code {response.status_code}.")  
          
        except requests.exceptions.Timeout:  
            print(f"Request to {url} timed out.")  
          
        except requests.exceptions.RequestException as e:  
            print(f"An error occurred while requesting {url}: {e}")  
      
    # 保存到新文件（这里为了区分，使用不同的文件名或添加时间戳）  
    timestamp = time.strftime("%Y%m%d_%H%M%S")  
    with open(f'my_processed_contents_{timestamp}.txt', 'w') as file:  
        for content in processed_contents:  
            file.write(content + '\n\n')  # 每个URL的内容之间添加两个换行符作为分隔  
  
if __name__ == "__main__":  
    # 定义多个URL  
    urls = [  
        'https://raw.githubusercontent.com/SSM0415/apptest/main/TVonline.txt',  
        'https://raw.githubusercontent.com/SSM0415/apptest/refs/heads/main/TVbox2livefomi243.txt',
    ]  
      
    fetch_and_replace(urls)
