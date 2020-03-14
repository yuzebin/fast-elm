from typing import Optional, List, Dict

from datetime import datetime, timezone

from pydantic import BaseModel, Schema, BaseConfig, EmailStr, HttpUrl

from fmsecurity import generate_salt, verify_password, get_password_hash


# -----------------------------------------------------------------------------
# DateTimeModel
class DateTimeModelMixin(BaseModel):
    created_at: Optional[datetime] = Schema(None, alias="createdAt")
    updated_at: Optional[datetime] = Schema(None, alias="updatedAt")
# =============================================================================


# -----------------------------------------------------------------------------
# DBModel
class DBModelMixin(DateTimeModelMixin):
    id: Optional[int] = None
# =============================================================================


# -----------------------------------------------------------------------------
# RWModel
class RWModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_alias = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }
# =============================================================================


# -----------------------------------------------------------------------------
# RWUser
class RWUserBase(RWModel):
    username: str
    email: EmailStr
    bio: Optional[str] = ""
    image: Optional[HttpUrl] = None


class RWUserInDB(DBModelMixin, RWUserBase):
    salt: str = ""
    hashed_password: str = ""

    def check_password(self, password: str):
        return verify_password(self.salt + password, self.hashed_password)

    def change_password(self, password: str):
        self.salt = generate_salt()
        self.hashed_password = get_password_hash(self.salt + password)


class RWUser(RWUserBase):
    token: str


class RWUserInResponse(RWModel):
    user: RWUser


class RWUserInLogin(RWModel):
    email: EmailStr
    password: str
    vcode: str


class RWUserInCreate(RWUserInLogin):
    username: str


class RWUserInUpdate(RWModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[HttpUrl] = None
# =============================================================================


# -----------------------------------------------------------------------------
# Profile
class Profile(RWModel):
    username: str
    bio: Optional[str] = ""
    image: Optional[HttpUrl] = None
    following: bool = False


class ProfileInResponse(RWModel):
    profile: Profile
# =============================================================================


# -----------------------------------------------------------------------------
# Article
class ArticleFilterParams(RWModel):
    tag: str = ""
    author: str = ""
    favorited: str = ""
    limit: int = 20
    offset: int = 0


class ArticleBase(RWModel):
    title: str
    description: str
    body: str
    tag_list: List[str] = Schema([], alias="tagList")


class Article(DateTimeModelMixin, ArticleBase):
    slug: str
    author: Profile
    favorited: bool
    favorites_count: int = Schema(..., alias="favoritesCount")


class ArticleInDB(DBModelMixin, Article):
    pass


class ArticleInResponse(RWModel):
    article: Article


class ManyArticlesInResponse(RWModel):
    articles: List[Article]
    articles_count: int = Schema(..., alias="articlesCount")


class ArticleInCreate(ArticleBase):
    pass


class ArticleInUpdate(RWModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    tag_list: List[str] = Schema([], alias="tagList")
# =============================================================================


# -----------------------------------------------------------------------------
# Tag
class Tag(RWModel):
    tag: str


class TagInDB(DBModelMixin, Tag):
    pass


class TagsList(RWModel):
    tags: List[str] = []
# =============================================================================


# -----------------------------------------------------------------------------
# Cities
class CitiesModel(BaseModel):
    id: Optional[int] = None
    data: Dict = None
    v: int = None
# =============================================================================


# -----------------------------------------------------------------------------
# Entry
class EntryModel(BaseModel):
    id: int
    is_in_serving: bool
    description: str
    title: str = None
    link: str = None
    image_url: str = None
    icon_url: str = None
    title_color: str = None
# =============================================================================


# -----------------------------------------------------------------------------
# User
class UserModel(BaseModel):
    user_id: int
    username: str
    password: str

    def change_password(self, password: str):
        self.salt = generate_salt()
        self.hashed_password = get_password_hash(self.salt + password)

class ColumnDesc(BaseModel):
    _desc: str =  '玩游戏领红包'
    game_image_hash: str = '05f108ca4e0c543488799f0c7c708cb1jpeg'
    game_is_show: int = 1
    game_link: str = 'https://gamecenter.faas.ele.me'
    gift_mall_desc: str = '0元好物在这里'


class UserInfoModel(BaseModel):
    id: int
    city: str
    user_id: int
    username: str 
    registe_time: str
    column_desc: ColumnDesc
    avatar: str = 'default.jpg'
    balance: int = 0
    brand_member_new: int = 0
    current_address_id: int = 0
    current_invoice_id: int = 0
    delivery_card_expire_days: int = 0
    email: str = ''
    gift_amount: int = 3
    is_active: int = 1
    is_email_valid: bool = False
    is_mobile_valid: bool = True
    mobile: str = ''
    point: int =  0

# =============================================================================


# -----------------------------------------------------------------------------
# CategoryModel
class SubCategoriesModel(BaseModel):
    id: int = None
    image_url: str = None
    level: int = 0
    name: str = ""
    count: int = 0


class CategoryModel(BaseModel):
    count: int = None
    id: int = None
    name: str = None
    level: int = None
    image_url: str = ""
    ids:  List[int] = None
    sub_categories: List[SubCategoriesModel] = None
# =============================================================================


# -----------------------------------------------------------------------------
# ShopModel
from datetime import datetime 

class ActivitiesModel(BaseModel):
    id: int
    name: str = None
    description: str = None
    icon_name: str = None
    icon_color: str = None
    ranking_weiight: int = None


class DeliveriesModel(BaseModel):
    color: str = None
    id: int
    is_solid: bool = None
    text: str = None


class IdentificationModel(BaseModel):
    registered_number: str = ""
    registered_address: str = ""
    operation_period: str = ""
    licenses_scope: str = ""
    licenses_number: str = ""
    licenses_date: str = ""
    legal_person: str = ""
    identificate_date: datetime  = None
    identificate_agency: str = ""
    company_name: str = ""


class LicenseModel(BaseModel):
    business_license_image: str
    catering_service_license_image: str


class SupportsModel(BaseModel):
    description: str
    icon_color: str
    icon_name: str
    id: int
    name: str


class ShopModel(BaseModel):
    name: str 
    address: str
    id: int
    latitude: float
    longitude: float
    location: List[float]
    phone: str
    category: str
    supports: List[SupportsModel]
    status: int
    recent_order_num: int
    rating_count: int
    rating: float
    promotion_info: str
    piecewise_agent_fee: Dict[str, str]
    opening_hours: List[str]
    license: LicenseModel
    is_new: bool
    is_premium: bool
    image_path: str
    delivery_mode: DeliveriesModel
    activities: List[ActivitiesModel]
    identification: IdentificationModel
    float_delivery_fee: int = 0
    distance: str = ""
    order_lead_time: str = ""
    description: str = ""
    float_minimum_order_amount: int = 0
# =============================================================================


# -----------------------------------------------------------------------------
# FoodModel
class SpecsModel(BaseModel):
    name: str
    value: str


class SpecfoodsModel(BaseModel):
    original_price: float
    sku_id: int
    name: str
    pinyin_name: str
    restaurant_id: int
    food_id: int
    packing_fee: float
    recent_rating: float
    promotion_stock: int
    price: float
    sold_out: bool 
    recent_popularity: int
    is_essential: bool
    item_id: int
    checkout_mode: int
    stock: int
    specs_name: str
    specs: List[SpecsModel]


class FoodModel(BaseModel):
	rating: float
	is_featured: int
	restaurant_id: int
	category_id: int
	pinyin_name: str
	display_times: List[str]
	attrs: List[str]
	description: str
	month_sales: int
	rating_count: int
	tips: str
	image_path: str
	specifications: List[str]
	server_utc: datetime
	is_essential: bool
	attributes: List[str]
	item_id: int
	limitation: str
	name: str
	satisfy_count: int
	activity: str
	satisfy_rate: float
	specfoods: List[SpecfoodsModel]
# =============================================================================


# -----------------------------------------------------------------------------
# MenuModel
class MenusModel(BaseModel):
    description: str
    is_selected: bool
    icon_url: str
    name: str
    id:  int
    restaurant_id: int
    type: int
    foods: List[FoodModel]
# =============================================================================


# -----------------------------------------------------------------------------
# RateModel
class ItemRatingsModel(BaseModel):
    food_id: int
    food_name: str
    image_hash: str
    is_valid: int


class RateModel(BaseModel):
    avatar: str
    item_ratings: List[ItemRatingsModel]
    rated_at: str
    rating_star: int
    rating_text: str
    time_spent_desc: str
    username: str
    tags: List = []
    highlights: List = []


class ScoresModel(BaseModel):
    compare_rating: float
    deliver_time: int
    food_score: float
    order_rating_amount: int
    overall_score: float
    service_score: float


class TagsModel(BaseModel):
    count: int
    name: str
    unsatisfied: bool


class RatingsModel(BaseModel):
    restaurant_id: int
    ratings: List[RateModel]
    scores: ScoresModel
    tags: List[TagsModel]
# =============================================================================