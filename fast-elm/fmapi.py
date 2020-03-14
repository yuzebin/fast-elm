from datetime import timedelta
from typing import Optional, List

from fastapi import Body
from fastapi import Path
from fastapi import Query
from fastapi import Cookie 
from fastapi import Header
from fastapi import Depends
from fastapi import APIRouter
from fastapi import HTTPException

from slugify import slugify
from pydantic import BaseModel
from starlette.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient

from fmdb import get_database

from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fmtoken import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user_authorizer,
)

from fmmodel import (
    RWUser,
    RWUserInLogin,
    RWUserInCreate,
    RWUserInResponse,
    ArticleInCreate,
    ArticleInResponse,
    ArticleFilterParams,
    ManyArticlesInResponse,
    CitiesModel,
    CategoryModel,
    ShopModel,
    DeliveriesModel,
    ActivitiesModel,
    MenusModel,
)

from fmcrud import (
    check_free_username_and_email,
    get_article_by_slug,
    create_article_by_slug,
    get_user_by_email,
    create_user,
    get_articles_with_filters,
    get_cities_by_key,
    get_cities_by_id,
    get_pois_by_ip,
    get_pois_by_latlng,
    get_index_entry,
    get_userinfos,
    get_categories,
    get_restaurants,
    get_deliveries,
    get_activities,
    get_restaurant_detail,
    get_menus,
    get_restaurant_ratings,
    get_restaurant_ratings_scores,
    get_restaurant_ratings_tags,
)

v1router = APIRouter()
v2router = APIRouter()
v3router = APIRouter()
v4router = APIRouter()
shoppingrouter = APIRouter()
ugcrouter = APIRouter()
payapirouter = APIRouter()
bosrouter = APIRouter()
eusrouter = APIRouter()

def create_aliased_response(model: BaseModel) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(model, by_alias=True))


# -----------------------------------------------------------------------------
# users
@v1router.post(
    "/users/login", 
    response_model=RWUserInResponse, 
    tags=["authentication"]
)
async def login(
        user: RWUserInLogin = Body(..., embed=False), 
        cap: str = Cookie(...),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if not cap:
        return {"status":0, "type": "ERROR_CAPTCHA", "message": "验证码失效"}

    if user.vcode != cap:
        return {"status":0, "type": "ERROR_CAPTCHA", "message": "验证码不正确"}

    dbuser = await get_user_by_email(db, user.email)
    if not dbuser:
        # create user
        # const user_id = await this.getId('user_id');
        # const cityInfo = await this.guessPosition(req);
        # const registe_time = dtime().format('YYYY-MM-DD HH:mm');
        # const newUser = {username, password: newpassword, user_id};
        # const newUserInfo = {username, user_id, id: user_id, city: cityInfo.city, registe_time, };
        # UserModel.create(newUser);
        # const createUser = new UserInfoModel(newUserInfo);
        # const userinfo = await createUser.save();
        # req.session.user_id = user_id;
        # res.send(userinfo);
        async with await db.start_session() as s:
            async with s.start_transaction():
                dbuser = await create_user(db, user)
                access_token_expires = timedelta(
                    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
                )
                token = create_access_token(
                    data={"username": dbuser.username}, 
                    expires_delta=access_token_expires
                )

            return RWUserInResponse(user=RWUser(**dbuser.dict(), token=token))
        pass
    else:
        if not dbuser.check_password(user.password):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, 
                detail="Incorrect email or password"
            )
        else:
            # login ok
            # req.session.user_id = user.user_id;
            # const userinfo = await UserInfoModel.findOne({user_id: user.user_id}, '-_id');
            # res.send(userinfo) 
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            token = create_access_token(
                data={"username": dbuser.username}, expires_delta=access_token_expires
            )
            return RWUserInResponse(user=RWUser(**dbuser.dict(), token=token))


@v1router.post(
    "/users",
    response_model=RWUserInResponse,
    tags=["authentication"],
    status_code=HTTP_201_CREATED,
)
async def register(
        user: RWUserInCreate = Body(..., embed=True), 
        db: AsyncIOMotorClient = Depends(get_database)
):
    await check_free_username_and_email(db, user.username, user.email)

    async with await db.start_session() as s:
        async with s.start_transaction():
            dbuser = await create_user(db, user)
            access_token_expires = timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
            token = create_access_token(
                data={"username": dbuser.username}, 
                expires_delta=access_token_expires
            )

            return RWUserInResponse(user=RWUser(**dbuser.dict(), token=token))
# =============================================================================


# -----------------------------------------------------------------------------
# artiicles
@v1router.get(
    "/articles", 
    response_model=ManyArticlesInResponse, 
    tags=["articles"]
)
async def get_articles(
    tag: str = "",
    author: str = "",
    favorited: str = "",
    limit: int = Query(20, gt=0),
    offset: int = Query(0, ge=0),
    user: RWUser = Depends(get_current_user_authorizer(required=False)),
    db: AsyncIOMotorClient = Depends(get_database),
):
    filters = ArticleFilterParams(
        tag=tag, author=author, favorited=favorited, limit=limit, offset=offset
    )
    dbarticles = await get_articles_with_filters(
        db, filters, user.username if user else None
    )
    return create_aliased_response(
        ManyArticlesInResponse(
            articles=dbarticles,
            articles_count=len(dbarticles)
        )
    )


@v1router.post(
    "/articles",
    response_model=ArticleInResponse,
    tags=["articles"],
    status_code=HTTP_201_CREATED,
)
async def create_new_article(
        article: ArticleInCreate = Body(..., embed=True),
        user: RWUser = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    article_by_slug = await get_article_by_slug(
        db, slugify(article.title), user.username
    )
    if article_by_slug:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"文章已存在 slug='{article_by_slug.slug}'",
        )

    dbarticle = await create_article_by_slug(db, article, user.username)
    return create_aliased_response(ArticleInResponse(article=dbarticle))
# =============================================================================


# -----------------------------------------------------------------------------
# cities
@v1router.get(
    "/cities/", 
#    response_model=CitiesModel, 
    tags=["cities"]
)
async def get_cities(
    type: str = "",
    db: AsyncIOMotorClient = Depends(get_database),
):
    cities = await get_cities_by_key(db, type)
    return cities


@v1router.get(
    "/cities/{id}", 
#    response_model=CitiesModel, 
    tags=["cities"]
)
async def get_cities(
    id: int = "",
    db: AsyncIOMotorClient = Depends(get_database),
):
    cities = await get_cities_by_id(db, id)
    return cities
# =============================================================================


# ----------------------------------------------------------------------------- 
# pois
from starlette.requests import Request

@v1router.get(
    "/pois/",
    tags=["pois"],
)
async def getpois(
    *,
    request: Request,
    type: str = None,
    city_id: int = None,
    keyword: str = None,
    db: AsyncIOMotorClient = Depends(get_database),
):
    ip = await get_client_ip(request)

    results = await get_pois_by_ip(db, type, city_id, keyword, ip)
    return results

async def get_client_ip(request: Request):
    x_forwarded_for = request.client.host
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@v2router.get(
    "/pois/{location}",
    tags=["pois"],
)
async def getpois(
    location: str = Path(..., regex=".*,.*")
):
    results = await get_pois_by_latlng(location)
    return results

@v2router.get(
    "/pois/",
    tags=["pois"],
)
async def getpois(
    *,
    request: Request,
    type: str = None,
    city_id: int = None,
    keyword: str = None,
    db: AsyncIOMotorClient = Depends(get_database),
):
    ip = await get_client_ip(request)

    results = await get_pois_by_ip(db, type, city_id, keyword, ip)
    return results
# =============================================================================


# -----------------------------------------------------------------------------
# 
@v2router.get(
    "/index_entry",
    tags=["index_entry"],
)
async def index_entry(
    geohash: str = "40.043021,116.434523",
    flags: str = "F",
    group_type: int = 1,
    db: AsyncIOMotorClient = Depends(get_database),
):
    results = await get_index_entry(db, geohash, flags, group_type)
    return results
# =============================================================================


# -----------------------------------------------------------------------------
# user
@v1router.get(
    "/user",
    tags=["user"], 
)
async def v1_user(
    user_id: int = None,
    db: AsyncIOMotorClient = Depends(get_database)
):
    results = await get_userinfos(db, user_id)
    return results

# =============================================================================


# -----------------------------------------------------------------------------
# categories
@shoppingrouter.get(
    "/v2/restaurant/category/",
    tags=["shopping"],
)
async def getcategories(
    latitude: str = None,
    longitude: str = None,
    db: AsyncIOMotorClient = Depends(get_database)
):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except:
        latitude = 40.043021
        longitude = 116.434523

    res = await get_categories(db, latitude, longitude)
    return res

# =============================================================================

# -----------------------------------------------------------------------------
# restaurants
@shoppingrouter.get(
    "/restaurants",
    tags=["shopping"],
)
async def getrestaurants(
    # latitude: float = 39.944971,
    # longitude: float = 116.482313,
    latitude: str,
    longitude: str,
    # latitude: float = None,
    # longitude: float = None,
    offset: int = 0,
    limit: int = 20,
    extras: List[str] = "activites",
    keyword: str = None,
    restaurant_category_id: int = None,
    restaurant_category_ids: List[int] = None,
    order_by: int = None,
    delivery_mode: List[int] = None,
    db: AsyncIOMotorClient = Depends(get_database)
) -> List[ShopModel]:

    print('api')
    print(latitude)
    print(longitude)
    print(keyword)
    print(order_by)
    print(extras)
    print(offset)
    print(limit)
    print(delivery_mode)
    print(restaurant_category_id)
    print(restaurant_category_ids)
    res = await get_restaurants(
        db, 
        latitude, 
        longitude, 
        keyword,
        restaurant_category_id,
        order_by,
        extras, 
        offset, 
        limit, 
        delivery_mode,
        [],
        restaurant_category_ids,
    )
    print('end')

    return res

@shoppingrouter.get(
    "/restaurant/{restaurant_id}",
    tags=["shopping"],
)
async def restaurant_restaurant_id(
    restaurant_id: int,
    db: AsyncIOMotorClient = Depends(get_database),
):
    res = await get_restaurant_detail(db, restaurant_id)
    return res
# =============================================================================


# -----------------------------------------------------------------------------
# Deliveries
@shoppingrouter.get(
    "/v1/restaurants/delivery_modes",
    tags=["shopping"],
)
async def v1_restaurants_deliverymodes(
    db: AsyncIOMotorClient = Depends(get_database),
):
    res = await get_deliveries(db)
    return res

# =============================================================================


# -----------------------------------------------------------------------------
# Activities
@shoppingrouter.get(
    "/v1/restaurants/activity_attributes",
    tags=["shopping"],
)
async def v1_restaurants_activity_attributes(
    db: AsyncIOMotorClient = Depends(get_database)
):
    res = await get_activities(db)
    return res

# =============================================================================


# -----------------------------------------------------------------------------
# Menus
@shoppingrouter.get(
    "/v2/menu",
    tags=["shopping"],
)
async def v2_menu(
    restaurant_id: int,
    db: AsyncIOMotorClient = Depends(get_database),
):
    res = await get_menus(db, restaurant_id)
    return res
# =============================================================================


# -----------------------------------------------------------------------------
# ratings
@ugcrouter.get(
    "/v2/restaurants/{restaurant_id}/ratings",
    tags=["shopping"],
)
async def v2_restaurants_restaurant_id_ratings(
    restaurant_id: int,
    db: AsyncIOMotorClient = Depends(get_database),
):
    res = await get_restaurant_ratings(db, restaurant_id)
    return res
# =============================================================================


# -----------------------------------------------------------------------------
# scores
@ugcrouter.get(
    "/v2/restaurants/{restaurant_id}/ratings/scores",
    tags=["shopping"],
)
async def v2_restaurants_restaurant_id_ratings_scores(
    restaurant_id: int,
    db: AsyncIOMotorClient = Depends(get_database),
):
    res = await get_restaurant_ratings_scores(db, restaurant_id)
    return res
# =============================================================================


# -----------------------------------------------------------------------------
# tags
@ugcrouter.get(
    "/v2/restaurants/{restaurant_id}/ratings/tags",
    tags=["shopping"],
)
async def v2_restaurants_restaurant_id_ratings_tags(
    restaurant_id: int,
    db: AsyncIOMotorClient = Depends(get_database),
):
    res = await get_restaurant_ratings_tags(db, restaurant_id)
    return res
# =============================================================================