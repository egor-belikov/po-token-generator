from fastapi import FastAPI, HTTPException
from pytube import YouTube  # Используем стандартный импорт
import uvicorn

app = FastAPI()

@app.post("/generate-po-token")
async def generate_po_token(data: dict):
    try:
        video_id = data.get("video_id")
        if not video_id:
            raise HTTPException(status_code=400, detail="video_id required")
        
        # Используем встроенный генератор токенов
        po_token = YouTube(f"https://youtube.com/watch?v={video_id}").po_token
        return {"po_token": po_token}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
