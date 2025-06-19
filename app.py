from fastapi import FastAPI, HTTPException
from pytubefix import YouTube
from pytubefix.extract import video_id
import uvicorn

app = FastAPI()

@app.post("/generate-po-token")
async def generate_po_token(data: dict):
    try:
        video_url = data.get("video_url")
        if not video_url:
            raise HTTPException(status_code=400, detail="video_url required")
        
        # Извлекаем ID видео
        vid = video_id(video_url)
        if not vid:
            raise ValueError("Invalid YouTube URL")
        
        # Создаем объект YouTube
        yt = YouTube(f"https://www.youtube.com/watch?v={vid}")
        
        # Инициируем запрос данных видео
        yt.bypass_age_gate()
        
        # Извлекаем PoToken из ответа
        player_response = yt._vid_info.get("playerResponse", {})
        playability_status = player_response.get("playabilityStatus", {})
        po_token = playability_status.get("poToken", "")
        
        if not po_token:
            raise Exception("PoToken not found in response")
        
        return {"po_token": po_token}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.get("/")
def home():
    return {"message": "PoToken Generator Service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)