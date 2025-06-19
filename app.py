from fastapi import FastAPI, HTTPException
from pytube import YouTube
from pytube.extract import video_id
from pytube.request import create_po_token
import uvicorn

app = FastAPI()

@app.post("/generate-po-token")
async def generate_po_token(data: dict):
    try:
        video_url = data.get("video_url")
        if not video_url:
            raise HTTPException(status_code=400, detail="video_url required")
        
        # Извлекаем ID видео из URL
        vid = video_id(video_url)
        
        # Создаем PoToken
        po_token = create_po_token(vid)
        
        return {"po_token": po_token}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
