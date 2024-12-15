import x
import uuid
import time
import random
from werkzeug.security import generate_password_hash
from faker import Faker

fake = Faker()

from icecream import ic
ic.configureOutput(prefix=f'***** | ', includeContext=True)

# Connect to the database
db, cursor = x.db()

def insert_user(user):
    """
    Inserts a user into the database.
    """
    q = """
        INSERT INTO users
        VALUES (%s, %s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s)
    """
    values = tuple(user.values())
    cursor.execute(q, values)

def insert_user_with_role(user, role_pk):
    """
    Inserts a user and assigns them a role.
    """
    insert_user(user)
    q = """
        INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
        VALUES (%s, %s)
    """
    cursor.execute(q, (user["user_pk"], role_pk))

try:
    ##############################
    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS restaurant_info")  # dependent table
    cursor.execute("DROP TABLE IF EXISTS items")  # dependent table
    cursor.execute("DROP TABLE IF EXISTS users_roles")  # dependent table
    cursor.execute("DROP TABLE IF EXISTS restaurant_food_category")  # dependent table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS roles")
    cursor.execute("DROP TABLE IF EXISTS food_categories")

    ##############################
    # Create tables
    cursor.execute("""
        CREATE TABLE users (
            user_pk CHAR(36),
            user_name VARCHAR(20) NOT NULL,
            user_last_name VARCHAR(20) NOT NULL,
            user_email VARCHAR(100) NOT NULL UNIQUE,
            user_password VARCHAR(255) NOT NULL,
            user_avatar VARCHAR(50),
            user_created_at INTEGER UNSIGNED,
            user_deleted_at INTEGER UNSIGNED,
            user_blocked_at INTEGER UNSIGNED,
            user_updated_at INTEGER UNSIGNED,
            user_verified_at INTEGER UNSIGNED,
            user_verification_key CHAR(36),
            PRIMARY KEY(user_pk)
        )
    """)

    cursor.execute("""
        CREATE TABLE items (
            item_pk CHAR(36),
            item_user_fk CHAR(36),
            item_title VARCHAR(50) NOT NULL,
            item_price DECIMAL(5,2) NOT NULL,
            item_description VARCHAR(500),
            item_image VARCHAR(255),
            item_blocked_at INTEGER UNSIGNED,
            PRIMARY KEY(item_pk),
            FOREIGN KEY (item_user_fk) REFERENCES users(user_pk) ON DELETE CASCADE ON UPDATE RESTRICT
        )
    """)

    cursor.execute("""
        CREATE TABLE roles (
            role_pk CHAR(36),
            role_name VARCHAR(10) NOT NULL UNIQUE,
            PRIMARY KEY(role_pk)
        )
    """)

    cursor.execute("""
        CREATE TABLE users_roles (
            user_role_user_fk CHAR(36),
            user_role_role_fk CHAR(36),
            PRIMARY KEY(user_role_user_fk, user_role_role_fk),
            FOREIGN KEY (user_role_user_fk) REFERENCES users(user_pk) ON DELETE CASCADE ON UPDATE RESTRICT,
            FOREIGN KEY (user_role_role_fk) REFERENCES roles(role_pk) ON DELETE CASCADE ON UPDATE RESTRICT
        )
    """)

    #############################    
    q = """
        CREATE TABLE food_categories (
            food_category_pk CHAR(36),
            food_category_name VARCHAR(50) NOT NULL UNIQUE,
            PRIMARY KEY(food_category_pk)
        );
        """        
    cursor.execute(q)

#############################    
    q = """
        CREATE TABLE restaurant_food_category (
            restaurant_food_category_food_category_fk CHAR(36),
            restaurant_food_category_user_fk CHAR(36),
            PRIMARY KEY(restaurant_food_category_food_category_fk, restaurant_food_category_user_fk)
        );
        """        
    cursor.execute(q)
    cursor.execute("ALTER TABLE restaurant_food_category ADD FOREIGN KEY (restaurant_food_category_food_category_fk) REFERENCES food_categories(food_category_pk) ON DELETE CASCADE ON UPDATE RESTRICT")
    cursor.execute("ALTER TABLE restaurant_food_category ADD FOREIGN KEY (restaurant_food_category_user_fk) REFERENCES users(user_pk) ON DELETE CASCADE ON UPDATE RESTRICT")
    #############################
    q = """
        CREATE TABLE restaurant_info (
            restaurant_info_pk CHAR(36),
            restaurant_info_user_fk CHAR(36),
            restaurant_info_restaurant_name VARCHAR(50) NOT NULL,
            restaurant_info_longitude DECIMAL(10, 8) NOT NULL,
            restaurant_info_latitude DECIMAL(10, 8) NOT NULL,
            restaurant_info_restaurant_phone VARCHAR(50) NOT NULL,
            restaurant_info_restaurant_image VARCHAR(50),
            restaurant_info_created_at INTEGER UNSIGNED,
            restaurant_info_updated_at INTEGER UNSIGNED,
            PRIMARY KEY(restaurant_info_pk, restaurant_info_user_fk)
        );
        """
    cursor.execute(q)
    cursor.execute("ALTER TABLE restaurant_info ADD FOREIGN KEY (restaurant_info_user_fk) REFERENCES users(user_pk) ON DELETE CASCADE ON UPDATE RESTRICT")





    ##############################
    # Insert roles
    cursor.execute("""
        INSERT INTO roles (role_pk, role_name)
        VALUES (%s, %s), (%s, %s), (%s, %s), (%s, %s)
    """, (
        x.ADMIN_ROLE_PK, "admin",
        x.CUSTOMER_ROLE_PK, "customer",
        x.PARTNER_ROLE_PK, "partner",
        x.RESTAURANT_ROLE_PK, "restaurant"
    ))

    ##############################
    # Insert admin user
    admin_user = {
        "user_pk": str(uuid.uuid4()),
        "user_name": "Santiago",
        "user_last_name": "Donoso",
        "user_email": "admin@fulldemo.com",
        "user_password": generate_password_hash("password"),
        "user_avatar": "profile_10.jpg",
        "user_created_at": int(time.time()),
        "user_deleted_at": 0,
        "user_blocked_at": 0,
        "user_updated_at": 0,
        "user_verified_at": int(time.time()),
        "user_verification_key": str(uuid.uuid4())
    }
    insert_user_with_role(admin_user, x.ADMIN_ROLE_PK)

    customer_user = {
        "user_pk": str(uuid.uuid4()),
        "user_name": "Customer",
        "user_last_name": "User",
        "user_email": "customer@fulldemo.com",
        "user_password": generate_password_hash("password"),
        "user_avatar": "profile_10.jpg",
        "user_created_at": int(time.time()),
        "user_deleted_at": 0,
        "user_blocked_at": 0,
        "user_updated_at": 0,
        "user_verified_at": int(time.time()),
        "user_verification_key": str(uuid.uuid4())
    }
    insert_user_with_role(customer_user, x.CUSTOMER_ROLE_PK)
    
    partner_user = {
        "user_pk": "542dbb52-17c1-4685-abe7-bebb9d8da70a",
        "user_name": "Partner",
        "user_last_name": "User",
        "user_email": "partner@fulldemo.com",
        "user_password": generate_password_hash("password"),
        "user_avatar": "profile_10.jpg",
        "user_created_at": int(time.time()),
        "user_deleted_at": 0,
        "user_blocked_at": 0,
        "user_updated_at": 0,
        "user_verified_at": int(time.time()),
        "user_verification_key": str(uuid.uuid4())
    }
    insert_user_with_role(partner_user, x.PARTNER_ROLE_PK)

    restaurant_user = {
        "user_pk": str(uuid.uuid4()),
        "user_name": "Restaurant",
        "user_last_name": "User",
        "user_email": "restaurant@fulldemo.com",
        "user_password": generate_password_hash("password"),
        "user_avatar": "profile_10.jpg",
        "user_created_at": int(time.time()),
        "user_deleted_at": 0,
        "user_blocked_at": 0,
        "user_updated_at": 0,
        "user_verified_at": int(time.time()),
        "user_verification_key": str(uuid.uuid4())
    }
    insert_user_with_role(restaurant_user, x.RESTAURANT_ROLE_PK)


    ##############################
    # Insert 50 customers
    domains = ["example.com", "testsite.org", "mydomain.net", "website.co", "fakemail.io"]
    for _ in range(50):
        user = {
            "user_pk": str(uuid.uuid4()),
            "user_name": fake.first_name(),
            "user_last_name": fake.last_name(),
            "user_email": fake.unique.user_name() + "@" + random.choice(domains),
            "user_password": generate_password_hash("password"),
            "user_avatar": "profile_" + str(random.randint(1, 100)) + ".jpg",
            "user_created_at": int(time.time()),
            "user_deleted_at": 0,
            "user_blocked_at": 0,
            "user_updated_at": 0,
            "user_verified_at": random.choice([0, int(time.time())]),
            "user_verification_key": str(uuid.uuid4())
        }
        insert_user_with_role(user, x.CUSTOMER_ROLE_PK)

    ##############################
    # Insert 50 partners
    for _ in range(50):
        user = {
            "user_pk": str(uuid.uuid4()),
            "user_name": fake.first_name(),
            "user_last_name": fake.last_name(),
            "user_email": fake.unique.email(),
            "user_password": generate_password_hash("password"),
            "user_avatar": "profile_" + str(random.randint(1, 100)) + ".jpg",
            "user_created_at": int(time.time()),
            "user_deleted_at": 0,
            "user_blocked_at": 0,
            "user_updated_at": 0,
            "user_verified_at": random.choice([0, int(time.time())]),
            "user_verification_key": str(uuid.uuid4())
        }
        insert_user_with_role(user, x.PARTNER_ROLE_PK)

    ##############################
    # Insert 50 restaurants and their items
    dishes = ["Pizza", "Burger", "Sushi", "Pasta", "Salad"]
    for _ in range(50):
        user = {
            "user_pk": str(uuid.uuid4()),
            "user_name": fake.first_name(),
            "user_last_name": fake.last_name(),
            "user_email": fake.unique.email(),
            "user_password": generate_password_hash("password"),
            "user_avatar": "profile_" + str(random.randint(1, 100)) + ".jpg",
            "user_created_at": int(time.time()),
            "user_deleted_at": 0,
            "user_blocked_at": 0,
            "user_updated_at": 0,
            "user_verified_at": random.choice([0, int(time.time())]),
            "user_verification_key": str(uuid.uuid4())
        }
        insert_user_with_role(user, x.RESTAURANT_ROLE_PK)

        for _ in range(random.randint(5, 15)):
            cursor.execute("""
                INSERT INTO items (item_pk, item_user_fk, item_title, item_price, item_image, item_blocked_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), user["user_pk"], random.choice(dishes),
                round(random.uniform(10, 100), 2), f"dish_{random.randint(1, 100)}.jpg", 0
            ))
    
     ##############################

        SUSHI_CATEGORY_PK = "16bfbe4a-16c1-4cb0-a7b2-090729f78c38"
        PASTA_CATEGORY_PK = "f43b1f39-27f5-4edc-a859-39c2c1ea5ac3"
        BURGER_CATEGORY_PK = "32c83790-34f5-4b86-9bf3-5bffdaa14285"
        PIZZA_CATEGORY_PK = "ba9762b0-793f-417f-a5eb-b46ab53d1eb5"
        SALAD_CATEGORY_PK = "2688be80-6ead-40af-8a36-366607ec0348"

        category_map = {
            "SUSHI": SUSHI_CATEGORY_PK,
            "PASTA": PASTA_CATEGORY_PK,
            "BURGER": BURGER_CATEGORY_PK,
            "PIZZA": PIZZA_CATEGORY_PK,
            "SALAD": SALAD_CATEGORY_PK
        }
    # Create food categories
    categories = ["Pizza", "Pasta", "Sushi", "Burger", "Salad"]
    for category in categories:

        category_pk_variable = category_map[category.upper()]
        cursor.execute("""
        INSERT INTO food_categories (
            food_category_pk, food_category_name)
            VALUES (%s, %s)
        """, (category_pk_variable, category))
    
    ##############################
    
    # Assign one food category to each restaurant user
    cursor.execute("SELECT user_role_user_fk FROM users_roles WHERE user_role_role_fk = %s", (x.RESTAURANT_ROLE_PK,))
    restaurant_users = cursor.fetchall()
    # ic(restaurant_users)
    cursor.execute("SELECT food_category_pk FROM food_categories")
    food_categories = cursor.fetchall()
    for restaurant_user in restaurant_users:
        food_category = random.choice(food_categories)
        cursor.execute("""
        INSERT INTO restaurant_food_category (
            restaurant_food_category_food_category_fk, restaurant_food_category_user_fk)
            VALUES (%s, %s)
        """, (food_category["food_category_pk"], restaurant_user["user_role_user_fk"]))


    ##############################
    # insert into restaurant_info
    copenhagen_lat_range = (55.61, 55.73)
    copenhagen_long_range = (12.48, 12.60)
    cursor.execute("SELECT user_pk FROM users WHERE user_pk IN (SELECT restaurant_food_category_user_fk FROM restaurant_food_category)")
    restaurant_users = cursor.fetchall()
    for restaurant_user in restaurant_users:
        cursor.execute("""
        INSERT INTO restaurant_info (
            restaurant_info_pk, restaurant_info_user_fk, restaurant_info_restaurant_name, restaurant_info_longitude, restaurant_info_latitude, restaurant_info_restaurant_phone, restaurant_info_restaurant_image, restaurant_info_created_at, restaurant_info_updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), restaurant_user["user_pk"], fake.company(), random.uniform(*copenhagen_long_range), random.uniform(*copenhagen_lat_range), fake.phone_number(),f"dish_{random.randint(1, 100)}.jpg", int(time.time()), 0))





    ##############################
    db.commit()
    ic("Data seeded successfully!")

except Exception as ex:
    ic(ex)
    if "db" in locals(): db.rollback()

finally:
    if "cursor" in locals(): cursor.close()
    if "db" in locals(): db.close()