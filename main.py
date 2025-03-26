from fastapi import FastAPI
from typing import Optional

# import uvicorn

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/greet")
async def greet1(name: str) -> dict:
    return {"Hello": name}


@app.get("/greet1")
async def greet2(name: Optional[str] = "User", age: int = 0) -> dict:
    return {"Hello": name, "Age": age}


#      ZA DOCKER
# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         log_level="info",
#         loop="uvloop",
#     )
