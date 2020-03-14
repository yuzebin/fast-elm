import json
import requests

from bson import ObjectId
from datetime import datetime
from typing import Optional, List

from slugify import slugify
from pydantic import EmailStr
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from fmtoken import get_user

from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY, 
    HTTP_404_NOT_FOUND
)

from fmmodel import (
    ArticleInDB, 
    ArticleInCreate, 
    Profile, RWUserInDB, 
    RWUserInCreate, 
    RWUserInUpdate, 
    TagInDB,
    ArticleFilterParams,
    CitiesModel,
    EntryModel,
    UserModel,
    UserInfoModel,
    CategoryModel,
    ShopModel,
    DeliveriesModel,
    ActivitiesModel,
    MenusModel,
    RatingsModel,
)

from fmdb import (
    db_name, 
    articles_collection_name, 
    favorites_collection_name, 
    users_collection_name, 
    followers_collection_name, 
    tags_collection_name,
    cities_collection_name,
    entries_collection_name,
    users_collection_name,
    userinfos_collection_name,
    categories_collection_name,
    restaurants_collection_name,
    deliveries_collection_name,
    activities_collection_name,
    menus_collection_name,
    ratings_collection_name,
)


# -----------------------------------------------------------------------------
# user
async def check_free_username_and_email(
        conn: AsyncIOMotorClient, 
        username: Optional[str] = None, 
        email: Optional[EmailStr] = None
):
    if username:
        user_by_username = await get_user(conn, username)
        if user_by_username:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this username already exists",
            )
    if email:
        user_by_email = await get_user_by_email(conn, email)
        if user_by_email:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this email already exists",
            )


async def get_profile_for_user(
    conn: AsyncIOMotorClient,
    target_username: str,
    current_username: Optional[str] = None
) -> Profile:
    user = await get_user(conn, target_username)
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"User {target_username} not found"
        )

    profile = Profile(**user.dict())
    profile.following = await is_following_for_user(
        conn, current_username, target_username
    )

    return profile


async def is_following_for_user(
    conn: AsyncIOMotorClient, 
    current_username: str, 
    target_username: str
) -> bool:
    count = await conn[db_name][followers_collection_name].count_documents(
        {"follower": current_username,
        "following": target_username}
    )
    return count > 0


async def get_user_by_email(
    conn: AsyncIOMotorClient, 
    email: EmailStr
) -> RWUserInDB:
    row = await conn[db_name][users_collection_name].find_one({"email": email})
    if row:
        return RWUserInDB(**row)


async def create_user(
    conn: AsyncIOMotorClient, 
    user: RWUserInCreate
) -> RWUserInDB:
    dbuser = RWUserInDB(**user.dict())
    dbuser.change_password(user.password)
    print(user)
    row = await conn[db_name][users_collection_name].insert_one(dbuser.dict())

    dbuser.id = row.inserted_id
    dbuser.created_at = ObjectId(dbuser.id ).generation_time
    dbuser.updated_at = ObjectId(dbuser.id ).generation_time

    return dbuser


async def create_user_info(
    conn: AsyncIOMotorClient, 
    user: UserModel,
    userinfo: UserInfoModel,
) -> UserInfoModel:
    print(user)
    print(userinfo)

    dbuser = UserModel(**user.dict())
    dbuser.change_password(user.password)

    dbuserinfo = UserInfoModel(**userinfo.dict())
    rowuserinfo = await conn[db_name][userinfos_collection_name].insert_one(dbuserinfo.dict())
    dbuserinfo.id = rowuserinfo.inserted_id
    dbuserinfo.user_id = dbuserinfo.id

    rowuser = await conn[db_name][users_collection_name].insert_one(dbuser.dict())

    return dbuserinfo

async def update_user(
    conn: AsyncIOMotorClient, 
    username: str, 
    user: RWUserInUpdate
) -> RWUserInDB:
    dbuser = await get_user(conn, username)

    dbuser.username = user.username or dbuser.username
    dbuser.email = user.email or dbuser.email
    dbuser.bio = user.bio or dbuser.bio
    dbuser.image = user.image or dbuser.image
    if user.password:
        dbuser.change_password(user.password)

    updated_at = await conn[db_name][users_collection_name].update_one(
        {"username": dbuser.username}, 
        {'$set': dbuser.dict()}
    )
    dbuser.updated_at = updated_at
    return dbuser
# =============================================================================


# -----------------------------------------------------------------------------
# article
async def get_article_by_slug(
    conn: AsyncIOMotorClient, slug: str, username: Optional[str] = None
) -> ArticleInDB:
    article_doc = await conn[db_name][articles_collection_name].find_one(
        {"slug": slug}
    )
    if article_doc:
        article_doc["favorites_count"] = await get_favorites_count_for_article(
            conn, slug
        )
        article_doc["favorited"] = await is_article_favorited_by_user(
            conn, slug, username
        )
        article_doc["author"] = await get_profile_for_user(
            conn,
            article_doc["author_id"]
        )

        return ArticleInDB(
            **article_doc,
            created_at=ObjectId(article_doc["_id"]).generation_time
        )


async def create_article_by_slug(
    conn: AsyncIOMotorClient, article: ArticleInCreate, username: str
) -> ArticleInDB:
    slug = slugify(article.title)
    article_doc = article.dict()
    article_doc["slug"] = slug
    article_doc["author_id"] = username
    article_doc["updated_at"] = datetime.now()
    await conn[db_name][articles_collection_name].insert_one(article_doc)

    if article.tag_list:
        await create_tags_that_not_exist(conn, article.tag_list)

    author = await get_profile_for_user(conn, username, "")
    return ArticleInDB(
        **article_doc,
        created_at=ObjectId(article_doc["_id"]).generation_time,
        author=author,
        favorites_count=1,
        favorited=True,
    )


async def get_favorites_count_for_article(
    conn: AsyncIOMotorClient,
    slug: str
) -> int:
    article_doc = await conn[db_name][articles_collection_name].find_one(
        {"slug": slug},
        projection={"id": True}
    )
    if article_doc:
        return await conn[db_name][favorites_collection_name].count_documents(
            {"article_id": article_doc['_id']}
        )
    else:
        raise RuntimeError(f"没有找到对应的article_id,"
                           f" slug={slug} article_id={article_doc}")


async def is_article_favorited_by_user(
    conn: AsyncIOMotorClient, slug: str, username: str
) -> bool:
    user_doc = await conn[db_name][users_collection_name].find_one(
        {"username": username},
        projection={"id": True}
    )
    article_doc = await conn[db_name][articles_collection_name].find_one(
        {"slug": slug},
        projection={"id": True}
    )
    if article_doc and user_doc:
        count = await conn[db_name][favorites_collection_name].count_documents(
            {"user_id": user_doc['_id'],
            "article_id": article_doc['_id']}
        )
        return count > 0
    else:
        raise RuntimeError(
            f"没有找到对应的user_id或article_id,"
            f"用户名={username} user={user_doc},slug={slug} article={article_doc}"
        )


async def get_articles_with_filters(
    conn: AsyncIOMotorClient,
    filters: ArticleFilterParams,
    username: Optional[str] = None
) -> List[ArticleInDB]:
    articles: List[ArticleInDB] = []
    base_query = {}

    if filters.tag:
        base_query["tag_list"] = f"$all: [\"{filters.tag}\"]"

    if filters.favorited:
        base_query["slug"] = f"$in: [\"{filters.favorited}\"]"

    if filters.author:
        base_query["author"] = f"$in: [\"{filters.author}]\""

    rows = conn[db_name][articles_collection_name].find(
        {"author_id": username},
        limit=filters.limit,
        skip=filters.offset
    )

    async for row in rows:
        slug = row["slug"]
        # author = await get_profile_for_user(conn, row["author_id"], username)
        # tags = await get_tags_for_article(conn, slug)
        # favorites_count = await get_favorites_count_for_article(conn, slug)
        # favorited_by_user = await is_article_favorited_by_user(conn, slug, username)
        author = "author"
        tags = await get_tags_for_article(conn, slug)
        favorites_count = 1
        favorited_by_user = True
        articles.append(
            ArticleInDB(
                **row,
                author=author,
                created_at=ObjectId(row["_id"]).generation_time,
                favorites_count=favorites_count,
                favorited=favorited_by_user,
            )
        )
    return articles
# =============================================================================


# -----------------------------------------------------------------------------
# tags
async def fetch_all_tags(conn: AsyncIOMotorClient) -> List[TagInDB]:
    tags = []
    rows = conn[db_name][tags_collection_name].find()
    async for row in rows:
        tags.append(TagInDB(**row))

    return tags


async def get_tags_for_article(
    conn: AsyncIOMotorClient,
    slug: str
) -> List[TagInDB]:
    tags = []
    article_tags = await conn[db_name][articles_collection_name].find_one(
        {"slug": slug},
        projection={"tag_list": True}
    )
    for row in article_tags["tag_list"]:
        tags.append(TagInDB({"tag": row}))

    return tags


async def create_tags_that_not_exist(
    conn: AsyncIOMotorClient,
    tags: List[str]
):
    await conn[db_name][tags_collection_name].insert_many(
        [{"tag": tag} for tag in tags]
    )
# =============================================================================


# -----------------------------------------------------------------------------
# cities
async def get_cities_by_key(
    conn: AsyncIOMotorClient,
    key: str
):
    cities = conn['test']['cities'].find()
    key_cities = None

    data = None
    if key == 'hot':
        async for c in cities:
            data = c['data']['hotCities']

    if key == 'group':

        async for c in cities:
            data = c['data']
        data.pop('hotCities', None)
        data.pop('_id', None)

    if key == 'guess':
        name = get_city_name()
        city = None
        fw = name[0:1].upper()
        async for c in cities:
            data = c['data'][fw]

        for k in data:
            if k['pinyin'] == name:
                city = k
        data = city
    
    return data

def get_city_name():
    return "beijing"


async def get_cities_by_id(
    conn: AsyncIOMotorClient,
    id: int
):
    cities = conn['test']['cities'].find()
    key_cities = None

    data = None
    async for c in cities:
        data = c['data']
    
    for d in data:
        for v in data[d]:
            if v['id'] == id:
                key_cities = v
    
    data = key_cities

    return data
# =============================================================================


# ----------------------------------------------------------------------------- 
# pois
# 获取定位
async def get_pois_by_ip(
    conn: AsyncIOMotorClient,
    type: str,
    city_id: int,
    keyword: str,
    ip: str
):
    txkey = 'RLHBZ-WMPRP-Q3JDS-V2IQA-JNRFH-EJBHL';
    txkey2 = 'RRXBZ-WC6KF-ZQSJT-N2QU7-T5QIT-6KF5X';
    txkey3 = 'OHTBZ-7IFRG-JG2QF-IHFUK-XTTK6-VXFBN';
    txkey4 = 'Z2BBZ-QBSKJ-DFUFG-FDGT3-4JRYV-JKF5O';
    bdkey = 'fjke3YUipM9N64GdOIh1DNeK2APO2WcT';
    # baidukey2 = 'fjke3YUipM9N64GdOIh1DNeK2APO2WcT';

    posi = await guess_position(ip, txkey)

    city_name = posi["result"]["ad_info"]["city"].replace("市", "")

    place = await search_place(keyword, city_name, txkey, 10)

    return place['data']


async def guess_position(
    ip: str,
    txkey: str,
):
    # get position
    # demo: http://apis.map.qq.com/ws/location/v1/ip?key=Z2BBZ-QBSKJ-DFUFG-FDGT3-4JRYV-JKF5O&ip=223.20.22.111
    ip = '180.158.102.141'
    posi_api = "http://apis.map.qq.com/ws/location/v1/ip"
    res = requests.get(f"{posi_api}?key={txkey}&ip={ip}")
    posi = res.json()

    return posi
    

# 搜索地址
async def search_place(
    kw: str,
    cn: str,
    key: str,
    ps: int = 10,
):
    # get place
    # demo: http://apis.map.qq.com/ws/place/v1/search?key=Z2BBZ-QBSKJ-DFUFG-FDGT3-4JRYV-JKF5O&boundary=region(%E5%8C%97%E4%BA%AC,0)&keyword=%E6%9C%9D%E9%98%B3
    place_api = "http://apis.map.qq.com/ws/place/v1/search"
    bd = f"region({cn},0)"
    res = requests.get(f"{place_api}?key={key}&boundary={bd}&keyword={kw}")
    place = res.json()
    return place

# 搜索经纬度
async def get_pois_by_latlng(
    location: str,
):
    txkey = 'RLHBZ-WMPRP-Q3JDS-V2IQA-JNRFH-EJBHL';
    data = {"key": txkey, "location": location}
    headers = {'Content-Type': 'application/json'}
    geocoder_api = "http://apis.map.qq.com/ws/geocoder/v1/"
    res = requests.post(geocoder_api, headers=headers, data=json.dumps(data))
    data = res.json()
    if data["status"]==0:
        return data
    else:
        return {"msg": "获取定位失败"}
# =============================================================================


# -----------------------------------------------------------------------------
# entry
async def get_index_entry(
    conn: AsyncIOMotorClient,
    geohash: str, 
    flags: str,
    group_type: int,
) -> List[EntryModel]:
    entrys = []
    # rows = conn[db_name][entry_collection_name].find({}, '-_id')
    rows = conn[db_name][entries_collection_name].find()
    print(db_name)
    print(entries_collection_name)
    async for row in rows:
        print(row)
        entrys.append(EntryModel(**row))
    return entrys 

# =============================================================================


# -----------------------------------------------------------------------------
# user
async def get_userinfos(
    conn: AsyncIOMotorClient,
    user_id: int = None,
):
#    userinfo = await UserInfoModel.findOne({user_id}, '-_id')
    print('crud 1')
    row = await conn[db_name][userinfos_collection_name].find_one({"user_id": user_id})
    res = UserInfoModel(**row)
    print(res)
    return res

# =============================================================================


# -----------------------------------------------------------------------------
# categories
async def get_categories(
    conn: AsyncIOMotorClient,
    latitude: float = None,
    longitude: float = None,
) -> List[CategoryModel]:
    # userinfo = await UserInfoModel.findOne({user_id}, '-_id')
    rows= conn[db_name][categories_collection_name].find({})
    res = []
    async for row in rows:
        res.append(CategoryModel(**row))
    return res 

async def get_category_by_id(
    conn: AsyncIOMotorClient,
    category_id: int,
) -> CategoryModel:
    rows = conn[db_name][categories_collection_name].findOne(
        {'sub_categories.id': category_id}
    )

    res = []
    async for row in rows:
        res.append(CategoryModel(**row))

    res0 = res[0]
    categoName = res0["name"]
    for sub in res0["subcategories"]:
        if sub["id"] == category_id:
            categoName += '/' + sub["name"]
    
    return categoName

# ============================================================================


# -----------------------------------------------------------------------------
# restaurants
async def get_restaurants(
    conn: AsyncIOMotorClient,
    latitude: float,
    longitude: float,
    keyword: str,
    restaurant_category_id: int,
    order_by: int,
    extras: str,
    offset: int = 0,
    limit: int = 20,
    delivery_mode: List = [],
    support_ids: List[int] = [],
    restaurant_category_ids: List[int] = [],
):
    filter = {}
    if restaurant_category_ids:
        category = await get_category_by_id(conn, restaurant_category_ids[0])
        filter = category.copy()

    # 按照距离，评分，销量等排序
    sortby = {}
    if order_by:
        if order_by == 1:
            sortby["float_minimum_order_amount"] = 1
        if order_by == 2:
            filter["location"] = {"$near":[longitude, latitude]}
        if order_by == 3:
            sortby["rating"] = -1
        if order_by == 5:
            filter["location"] = {"$near":[longitude, latitude]}
        if order_by == 6:
            sortby["recent_order_num"] = -1
    print('sortby')
    print(sortby)

    #   查找配送方式
    if delivery_mode:
        for d in delivery_mode:
            filter["delivery_mode.id"] = d

    # 	//查找活动支持方式
    filterarr = []
    if support_ids:
        for s in support_ids:
            if s != 8:
                filterarr.aappend(s)
            else:
                filter["is_premium"] = True

        filter["supports.id"] = {"$all": filterarr}

    print('filter')
    print(filter)

    res = []
    # rows = conn[db_name][restaurants_collection_name].find(
        # filter
    # ).sort(sortby).limit(limit).skip(offset)
    rows = conn[db_name][restaurants_collection_name].find()

    async for row in rows:
        res.append(ShopModel(**row))

    print('res')
    print(res)
    # 获取百度地图测局所需经度纬度
    # from = str(latitude) + ',' + str(longitude)
    # to = ''

    # for i in res:

    # 	restaurants.forEach((item, index) => {
    # 		const slpitStr = (index == restaurants.length -1) ? '' : '|';
    # 		to += item.latitude + ',' + item.longitude + slpitStr;
    # 	})

    # 	try{
    # 		if (restaurants.length) {
    # 			//获取距离信息，并合并到数据中
    # 			const distance_duration = await this.getDistance(from, to)
    # 			restaurants.map((item, index) => {
    # 				return Object.assign(item, distance_duration[index])
    # 			})
    # 		}
    # 	}catch(err){
    # 		// 百度地图达到上限后会导致加车失败，需优化
    # 		console.log('从addressComoponent获取测距数据失败', err);
    # 		restaurants.map((item, index) => {
    # 			return Object.assign(item, {distance: '10公里', order_lead_time: '40分钟'})
    # 		})
    # 	}
    return res

async def get_restaurant_detail(
    conn: AsyncIOMotorClient,
    restaurant_id: int,
):
    rows = conn[db_name][restaurants_collection_name].find({"id": restaurant_id})
    res = []
    async for row in rows:
        res = ShopModel(**row)
    return res 

# =============================================================================


# -----------------------------------------------------------------------------
# deliveries
async def get_deliveries(
    conn: AsyncIOMotorClient,
):
    rows= conn[db_name][deliveries_collection_name].find({})
    res = []
    async for row in rows:
        res.append(DeliveriesModel(**row))
    return res 
# =============================================================================


# -----------------------------------------------------------------------------
# activties
async def get_activities(
    conn: AsyncIOMotorClient,
):
    rows= conn[db_name][activities_collection_name].find({})
    res = []
    async for row in rows:
        res.append(ActivitiesModel(**row))
    return res 
# =============================================================================

# -----------------------------------------------------------------------------
# menu
async def get_menus(
    conn: AsyncIOMotorClient,
    id:int,
):
    rows= conn[db_name][menus_collection_name].find({"restaurant_id":id})
    res = []
    async for row in rows:
        res.append(MenusModel(**row))
    return res 
    # const category_id = req.params.category_id;
    # const menu = await MenuModel.findOne({id: category_id}, '-_id');
# =============================================================================


# -----------------------------------------------------------------------------
# ratings
async def get_restaurant_ratings(
    conn: AsyncIOMotorClient,
    id:int,
):
    rows= conn[db_name][ratings_collection_name].find({"restaurant_id":id})
    res = []
    async for row in rows:
        k = RatingsModel(**row)
        res = k.ratings
    return res 


async def get_restaurant_ratings_scores(
    conn: AsyncIOMotorClient,
    id:int,
):
    rows= conn[db_name][ratings_collection_name].find({"restaurant_id":id})
    res = []
    async for row in rows:
        k = RatingsModel(**row)
        res = k.scores
    return res 


async def get_restaurant_ratings_tags(
    conn: AsyncIOMotorClient,
    id:int,
):
    rows= conn[db_name][ratings_collection_name].find({"restaurant_id":id})
    res = []
    async for row in rows:
        k = RatingsModel(**row)
        res = k.tags
    return res 



# =============================================================================