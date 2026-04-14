import os
import uuid
import base64
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from .ocr_service import ocr_service
from .bitable_service import BitableService, InvoiceWriter, parse_app_token_from_url

app = FastAPI(title="发票识别服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

# 初始化飞书服务
bitable_service = BitableService()


@app.get("/health")
async def health():
    return {"status": "ok", "message": "服务器运行正常"}


@app.post("/test-ocr")
async def test_ocr(file: UploadFile = File(...)):
    """测试OCR识别接口"""
    try:
        # 保存文件
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        save_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)
        
        # 读取图片并转Base64
        with open(save_path, "rb") as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # 调用百度OCR
        ocr_result = ocr_service.recognize_vat_invoice(image_base64)
        
        # 清理临时文件
        os.unlink(save_path)
        
        return {
            "success": True,
            "file_name": file.filename,
            "ocr_result": ocr_result
        }
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

#测试接口
@app.post("/test-write")
async def test_write(
    app_token: str = Form(...),
    table_id: str = Form(...)
):
    """测试飞书写入功能"""
    try:
        # 准备测试数据 - 使用字段名
        test_fields = {
            "文件名": "测试文件.jpg",
            "发票代码": "TEST12345678",
            "价税合计": 100.00
        }
        
        # 获取字段映射（字段名 -> 字段ID）
        fields = await bitable_service.get_table_fields(app_token, table_id)
        print(f"表格字段: {fields}")
        
        # 构建写入数据（将字段名转换为字段ID）
        write_data = {}
        for field_name, field_value in test_fields.items():
            if field_name in fields:
                write_data[fields[field_name]] = field_value
                print(f"匹配字段: {field_name} -> {field_value}")
            else:
                print(f"未匹配字段: {field_name} (表格中不存在)")
        
        if not write_data:
            return {
                "success": False,
                "error": "没有匹配的字段，请检查表格字段名",
                "available_fields": list(fields.keys()),
                "test_fields": list(test_fields.keys())
            }
        
        # ✅ 修改这里：添加 fields 参数作为 field_map
        result = await bitable_service.add_record(app_token, table_id, write_data, fields)
        
        return {
            "success": True,
            "message": "测试写入成功",
            "result": result
        }
        
    except Exception as e:
        print(f"测试写入失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
@app.post("/process")
async def process_files(
    files: list[UploadFile] = File(...),
    app_token: str = Form(...),
    table_id: str = Form(...)
):
    """
    批量处理发票：OCR识别 + 写入飞书多维表格
    """
    results = []
    success_count = 0
    fail_count = 0
    
    print(f"收到请求 - app_token: {app_token}, table_id: {table_id}")
    
    # 初始化写入器
    writer = InvoiceWriter(bitable_service, app_token, table_id)
    
    # 处理每个文件
    for idx, file in enumerate(files):
        result_item = {
            "file_name": file.filename,
            "status": "processing"
        }
        
        try:
            print(f"处理文件: {file.filename}")
            
            # 1. 保存文件
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix
            save_path = UPLOAD_DIR / f"{file_id}{file_ext}"
            
            content = await file.read()
            with open(save_path, "wb") as f:
                f.write(content)
            
            # 2. 读取图片并转Base64
            with open(save_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            # 3. 调用百度OCR
            print("调用百度OCR...")
            ocr_result = ocr_service.recognize_vat_invoice(image_base64)
            print(f"OCR结果: {ocr_result}")
            
            # 4. 准备写入数据
            invoice_data = {
                "file_name": file.filename,
                "status": "success",
                **ocr_result
            }
            
            # 5. 写入飞书多维表格
            print("写入多维表格...")
            write_success = await writer.write_invoice(invoice_data)
            
            if write_success:
                result_item["status"] = "success"
                result_item.update(ocr_result)
                success_count += 1
                print(f"成功处理: {file.filename}")
            else:
                result_item["status"] = "error"
                result_item["error_msg"] = "写入表格失败"
                fail_count += 1
            
            # 6. 清理临时文件
            os.unlink(save_path)
            
        except Exception as e:
            print(f"处理失败 {file.filename}: {e}")
            import traceback
            traceback.print_exc()
            result_item["status"] = "error"
            result_item["error_msg"] = str(e)
            fail_count += 1
        
        results.append(result_item)
    
    return {
        "success": fail_count == 0,
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results
    }
@app.get("/files")
async def list_files():
    """列出所有上传的文件"""
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "size": stat.st_size,
                "created": stat.st_ctime
            })
    return {"files": files}


@app.delete("/cleanup")
async def cleanup():
    """清理所有临时文件"""
    import shutil
    shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(exist_ok=True)
    return {"message": "清理完成"}