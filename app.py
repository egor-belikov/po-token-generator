from fastapi import FastAPI, HTTPException
from pytubefix import YouTube
from pytubefix.exceptions import VideoUnavailable
import uvicorn
import logging

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/generate-po-token")
async def generate_po_token(data: dict):
    try:
        video_url = data.get("video_url")
        if not video_url:
            raise HTTPException(status_code=400, detail="video_url required")
        
        logger.info(f"Processing video URL: {video_url}")
        
        # Создаем объект YouTube
        yt = YouTube(video_url)
        
        yt._vid_info = yt.vid_info
        po_token = yt._vid_info.get("playerResponse", {}).get("playabilityStatus", {}).get("poToken", "")
        
        if not po_token:
            # Альтернативный способ получения PoToken
            po_token = get_po_token_from_html(yt.watch_html)
        
        if not po_token:
            raise Exception("PoToken not found in response")
        
        logger.info(f"Generated PoToken for video: {yt.video_id}")
        return {"po_token": po_token}
    
    except Exception as e:
        logger.error(f"Error generating PoToken: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def get_po_token_from_html(html: str) -> str:
    """Альтернативный способ извлечения PoToken из HTML"""
    import re
    import json
    
    # Поиск player_response в HTML
    patterns = [
        r'var ytInitialPlayerResponse\s*=\s*({.*?});',
        r'ytInitialPlayerResponse\s*=\s*({.*?});',
        r'ytInitialPlayerResponse\s*=\s*({.*?})<'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            try:
                player_response = json.loads(match.group(1))
                return player_response.get("playabilityStatus", {}).get("poToken", "")
            except json.JSONDecodeError:
                continue
    
    return ""

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.get("/")
def home():
    return {"message": "PoToken Generator Service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)