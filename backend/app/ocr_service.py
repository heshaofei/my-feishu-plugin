"""
百度OCR服务模块
"""
import requests
import os
import re
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class BaiduOCRService:
    """百度OCR服务类"""
    
    def __init__(self):
        self.api_key = os.getenv("BAIDU_API_KEY", "")
        self.secret_key = os.getenv("BAIDU_SECRET_KEY", "")
        self.access_token = None
        
        # 检查密钥是否配置
        if not self.api_key or not self.secret_key:
            print("警告: 百度OCR密钥未配置，请检查 .env 文件")
    
    def get_access_token(self) -> str:
        """获取百度API访问令牌"""
        if self.access_token:
            return self.access_token
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            response = requests.post(url, params=params, timeout=30)
            data = response.json()
            
            if "access_token" in data:
                self.access_token = data["access_token"]
                print("获取Access Token成功")
                return self.access_token
            else:
                error_msg = data.get("error_description", "未知错误")
                raise Exception(f"获取Token失败: {error_msg}")
        except Exception as e:
            raise Exception(f"请求Access Token异常: {str(e)}")
    
    def recognize_vat_invoice(self, image_base64: str) -> Dict[str, Any]:
        """
        识别增值税发票
        """
        access_token = self.get_access_token()
        
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice"
        params = {"access_token": access_token}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"image": image_base64}
        
        try:
            response = requests.post(url, params=params, data=data, headers=headers, timeout=60)
            result = response.json()
            
            # 打印完整响应用于调试
            print(f"百度OCR响应: {json.dumps(result, ensure_ascii=False)[:500]}")
            
            if "error_code" in result:
                error_msg = result.get("error_msg", "未知错误")
                raise Exception(f"OCR识别失败: {error_msg}")
            
            return self._parse_vat_invoice_result(result)
            
        except requests.exceptions.Timeout:
            raise Exception("OCR识别超时，请稍后重试")
        except Exception as e:
            raise Exception(f"调用百度OCR API异常: {str(e)}")
    
    def _parse_vat_invoice_result(self, result: Dict) -> Dict[str, Any]:
        """解析增值税发票识别结果"""
        
        # 百度返回的数据结构: {"words_result": {...}, "log_id": xxx}
        words_result = result.get("words_result", {})
        
        # 如果 words_result 是字符串，尝试解析
        if isinstance(words_result, str):
            try:
                words_result = json.loads(words_result)
            except:
                words_result = {}
        
        # 提取各个字段
        def get_field_value(field_data):
            """安全获取字段值"""
            if isinstance(field_data, dict):
                return field_data.get("words", "")
            return str(field_data) if field_data else ""
        
        invoice_data = {
            "invoice_code": get_field_value(words_result.get("InvoiceCode")),
            "invoice_number": get_field_value(words_result.get("InvoiceNum")),
            "invoice_date": get_field_value(words_result.get("InvoiceDate")),
            "amount": self._parse_amount(get_field_value(words_result.get("Amount"))),
            "tax_amount": self._parse_amount(get_field_value(words_result.get("Tax"))),
            "total_amount": self._parse_amount(get_field_value(words_result.get("AmountInFiguers"))),
            "seller_name": get_field_value(words_result.get("SellerName")),
            "buyer_name": get_field_value(words_result.get("BuyerName")),
            "seller_tax_id": get_field_value(words_result.get("SellerRegisterNum")),
            "buyer_tax_id": get_field_value(words_result.get("BuyerRegisterNum")),
        }
        
        print(f"解析后的发票数据: {invoice_data}")
        return invoice_data
    
    def _parse_amount(self, amount_str: str) -> float:
        """解析金额字符串"""
        if not amount_str:
            return 0.0
        
        # 移除货币符号、逗号和空格
        cleaned = re.sub(r'[^\d.-]', '', str(amount_str))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


# 创建全局实例
ocr_service = BaiduOCRService()