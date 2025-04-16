import re
from typing import Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlmodel import Session, create_engine

from core.config import settings
from models import ProductStudioPackage
from models.product_studios import ProductStudio
from models.products import Product
from utils.utils import utc_now

PROD_PG_CONNECTION = {
    "host": settings.POSTGRES_SERVER,
    "database": settings.POSTGRES_DB,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "port": settings.POSTGRES_PORT,
}

target_env = "prod"
target_database = (
    settings.DATABASE_URI.replace("postgresql+asyncpg", "postgresql")
    if target_env == "prod"
    else "postgresql://reborn:reborn@postgres-container.orb.local:5432/reborn"
)


def connect_to_source_db():
    """Connect to the source PostgreSQL database."""
    try:
        conn = psycopg2.connect(**PROD_PG_CONNECTION, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error connecting to source database: {e}")
        return None


def get_enterprise_data(conn):
    """Get enterprise data from source database."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT 
        e.enterprise_code,
        e.enterprise_name,
        e.represent,
        e.addr,
        e.phone,
        e.category,
        e.use_check,
        e.del_check,
        e.holiday2 as holiday,
        e.no_guide,
        e.bpchk,
        e.logo
    FROM 
        reference.iw_studio_enterprises e
    WHERE
        e.del_check = false
    """
    cursor.execute(query)
    enterprises = cursor.fetchall()

    # Get all products for each enterprise
    for enterprise in enterprises:
        enterprise_code = enterprise["enterprise_code"]

        # Get all products for this enterprise
        cursor.execute(
            """
        SELECT 
            p.no, 
            p.name, 
            p.thumb, 
            p.cmt, 
            p.product_price, 
            p.price, 
            p.event_price, 
            p.reg_date, 
            p.view_cnt, 
            p.order_cnt, 
            p.like_cnt,
            p.category
        FROM 
            reference.iw_studio_products p
        WHERE 
            p.enterprise_code = %s
        """,
            (enterprise_code,),
        )
        products = cursor.fetchall()

        enterprise["products"] = products

    cursor.close()
    return enterprises


def get_product_detail(conn, product_id, enterprise_code):
    """Get detailed information for a specific product."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get product details
    cursor.execute(
        """
    SELECT 
        p.no, 
        p.enterprise_code, 
        p.name, 
        p.thumb, 
        p.cmt, 
        p.product_price, 
        p.price, 
        p.event_price, 
        p.reg_date, 
        p.view_cnt, 
        p.order_cnt, 
        p.like_cnt,
        p.category,
        pd.detail,
        pd.sub_category
    FROM 
        reference.iw_studio_products p
    LEFT JOIN 
        reference.iw_studio_product_details pd ON p.no = pd.product_no
    WHERE 
        p.no = %s AND p.enterprise_code = %s
    """,
        (product_id, enterprise_code),
    )

    product = cursor.fetchone()
    if not product:
        return None

    # Get product info
    cursor.execute(
        """
    SELECT title, value, description
    FROM reference.iw_studio_product_info
    WHERE product_no = %s
    """,
        (product_id,),
    )
    product_info = cursor.fetchall()

    # Get add options
    cursor.execute(
        """
    SELECT option_name, option_detail_name, price
    FROM reference.iw_studio_add_options ao
    JOIN reference.iw_studio_option_details od 
        ON ao.product_no = od.product_no AND ao.option_no = od.option_no
    WHERE ao.product_no = %s
    """,
        (product_id,),
    )
    options = cursor.fetchall()

    # Get addcost items
    cursor.execute(
        """
    SELECT name, comment, price, required
    FROM reference.iw_studio_addcost
    WHERE product_no = %s
    """,
        (product_id,),
    )
    addcosts = cursor.fetchall()

    # Get tags
    cursor.execute(
        """
    SELECT no, tag_type, tag, item_value_no, tag_regdate
    FROM reference.iw_studio_tags
    WHERE product_no = %s
    """,
        (product_id,),
    )
    tags = cursor.fetchall()

    # Combine all data
    product["product_info"] = product_info
    product["options"] = options
    product["addcosts"] = addcosts
    product["tag"] = tags

    cursor.close()
    return product


def extract_location_info(address: str) -> Dict[str, str]:
    """Extract sido, gugun, and dong from address."""
    # Example address: "서울시 강남구 봉은사로 47길 53"
    location = {"sido": "", "gugun": "", "dong": "", "full_address": address}

    # Simple pattern matching for Korean addresses
    sido_pattern = r"^(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)(?:특별시|광역시|특별자치시|특별자치도|도)?"
    sido_match = re.search(sido_pattern, address)
    if sido_match:
        location["sido"] = sido_match.group(0)

        # Extract gugun
        gugun_pattern = (
            r"(?:특별시|광역시|특별자치시|특별자치도|도)?\s*(\w+(?:시|군|구))"
        )
        gugun_match = re.search(gugun_pattern, address)
        if gugun_match:
            location["gugun"] = gugun_match.group(1)

    return location


def parse_product_info(product_info: List[Dict]) -> Dict:
    """Parse product info into structured data."""
    info = {}

    for item in product_info:
        key = item["title"].lower() if "title" in item else ""
        value = item["value"] if "value" in item else ""

        if "앨범" in key or "상품구성" in key:
            # Extract album info
            album_match = re.search(r"앨범\s+(\d+)권", value)
            if album_match:
                info["album_count"] = int(album_match.group(1))

            page_match = re.search(r"(\d+)P", value)
            if page_match:
                info["album_page_count"] = int(page_match.group(1))

            frame_match = re.search(r"액자\s+(\d+)개", value)
            if frame_match:
                info["frame_count"] = int(frame_match.group(1))

            if "원본" in value and "데이터" in value:
                info["include_original_data"] = True

            if "수정" in value and "데이터" in value:
                info["include_edited_data"] = True

        elif "촬영" in key and "시간" in key:
            # Extract shooting duration
            duration_match = re.search(r"(\d+)시간", value)
            if duration_match:
                info["shooting_duration"] = (
                    int(duration_match.group(1)) * 60
                )  # convert to minutes

            # Also check for additional minutes
            minutes_match = re.search(r"(\d+)분", value)
            if minutes_match:
                info["shooting_duration"] = info.get("shooting_duration", 0) + int(
                    minutes_match.group(1)
                )

        elif "의상" in key or "벌" in key:
            # Extract outfit counts
            dress_match = re.search(r"드레스\s*(\d+)벌", value)
            if dress_match:
                info["dress_count"] = int(dress_match.group(1))

            casual_match = re.search(r"개인의상\s*(\d+)벌", value)
            if casual_match:
                info["casual_count"] = int(casual_match.group(1))

            # Total outfit count
            total_match = re.search(r"총\s*(\d+)벌", value)
            if total_match:
                info["outfit_count"] = int(total_match.group(1))
            else:
                info["outfit_count"] = info.get("dress_count", 0) + info.get(
                    "casual_count", 0
                )

    return info


def parse_studio_scenes(tags: List[Dict]) -> Dict[str, bool]:
    """Parse tags to determine available scenes."""
    scenes = {
        "has_garden_scene": False,
        "has_road_scene": False,
        "has_rooftop_scene": False,
        "has_night_scene": False,
        "has_hanbok_scene": False,
        "has_pet_scene": False,
        "has_black_white_scene": False,
    }

    scene_keywords = {
        "has_garden_scene": ["가든", "가든씬"],
        "has_road_scene": ["로드", "로드씬"],
        "has_rooftop_scene": ["옥상", "옥상씬"],
        "has_night_scene": ["야간", "야간씬"],
        "has_hanbok_scene": ["한복", "한복씬"],
        "has_pet_scene": ["반려동물", "반려동물씬", "애견", "펫"],
        "has_black_white_scene": ["흑백", "흑백씬"],
    }

    for tag_item in tags:
        tag = tag_item.get("tag", "").lower()

        for scene_key, keywords in scene_keywords.items():
            if any(keyword in tag for keyword in keywords):
                scenes[scene_key] = True

    return scenes


def has_hair_makeup(addcosts: List[Dict]) -> bool:
    """Check if hair makeup is available."""
    for item in addcosts:
        name = item.get("name", "").lower()
        if "헤어" in name or "메이크업" in name:
            return True
    return False


def format_additional_info(product_data: Dict) -> str:
    """Format additional information about the product."""
    info_parts = []

    # Add any important information from the product
    if product_data.get("cmt"):
        info_parts.append(product_data["cmt"])

    # Add option information
    if product_data.get("options"):
        discount_options = []
        for option in product_data["options"]:
            option_name = option.get("option_name", "")
            detail_name = option.get("option_detail_name", "")
            price = option.get("price", 0)

            if price and price < 0:
                discount_options.append(
                    f"{option_name}: {detail_name} (할인: {abs(price)}원)"
                )

        if discount_options:
            info_parts.append("할인 옵션: " + ", ".join(discount_options))

    # Add addcost information
    if product_data.get("addcosts"):
        addcost_info = []
        for item in product_data["addcosts"]:
            name = item.get("name", "")
            price = item.get("price", "")
            if price:
                addcost_info.append(f"{name}: {price}")

        if addcost_info:
            info_parts.append("추가 비용: " + ", ".join(addcost_info))

    return "\n".join(info_parts) if info_parts else None


def create_product_from_enterprise(conn, enterprise_data, engine):
    """Create a product entry from enterprise data and return its ID."""
    with Session(engine) as session:
        # Extract location information
        location = extract_location_info(enterprise_data.get("addr", ""))

        # Determine category ID
        category_id = 2

        # Find business hours and holiday from the first product if available
        business_hours = None
        if enterprise_data.get("products") and len(enterprise_data["products"]) > 0:
            first_product_id = enterprise_data["products"][0]["no"]
            first_product = get_product_detail(
                conn, first_product_id, enterprise_data["enterprise_code"]
            )
            if first_product and "product_info" in first_product:
                for info in first_product["product_info"]:
                    if "title" in info and "스케줄" in info["title"]:
                        business_hours = info.get("value")

        # Create product
        product = Product(
            product_category_id=category_id,
            name=enterprise_data.get("enterprise_name", ""),
            description="",  # Will be updated below
            hashtag=None,
            direct_link=f"https://www.iwedding.co.kr/center/web/brand_detail/{enterprise_data.get('enterprise_code')}",
            thumbnail_url=None,  # Will be updated below
            logo_url=enterprise_data.get("logo", ""),
            enterprise_name=enterprise_data.get("enterprise_name", ""),
            enterprise_code=enterprise_data.get("enterprise_code", ""),
            tel=enterprise_data.get("phone", ""),
            fax_tel="",
            sido=location.get("sido", ""),
            gugun=location.get("gugun", ""),
            dong=location.get("dong", None),
            address=location.get("full_address", ""),
            lat=0.0,
            lng=0.0,
            subway_line=None,
            subway_name=None,
            subway_exit=None,
            park_limit=0,
            park_free_hours=0,
            way_text=None,
            holiday=enterprise_data.get("holiday"),
            business_hours=business_hours,
            available=True,
            is_deleted=False,
            created_datetime=utc_now(),
            updated_datetime=utc_now(),
        )

        session.add(product)
        session.commit()
        session.refresh(product)

        # If enterprise has products, update product info from the first/main product
        if enterprise_data.get("products"):
            main_product = enterprise_data["products"][0]

            product.description = main_product.get("cmt", "")
            product.thumbnail_url = main_product.get("thumb")

            session.add(product)
            session.commit()

        return product.id


def create_product_studio(product_id, studio_data, engine):
    """Create a product_studio entry and return its ID."""
    with Session(engine) as session:
        # Parse scenes from tags
        scenes = parse_studio_scenes(studio_data.get("tag", []))

        # Create product_studio
        product_studio = ProductStudio(
            product_id=product_id,
            # Studio capabilities
            has_garden_scene=scenes.get("has_garden_scene", False),
            has_road_scene=scenes.get("has_road_scene", False),
            has_rooftop_scene=scenes.get("has_rooftop_scene", False),
            has_night_scene=scenes.get("has_night_scene", False),
            has_hanbok_scene=scenes.get("has_hanbok_scene", False),
            has_pet_scene=scenes.get("has_pet_scene", False),
            has_black_white_scene=scenes.get("has_black_white_scene", False),
            # Additional services
            hair_makeup_available=has_hair_makeup(studio_data.get("addcosts", [])),
            # System fields
            is_deleted=False,
            created_datetime=utc_now(),
            updated_datetime=utc_now(),
        )

        session.add(product_studio)
        session.commit()
        session.refresh(product_studio)

        return product_studio.id


def create_studio_package(studio_id, product_data, engine):
    """Create a studio_package entry from product data."""
    with Session(engine) as session:
        # Parse product info
        product_info = parse_product_info(product_data.get("product_info", []))

        # Create studio package
        package = ProductStudioPackage(
            product_studio_id=studio_id,
            name=product_data.get("name", ""),
            description=product_data.get("cmt", ""),
            original_price=product_data.get("product_price"),
            price=product_data.get("price", 0),
            discount_price=product_data.get("event_price"),
            # Package components
            album_count=product_info.get("album_count", 0),
            album_page_count=product_info.get("album_page_count", 0),
            frame_count=product_info.get("frame_count", 0),
            include_original_data=product_info.get("include_original_data", False),
            include_edited_data=product_info.get("include_edited_data", False),
            # Outfit info
            outfit_count=product_info.get("outfit_count", 0),
            dress_count=product_info.get("dress_count", 0),
            casual_count=product_info.get("casual_count", 0),
            # Additional info
            shooting_duration=product_info.get("shooting_duration", 0),
            additional_info=format_additional_info(product_data),
            # Save original ID for reference
            original_id=product_data.get("no"),
            is_deleted=False,
            created_datetime=utc_now(),
            updated_datetime=utc_now(),
        )

        session.add(package)
        session.commit()


def migrate_enterprise_to_product_and_packages(conn, engine):
    """Migrate enterprises to products and their packages."""
    # Get all enterprises
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
    SELECT 
        e.enterprise_code,
        e.enterprise_name,
        e.represent,
        e.addr,
        e.phone,
        e.category,
        e.holiday2 as holiday,
        e.logo
    FROM 
        reference.iw_studio_enterprises e
    WHERE
        e.del_check = false
    """
    )
    enterprises = cursor.fetchall()

    for enterprise in enterprises:
        enterprise_code = enterprise["enterprise_code"]
        print(f"Processing enterprise: {enterprise['enterprise_name']}")

        # 1. Create Product for this enterprise
        product_id = create_product_from_enterprise(conn, enterprise, engine)

        # 2. Get all products for this enterprise
        cursor.execute(
            """
        SELECT 
            p.no as product_no
        FROM 
            reference.iw_studio_products p
        WHERE 
            p.enterprise_code = %s
        """,
            (enterprise_code,),
        )
        products = cursor.fetchall()

        if not products:
            print(f"No products found for enterprise: {enterprise['enterprise_name']}")
            continue

        # 3. Get base studio information from the products
        # Use the first product as base for the studio details
        first_product = get_product_detail(
            conn, products[0]["product_no"], enterprise_code
        )

        # 4. Create ProductStudio
        studio_id = create_product_studio(product_id, first_product, engine)

        # 5. Create StudioPackage for each product
        for product_data in products:
            product_detail = get_product_detail(
                conn, product_data["product_no"], enterprise_code
            )
            if product_detail:
                create_studio_package(studio_id, product_detail, engine)
                print(f"Created package: {product_detail.get('name')}")

    cursor.close()


def main():
    # Connect to source database
    source_conn = connect_to_source_db()
    if not source_conn:
        print("Failed to connect to source database. Exiting.")
        return

    # Create engine for target database
    target_engine = create_engine(target_database)

    try:
        # Do the migration
        migrate_enterprise_to_product_and_packages(source_conn, target_engine)
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Close database connections
        source_conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
