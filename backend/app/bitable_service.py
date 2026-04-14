"""
飞书多维表格服务模块
"""
import httpx
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class BitableService:
    """飞书多维表格服务"""
    
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID", "")
        self.app_secret = os.getenv("FEISHU_APP_SECRET", "")
        self._tenant_token = None
        self._base_url = "https://open.feishu.cn/open-apis"
        
        if not self.app_id or not self.app_secret:
            print("警告: 飞书应用凭证未配置，请检查 .env 文件")
    
    async def get_tenant_token(self) -> str:
        """获取租户访问令牌"""
        if self._tenant_token:
            return self._tenant_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                }
            )
            data = response.json()
            
            if data.get("code") != 0:
                error_msg = data.get("msg", "未知错误")
                raise Exception(f"获取token失败: {error_msg}")
            
            self._tenant_token = data.get("tenant_access_token")
            print("获取租户访问令牌成功")
            return self._tenant_token
    
    async def get_table_fields(self, app_token: str, table_id: str) -> Dict[str, str]:
        """获取表格字段列表，返回 {字段名: 字段ID} 映射"""
        token = await self.get_tenant_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                headers={"Authorization": f"Bearer {token}"}
            )
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"获取字段失败: {data.get('msg', '未知错误')}")
            
            field_map = {}
            for field in data.get("data", {}).get("items", []):
                field_map[field["field_name"]] = field["field_id"]
            
            print(f"获取到 {len(field_map)} 个字段: {list(field_map.keys())}")
            return field_map
    
    async def add_record(self, app_token: str, table_id: str, fields_data: Dict[str, Any], field_map: Dict[str, str]) -> Dict:
        """添加单条记录到多维表格"""
        token = await self.get_tenant_token()
        
        # 将字段ID映射回字段名
        id_to_name_map = {v: k for k, v in field_map.items()}
        fields_with_names = {}
        for field_id, value in fields_data.items():
            field_name = id_to_name_map.get(field_id)
            if field_name:
                fields_with_names[field_name] = value
            else:
                print(f"警告: 未找到字段ID '{field_id}' 对应的字段名")
                fields_with_names[field_id] = value
        
        # 使用字段名作为键
        payload = {
            "fields": fields_with_names
        }
        
        print(f"=== 写入请求（使用字段名） ===")
        print(f"payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            data = response.json()
            
            print(f"=== 写入响应 ===")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {data}")
            
            if data.get("code") != 0:
                error_msg = data.get("msg", "未知错误")
                print(f"写入失败: {error_msg}")
                raise Exception(f"添加记录失败: {error_msg}")
            
            record = data.get("data", {}).get("record", {})
            print(f"成功添加记录: {record.get('record_id')}")
            return record
    
    async def add_records_batch(self, app_token: str, table_id: str, records: List[Dict[str, Any]]) -> List[str]:
        """批量添加多条记录到多维表格"""
        token = await self.get_tenant_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "records": [{"fields": r} for r in records]
                }
            )
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"批量添加记录失败: {data.get('msg', '未知错误')}")
            
            record_ids = [r.get("record_id") for r in data.get("data", {}).get("records", [])]
            print(f"成功批量添加 {len(record_ids)} 条记录")
            return record_ids


class InvoiceWriter:
    """发票写入器：将OCR结果映射到飞书多维表格字段"""
    
    def __init__(self, bitable_service: BitableService, app_token: str, table_id: str):
        self.bitable = bitable_service
        self.app_token = app_token
        self.table_id = table_id
        self._field_map = None
    
    async def _ensure_field_map(self):
        """确保字段映射已加载"""
        if self._field_map is None:
            self._field_map = await self.bitable.get_table_fields(self.app_token, self.table_id)
    
    def _format_field_value(self, field_name: str, value: Any) -> Any:
        """根据字段类型格式化值"""
        text_fields = ["文件名", "发票代码", "发票号码", "销售方", "购买方", "销售方税号", "购买方税号"]
        if field_name in text_fields:
            return str(value) if value else ""
        
        if field_name == "发票日期":
            if value:
                return self._date_to_timestamp(value)
            return None
        
        if field_name in ["金额", "税额", "价税合计"]:
            return float(value) if value else 0.0
        
        return value
    
    def _date_to_timestamp(self, date_str: str) -> int:
        """将日期字符串转换为毫秒级时间戳"""
        match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            year, month, day = map(int, match.groups())
            dt = datetime(year, month, day)
            return int(dt.timestamp() * 1000)
        
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = map(int, match.groups())
            dt = datetime(year, month, day)
            return int(dt.timestamp() * 1000)
        
        return None
    
    async def write_invoice(self, invoice: Dict[str, Any]) -> bool:
        """写入单张发票到多维表格"""
        try:
            await self._ensure_field_map()
            
            fields = {}
            mapping = {
                "文件名": invoice.get("file_name", ""),
                "发票代码": invoice.get("invoice_code", ""),
                "发票号码": invoice.get("invoice_number", ""),
                "发票日期": invoice.get("invoice_date", ""),
                "金额": invoice.get("amount", 0),
                "税额": invoice.get("tax_amount", 0),
                "价税合计": invoice.get("total_amount", 0),
                "销售方": invoice.get("seller_name", ""),
                "购买方": invoice.get("buyer_name", ""),
                "销售方税号": invoice.get("seller_tax_id", ""),
                "购买方税号": invoice.get("buyer_tax_id", ""),
            }
            
            for field_name, field_value in mapping.items():
                if field_name in self._field_map:
                    formatted_value = self._format_field_value(field_name, field_value)
                    if formatted_value is not None:
                        fields[self._field_map[field_name]] = formatted_value
            
            if not fields:
                print("警告: 没有可写入的字段数据")
                return False
            
            await self.bitable.add_record(self.app_token, self.table_id, fields, self._field_map)
            return True
            
        except Exception as e:
            print(f"写入发票失败: {e}")
            return False


def parse_app_token_from_url(url: str) -> Optional[str]:
    """从飞书多维表格URL中解析app_token"""
    match = re.search(r'/base/([^/?]+)', url)
    if match:
        return match.group(1)
    return None