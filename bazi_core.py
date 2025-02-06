from datetime import datetime
import pytz
from dateutil import tz

class BaziCalculator:
    TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    SOLAR_TERMS = {  # 简化版节气数据（需补充完整）
        2023: [("立春", datetime(2023, 2, 4)), ("雨水", datetime(2023, 2, 19))],
        1990: [("立春", datetime(1990, 2, 4))]
    }

    def __init__(self, birth_datetime: datetime, timezone: str = 'Asia/Shanghai'):
        self.birth_time = birth_datetime.astimezone(pytz.timezone(timezone))
        self.timezone = timezone

    def _get_year_ganzhi(self) -> str:
        """计算年柱（考虑立春）"""
        year = self.birth_time.year
        # 检查是否在立春前
        if self.birth_time < self._get_solar_term_date(year, "立春"):
            year -= 1
        return self.TIANGAN[(year - 4) % 10] + self.DIZHI[(year - 4) % 12]

    def _get_month_ganzhi(self) -> str:
        """计算月柱（基于节气）"""
        month_stems = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0, 2, 4]
        year_gan = self.TIANGAN.index(self._get_year_ganzhi()[0])
        month_index = (year_gan % 5) * 2 + (self.birth_time.month + 1) // 2
        return self.TIANGAN[month_stems[month_index % 12]] + self.DIZHI[(self.birth_time.month + 1) % 12]

    def _get_day_ganzhi(self) -> str:
        """计算日柱（基准日法）"""
        base_date = datetime(2020, 12, 27, tzinfo=pytz.utc)  # 基准日：庚子日
        delta = self.birth_time - base_date
        days = delta.days
        ganzhi_index = days % 60
        return self.TIANGAN[ganzhi_index % 10] + self.DIZHI[ganzhi_index % 12]

    def _get_hour_ganzhi(self) -> str:
        """计算时柱"""
        day_gan = self.TIANGAN.index(self._get_day_ganzhi()[0])
        hour = self.birth_time.hour
        zhi_index = (hour + 1) // 2 % 12
        gan_index = (day_gan % 5 * 2 + zhi_index) % 10
        return self.TIANGAN[gan_index] + self.DIZHI[zhi_index]

    def _get_solar_term_date(self, year: int, term: str) -> datetime:
        """获取指定年份节气时间（示例数据）"""
        for t, dt in self.SOLAR_TERMS.get(year, []):
            if t == term:
                return dt.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.timezone))
        return datetime(year, 1, 1, tzinfo=pytz.timezone(self.timezone))

    def get_wuxing_strength(self) -> dict:
        """五行强度计算（简化版）"""
        elements = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        for ganzhi in [self._get_year_ganzhi(), self._get_month_ganzhi(),
                       self._get_day_ganzhi(), self._get_hour_ganzhi()]:
            element = self._get_element(ganzhi)
            elements[element] += 1
        return elements

    def _get_element(self, ganzhi: str) -> str:
        """天干地支对应的五行"""
        element_map = {
            "甲": "木", "乙": "木", "寅": "木", "卯": "木",
            "丙": "火", "丁": "火", "巳": "火", "午": "火",
            "戊": "土", "己": "土", "辰": "土", "戌": "土", "丑": "土", "未": "土",
            "庚": "金", "辛": "金", "申": "金", "酉": "金",
            "壬": "水", "癸": "水", "亥": "水", "子": "水"
        }
        return element_map.get(ganzhi[0], "土")

    def generate_report(self) -> dict:
        return {
            "sizhu": {
                "year": self._get_year_ganzhi(),
                "month": self._get_month_ganzhi(),
                "day": self._get_day_ganzhi(),
                "hour": self._get_hour_ganzhi()
            },
            "wuxing": self.get_wuxing_strength()
        }

if __name__ == "__main__":
    test_time = datetime(1990, 11, 22, 8, 0)
    calculator = BaziCalculator(test_time)
    print(calculator.generate_report())