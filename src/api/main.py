from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import shutil
import os
from typing import Optional
import json

from ..models.invoice_processor import InvoiceProcessor

app = FastAPI(title="Invoice Recognition API")

# Создаем директорию для временных файлов
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Инициализация процессора счетов
processor = InvoiceProcessor()

@app.post("/process_invoice")
async def process_invoice(
    file: UploadFile = File(...),
    visualize: bool = False,
    ocr_engine: Optional[str] = "easyocr"
):
    """
    Обработка загруженного счета
    
    Args:
        file: файл изображения счета
        visualize: флаг визуализации результатов
        ocr_engine: движок OCR ('easyocr' или 'google')
        
    Returns:
        JSON с результатами распознавания
    """
    try:
        # Сохраняем загруженный файл
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Обрабатываем счет
        results = processor.process_invoice(
            str(file_path),
            visualize=visualize
        )
        
        # Извлекаем структурированные данные
        structured_data = processor.extract_structured_data(results)
        
        # Удаляем временный файл
        os.remove(file_path)
        
        return JSONResponse(content={
            "status": "success",
            "data": structured_data,
            "visualization_path": results.get('visualization_path')
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке счета: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 