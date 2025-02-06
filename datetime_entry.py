import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from datetime import datetime
import pytz
from lunardate import LunarDate

class DateTimeEntry(ttk.Frame):
    """增强版日期时间输入组件"""
    TIMEZONES = [
        ('北京时区', 'Asia/Shanghai'),
        ('香港时区', 'Asia/Hong_Kong'),
        ('台北时区', 'Asia/Taipei'),
        ('日本时区', 'Asia/Tokyo'),
        ('纽约时区', 'America/New_York')
    ]

    def __init__(self, master):
        super().__init__(master)
        self.date_type = tk.StringVar(value='公历')  # 公历/农历
        self.selected_date = None
        self._create_widgets()

    def _create_widgets(self):
        """创建界面组件"""
        # 日期类型选择
        ttk.Label(self, text="日期类型:").grid(row=0, column=0)
        ttk.Radiobutton(self, text="公历", variable=self.date_type, 
                       value='公历', command=self._update_calendar).grid(row=0, column=1)
        ttk.Radiobutton(self, text="农历", variable=self.date_type,
                       value='农历', command=self._update_calendar).grid(row=0, column=2)

        # 日期选择器
        self.cal = Calendar(self, selectmode='day', year=2000, month=1, day=1,
                          date_pattern='y-mm-dd', locale='zh_CN')
        self.cal.grid(row=1, column=0, columnspan=4, pady=5)

        # 时间输入
        ttk.Label(self, text="时间 (HH:MM):").grid(row=2, column=0)
        self.time_entry = ttk.Entry(self, width=8)
        self.time_entry.grid(row=2, column=1)
        self.time_entry.insert(0, "08:00")

        # 时区选择
        ttk.Label(self, text="时区:").grid(row=3, column=0)
        self.tz_combobox = ttk.Combobox(self, values=[tz[0] for tz in self.TIMEZONES])
        self.tz_combobox.current(0)
        self.tz_combobox.grid(row=3, column=1)

        # 日期转换按钮
        ttk.Button(self, text="转换公历/农历", command=self._convert_date).grid(row=4, column=0, columnspan=2)

    def _update_calendar(self):
        """切换日历类型"""
        if self.date_type.get() == '农历':
            self._show_lunar_calendar()
        else:
            self.cal.config(date_pattern='y-mm-dd')

    def _show_lunar_calendar(self):
        """显示农历日历（示例实现）"""
        # 此处需完整实现农历日期显示
        self.cal.config(date_pattern='农历 y 年 m 月 d 日')

    def _convert_date(self):
        """公历农历转换"""
        try:
            if self.date_type.get() == '公历':
                solar_date = self.get_datetime().date()
                lunar_date = LunarDate.fromSolarDate(solar_date.year, solar_date.month, solar_date.day)
                self.date_type.set('农历')
                self.cal.selection_set(lunar_date.toSolarDate())
            else:
                lunar_date = LunarDate.fromSolarDate(*self._parse_date())
                solar_date = lunar_date.toSolarDate()
                self.date_type.set('公历')
                self.cal.selection_set(solar_date)
        except Exception as e:
            tk.messagebox.showerror("转换错误", str(e))

    def get_datetime(self) -> datetime:
        """获取输入的日期时间"""
        try:
            # 解析日期
            year, month, day = map(int, self.cal.get_date().split('-'))
            
            # 处理农历转换
            if self.date_type.get() == '农历':
                lunar_date = LunarDate(year, month, day)
                solar_date = lunar_date.toSolarDate()
                year, month, day = solar_date.year, solar_date.month, solar_date.day

            # 解析时间
            time_str = self.time_entry.get()
            if len(time_str.split(':')) != 2:
                raise ValueError("时间格式应为 HH:MM")
            hour, minute = map(int, time_str.split(':'))
            
            # 输入验证
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError("时间值无效")
            
            # 构建时区感知的datetime对象
            tz_name = dict(self.TIMEZONES)[self.tz_combobox.get()]
            return pytz.timezone(tz_name).localize(
                datetime(year, month, day, hour, minute)
            )
        except Exception as e:
            raise ValueError(f"日期时间输入无效: {str(e)}")

    def set_default_time(self):
        """设置默认时间为当前时间"""
        now = datetime.now(pytz.timezone('Asia/Shanghai'))
        self.cal.selection_set(now.date())
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, now.strftime("%H:%M"))