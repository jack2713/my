import requests
import time
import os

urls = [
    'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp.txt', 
    'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp01.txt',
    'http://156.238.248.80/2099.php',
    'http://bxtv.3a.ink/live.txt',
    'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP1.txt',
    'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/dy01.txt',
    'http://rihou.cc:555/gggg.nzk',
    'https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/bbxx.txt',
    'https://live.hacks.tools/tv/iptv4.txt',
    'http://iptv.4666888.xyz/FYTV.txt',
]

github_token = "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"
all_lines = []

for i, url in enumerate(urls, 1):
    print(f"[{i}/{len(urls)}] 获取: {url[:50]}...")
    
    try:
        # 简化GitHub URL
        if '/refs/heads/' in url:
            url = url.replace('/refs/heads/', '/')
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        if 'github.com/jack2713/my' in url and github_token:
            headers['Authorization'] = f'token {github_token}'
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            response.encoding = 'utf-8'
            for line in response.text.splitlines():
                line = line.rstrip()
                
                # 过滤行
                if any(k in line for k in ['更新时间', '关于', '解锁', '公众号', '软件库', '#EXTINF:']):
                    continue
                
                # 处理#genre#行
                if '#genre#' in line.lower():
                    line = line.replace('_', '').replace('??', '')
                
                if line.strip():
                    all_lines.append(line)
            
            print(f"  成功，添加 {len(response.text.splitlines())} 行中的有效内容")
    except Exception as e:
        print(f"  失败: {e}")

# 保存到文件
timestamp = time.strftime("%Y%m%d%H%M%S")
with open('myq.txt', 'w', encoding='UTF-8') as f:
    f.write("注意事项,#genre#\n")
    f.write(f"{timestamp}仅供测试自用如有侵权请通知,http://zzy789.xyz/douyu1.php?id=3186217\n\n")
    for line in all_lines:
        f.write(line + '\n')

print(f"\n✅ 完成！共保存 {len(all_lines)} 行到 myq.txt")
