from fastapi import FastAPI                     # 引入 FastAPI 
from pydantic import BaseModel                  # 引入 BaseModel

app = FastAPI()

###############################################################################
# Demo Begin                                                                  #
###############################################################################
# 模型定义 --------------------------------------------------------------------
from typing import List                         # 引入 List 类型

class DemoItem(BaseModel):
    name: str
    description: str = None                     # None 表明可以为空
    price: float                                # 不能省略的 float
    tax: float = 10.5                           # 有缺省值的 float
    tags: List[str] = []                        # 缺省为空的列表
# =============================================================================


# 模型定义：自定义类型 --------------------------------------------------------
from pydantic import HttpUrl                    # 引入 HttpUrl 类型

class DemoImage(BaseModel):
    url: HttpUrl                                # HttpUrl 类型
    name: str   
# =============================================================================

# 模型定义：用 Schema 定义数据类型 --------------------------------------------
from pydantic import Schema                     # 引入 Schema

class DemoItemSchema(BaseModel):    
    name: str   
    description: str = Schema(  
        None,                                   # 此值可可以为空
        title="The description of the item",     
        max_length=300                          # 最大长度 300
    )   
    price: float = Schema(  
        ...,                                    # 必须提供此值
        gt=0,                                   # 必须大于等于0
        description="The price must be greater than zero"
    )
    tax: float = None
# =============================================================================


# 模型定义：嵌套定义类型-------------------------------------------------------
from typing import Set                          # 引入 Set 类型

class DemoItemEx(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None
    tags: Set[str] = set()                      # 定义集合
    main_img: DemoImage = None                  # 内嵌 DemoImage
    images: List[DemoImage] = None              # DemoImage 还可以嵌套在 List 里
# =============================================================================


# Default ---------------------------------------------------------------------
@app.get(
    "/", 
    tags=["default"],                           # 定义文档标签
    summary="this is a document demo",          # 定义文档简介
#    description="在这里添加详细的接口描述",        # 定义文档描述，空缺则取函数文档字符串
    response_description="The created item"     # 定义响应描述
)
async def read_root():                          # 函数文档字符串，可替代 description
    """                                         
    - 特性1: xxxxx
        - 子特性1: xxxxx
        - 子特性2: xxxxx
    - 特性2: xxxxx
    \f                                          # 翻页，后面的内容 OpenAPI 不输出
    - 第二页                                        
    """
    return {"Hello": "World"}
# =============================================================================


# Query -----------------------------------------------------------------------
from fastapi import Query                       # 引入 Query

@app.get("/querynone/", tags=["query"])
async def read_items(q: str = None):            # 定义 ? 后的 Query 参数
    results = {"items": [
        {"item_id": "Foo"}, 
        {"item_id": "Bar"}
    ]}
    if q:
        results.update({"q": q})
    return results


@app.get("/queryregex/", tags=["query"])
async def read_items(
    q: str = Query(                             # 定义 ? 后的 Query 参数
        ...,                                    # ... 表示必须提供此值
        min_length=3,                           # 最短 3 个字符
        max_length=50,                          # 最长 50 个字符
        regex="^fix"                            # 满足匹配正则：^fix
    )   
):  
    results = {"items": [   
        {"item_id": "Foo"},     
        {"item_id": "Bar"}  
    ]}  
    if q:   
        results.update({"q": q})    
    return results  


@app.get("/querylist/", tags=["query"]) 
async def read_items(   
    q: List[int] = Query(None)                  # List 其值为 int
):  
    results = {"items": [   
        {"item_id": "Foo"},     
        {"item_id": "Bar"}  
    ]}  
    if q:   
        results.update({"q": q})    
    return results  

from typing import Optional                     # 引入 Optional


@app.get("/queryliststr/", tags=["query"])  
async def read_items(   
    q: List[str] = Query(None),                 # List 其值为 str
    limit: Optional[int] = None                 # 解决 Incompatible types 问题
):
    results = {"items": [
        {"item_id": "Foo"}, 
        {"item_id": "Bar"}
    ]}
    if q:
        results.update({"q": q})
    return results


@app.get("/querydeprecated/", tags=["query"])
async def read_items(
    q: str = Query(                             # 定义 ? 后的 Query 参数
        None,                                   # 可以空缺
        title="Query string",                   # 文档标题
        alias="i-query",                        # 请求参数别名，在 url 里的样子
        deprecated=True                         # deprecated 表示不再推荐使用
    )
):
    results = {"items": [
        {"item_id": "Foo"}, 
        {"item_id": "Bar"}
    ]}
    if q:
        results.update({"q": q})
    return results
# =============================================================================


# Path ------------------------------------------------------------------------
from fastapi import Path                        # 引入 Path

@app.get('/path/{item_id}', tags=["path"])      # 引入 Path 参数
async def read_item(
    item_id: int = Path(..., title="item_id"),  # 定义 Path 参数
    q: str = None                               # 定义 ？ 后的 Query 参数
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


@app.get('/pathgele/{item_id}', tags=["path"])  # 引入 Path 参数
async def read_item(
    *,                                          # 多个参数
    item_id: int = Path(                        # 定义 Path 参数 int 型
        ...,                                        # 必须提供
        title="item_id",                            # 文档标题
        ge=1,                                       # 大于等于 1
        le=1000                                     # 小于等于 1000
    ), 
    q: str                                      # 定义 Query 参数
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


@app.post("/item/", tags=["path"])
async def create_item(
    item: DemoItem                              # FastAPI 自动将数据模型参数识别为 Body 参数
):
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
        return item_dict
# =============================================================================


# Schhema ---------------------------------------------------------------------
from fastapi import Body                        # 引入 Body 参数

@app.put("/schemaitem/{item_id}", tags=["schema"])
async def update_item(
    *,                                          # 多个参数
    item_id: int,                               # 定义 Query 参数
    item: DemoItem = Body(                      # 定义 Body 参数
        ...,                                    # 必须提供
        embed=True                              # 单个 Body 参数时，用 embed 参数外边包一层{}
    )
):
    results = {"item_id": item_id, "item": item}
    return results
# =============================================================================


# Body ------------------------------------------------------------------------
class User(BaseModel):
    username: str
    full_name: str = None

@app.put("/bodymulti/{item_id}", tags=["body"])
async def update_item(
    *,                                          # 多个参数
    item_id: int,                               # Path 参数
    item: DemoItem,                             # Body 参数
    user: User                                  # Body 参数
):
    results = {"item_id": item_id, "item": item, "user": user}
    return results


@app.put("/bodymore/{item_id}", tags=["body"])
async def update_item(
    *,                                          # 多个参数
    item_id: int,                               # Path 参数
    item: DemoItem,                             # Body 参数
    user: User,                                 # Body 参数
    importance: int = Body(...)                 # Body 参数，不指定 Body 则成为 Query 参数
):
    results = {
        "item_id": item_id, 
        "item": item, 
        "user": user, 
        "importance": importance
    }
    return results


@app.put("/bodyquery/{item_id}", tags=["body"])
async def update_item(
    *,                                          # 多个参数
    item_id: int,                               # Path 参数
    item: DemoItem,                             # Body 参数
    user: User,                                 # Body 参数
    importance: int = Body(..., gt=0),          # Body 参数
    q: str = None                               # Query 参数
):
    results = {
        "item_id": item_id, 
        "item": item, 
        "user": user, 
        "importance": importance
    }
    if q:
        results.update({"q": q})
    return results


@app.put("/bodysingle/{item_id}", tags=["body"])
async def update_item(
    *, 
    item_id: int, 
    item: DemoItem = Body(..., embed=True)      # 单个 Body 参数时，用 embed 参数外边包一层{}
):
    results = {"item_id": item_id, "item": item}
    return results


@app.put("/bodyset/{item_id}", tags=["body"])
async def update_item(
    *, 
    item_id: int, 
    item: Set[DemoItem]                         # 定义 DemoItem 集合
):
    results = {"item_id": item_id, "item": item}
    return results


@app.put("/bodymoreparam/{item_id}", tags=["body"])
async def update_item(
    *,
    item_id: int,
    item: DemoItem = Body(
        ...,
        example={                               # example 将原样出现在文档中
            "name": "Foo", 
            "description": "A very nice Item", 
            "price": 35.4, 
            "tax": 3.2, 
        },    
    )
):
    results = {"item_id": item_id, "item": item}
    return results
# =============================================================================


# More Type --------------------------------------------------------------
from typing import Dict                         # 引入 Dict 类型

@app.put(
    "/itemquery/{item_id}", 
    tags=["more type"], 
    include_in_schema=False                     # 表明此接口将排除在文档外
)
async def update_item(
    item_id: int,
    item: DemoItem,
    q: str = None
):
    result = {"item_id": item_id, **item.dict()}
    if q:
        result.update({"q": q})
    return result


@app.post("/imagelist/", tags=["more type"])
async def create_multiple_images(
    *, 
    images: List[DemoImage]
):
    return images


@app.post("/anydict/", tags=["more type"])
async def create_index_weights(
    weights: Dict[int, float]                   # 自定义 Dict, key 为 int, value 为 float
):
    return weights
# =============================================================================


# UUID, datetime --------------------------------------------------------------
from uuid import UUID                           # 引入 UUID 类型

from datetime import datetime                   # 引入日期时间类型
from datetime import time                       # 引入时间类型
from datetime import timedelta                  # 引入时间间隔类型

@app.put("/typemore/{item_id}", tags=["more type"])
async def read_items(
    item_id: UUID = Path(
        ..., 
        example="a6eb7fe8-5acd-11ea-8e2d-0242ac130003" # UUID 缺省值
    ),
    start_datetime: datetime = Body(None),      # 开始日期时间
    end_datetime: datetime = Body(None),        # 结束日期时间
    repeat_at: time = Body(None),               # 重复时间
    process_after: timedelta = Body(None)       # 时间间隔
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process

    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "repeat_at": repeat_at,
        "process_after": process_after,
        "start_process": start_process,
        "duration": duration,
    }
# =============================================================================


# Cookie ----------------------------------------------------------------------
from fastapi import Cookie                      # 引入 Cookie

@app.get("/cookies/", tags=["cookie"])
async def cookies(*, 
    ads_id: str = Cookie(None)                  # 读取 Cookie
):
    return {"ads_id": ads_id}
# =============================================================================


# Header ----------------------------------------------------------------------
from fastapi import Header                      # 引入 Header
from starlette.requests import Request

@app.get("/headers/", tags=["header"])
async def read_items(
    *, 
    user_agent: str = Header(None),             # 读取 Header
    request: Request,
):
    ip = request.client.host
    return {"User-Agent": user_agent, "ip": ip}


@app.get("/headersrepeat/", tags=["header"])
async def read_items(
    x_token: List[str] = Header(None)           # 读取有重复值的 Header
):
    return {"X-Token values": x_token}
# =============================================================================


# Response Model --------------------------------------------------------------
@app.post("/responsemodel/", response_model=DemoItem, tags=["response model"]) 
async def create_item(item: DemoItem):
    return item                                 # 响应直接转 JSON 输出
# =============================================================================


# Response Model --------------------------------------------------------------
items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {
        "name": "Bar", 
        "description": "The bartenders", 
        "price": 62, 
        "tax": 20.2
    },
    "baz": {
        "name": "Baz", 
        "description": None, 
        "price": 50.2, 
        "tax": 10.5, 
        "tags": []
    },
}

@app.get(
    "/responsemodelskipdefaults/{item_id}", 
    response_model=DemoItem,                    # 响应模型
    response_model_skip_defaults=True,          # 跳过默认值
    tags=["response model"]
)
async def read_item(item_id: str):
    return items[item_id]
# =============================================================================


# Response Model --------------------------------------------------------------
items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {
        "name": "Bar", 
        "description": "The Bar fighters", 
        "price": 62, 
        "tax": 20.2
    },
    "baz": {
        "name": "Baz",
        "description": "There goes my baz",
        "price": 50.2,
        "tax": 10.5,
    },
}

@app.get(
    "/responsemodelinclude/{item_id}/name", 
    response_model=DemoItem, 
    response_model_include={                    # 输出包含字段
        "name", 
        "description"
    }, 
    tags=["response model"]
)
async def read_item_name(item_id: str):
    return items[item_id]

@app.get(
    "/responsemodelexclude/{item_id}/public", 
    response_model=DemoItem, 
    response_model_exclude={"tax"},              # 输出排除字段
    tags=["response model"]
)
async def read_item_public_data(item_id: str):
    return items[item_id]
# =============================================================================


# DemoUser ------------------------------------------------------------------------
from pydantic import EmailStr                   # 引入 EmailStr 类型

class DemoUserBase(BaseModel):                      # 定义数据模型：基础 DemoUser 
    username: str
    email: EmailStr
    full_name: str = None

class DemoUserIn(DemoUserBase):                         # 定义数据模型：DemoUserIn 增加 password
    password: str

class DemoUserOut(BaseModel):                       # 定义数据模型：DemoUserOut 不添加
    pass

class DemoUserInDB(BaseModel):                      # 定义数据模型：DemoUserInDB 只保存 Hash 过的密码
    hashed_password: str

# 不要在生产环境中输出用户密码
@app.post(
    "/userinout/", 
    response_model=DemoUserOut,                     # 输出 DemoUserOut
    tags=["user"]
)
async def create_demo_user(
    *, 
    user: DemoUserIn                                # 输入 DemoUserIn
):
    return user

def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password

def fake_save_user(user_in: DemoUserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = DemoUserInDB(
        **user_in.dict(),                       # ** 用于将 dict 解包，dict() 将模型中的数据转化为 dict
        hashed_password=hashed_password,        # 添加额外参数：Hash 后的密码
        tags=["user"]
    )    
    print("User saved! ..not really")
    return user_in_db

@app.post("/userindb/", response_model=DemoUserOut, tags=["user"])
async def create_demo_user(*, user_in: DemoUserIn):
    user_saved = fake_save_user(user_in)
    return user_saved
# =============================================================================


# Extra Model : Union ---------------------------------------------------------
from typing import Union                        # 引入 Union 类型

class DemoItemBase(BaseModel):
    description: str
    type: str

class DemoItemCar(DemoItemBase):
    type = "car" 

class DemoItemPlane(DemoItemBase):
    type = "plane"
    size: int 

items = {
    "item1": {
        "description": "All my friends drive a low rider", 
        "type": "car"
    },
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}

@app.get(
    "/extramodelunion/{item_id}", 
    response_model=Union[                       # 定义返回数据类型，为以下的 Union
        DemoItemPlane,                              # 或者 DemoItemPlan
        DemoItemCar                                 # 或者 DemoItemCar
    ],                                          # 注意 Union 的两者字段可以不一致
    tags=["extramodel"]
)
async def read_item(item_id: str):
    return items[item_id]
# =============================================================================


# Extra Model : List ----------------------------------------------------------
items = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It's my aeroplane"},
]

@app.get(
    "/extramodellist/", 
    response_model=List[DemoItem],              # 定义返回的是 List
    tags=["extramodel"]
) 
async def read_items():
    return items
# =============================================================================


# Extra Model : Dict ----------------------------------------------------------
@app.get(
    "/extramodeldict/", 
    response_model=Dict[str, float],            # 定义返回的是 Dict
    tags=["extramodel"]
)
async def read_keyword_weights():
    return {"foo": 2.3, "bar": 3.4}
# =============================================================================


# Response Status Code --------------------------------------------------------
from starlette.status import HTTP_201_CREATED   # 引入 HTTP 状态码，不用费力记忆

@app.post(
    "/items/", 
    status_code=HTTP_201_CREATED,               # 定义接口状态码
    tags=["response"]
)
async def create_item(name: str):
    return {"name": name}
# =============================================================================


# Form ------------------------------------------------------------------------
from fastapi import Form                        # 引入 Form 表单

@app.post("/form/", tags=["form"])
async def login(*,
    username: str = Form(...),                  # 定义 Fomr 参数
    password: str = Form(...)                   # 定义 Fomr 参数
):
    return {"username": username}
# =============================================================================


# File ------------------------------------------------------------------------
from fastapi import File                        # 引入 File 上传的文件字节序列
from fastapi import UploadFile                  # 引入 UploadFile 上传的文件对象


@app.post("/fileone/", tags=["file"])
async def create_file(
    file: bytes = File(...)                     # 定义 File 上传的文件字节序列
):
    return {"file_size": len(file)}

@app.post("/uploadfileone/", tags=["file"])
async def create_upload_file(
    file: UploadFile = File(...)                # 定义 UploadFile 上传的文件对象
):
    contents = await file.read()                # 异步读取文件
    return {
        "filename": file.filename,              # 获取文件名
        "content_type": file.content_type,      # 获取文件 MIME 类型
        "file_len": len(contents)               # 获取文件长度
    }
# =============================================================================


# Files -----------------------------------------------------------------------
from starlette.responses import HTMLResponse    # 引入 HTMLResponse

@app.post("/files/", tags=["file"])
async def create_files(
    files: List[bytes] = File(...)              # 定义多文件上传的文件字节序列的 List
):
    return {"file_sizes": [len(file) for file in files]}

@app.post("/uploadfiles/", tags=["file"])
async def create_upload_files(
    files: List[UploadFile] = File(...)         # 定义多文件上传的文件对象的 List
):
    return {"filenames": [file.filename for file in files]}

@app.get("/files/", tags=["file"])              # 返回多文件上传的 Form 框
async def main():
    content = """
<body>
Files：<form action="/files/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
UploadFiles：<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
 """
    return HTMLResponse(content=content)
# =============================================================================


# File & Form -----------------------------------------------------------------
@app.post("/fileform/", tags=["file"])
async def create_file(
    file: bytes = File(...), 
    fileb: UploadFile = File(...), 
    token: str = Form(...) 
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }
# =============================================================================


# HTTPException ---------------------------------------------------------------
from fastapi import HTTPException               # 引入 HTTPException

items = {"foo": "The Foo Wrestlers"}

@app.get("/httpexception/{item_id}", tags=["exception"])
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(                    # raise 一个 HTTPException
            status_code=404,                    # Status Code 设为 404
            detail="Item not found"             # 详细信息
        )
    return {"item": items[item_id]}
# =============================================================================


# add headers -----------------------------------------------------------------
items = {"foo": "The Foo Wrestlers"}

@app.get("/addheader/{item_id}", tags=["exception"])
async def read_item_header(item_id: str):
    if item_id not in items:
        raise HTTPException(                    # raise 一个 HTTPException
            status_code=404,                    # Status Code 设为 404
            detail="Item not found",            # 详细信息
            headers={"X-Error": "There goes my error"}, # 添加新的 Header
        )
    return {"item": items[item_id]}
# =============================================================================


# custom exception ------------------------------------------------------------
from starlette.requests import Request          # 引入 Request
from starlette.responses import JSONResponse    # 引入 JSONResponse

class UnicornException(Exception):              # 自定义异常
    def __init__(self, name: str): 
        self.name = name 

@app.exception_handler(UnicornException)        # 自定义异常的统一处理方法
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,                        # 自定义 Status Code
        content={                               # 自定义详细信息
            "message": 
            f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

@app.get("/customexception/{name}", tags=["exception"])
async def read_unicorn(name: str):
    if name == "yolo": 
        raise UnicornException(name=name)       # raise 自定义异常
    return {"unicorn_name": name}
# =============================================================================


# override exception ------------------------------------------------------------
from fastapi.exceptions import RequestValidationError 
from starlette.exceptions import HTTPException as StarletteHTTPException # 改名防止与 FastAPI 的异常冲突
from starlette.responses import PlainTextResponse

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400) 

@app.get("/overrideexception/{item_id}", tags=["exception"])
async def read_item(item_id: int):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.") # 覆盖默认的异常
    return {"item_id": item_id}
# =============================================================================


# override status code ------------------------------------------------------------
from starlette.status import HTTP_201_CREATED   # 引入 201 状态码

items = {
    "foo": {"name": "Fighters", "size": 6}, 
    "bar": {"name": "Tenders", "size": 3}
}

@app.put("/overridestatuscode/{item_id}", tags=["response"])
async def upsert_item(
    item_id: str,
    name: str = Body(None),
    size: int = Body(None)
):
    if item_id in items:
        item = items[item_id]
        item["name"] = name
        item["size"] = size
        return item
    else:
        item = {"name": name, "size": size}
        items[item_id] = item
    return JSONResponse(
        status_code=HTTP_201_CREATED,           # 输出时覆盖默认状态码
        content=item
    ) 
# =============================================================================


# jsonable_encoder ------------------------------------------------------------
from fastapi.encoders import jsonable_encoder

fake_db = {}                                    # fake_db 是某个只能接收 JSON 兼容数据类型的对象

class DemoItemDB(BaseModel):
    title: str
    timestamp: datetime
    description: str = None


@app.put("/jsonable_encoder/{id}", tags=["db"])
def update_item(id: str, item: DemoItemDB):
    json_compatible_item_data = jsonable_encoder(item)  # 将数据模型 jsonable_encoder 为普通 JSON
    fake_db[id] = json_compatible_item_data             # 这个普通 JSON 在 Python 内其实是 dict
# =============================================================================

###############################################################################
# Demo End                                                                    #
###############################################################################
