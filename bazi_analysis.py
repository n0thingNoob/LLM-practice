from openai import OpenAI
from openai import APIConnectionError, APIError, RateLimitError
import json

class BaziAnalyzer:
    SUPPORTED_MODELS = [
        "deepseek-ai/DeepSeek-V2.5",  # 最新旗舰模型
        "deepseek-ai/DeepSeek-V2",    # 上一代版本
        "deepseek-chat",              # 通用对话模型
        "deepseek-math",             # 数学专用模型
        "deepseek-ai/DeepSeek-R1"     # 推理模型
    ]
     
    def __init__(self, api_key: str, model: str = "deepseek-ai/DeepSeek-R1"):
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"  # 指定SiliconFlow接口地址
        )
        self.model = model

    def _build_messages(self, report: dict) -> list:
        return [{
            "role": "system",
            "content": "你是一位精通中国传统命理学的专家，擅长解读八字命盘。"
        }, {
            "role": "user",
            "content": f"""请基于以下命盘信息进行分析：
            {json.dumps(report, indent=2, ensure_ascii=False)}

            请按以下要求用中文回答：
            1. 用比喻手法描述命局特点（不超过200字）
            2. 五行平衡分析（含补救建议）
            3. 职业发展建议（结合现代行业）
            4. 健康注意事项
            5. 使用✅表示优势，⚠️表示需要注意
            6. 可以添加其他命理建议比如财运、婚姻等

            要求：
            - 避免专业术语堆砌
            - 分点说明用🔹符号
            - 重要结论前添加表情符号"""
                    }]

    def analyze(self, report: dict, stream: bool = False) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._build_messages(report),
                temperature=0.3,  # 降低随机性
                top_p=0.9,
                max_tokens=1000,
                stream=stream     # 支持流式输出
            )
            
            if stream:
                return self._handle_stream_response(response)
            else:
                return response.choices[0].message.content

        except APIConnectionError as e:
            return f"连接失败：{e.__cause__}"
        except RateLimitError:
            return "请求过于频繁，请稍后重试"
        except APIError as e:
            return f"API错误（{e.status_code}）：{e.message}"
        except Exception as e:
            return f"未知错误：{str(e)}"

    def _handle_stream_response(self, response):
        """处理流式响应"""
        full_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                full_content += chunk.choices[0].delta.content
        return full_content