# api/app.py
from fastapi import FastAPI
import threading, time
from detector.detector import ParkingDetector

app = FastAPI()
detector = ParkingDetector(cam_idx=1)

@app.on_event("startup")
def start_background_detector():
    def loop():
        while True:
            detector.get_status()
            time.sleep(0.5)                # adjust polling rate as needed
    t = threading.Thread(target=loop, daemon=True)
    t.start()

@app.get("/parking_status")
def parking_status():
    return detector._package()
