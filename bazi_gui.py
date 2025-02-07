import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from bazi_core import BaziCalculator
from bazi_analysis import BaziAnalyzer
# from datetime_entry import DateTimeEntry
import threading
class DateTimeEntry(ttk.Frame):
    """自定义日期时间输入组件"""
    def __init__(self, master):
        super().__init__(master)
        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()

        ttk.Label(self, text="年").grid(row=0, column=0)
        ttk.Combobox(self, textvariable=self.year_var, width=5, 
                    values=[str(y) for y in range(1950, 2025)]).grid(row=0, column=1)
        
        ttk.Label(self, text="月").grid(row=0, column=2)
        ttk.Combobox(self, textvariable=self.month_var, width=3,
                    values=[f"{m:02d}" for m in range(1,13)]).grid(row=0, column=3)
        
        ttk.Label(self, text="日").grid(row=0, column=4)
        ttk.Combobox(self, textvariable=self.day_var, width=3,
                    values=[f"{d:02d}" for d in range(1,32)]).grid(row=0, column=5)
        
        ttk.Label(self, text="时间").grid(row=0, column=6)
        ttk.Combobox(self, textvariable=self.hour_var, width=3,
                    values=[f"{h:02d}" for h in range(0,24)]).grid(row=0, column=7)
        ttk.Label(self, text=":").grid(row=0, column=8)
        ttk.Combobox(self, textvariable=self.minute_var, width=3,
                    values=[f"{m:02d}" for m in range(0,60,5)]).grid(row=0, column=9)

    def get_datetime(self) -> datetime:
        """获取输入的日期时间"""
        try:
            return datetime(
                year=int(self.year_var.get()),
                month=int(self.month_var.get()),
                day=int(self.day_var.get()),
                hour=int(self.hour_var.get()),
                minute=int(self.minute_var.get())
            )
        except ValueError:
            raise ValueError("无效的日期时间输入")
        
class BaziApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AI 命理分析系统")
        self.window.geometry("1000x800")
        self._create_widgets()
        self.streaming = False
        self.current_report = None

    def _get_base_report(self) -> dict:
        """获取当前命盘数据"""
        if not self.current_report:
            raise ValueError("请先进行排盘分析")
        return self.current_report
    
    def _create_widgets(self):
        # 控制面板
        control_frame = ttk.Frame(self.window)
        control_frame.pack(pady=10, fill="x")
        
        # 模型选择
        ttk.Label(control_frame, text="选择模型：").grid(row=0, column=0)
        self.model_var = tk.StringVar(value=BaziAnalyzer.SUPPORTED_MODELS[0])
        self.model_menu = ttk.Combobox(
            control_frame,
            textvariable=self.model_var,
            values=BaziAnalyzer.SUPPORTED_MODELS,
            width=30,
            state="readonly"
        )
        self.model_menu.grid(row=0, column=1, padx=5)
        
        # 流式输出开关
        self.stream_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            control_frame,
            text="流式输出",
            variable=self.stream_var,
            command=self._toggle_stream
        ).grid(row=0, column=2, padx=10)

        # 输入区域
        input_frame = ttk.LabelFrame(self.window, text="出生信息")
        input_frame.pack(padx=10, pady=10, fill="x")

        # 日期时间输入组件（使用 grid）
        self.datetime_entry = DateTimeEntry(input_frame)
        self.datetime_entry.grid(row=0, column=0, columnspan=4, pady=5)

        # 使用增强版日期时间组件
        # self.datetime_entry = DateTimeEntry(input_frame)
        # self.datetime_entry.pack(padx=10, pady=5)
        # ttk.Button(input_frame, text="设为当前时间", 
        #          command=self.datetime_entry.set_default_time).pack(pady=5)

        # API密钥
        ttk.Label(input_frame, text="API密钥：").grid(row=1, column=0, sticky="e")
        self.api_entry = ttk.Entry(input_frame, width=50)
        self.api_entry.grid(row=1, column=1, columnspan=3, sticky="w", padx=5)

        # 按钮区域
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="排盘", command=self.generate_report).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="AI解析", command=self.analyze_report).pack(side="left", padx=5)

        # 新增对话输入区
        chat_frame = ttk.Frame(self.window)
        chat_frame.pack(pady=10, fill="x")
        
        self.chat_entry = ttk.Entry(chat_frame, width=60)
        self.chat_entry.pack(side="left", padx=5)
        ttk.Button(chat_frame, text="提问", 
                 command=self.ask_question).pack(side="left")
        
        # 初始化对话历史
        self.conversation_history = []

        # 结果展示
        self.result_text = tk.Text(
            self.window,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 11),
            padx=10,
            pady=10
        )
        self.result_text.pack(expand=True, fill="both")

        # 状态栏
        self.status_var = tk.StringVar()
        ttk.Label(
            self.window,
            textvariable=self.status_var,
            foreground="gray"
        ).pack(side="bottom", fill="x")

    def ask_question(self):
        """处理用户提问"""
        question = self.chat_entry.get().strip()
        if not question:
            return
        
        try:
            # 保存对话历史
            self.conversation_history.append({"role": "user", "content": question})
            
            # 在子线程中处理
            threading.Thread(
                target=self._process_question,
                args=(question,),
                daemon=True
            ).start()
            
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def _process_question(self, question: str):
        """处理问题并获取回答"""
        response_content = ""  # 初始化响应内容
        
        try:
            analyzer = BaziAnalyzer(
                api_key=self.api_entry.get(),
                model=self.model_var.get()
            )
            full_prompt = self._build_full_prompt()
            
            self._update_display(f"\n\n[用户提问] {question}\n[AI正在思考...]")
            
            if self.streaming:
                response_stream = analyzer.analyze_with_history(full_prompt, stream=True)
                for chunk in response_stream:
                    response_content += chunk  # 累积响应内容
                    self._update_display(chunk)
            else:
                response_content = analyzer.analyze_with_history(full_prompt)  # 直接获取响应
                self._update_display(f"\n{response_content}")
                
            # 保存完整响应到历史记录
            self.conversation_history.append(
                {"role": "assistant", "content": response_content}
            )
            
        except Exception as e:
            error_msg = f"\n[错误] {str(e)}"
            self._update_display(error_msg)
            self.conversation_history.append(
                {"role": "system", "content": error_msg}
            )

    def _build_full_prompt(self) -> list:
        """构建包含历史记录的完整prompt"""
        base_report = self._get_base_report()  # 获取排盘数据
        return [
            {"role": "system", "content": f"八字排盘数据：{base_report}"}
        ] + self.conversation_history

    def _update_display(self, content: str):
        """线程安全的显示更新"""
        self.window.after(0, lambda: self.result_text.insert(tk.END, content))
        self.window.after(0, lambda: self.result_text.see(tk.END))
        
    def generate_report(self):
        try:
            birth_time = self.datetime_entry.get_datetime()
            calculator = BaziCalculator(birth_time)
            report = calculator.generate_report()

            self.current_report = report

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "【命盘结构】\n")
            self.result_text.insert(tk.END, f"年柱：{report['sizhu']['year']}\n")
            self.result_text.insert(tk.END, f"月柱：{report['sizhu']['month']}\n")
            self.result_text.insert(tk.END, f"日柱：{report['sizhu']['day']}\n")
            self.result_text.insert(tk.END, f"时柱：{report['sizhu']['hour']}\n\n")
            self.result_text.insert(tk.END, "【五行分布】\n")
            for element, count in report['wuxing'].items():
                self.result_text.insert(tk.END, f"{element}：{'★' * count}\n")
            
        except Exception as e:
            self.current_report = None
            messagebox.showerror("错误", f"排盘失败：{str(e)}")

    def _toggle_stream(self):
        """切换流式输出模式"""
        self.streaming = self.stream_var.get()
        self.status_var.set(f"当前模式：{'流式' if self.streaming else '批量'}输出")

    def analyze_report(self):
        # 获取并验证API密钥
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("警告", "请输入API密钥")
            return
        if not api_key.startswith("sk-"):
            messagebox.showerror("错误", "API密钥格式不正确（必须以sk-开头）")
            return

        # 添加线程状态检测
        if hasattr(self, '_analysis_thread') and self._analysis_thread.is_alive():
            messagebox.showwarning("警告", "已有分析任务在进行中")
            return

        try:
            self._analysis_thread = threading.Thread(
                target=self._perform_analysis,
                daemon=True
            )
            self._analysis_thread.start()
            
        except Exception as e:
            messagebox.showerror("线程错误", f"无法启动分析线程：{str(e)}")

    def _perform_analysis(self):
        try:
            print("\n=== 开始分析流程 ===")
            
            # 验证日期输入
            try:
                birth_time = self.datetime_entry.get_datetime()
                print(f"输入的日期时间：{birth_time} (时区：{birth_time.tzinfo})")
            except Exception as e:
                messagebox.showerror("日期错误", f"日期输入无效：{str(e)}")
                return
                
            # 生成命盘报告
            calculator = BaziCalculator(birth_time)
            report = calculator.generate_report()
            print("生成的命盘报告：", report)
            
            # 调用API分析
            analyzer = BaziAnalyzer(
                api_key=self.api_entry.get().strip(),
                model=self.model_var.get()
            )
            print(f"使用的模型：{analyzer.model}")
            
            # 流式处理
            if self.streaming:
                response_stream = analyzer.analyze(report, stream=True)
                for chunk in response_stream:
                    self.window.after(0, self._update_text, chunk)
            else:
                analysis = analyzer.analyze(report)
                self.window.after(0, self._update_text, analysis)
                
            print("=== 分析完成 ===")
            
        except Exception as e:
            error_msg = f"""
            分析过程中发生错误：
            {str(e)}
            
            可能原因：
            1. API密钥无效或过期
            2. 网络连接问题
            3. 模型服务不可用
            """
            self.window.after(0, lambda: messagebox.showerror("严重错误", error_msg))
            
        finally:
            self.window.after(0, lambda: self.model_menu.config(state="readonly"))

    def _update_text(self, content: str):
        """线程安全的文本更新"""
        self.result_text.insert(tk.END, content)
        self.result_text.see(tk.END)
        self.window.update_idletasks()

if __name__ == "__main__":
    app = BaziApp()
    app.window.mainloop()