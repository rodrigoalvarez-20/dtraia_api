from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uvicorn
import os

### Custom imports

from dtraia_api.routes.users import users_router
from dtraia_api.routes.chat import chat_websocket


app = FastAPI(
    title="DTRAIA API service"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_websocket_route("/chat", chat_websocket)
app.include_router(router=users_router, prefix="/api")

@app.get("/api")
def start_route():
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Ok"
        }
    )


if __name__ == "__main__":
    PORT = os.environ["PORT"] if "PORT" in os.environ else "5000"
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    