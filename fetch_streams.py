import requests
import time

def fetch_and_replace(urls):
    all_processed_lines = []  # 用于存储所有URL处理后的行（不去重）

    for url in urls:
        try:
            # 设置超时时间为15秒
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
                    # 过滤掉不需要的行
                    if '更新时间' in line or time.strftime("%Y%m%d") in line or '关于' in line or '解锁' in line or '公众号' in line or '软件库' in line:
                        continue

                    # 检查行是否包含#genre#，并根据条件处理下划线和'??'
                    if '#genre#' in line.lower():
                        # 如果同时包含#genre#和_，则过滤掉_
                        if '_' in line:
                            processed_line = line.replace('_', '').replace('??', '')
                        else:
                            processed_line = line.replace('??', '')  # 如果没有_，则只替换'??'
                    else:
                        processed_line = line  # 如果不包含#genre#，则不进行替换

                    # 直接添加到最终列表中（不去重）
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
    notice = "注意事项,#genre#\n" + timestamp + "仅供测试自用如有侵权请通知,http://rihou.cc:555/mp4?id=lndjll.mp4\n"
    with open(f'myq.txt', 'w', encoding='UTF-8') as file:
        file.write(notice)  # 首先写入注意事项
        for line in all_processed_lines:
            file.write(line + '\n')  # 每个行之间添加一个换行符

if __name__ == "__main__":
    # 定义多个URL
    urls = [
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/my03.txt',
        'http://aktv.top/live.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/dy.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP1.txt',
        'http://rihou.cc:555/gggg.nzk',
        'https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.txt',
        'http://47.99.102.252/live.txt',
        #'http://kxrj.site:55/lib/kx2024.txt',
        'https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt',
        'https://raw.githubusercontent.com/qinvision/Film-Television/refs/heads/main/dujuejiami.txt',
        'https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.txt',
        'https://live.zbds.top/tv/iptv6.txt',
        'https://live.zbds.top/tv/iptv4.txt',
        'http://yyrj.fun/tv',
    ]

    fetch_and_replace(urls)
