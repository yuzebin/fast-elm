from fastapi import FastAPI                     # 引入 FastAPI 
from fmdb import connect_to_mongo, close_mongo_connection
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()                                 # app 实例

origins = [
    "http://127.0.0.1:8000",
    "https://127.0.0.1:8000",
    "http://localhost",
    "https://localhost",
    "http://localhost:8000",
    "https://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fmapi import (
    v1router, 
    v2router,
    v3router,
    v4router,
    shoppingrouter,
    ugcrouter,
    payapirouter,
    bosrouter,
    eusrouter,
)

# Add App Event Handler -------------------------------------------------------
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(v1router, prefix='/v1')
app.include_router(v2router, prefix='/v2')
app.include_router(v3router, prefix='/v3')
app.include_router(v4router, prefix='/v4')
app.include_router(shoppingrouter, prefix='/shopping')
app.include_router(ugcrouter, prefix='/ugc')
app.include_router(payapirouter, prefix='/payapi')
app.include_router(bosrouter, prefix='/bos')
app.include_router(eusrouter, prefix='/eus')