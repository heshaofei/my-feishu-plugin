@app.post("/test-ocr")
async def test_ocr(file: UploadFile = File(...)):
    """测试OCR识别接口"""
    try:
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
        ocr_result = ocr_service.recognize_vat_invoice(image_base64)
        
        # 4. 清理临时文件
        os.unlink(save_path)
        
        return {
            "success": True,
            "file_name": file.filename,
            "ocr_result": ocr_result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }