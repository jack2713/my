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

# --- 统一管理版本信息 ---
APP_VERSION = "1.0"
APP_TITLE = f"电视直播源检测工具 V{APP_VERSION}"
# --- 统一管理版本信息结束 ---


class StreamCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1200x800")

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
            messagebox.showinfo("提示", f"输入文件 {self.input_file} 已创建，请添加直播源后重新运行程序")

        # --- 变量 ---
        self.file_path = tk.StringVar(value=self.input_file)
        self.export_dir = tk.StringVar(value="TMP")
        self.source_file_basename = tk.StringVar(value="169")
        self.timeout, self.max_threads = tk.IntVar(value=8), tk.IntVar(value=30)
        # 默认开启的选项
        self.use_deep_check, self.run_speed_test = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
        self.status_message = tk.StringVar()
        self.total_links, self.checked_links = tk.IntVar(value=0), tk.IntVar(value=0)
        self.valid_links, self.invalid_links = tk.IntVar(value=0), tk.IntVar(value=0)
        self.links_to_check, self.last_export_path = [], None
        self.is_running, self.stop_requested, self.executor = False, False, None
        self.result_queue = queue.Queue()
        self.sort_state = {
            "all": {"col": "原始序号", "rev": False},
            "valid": {"col": "原始序号", "rev": False},
            "invalid": {"col": "原始序号", "rev": False},
        }

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
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
            config_frame, from_=1, to=60, textvariable=self.timeout, width=8
        )
        self.timeout_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Label(config_frame, text="线程数:").grid(row=2, column=2, padx=(10, 5), pady=5, sticky=W)
        self.threads_spinbox = ttk.Spinbox(
            config_frame, from_=1, to=100, textvariable=self.max_threads, width=8
        )
        self.threads_spinbox.grid(row=2, column=3, padx=5, pady=5, sticky=W)
        
        check_options_frame = ttk.Frame(config_frame)
        check_options_frame.grid(row=2, column=4, padx=5, pady=5, sticky=E)
        
        self.deep_check_btn = ttk.Checkbutton(
            check_options_frame,
            text="深度检测",
            variable=self.use_deep_check,
            style="primary.Roundtoggle.Toolbutton",
        )
        self.deep_check_btn.pack(side=LEFT, padx=(0, 5))
        
        self.speed_test_btn = ttk.Checkbutton(
            check_options_frame,
            text="速度测试(慢)",
            variable=self.run_speed_test,
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
        ttk.Label(stats_inner_frame, textvariable=self.total_links).pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(stats_inner_frame, text="已检:").pack(side=LEFT, padx=(0, 2))
        ttk.Label(stats_inner_frame, textvariable=self.checked_links).pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(stats_inner_frame, text="有效:").pack(side=LEFT, padx=(0, 2))
        ttk.Label(
            stats_inner_frame, textvariable=self.valid_links, foreground="green"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(stats_inner_frame, text="无效:").pack(side=LEFT, padx=(0, 2))
        ttk.Label(
            stats_inner_frame, textvariable=self.invalid_links, foreground="red"
        ).pack(side=LEFT)
        
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

    def select_all_items(self, tree):
        tree.selection_set(tree.get_children())
        return "break"

    def show_context_menu(self, event, tree):
        clicked_item = tree.identify_row(event.y)
        if not clicked_item:
            return

        selected_items = tree.selection()
        num_selected = len(selected_items)

        if clicked_item not in selected_items:
            tree.selection_set(clicked_item)
            selected_items = tree.selection()
            num_selected = 1

        context_menu = tk.Menu(tree, tearoff=0)

        if num_selected <= 1:
            context_menu.add_command(
                label="复制 URL", command=lambda: self.copy_cell_value(tree, "URL")
            )
            context_menu.add_command(
                label="复制 频道名称",
                command=lambda: self.copy_cell_value(tree, "频道名称"),
            )
            context_menu.add_separator()
            context_menu.add_command(
                label="复制 整行数据", command=lambda: self.copy_cell_value(tree, None)
            )
        else:
            context_menu.add_command(
                label=f"复制 {num_selected} 个 URL (每行一个)",
                command=lambda: self.copy_multiple_values(tree, "URL"),
            )
            context_menu.add_command(
                label=f"复制 {num_selected} 个 频道名称",
                command=lambda: self.copy_multiple_values(tree, "频道名称"),
            )
            context_menu.add_separator()
            context_menu.add_command(
                label=f"复制 {num_selected} 行的全部数据",
                command=lambda: self.copy_multiple_values(tree, None),
            )

        context_menu.post(event.x_root, event.y_root)

    def copy_cell_value(self, tree, column_name):
        selected_items = tree.selection()
        if not selected_items:
            return
        item_id = selected_items[0]
        all_values = tree.item(item_id, "values")

        if column_name is None:
            text_to_copy = ", ".join(map(str, all_values))
            message = "整行数据已复制到剪贴板"
        else:
            try:
                col_index = tree["columns"].index(column_name)
                text_to_copy = all_values[col_index]
                message = f"{column_name} 已复制到剪贴板"
            except (ValueError, IndexError):
                self.set_status_message("错误：找不到指定的列", error=True)
                return

        self.root.clipboard_clear()
        self.root.clipboard_append(text_to_copy)
        self.set_status_message(message)

    def copy_multiple_values(self, tree, column_name):
        selected_items = tree.selection()
        if not selected_items:
            return

        data_to_copy = []
        try:
            col_index = tree["columns"].index(column_name) if column_name else -1
            for item_id in selected_items:
                all_values = tree.item(item_id, "values")
                if column_name is None:
                    data_to_copy.append(", ".join(map(str, all_values)))
                else:
                    data_to_copy.append(all_values[col_index])

            text_to_copy = "\n".join(data_to_copy)
            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)

            noun = "行数据" if column_name is None else column_name
            self.set_status_message(f"已复制 {len(data_to_copy)} 个 {noun} 到剪贴板")

        except (ValueError, IndexError):
            self.set_status_message("错误：处理批量复制时出错", error=True)

    def set_status_message(self, message, error=False, duration=3000):
        self.status_message.set(message)
        self.status_label.config(bootstyle="danger" if error else "primary")
        self.root.after(duration, lambda: self.status_message.set(""))

    def sort_treeview_column(self, tv, col, tree_name):
        sort_info = self.sort_state[tree_name]
        reverse = not sort_info["rev"] if col == sort_info["col"] else False
        sort_info["col"] = col
        sort_info["rev"] = reverse
        l = [(tv.set(k, col), k) for k in tv.get_children("")]

        def safe_float_convert(s):
            try:
                return float(s)
            except (ValueError, TypeError):
                return -1

        if col in ("原始序号", "延迟(ms)", "速度(KB/s)"):
            l.sort(key=lambda t: safe_float_convert(t[0]), reverse=reverse)
        else:
            l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, "", index)

    def toggle_theme(self):
        current_theme = self.root.style.theme_use()
        if current_theme == "litera":
            self.root.style.theme_use("darkly")
        else:
            self.root.style.theme_use("litera")

    def parse_file(self):
        """解析输入文件，支持多种格式"""
        if not os.path.exists(self.input_file):
            self.set_status_message(f"错误：输入文件 {self.input_file} 不存在", error=True)
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
            messagebox.showerror("文件读取错误", f"解析文件时出错: {e}")
            return []
            
        return links

    def start_checking(self):
        """开始检测"""
        self.links_to_check = self.parse_file()
        if not self.links_to_check:
            self.set_status_message("没有找到可检测的直播源", error=True)
            return
            
        self.is_running, self.stop_requested = True, False
        self.toggle_controls(True)
        self.reset_ui()
        self.total_links.set(len(self.links_to_check))
        self.progress_bar["maximum"] = len(self.links_to_check)
        
        self.set_status_message(f"开始检测 {len(self.links_to_check)} 个直播源...")
        threading.Thread(target=self.submit_tasks, daemon=True).start()
        self.root.after(100, self.process_queue)

    def submit_tasks(self):
        """提交检测任务到线程池"""
        check_function = (
            self.check_url_deep if self.use_deep_check.get() else self.check_url_simple
        )
        with ThreadPoolExecutor(max_workers=self.max_threads.get()) as executor:
            self.executor = executor
            for index, link_info in enumerate(self.links_to_check):
                if self.stop_requested:
                    break
                executor.submit(
                    check_function,
                    index,
                    link_info,
                    self.timeout.get(),
                    self.run_speed_test.get(),
                )

    def stop_checking(self):
        """停止检测"""
        if not self.is_running:
            return
        self.stop_requested = True
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        self.is_running = False
        self.toggle_controls(False)
        self.set_status_message("检测已停止")
        self.root.title(APP_TITLE)

    def toggle_controls(self, is_checking):
        """切换控件状态"""
        state = DISABLED if is_checking else NORMAL
        for widget in [
            self.start_button,
            self.timeout_spinbox,
            self.threads_spinbox,
            self.deep_check_btn,
            self.speed_test_btn,
        ]:
            widget.config(state=state)
        self.stop_button.config(state=NORMAL if is_checking else DISABLED)

    def reset_ui(self):
        """重置UI状态"""
        self.checked_links.set(0)
        self.valid_links.set(0)
        self.invalid_links.set(0)
        self.progress_bar["value"] = 0
        self.root.title(f"{APP_TITLE} - 检测中...")
        
        for name in ["all", "valid", "invalid"]:
            tree = getattr(self, f"tree_{name}")
            for item in tree.get_children():
                tree.delete(item)
            self.sort_state[name] = {"col": "原始序号", "rev": False}

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

    def process_queue(self):
        """处理结果队列"""
        try:
            while not self.result_queue.empty():
                result = self.result_queue.get_nowait()
                self.checked_links.set(self.checked_links.get() + 1)
                
                values = (
                    result["index"],
                    result["name"],
                    result["url"],
                    result["status"],
                    result["latency"],
                    result["speed"],
                    result["details"],
                )
                
                tag = "invalid"
                if result["status"] == "有效":
                    self.valid_links.set(self.valid_links.get() + 1)
                    tag = "valid"
                    self.tree_valid.insert("", END, values=values, tags=(tag,))
                else:
                    self.invalid_links.set(self.invalid_links.get() + 1)
                    self.tree_invalid.insert("", END, values=values, tags=(tag,))
                    
                self.tree_all.insert("", END, values=values, tags=(tag,))
                self.progress_bar["value"] = self.checked_links.get()
                
        except queue.Empty:
            pass
        finally:
            if self.is_running and not self.stop_requested:
                if self.checked_links.get() == self.total_links.get():
                    self.is_running = False
                    self.toggle_controls(False)
                    self.export_button.config(state=NORMAL)
                    self.root.title(APP_TITLE)
                    
                    # 自动导出结果
                    self.export_results()
                    
                    messagebox.showinfo(
                        "完成",
                        f"检测完成！\n有效: {self.valid_links.get()}\n无效: {self.invalid_links.get()}\n结果已保存到 {self.output_file}"
                    )
                else:
                    self.root.after(100, self.process_queue)

    def export_results(self):
        """导出有效结果到文件"""
        try:
            valid_items = self.tree_valid.get_children()
            if not valid_items:
                self.set_status_message("没有有效结果可导出", error=True)
                return
                
            with open(self.output_file, "w", encoding="utf-8") as f:
                for item in valid_items:
                    values = self.tree_valid.item(item, "values")
                    f.write(f"{values[2]}\n")  # 只写入URL
                    
            self.last_export_path = os.path.dirname(self.output_file)
            self.export_path_label.config(text=f"导出位置: {self.output_file}")
            self.set_status_message(f"已导出 {len(valid_items)} 个有效直播源")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"导出文件时出错: {e}")

    def open_export_folder(self, event=None):
        """打开导出文件夹"""
        if not os.path.exists(self.output_file):
            messagebox.showwarning("提示", "输出文件不存在，请先完成检测。")
            return
            
        folder_path = os.path.dirname(os.path.abspath(self.output_file))
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror(
                "打开失败",
                f"无法自动打开文件夹，请手动访问：\n{folder_path}\n错误: {e}",
            )

    def on_closing(self):
        """关闭窗口时的处理"""
        if self.is_running and messagebox.askyesno(
            "退出", "检测正在进行中，确定要退出吗？"
        ):
            self.stop_checking()
            self.root.destroy()
        elif not self.is_running:
            self.root.destroy()


if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    app = StreamCheckerApp(root)
    root.mainloop()
