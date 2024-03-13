import dotenv
import datetime
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import v1
from mangum import Mangum

dotenv.load_dotenv(".env")

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PREFIX = "/api"

app.include_router(v1.endpoints.router, prefix=PREFIX)


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
start_time = now_hk = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=8)))
start_time = start_time.strftime(DATE_FORMAT)


@app.get(f"{PREFIX}/health_check")
async def health_check():
    response = f"The server is up since {start_time}"
    return {"message": response, "start_hk_time": start_time}


handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
