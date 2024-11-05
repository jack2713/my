import requests  
  
def fetch_and_replace():  
    url = 'https://raw.githubusercontent.com/SSM0415/apptest/main/TVonline.txt'  
      
    # 获取文件内容  
    response = requests.get(url)  
    content = response.text  
      
    # 处理每一行，如果包含#genre#，则删除其中的_字符  
    processed_lines = []  
    for line in content.splitlines():  
        if '#genre#' in line.lower():  
            # 使用replace方法将_字符替换为空字符  
            processed_line = line.replace('_', '')  
        else:  
            # 保留原样  
            processed_line = line  
        processed_lines.append(processed_line)  
      
    # 保存到新文件  
    with open('my02.txt', 'w') as file:  
        file.write('\n'.join(processed_lines))  
  
if __name__ == "__main__":  
    fetch_and_replace()
