import requests
import time
import chardet  # 用于检测字节数据的编码

def fetch_and_replace(urls):
    all_processed_lines = []
    seen_lines = set()

    for url in urls:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=15)
            end_time = time.time()

            elapsed_time = end_time - start_time
            print(f"Request to {url} took {elapsed_time:.2f} seconds.")

            if response.status_code == 200:
                # 尝试使用响应头中的编码，如果失败则使用chardet检测编码
                try:
                    content = response.text
                except UnicodeDecodeError:
                    # 使用chardet检测编码
                    encoding = chardet.detect(response.content)['UTF-8']
                    content = response.content.decode(encoding)

                for line in content.splitlines():
                    # 你的原始处理逻辑
                    if '更新时间' in line or time.strftime("%Y%m%d") in line or '关于' in line or '解锁' in line or '公众号' in line or '软件库' in line:
                        continue
                    if '#genre#' in line.lower() or '更新时间' not in line:
                        processed_line = line.replace('_', '')
                    else:
                        processed_line = line

                    if processed_line not in seen_lines:
                        seen_lines.add(processed_line)
                        all_processed_lines.append(processed_line)

            else:
                print(f"Failed to retrieve {url} with status code {response.status_code}.")

        except requests.exceptions.Timeout:
            print(f"Request to {url} timed out.")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while requesting {url}: {e}")

    timestamp = time.strftime("%Y%m%d%H%M%S")
    notice = "注意事项,#genre#\n" + timestamp + "仅供测试自用如有侵权请通知,http://cfss.cc/cdn/dyu/11531165.m3u8\n"
    with open('my.txt', 'w', encoding='utf-8') as file:  # 确保文件以UTF-8编码写入
        file.write(notice)
        for line in all_processed_lines:
            file.write(line + '\n')

if __name__ == "__main__":
    urls = [
        'http://47.99.102.252/live.txt',
        'http://kxrj.site:55/lib/kx2024.txt',
    ]

    fetch_and_replace(urls)
