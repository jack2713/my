import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import queue
import requests
import time
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
import os
import sys
import subprocess
import argparse

# --- 统一管理版本信息 ---
APP_VERSION = "1.0"
APP_TITLE = f"电视直播源检测工具 V{APP_VERSION}"
# --- 统一管理版本信息结束 ---


class StreamCheckerApp:
    def __init__(self, root=None, headless=False):
        self.headless = headless
        if not headless:
            self.root = root
            self.root.title(APP_TITLE)
            self.root.geometry("1200x800")
        else:
            self.root = None

        # --- 设置输入输出文件路径 ---
        self.input_file = "TMP/169.txt"
        self.output_file = "TMP/1699.txt"
        
        # 确保TMP目录存在
        os.makedirs("TMP", exist_ok=True)
        
        # 检查输入文件是否存在
        if not os.path.exists(self.input_file):
            # 如果文件不存在，创建空文件
            with open(self.input_file, 'w', encoding='utf-8') as f:
                f.write("# 请在此文件中添加直播源，每行一个URL\n")
            if not headless:
                messagebox.showinfo("提示", f"输入文件 {self.input_file} 已创建，请添加直播源后重新运行程序")

        # --- 变量 ---
        self.file_path = tk.StringVar(value=self.input_file) if not headless else None
        self.export_dir = tk.StringVar(value="TMP") if not headless else None
        self.source_file_basename = tk.StringVar(value="169") if not headless else None
        self.timeout, self.max_threads = 8, 30
        # 默认开启的选项
        self.use_deep_check, self.run_speed_test = True, False
        self.status_message = tk.StringVar() if not headless else None
        self.total_links, self.checked_links = 0, 0
        self.valid_links, self.invalid_links = 0, 0
        self.links_to_check, self.last_export_path = [], None
        self.is_running, self.stop_requested, self.executor = False, False, None
        self.result_queue = queue.Queue()
        self.valid_results = []
        self.invalid_results = []

        if not headless:
            self.create_widgets()
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """创建GUI界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=5)
        top_frame.grid_columnconfigure(0, weight=1)
        
        config_frame = ttk.Labelframe(top_frame, text="配置选项", padding="10")
        config_frame.grid(row=0, column=0, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)
        
        # 显示输入输出文件信息
        ttk.Label(config_frame, text="输入文件:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Label(config_frame, text=self.input_file, foreground="blue").grid(row=0, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Label(config_frame, text="输出文件:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Label(config_frame, text=self.output_file, foreground="green").grid(row=1, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Label(config_frame, text="超时(秒):").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        self.timeout_spinbox = ttk.Spinbox(
            config_frame, from_=1, to=60, textvariable=tk.IntVar(value=self.timeout), width=8
        )
        self.timeout_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Label(config_frame, text="线程数:").grid(row=2, column=2, padx=(10, 5), pady=5, sticky=W)
        self.threads_spinbox = ttk.Spinbox(
            config_frame, from_=1, to=100, textvariable=tk.IntVar(value=self.max_threads), width=8
        )
        self.threads_spinbox.grid(row=2, column=3, padx=5, pady=5, sticky=W)
        
        check_options_frame = ttk.Frame(config_frame)
        check_options_frame.grid(row=2, column=4, padx=5, pady=5, sticky=E)
        
        self.deep_check_btn = ttk.Checkbutton(
            check_options_frame,
            text="深度检测",
            variable=tk.BooleanVar(value=self.use_deep_check),
            style="primary.Roundtoggle.Toolbutton",
        )
        self.deep_check_btn.pack(side=LEFT, padx=(0, 5))
        
        self.speed_test_btn = ttk.Checkbutton(
            check_options_frame,
            text="速度测试(慢)",
            variable=tk.BooleanVar(value=self.run_speed_test),
            style="success.Roundtoggle.Toolbutton",
        )
        self.speed_test_btn.pack(side=LEFT)

        control_theme_frame = ttk.Frame(main_frame)
        control_theme_frame.pack(fill=X, pady=10)
        
        self.start_button = ttk.Button(
            control_theme_frame,
            text="开始检测",
            command=self.start_checking,
            style="success",
        )
        self.start_button.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        self.stop_button = ttk.Button(
            control_theme_frame,
            text="停止检测",
            command=self.stop_checking,
            style="danger",
            state=DISABLED,
        )
        self.stop_button.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        self.export_button = ttk.Button(
            control_theme_frame,
            text="导出结果",
            command=self.export_results,
            style="info",
            state=DISABLED,
        )
        self.export_button.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        self.theme_button = ttk.Button(
            control_theme_frame,
            text="切换主题",
            command=self.toggle_theme,
            style="secondary",
        )
        self.theme_button.pack(side=LEFT, padx=5, fill=X, expand=True)

        status_frame = ttk.Labelframe(main_frame, text="检测状态", padding="10")
        status_frame.pack(fill=X, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_message, anchor=W
        )
        self.status_label.grid(
            row=4, column=0, columnspan=2, padx=5, pady=(10, 5), sticky=EW
        )
        
        self.progress_bar = ttk.Progressbar(status_frame, mode="determinate")
        self.progress_bar.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky=EW)
        
        stats_inner_frame = ttk.Frame(status_frame)
        stats_inner_frame.grid(row=1, column=0, columnspan=4, sticky=E)
        
        ttk.Label(stats_inner_frame, text="总数:").pack(side=LEFT, padx=(0, 2))
        self.total_label = ttk.Label(stats_inner_frame, text="0")
        self.total_label.pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(stats_inner_frame, text="已检:").pack(side=LEFT, padx=(0, 2))
        self.checked_label = ttk.Label(stats_inner_frame, text="0")
        self.checked_label.pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(stats_inner_frame, text="有效:").pack(side=LEFT, padx=(0, 2))
        self.valid_label = ttk.Label(stats_inner_frame, text="0", foreground="green")
        self.valid_label.pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(stats_inner_frame, text="无效:").pack(side=LEFT, padx=(0, 2))
        self.invalid_label = ttk.Label(stats_inner_frame, text="0", foreground="red")
        self.invalid_label.pack(side=LEFT)
        
        self.export_path_label = ttk.Label(
            status_frame, text="", style="info", cursor="hand2"
        )
        self.export_path_label.grid(
            row=3, column=0, columnspan=4, padx=5, pady=(10, 5), sticky=W
        )
        self.export_path_label.bind("<Button-1>", self.open_export_folder)

        result_frame = ttk.Labelframe(
            main_frame, text="检测结果 (支持Ctrl/Shift多选, 右键可复制)", padding="10"
        )
        result_frame.pack(fill=BOTH, expand=True, pady=5)
        
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill=BOTH, expand=True)
        
        self.create_result_tab("all", "全部")
        self.create_result_tab("valid", "有效源")
        self.create_result_tab("invalid", "无效源")

    def create_result_tab(self, name, text):
        """创建结果标签页"""
        tab = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab, text=text)
        cols = ("原始序号", "频道名称", "URL", "状态", "延迟(ms)", "速度(KB/s)", "信息")

        tree = ttk.Treeview(
            tab, columns=cols, show="headings", height=15, selectmode="extended"
        )
        setattr(self, f"tree_{name}", tree)

        tree.bind("<Button-3>", lambda event, t=tree: self.show_context_menu(event, t))
        tree.bind("<Control-a>", lambda event, t=tree: self.select_all_items(t))
        tree.bind("<Control-A>", lambda event, t=tree: self.select_all_items(t))

        for col in cols:
            tree.heading(
                col,
                text=col,
                command=lambda _col=col, _tree_name=name: self.sort_treeview_column(
                    getattr(self, f"tree_{_tree_name}"), _col, _tree_name
                ),
            )
        tree.column("原始序号", width=80, anchor=CENTER)
        tree.column("频道名称", width=200, anchor=W)
        tree.column("URL", width=400, anchor=W)
        tree.column("状态", width=80, anchor=CENTER)
        tree.column("延迟(ms)", width=100, anchor=CENTER)
        tree.column("速度(KB/s)", width=100, anchor=CENTER)
        tree.column("信息", width=150, anchor=W)

        vsb = ttk.Scrollbar(tab, orient=VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(tab, orient=HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        hsb.pack(side=BOTTOM, fill=X)
        tree.pack(fill=BOTH, expand=True)
        tree.tag_configure("valid", foreground="green")
        tree.tag_configure("invalid", foreground="red")

    def run_headless(self):
        """无头模式运行"""
        print(f"开始检测直播源...")
        print(f"输入文件: {self.input_file}")
        print(f"输出文件: {self.output_file}")
        print(f"超时时间: {self.timeout}秒")
        print(f"线程数: {self.max_threads}")
        print(f"深度检测: {'开启' if self.use_deep_check else '关闭'}")
        print("-" * 50)
        
        self.links_to_check = self.parse_file()
        if not self.links_to_check:
            print("错误: 没有找到可检测的直播源")
            return False
            
        self.total_links = len(self.links_to_check)
        print(f"找到 {self.total_links} 个直播源")
        
        # 开始检测
        self.is_running = True
        self.submit_tasks_headless()
        
        # 处理结果
        while self.checked_links < self.total_links and not self.stop_requested:
            self.process_queue_headless()
            time.sleep(0.1)
            
        # 导出结果
        self.export_results_headless()
        
        print("-" * 50)
        print(f"检测完成!")
        print(f"总数: {self.total_links}")
        print(f"有效: {self.valid_links}")
        print(f"无效: {self.invalid_links}")
        print(f"结果已保存到: {self.output_file}")
        
        return True

    def submit_tasks_headless(self):
        """无头模式提交任务"""
        check_function = self.check_url_deep if self.use_deep_check else self.check_url_simple
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for index, link_info in enumerate(self.links_to_check):
                if self.stop_requested:
                    break
                executor.submit(
                    check_function,
                    index,
                    link_info,
                    self.timeout,
                    self.run_speed_test,
                )

    def process_queue_headless(self):
        """无头模式处理队列"""
        try:
            while not self.result_queue.empty():
                result = self.result_queue.get_nowait()
                self.checked_links += 1
                
                # 更新进度显示
                progress = (self.checked_links / self.total_links) * 100
                print(f"\r进度: {progress:.1f}% [{self.checked_links}/{self.total_links}] - 有效: {self.valid_links} 无效: {self.invalid_links}", end="")
                
                if result["status"] == "有效":
                    self.valid_links += 1
                    self.valid_results.append(result)
                else:
                    self.invalid_links += 1
                    self.invalid_results.append(result)
                    
        except queue.Empty:
            pass

    def export_results_headless(self):
        """无头模式导出结果"""
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                for result in self.valid_results:
                    f.write(f"{result['url']}\n")
            print(f"\n已导出 {len(self.valid_results)} 个有效直播源到 {self.output_file}")
        except Exception as e:
            print(f"导出失败: {e}")

    def parse_file(self):
        """解析输入文件，支持多种格式"""
        if not os.path.exists(self.input_file):
            print(f"错误：输入文件 {self.input_file} 不存在")
            return []
            
        links = []
        try:
            with open(self.input_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                
            for index, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                    
                # 支持多种格式：URL, 名称,URL, #EXTINF格式
                if "," in line:
                    parts = line.split(",", 1)
                    name, url = parts[0].strip(), parts[1].strip()
                else:
                    name = f"频道_{index+1}"
                    url = line
                    
                if "://" in url:
                    links.append({"name": name, "url": url})
                    
        except Exception as e:
            print(f"文件读取错误: {e}")
            return []
            
        return links

    def check_url_simple(self, index, link_info, timeout, run_speed_test):
        """简单检测模式"""
        if self.stop_requested:
            return
        result = self._create_result_dict(index, link_info)
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            start_time = time.time()
            response = requests.get(link_info["url"], headers=headers, timeout=timeout)
            latency = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result.update({
                    "status": "有效",
                    "latency": latency,
                    "details": f"OK ({response.status_code})"
                })
            else:
                result["details"] = f"HTTP错误: {response.status_code}"
                
        except requests.exceptions.Timeout:
            result["details"] = f"超时 (>{timeout}s)"
        except requests.exceptions.RequestException as e:
            result["details"] = f"连接错误: {str(e)}"
        except Exception as e:
            result["details"] = f"未知错误: {str(e)}"
            
        if not self.stop_requested:
            self.result_queue.put(result)

    def check_url_deep(self, index, link_info, timeout, run_speed_test):
        """深度检测模式"""
        if self.stop_requested:
            return
        result = self._create_result_dict(index, link_info)
        base_url = link_info["url"]
        start_time = time.time()
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            with requests.get(
                base_url, headers=headers, timeout=timeout, stream=True
            ) as r:
                r.raise_for_status()
                latency = int((time.time() - start_time) * 1000)
                
                # 简单速度测试
                speed = "-"
                if run_speed_test:
                    test_start = time.time()
                    chunk = next(r.iter_content(chunk_size=1024), None)
                    if chunk:
                        test_time = time.time() - test_start
                        if test_time > 0:
                            speed = f"{len(chunk) / test_time / 1024:.2f}"
                
                result.update({
                    "status": "有效",
                    "latency": latency,
                    "speed": speed,
                    "details": f"OK ({r.status_code})"
                })
                
        except requests.exceptions.Timeout:
            result["details"] = f"超时 (>{timeout}s)"
        except requests.exceptions.HTTPError as e:
            result["details"] = f"HTTP错误: {e.response.status_code if hasattr(e, 'response') else str(e)}"
        except requests.exceptions.RequestException as e:
            result["details"] = f"连接错误: {str(e)}"
        except Exception as e:
            result["details"] = f"未知错误: {str(e)}"
            
        if not self.stop_requested:
            self.result_queue.put(result)

    def _create_result_dict(self, index, link_info):
        """创建结果字典"""
        return {
            "index": index + 1,
            "name": link_info["name"],
            "url": link_info["url"],
            "status": "无效",
            "latency": "-",
            "speed": "-",
            "details": "",
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='电视直播源检测工具')
    parser.add_argument('--headless', action='store_true', help='无头模式运行')
    parser.add_argument('--input', type=str, default='TMP/169.txt', help='输入文件路径')
    parser.add_argument('--output', type=str, default='TMP/1699.txt', help='输出文件路径')
    parser.add_argument('--timeout', type=int, default=8, help='超时时间(秒)')
    parser.add_argument('--threads', type=int, default=30, help='线程数')
    parser.add_argument('--deep', action='store_true', help='启用深度检测')
    parser.add_argument('--speed', action='store_true', help='启用速度测试')
    
    args = parser.parse_args()
    
    if args.headless:
        # 无头模式运行
        app = StreamCheckerApp(headless=True)
        app.input_file = args.input
        app.output_file = args.output
        app.timeout = args.timeout
        app.max_threads = args.threads
        app.use_deep_check = args.deep
        app.run_speed_test = args.speed
        
        success = app.run_headless()
        return 0 if success else 1
    else:
        # GUI模式运行
        try:
            root = ttk.Window(themename="litera")
            app = StreamCheckerApp(root)
            root.mainloop()
            return 0
        except Exception as e:
            print(f"GUI模式启动失败: {e}")
            print("尝试使用 --headless 参数运行无头模式")
            return 1


if __name__ == "__main__":
    sys.exit(main())
