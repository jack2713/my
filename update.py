import requests
import time
import chardet  # 用于检测字符编码

def decode_content(content_bytes):
    # 尝试使用 UTF-8 解码
    try:
        content = content_bytes.decode('utf-8')
        # 简单的乱码检测：如果包含无法解码的字符，则假定不是 UTF-8
        # 这里使用了一个简单的逻辑：如果解码后的字符串包含非打印字符（如 \x00），则认为是乱码
        if any(ord(char) < 32 for char in content):
            raise UnicodeDecodeError
        return content
    except UnicodeDecodeError:
        # 如果 UTF-8 解码失败，尝试使用 GBK 解码
        try:
            content = content_bytes.decode('gbk')
            return content
        except UnicodeDecodeError:
            # 如果 GBK 也失败，则打印错误信息并返回原始字节（或可选择其他处理方式）
            print("Failed to decode content with both UTF-8 and GBK.")
            return content_bytes.decode('latin1', errors='ignore')  # 使用 latin1 作为回退，忽略错误

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
                # 尝试解码内容
                content_bytes = response.content
                content = decode_content(content_bytes)

                for line in content.splitlines():
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
    with open(f'my.txt', 'w', encoding='utf-8') as file:
        file.write(notice)
        for line in all_processed_lines:
            file.write(line + '\n')

if __name__ == "__main__":
    urls = [
        'https://aktv.top/live.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/my03.txt',
        'http://rihou.cc:555/gggg.nzk',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP.txt',
        'https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.txt',
        'http://47.99.102.252/live.txt',
        'http://kxrj.site:55/lib/kx2024.txt',
    ]

    fetch_and_replace(urls)
