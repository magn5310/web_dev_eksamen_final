from flask import Flask, session, render_template, redirect, url_for, make_response, request, Blueprint, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import x
import uuid 
import time
import redis
import os
import random
from icecream import ic
ic.configureOutput(prefix=f'***** | ', includeContext=True)

app = Flask(__name__, static_folder="static")
app.config['SESSION_TYPE'] = 'filesystem'  # or 'redis', etc.
Session(app)


# app.secret_key = "your_secret_key"

##############################
##############################
##############################

def _________GET_________(): pass

##############################
##############################

##############################
@app.get("/test-set-redis")
def view_test_set_redis():
    redis_host = "redis"
    redis_port = 6379
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)    
    redis_client.set("name", "Santiago", ex=10)
    # name = redis_client.get("name")
    return "name saved"

@app.get("/test-get-redis")
def view_test_get_redis():
    redis_host = "redis"
    redis_port = 6379
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)    
    name = redis_client.get("name")
    if not name: name = "no name"
    return name

##############################
@app.get("/restaurants")
def view_restaurants():
    # make a variable that contains all users that has the role restaurant in the database and pass it to the template 
    db, cursor = x.db()
    q = """ SELECT * FROM restaurant_info """
    cursor.execute(q)
    restaurant_users = cursor.fetchall()
    q = """ SELECT * FROM food_categories"""
    cursor.execute(q)
    food_categories = cursor.fetchall()
    cursor.close()
    db.close()
    user = session.get("user")
    cart = session.get("cart")
    cart_count = len(cart) if cart else 0
    cart_price = 0
    if cart:
        for item in cart:
            cart_price += item["item_price"]
    return render_template("view_restaurants.html", user=user, cart_price=cart_price, cart_count=cart_count, cart=cart, restaurant_users=restaurant_users, food_categories=food_categories)

##############################
@app.get("/explore")
def view_explore():
    # make a variable that contains all users that has the role restaurant in the database and pass it to the template 
    db, cursor = x.db()
    q = """ SELECT * FROM users 
            JOIN users_roles 
            ON user_pk = user_role_user_fk 
            JOIN roles
            ON role_pk = user_role_role_fk
            WHERE role_name = 'restaurant'"""
    cursor.execute(q)
    restaurant_users = cursor.fetchall()
    cursor.close()
    db.close()
    user = session.get("user")
    cart = session.get("cart")
    cart_count = len(cart) if cart else 0
    cart_price = 0
    if cart:
        for item in cart:
            cart_price += item["item_price"]
    return render_template("view_explore.html", user=user, cart_price=cart_price, cart_count=cart_count, cart=cart, restaurant_users=restaurant_users)

##############################
@app.get("/signup")
@x.no_cache
def view_signup():  
    ic(session)
    if session.get("user"):
        if len(session.get("user").get("roles")) > 1:
            return redirect(url_for("view_choose_role")) 
        if "admin" in session.get("user").get("roles"):
            return redirect(url_for("view_admin"))
        if "customer" in session.get("user").get("roles"):
            return redirect(url_for("view_customer")) 
        if "partner" in session.get("user").get("roles"):
            return redirect(url_for("view_partner"))  
        
     
    return render_template("view_signup.html", x=x, title="Signup")



##############################
@app.get("/items/<item_pk>")
def edit_item(item_pk):
    try:
        if not session.get("user"): return redirect(url_for("view_login"))
        if not "restaurant" in session.get("user").get("roles"): return redirect(url_for("view_login"))
        item_pk = x.validate_uuid4(item_pk)

        db, cursor = x.db()
        q = """
            SELECT item_pk, item_title, item_description, item_price, item_image
            FROM items
            WHERE item_pk = %s
        """
        cursor.execute(q, (item_pk,))
        item = cursor.fetchone()
        if not item: return "item not found", 404
        return render_template("view_edit_item.html", item=item, title="Edit Item", x=x)
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): return ex.message, ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "Database under maintenance", 500        
        return "System under maintenance", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()





##############################
@app.get("/login")
@x.no_cache
def view_login():  
    # ic("#"*20, "VIEW_LOGIN")
    ic(session)
    # print(session, flush=True)  
    if session.get("user"):
        if len(session.get("user").get("roles")) > 1:
            return redirect(url_for("view_choose_role")) 
        if "admin" in session.get("user").get("roles"):
            return redirect(url_for("view_admin"))
        if "customer" in session.get("user").get("roles"):
            return redirect(url_for("view_customer")) 
        if "partner" in session.get("user").get("roles"):
            return redirect(url_for("view_partner"))
        if "restaurant" in session.get("user").get("roles"):
            return redirect(url_for("view_index"))

    if session.get("new_user"):
        message=session.get("new_user", "")  
        session.pop("new_user")
        return render_template("view_login.html", x=x, title="Login", message=message)
    return render_template("view_login.html", x=x, title="Login")



##############################
@app.get("/customer")
@x.no_cache
def view_customer():
    if not session.get("user", ""): 
        return redirect(url_for("view_login"))
    user = session.get("user")
    ic(user)
    if "partner" in user["roles"]:
        return redirect(url_for("view_partner"))
    if "resturant" in user["roles"]:
        return redirect(url_for("view_resturant"))
    return render_template("view_customer.html", user=user)

##############################
@app.get("/partner")
@x.no_cache
def view_partner():
    if not session.get("user", ""): 
        return redirect(url_for("view_login"))
    user = session.get("user")
    if len(user.get("roles", "")) < 1:
        return redirect(url_for("view_choose_role"))
    return render_template("view_partner.html", user=user)


##############################
@app.get("/admin")
@x.no_cache
def view_admin():
    try:
        if not session.get("user", ""): 
            return redirect(url_for("view_login"))
        user = session.get("user")
        if not "admin" in user.get("roles", ""):
            return redirect(url_for("view_login"))

        db, cursor = x.db()
        

        return render_template("view_admin.html")
    
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
        
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()
    

##############################
@app.get("/admin/users")
def view_admin_users():

        
    try:
        if not session.get("user", ""): 
            return redirect(url_for("view_login"))
        user = session.get("user")
        if not "admin" in user.get("roles", ""):
            return redirect(url_for("view_login"))

        db, cursor = x.db()
        
        # Get search query from request
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            # Modify query to include search functionality
            q = """
            SELECT * FROM users 
            WHERE CONCAT(user_name, ' ', user_last_name) LIKE %s OR 
            user_email LIKE %s
            """
            search_param = f'%{search_query}%'
            cursor.execute(q, (search_param, search_param))
        else:
            # Original query if no search
            q = "SELECT * FROM users"
            cursor.execute(q)

        users = cursor.fetchall()

        return render_template("view_admin_users.html", users=users, search_query=search_query)
    
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
      
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################
@app.get("/admin/items")
def view_admin_items():        
    try:
        if not session.get("user", ""): 
            return redirect(url_for("view_login"))
        user = session.get("user")
        if not "admin" in user.get("roles", ""):
            return redirect(url_for("view_login"))

        db, cursor = x.db()
        
        # Get search query from request
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            # Modify query to include search functionality
            q = """
            SELECT * FROM items 
            WHERE item_title LIKE %s 
            """
            search_param = f'%{search_query}%'
            cursor.execute(q, (search_param, ))
        else:
            # Original query if no search
            q = "SELECT * FROM items"
            cursor.execute(q)

        items = cursor.fetchall()

        return render_template("view_admin_items.html", user=user, items=items, search_query=search_query)
    
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
      
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()




##############################
@app.get("/items")
@x.no_cache
def view_items():


    if not session.get("user", ""):
        return redirect(url_for("view_login"))
    
    db, cursor = x.db()

    query = """
            SELECT items.item_title, items.item_price,items.item_description, items.item_image, users.user_name AS restaurant_name
            FROM items
            JOIN users ON items.item_user_fk = users.user_pk
            JOIN users_roles ON users.user_pk = users_roles.user_role_user_fk
            WHERE users_roles.user_role_role_fk = %s
        """
    
    cursor.execute(query, (x.RESTAURANT_ROLE_PK,))
    items = cursor.fetchall()

    return render_template("view_items.html", items=items)

##############################
@app.get("/restaurant/items")
def view_restaurant_items():
    try:
        # Ensure the user is logged in
        user = session.get("user")
        if not user:
            x.raise_custom_exception("Please log in to view your items", 401)

        user_pk = user.get("user_pk")

        # Ensure the user has the 'restaurant' role
        if not "restaurant" in user.get("roles"):
            x.raise_custom_exception("You do not have the restaurant role", 401)

        # Fetch items belonging to the current restaurant
        db, cursor = x.db()
        query_items = """
            SELECT item_pk, item_title, item_description, item_price, item_image
            FROM items
            WHERE item_user_fk = %s
        """
        cursor.execute(query_items, (user_pk,))
        items = cursor.fetchall()

        return render_template("view_restaurant_items.html", items=items, title="My Items")

    except Exception as ex:
        ic(ex)
        return "Error retrieving your items", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.get("/verify-partner")
@x.no_cache
def view_verify_partner():

    user = session.get("user")
    if not session.get("user", ""): 
        return redirect(url_for("view_login"))
    if "partner" in user["roles"]:
        return redirect(url_for("view_login"))
    return render_template("view_verify_partner.html", user=user)
    



##############################
@app.get("/items/new")
@x.no_cache
def view_new_item():
    if not session.get("user", ""): 
        return redirect(url_for("view_login"))
    user = session.get("user")
    if not "restaurant" in user.get("roles", ""):
        return redirect(url_for("view_login"))
    return render_template("view_create_item.html", user=user, title="New item", x=x)




##############################
@app.get("/choose-role")
@x.no_cache
def view_choose_role():
    if not session.get("user", ""): 
        return redirect(url_for("view_login"))
    if not len(session.get("user").get("roles")) >= 2:
        return redirect(url_for("view_login"))
    user = session.get("user")
    return render_template("view_choose_role.html", user=user, title="Choose role")

##############################
@app.get("/<user_pk>/items")
def view_customer_restaurant_items(user_pk):
    # make a variable that contains all users that has the role restaurant in the database and pass it to the template 
    random_image = request.args.get("image", default=None)
    db, cursor = x.db()
    q = """ SELECT * FROM items 
            WHERE item_user_fk = %s
            """

    cursor.execute(q, (user_pk,))
    restaurant_items = cursor.fetchall()
    q = """ SELECT * FROM restaurant_info WHERE restaurant_info_user_fk = %s"""
    cursor.execute(q, (user_pk,))
    restaurant_user = cursor.fetchone()
    cursor.close()
    db.close()
    user = session.get("user")
    cart = session.get("cart")
    cart_count = len(cart) if cart else 0
    cart_price = 0
    if cart:
        for item in cart:
            cart_price += item["item_price"]
    return render_template("view_customer_restaurant_items.html", user=user, cart_count=cart_count, cart_price=cart_price, restaurant_items=restaurant_items, restaurant_user=restaurant_user, random_image=random_image)

##############################
@app.get("/item/<item_pk>")
def view_item(item_pk):
    # make a variable that contains all users that has the role restaurant in the database and pass it to the template 
    random_image = request.args.get("image", default=None)
    db, cursor = x.db()
    q = """ SELECT * FROM items 
            WHERE item_pk = %s
            """
    cursor.execute(q, (item_pk,))
    dish_item = cursor.fetchone()
    cursor.close()
    db.close()
    user = session.get("user")
    cart = session.get("cart")
    cart_count = len(cart) if cart else 0
    cart_price = 0
    if cart:
        for item in cart:
            cart_price += item["item_price"]
    return render_template("view_item.html", user=user, dish_item=dish_item, cart=cart, cart_price=cart_price, random_image=random_image, cart_count=cart_count)
##############################

@app.get("/forgot-password")
def view_forgot_password():
    return render_template("view_forgot_password.html", title="Forgot Password")

##############################

@app.get("/reset-password/<user_verification_key>")
def view_reset_password(user_verification_key):
    db, cursor = x.db()
    q = "SELECT * FROM users WHERE user_verification_key = %s"
    cursor.execute(q, (user_verification_key,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404
    return render_template("view_reset_password.html", user_verification_key=user_verification_key, title="Reset Password", x=x)



##############################
@app.get("/restaurant-profile")
@x.no_cache
def view_restaurant_profile():
    try:
        if not session.get("user", ""): 
            return redirect(url_for("view_login"))
        user = session.get("user")
        if not "restaurant" in user.get("roles", ""):
            return redirect(url_for("view_login"))
        db, cursor = x.db()
        query = """
            SELECT user_name, user_email
            FROM users
            WHERE user_pk = %s
        """
        cursor.execute(query, (user.get("user_pk"),))
        user = cursor.fetchone()
        return render_template("view_restaurant_profile.html", user=user, title="Restaurant Profile", x=x)
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        x.ic(ex)
        
        return "Error updating profile", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

        

##############################
@app.get("/restaurant-profile/edit")
@x.no_cache
def view_edit_restaurant_profile():
    if not session.get("user", ""): 
        return redirect(url_for("view_login"))
    user = session.get("user")
    if not "restaurant" in user.get("roles", ""):
        return redirect(url_for("view_login"))
    return render_template("view_edit_restaurant_profile.html", user=user, title="Edit Restaurant Profile", x=x)


##############################
@app.get("/checkout")
def view_checkout():
    user = session.get("user")
    cart = session.get("cart")
    cart_count = len(cart) if cart else 0
    cart_price = 0
    if cart:
        for item in cart:
            cart_price += item["item_price"]
    if not user: 
        return redirect(url_for("view_login"))
    if not cart:
        return redirect(url_for("view_restaurants"))

    return render_template("view_checkout.html", user=user, title="Checkout", cart=cart, cart_price=cart_price, cart_count=cart_count)

##############################
@app.get("/restaurant-profile/delete")
def confirm_delete_restaurant():
    try:
        if not session.get("user"):
            return redirect(url_for("view_login"))
        if not "restaurant" in session.get("user").get("roles"):
            return redirect(url_for("view_login"))
        return render_template("confirm_delete_profile.html", title="Delete Profile", x=x)
    except Exception as ex:
        ic(ex)
        return redirect(url_for("view_index"))
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################
@app.get("/order-confirmed")
def view_order_confirmed():
    x.no_cache
    user = session.get("user")
    cart_items = session.get("cart")
    if not cart_items:
        return redirect(url_for("view_restaurants"))
    session.pop("cart")
    confirmed_template = render_template("view_order_confirmed.html", user=user, cart_items=cart_items, title="Order Confirmed")
    toast = render_template("___toast_success.html", message="Order confirmed. An email has been sent to you")
    return f"""<template mix-target="#checkoutBody" mix-replace>{confirmed_template}</template>
                <template mix-target="#toast" mix-bottom>{toast}</template>
                <template mix-target="#cartBtn" mix-replace></template>"""




##############################
@app.get("/restaurant/<food_category_pk>")
def view_restaurant_by_category(food_category_pk):
    # make a variable that contains all users that has the role restaurant in the database and pass it to the template 

    db, cursor = x.db()
    q = """ SELECT * FROM restaurant_info
            JOIN restaurant_food_category
            ON restaurant_info_user_fk = restaurant_food_category_user_fk
            WHERE restaurant_food_category_food_category_fk = %s 
            """

    cursor.execute(q, (food_category_pk,))
    restaurants = cursor.fetchall()
    q = """ SELECT * FROM food_categories WHERE food_category_pk = %s"""
    cursor.execute(q, (food_category_pk,))
    food_category = cursor.fetchone()
    cursor.close()
    db.close()
    user = session.get("user")
    cart = session.get("cart")
    cart_count = len(cart) if cart else 0
    cart_price = 0
    if cart:
        for item in cart:
            cart_price += item["item_price"]
    return render_template("view_restaurant_by_category.html", user=user, cart_count=cart_count, cart_price=cart_price, restaurants=restaurants, food_category=food_category)



##############################
@app.get("/view-all")
def view_all():
    search_query = request.args.get('search', '').strip()
    db, cursor = x.db()
    if search_query:
        # Modify query to include search functionality
        q = """
        SELECT * FROM restaurant_info 
        WHERE restaurant_info_restaurant_name LIKE %s
        """
        search_param = f'%{search_query}%'
        cursor.execute(q, (search_param,))
        restaurants = cursor.fetchall()
        q = """
        SELECT * FROM items 
        WHERE item_title LIKE %s
        """
        search_param = f'%{search_query}%'
        cursor.execute(q, (search_param,))
        items = cursor.fetchall()
    
    else:
        # Original query if no search
        q = "SELECT * FROM restaurant_info"
        cursor.execute(q)
        restaurants = cursor.fetchall()
        q = "SELECT * FROM items"
        cursor.execute(q)
        items = cursor.fetchall()


    
    return render_template("view_all.html", search_query=search_query, items=items, restaurants=restaurants)
##############################

##############################API_GET_ROUTE##############################
@app.get("/fetch-restaurants")
def fetch_restaurants():
    db, cursor = x.db()
    q = """ SELECT * FROM restaurant_info """
    cursor.execute(q)
    restaurants = cursor.fetchall()
    cursor.close()
    db.close()

    # Return restaurants in JSON format
    return jsonify(restaurants)




##############################
##############################
##############################

def _________POST_________(): pass

##############################
##############################
##############################

##############################
@app.post("/partner-verification/<user_pk>")
def send_partner_verification(user_pk):
    try:
        
        # VALIDATION
        if not session.get("user", ""): 
            return redirect(url_for("view_login"))

        

        user_password = x.validate_user_password()
        

        db, cursor = x.db()
        q = """SELECT * FROM users
            WHERE user_pk = %s 
            """
        cursor.execute(q, (user_pk,))

        user = cursor.fetchone()

        ic(user)

        database_password = user["user_password"]

        if not check_password_hash(database_password, user_password):
            toast = render_template("___toast.html", message="incorrect password")
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>"""

        q = """INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
            VALUES(%s, %s)
            """
        cursor.execute(q,(user["user_pk"], x.PARTNER_ROLE_PK))


        q = """
            SELECT * FROM users
            JOIN users_roles ON user_pk = user_role_user_fk
            JOIN roles ON role_pk = user_role_role_fk
            WHERE LOWER(TRIM(user_email)) = LOWER(TRIM(%s))
        """
        cursor.execute(q, (user["user_email"],))
        rows = cursor.fetchall()

        print("Number of rows found:", len(rows))
        if rows:
            print("Found user details:", rows[0])
        else:
            print("No user found with email:", user["user_email"])
        
        roles = []

        session.pop("user")

        for row in rows:
            roles.append(row["role_name"])
        user = {
            "user_pk": rows[0]["user_pk"],
            "user_name": rows[0]["user_name"],
            "user_last_name": rows[0]["user_last_name"],
            "user_email": rows[0]["user_email"],
            "user_avatar": rows[0]["user_avatar"],
            "roles": roles
        }
        ic(user)

        session["user"] = user

        db.commit()

        return """<template mix-redirect="/partner"></template>"""
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
      
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()








##############################
@app.post("/logout")

def logout():
    # ic("#"*30)
    # ic(session)
    session.pop("user", None)
    session.clear()
    # session.clear()
    # session.modified = True
    # ic("*"*30)
    # ic(session)
    return redirect(url_for("view_login"))

##############################
@app.post("/reset-password/<user_verification_key>")
def reset_password(user_verification_key):
    try:
        user_password = x.validate_user_password()
        user_confirm_new_password = x.validate_user_confirm_new_password()
        user_verification_key = x.validate_uuid4(user_verification_key)
        hashed_password = generate_password_hash(user_password)

        if user_password != user_confirm_new_password:
            x.raise_custom_exception("passwords do not match", 400)


        db, cursor = x.db()
        q = "UPDATE users SET user_password = %s WHERE user_verification_key = %s"
        cursor.execute(q, (hashed_password, user_verification_key))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot reset password", 400)
        db.commit()
        toast = render_template("___toast_success.html", message="password reset")
        return f"""<template mix-target="#toast" mix-bottom>{toast}</template>"""
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        toast = render_template("___toast.html", message="Error resetting password")
        return f"""<template mix-target="#toast" mix-bottom>{toast}</template>"""
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()




##############################
@app.post("/forgot-password/")
def forgot_password():
    try:
        user_email = x.validate_user_email()
        db, cursor = x.db()

        q = "SELECT * FROM users WHERE user_email = %s"
        cursor.execute(q, (user_email,))
        user = cursor.fetchone()
        if not user:
            return "user not found", 404
        x.send_forgot_password(user_email, user["user_verification_key"])
        toast = render_template("___toast.html", message="email sent")
        return f"""<template mix-target="#toast" mix-bottom>{toast}</template>"""
    except Exception as ex:
        ic(ex)
        return "error sending email", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.post("/users")
@x.no_cache
def signup():
    try:
        user_name = x.validate_user_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()
        user_password = x.validate_user_password()
        hashed_password = generate_password_hash(user_password)
        
        user_pk = str(uuid.uuid4())
        user_avatar = "profile_" + str(random.randint(1, 100)) + ".jpg"
        user_created_at = int(time.time())
        user_deleted_at = 0
        user_blocked_at = 0
        user_updated_at = 0
        user_verified_at = 0
        user_verification_key = str(uuid.uuid4())
        db, cursor = x.db()
        q = 'INSERT INTO users VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(q, (user_pk, user_name, user_last_name, user_email, 
                           hashed_password, user_avatar, user_created_at, user_deleted_at, user_blocked_at, 
                           user_updated_at, user_verified_at, user_verification_key))
        
        

        x.send_verify_email(user_email, user_verification_key)

        q = "INSERT INTO users_roles VALUES(%s, %s)"
        cursor.execute(q,(user_pk, x.CUSTOMER_ROLE_PK))
    
        db.commit()

        session["new_user"] = "A verification email has been sent to you"
        
        return f"""
        <template mix-redirect="/login"></template>
        """, 201
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex): 
                toast = render_template("___toast.html", message="email not available")
                return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", 400
            return f"""<template mix-target="#toast" mix-bottom>System upgrading</template>""", 500        
        return f"""<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.post("/login")
def login():
    try:

        user_email = x.validate_user_email()
        user_password = x.validate_user_password()


        db, cursor = x.db()

        q = """
            SELECT * FROM users
            JOIN users_roles ON user_pk = user_role_user_fk
            JOIN roles ON role_pk = user_role_role_fk
            WHERE LOWER(TRIM(user_email)) = LOWER(TRIM(%s))
        """
        cursor.execute(q, (user_email,))
        rows = cursor.fetchall()

        print("Number of rows found:", len(rows))
        if rows:
            print("Found user details:", rows[0])
        else:
            print("No user found with email:", user_email)

        if not rows[0]["user_verified_at"]:
            toast = render_template("___toast.html", message="Please verify your account")
            return f"""<template mix-target="#toast">{toast}</template>""", 400     

        if not rows:
            toast = render_template("___toast.html", message="user not registered")
            return f"""<template mix-target="#toast">{toast}</template>""", 400     
        if not check_password_hash(rows[0]["user_password"], user_password):
            toast = render_template("___toast.html", message="invalid credentials")
            return f"""<template mix-target="#toast">{toast}</template>""", 401
        
        roles = []
        for row in rows:
            roles.append(row["role_name"])
        user = {
            "user_pk": rows[0]["user_pk"],
            "user_name": rows[0]["user_name"],
            "user_last_name": rows[0]["user_last_name"],
            "user_email": rows[0]["user_email"],
            "user_avatar": rows[0]["user_avatar"],
            "roles": roles
        }
        ic(user)

        session["user"] = user

        if len(roles) == 1:
            return f"""<template mix-redirect="/{roles[0]}"></template>"""
        return f"""<template mix-redirect="/choose-role"></template>"""
        # db.commit()
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
      
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################





##############################
# @app.post("/login")
# def login():
#     try:

#         user_email = x.validate_user_email()
#         user_password = x.validate_user_password()

#         db, cursor = x.db()
#         q = """ SELECT * FROM users 
#                 JOIN users_roles 
#                 ON user_pk = user_role_user_fk 
#                 JOIN roles
#                 ON role_pk = user_role_role_fk
#                 WHERE user_email = %s"""
#         cursor.execute(q, (user_email,))
#         rows = cursor.fetchall()
#         ic(rows)
#         if not rows:
#             toast = render_template("___toast.html", message="user not registered")
#             return f"""<template mix-target="#toast">{toast}</template>""", 400     
#         if not check_password_hash(rows[0]["user_password"], user_password):
#             toast = render_template("___toast.html", message="invalid credentials")
#             return f"""<template mix-target="#toast">{toast}</template>""", 401
#         roles = []
#         for row in rows:
#             roles.append(row["role_name"])
#         user = {
#             "user_pk": rows[0]["user_pk"],
#             "user_name": rows[0]["user_name"],
#             "user_last_name": rows[0]["user_last_name"],
#             "user_email": rows[0]["user_email"],
#             "roles": roles
#         }
#         ic(user)
#         session["user"] = user
#         if len(roles) == 1:
#             return f"""<template mix-redirect="/{roles[0]}"></template>"""
#         return f"""<template mix-redirect="/choose-role"></template>"""
#     except Exception as ex:
#         ic(ex)
#         if "db" in locals(): db.rollback()
#         if isinstance(ex, x.CustomException): 
#             toast = render_template("___toast.html", message=ex.message)
#             return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code    
#         if isinstance(ex, x.mysql.connector.Error):
#             ic(ex)
#             return "<template>System upgrating</template>", 500        
#         return "<template>System under maintenance</template>", 500  
#     finally:
#         if "cursor" in locals(): cursor.close()
#         if "db" in locals(): db.close()



##############################
@app.post("/items")
def create_item():
    try:

        # check if user has the role restaurant
        if not session.get("user"): 
            return redirect(url_for("view_login"))
        if not "restaurant" in session.get("user").get("roles"): 
            return redirect(url_for("view_login"))


        # TODO: validate item_title, item_description, item_price
        item_title = x.validate_item_title()
        item_description = x.validate_item_description()
        item_price = x.validate_item_price()
        file, item_image_name = x.validate_item_image()

        # Save the image
        file.save(os.path.join(x.UPLOAD_ITEM_FOLDER, item_image_name))
        # TODO: if saving the image went wrong, then rollback by going to the exception
        if not item_image_name:
            x.raise_custom_exception("cannot save image", 500)
        


        item_pk = str(uuid.uuid4())
        item_user_fk = session.get("user").get("user_pk")
        

        db, cursor = x.db()

        q = """
            INSERT INTO items (item_pk, item_user_fk, item_title, item_description, item_price, item_image)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(q, (item_pk, item_user_fk, item_title, item_description, item_price, item_image_name))
        db.commit()
        toast = render_template("___toast_success.html", message="item created")


        # TODO: Success, commit

        return f"""<template>item created</template>
        <template mix-target="#toast" mix-bottom>{toast}</template>
        
        
        """, 201
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>System upgrating</template>", 500        
        return "<template>System under maintenance</template>", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()    


##############################

##############################
@app.post("/set-item-cookie/<item_pk>")
def set_item_cookie(item_pk):
    try:
        item_pk = x.validate_uuid4(item_pk)
        db, cursor = x.db()
        q = "SELECT * FROM items WHERE item_pk = %s"
        cursor.execute(q, (item_pk,))
        item = cursor.fetchone()
        if 'cart' not in session:
            # If not, create a new list with the current item
            session['cart'] = [item]
        else:
            # If it exists, append the new item to the list
            session['cart'].append(item)
        cart = session.get("cart")
        cart_count = len(cart) if cart else 0
        cart_price = 0
        if cart:
            for item in cart:
                cart_price += item["item_price"]
        toast = render_template("___toast_success.html", message="Item added to cart")
        cartBtn = render_template("__cart_button.html", cart_count=cart_count, cart_price=cart_price)
        return f"""<template mix-target="#toast" mix-bottom>{toast}</template>
                   <template mix-target="#cartBtn" mix-replace>{cartBtn}</template>
                    """
    except Exception as ex:
        ic(ex)
        return "Error setting cookie", 500


##############################
@app.post("/pay-now/<user_pk>")
def send_order_email(user_pk):
    try:
        user_pk = x.validate_uuid4(user_pk)
        db, cursor = x.db()
        q = "SELECT * FROM users WHERE user_pk = %s"
        cursor.execute(q, (user_pk,))
        user = cursor.fetchone()
        toast = render_template("___toast_success.html", message="An email has been sent to you with your order details.")
        x.send_order_email()
        return redirect(url_for("view_order_confirmed"))
    except Exception as ex:
        ic(ex)
        return "Error sending mail", 500


##############################
##############################
##############################

def _________PUT_________(): pass

##############################
##############################
##############################

##############################

@app.put("/users")
def user_update():
    try:
        if not session.get("user"): x.raise_custom_exception("please login", 401)

        user_pk = session.get("user").get("user_pk")
        user_name = x.validate_user_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()

        user_updated_at = int(time.time())

        db, cursor = x.db()
        q = """ UPDATE users
                SET user_name = %s, user_last_name = %s, user_email = %s, user_updated_at = %s
                WHERE user_pk = %s
            """
        cursor.execute(q, (user_name, user_last_name, user_email, user_updated_at, user_pk))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot update user", 401)
        db.commit()
        return """<template>user updated</template>"""
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            if "users.user_email" in str(ex): return "<template>email not available</template>", 400
            return "<template>System upgrating</template>", 500        
        return "<template>System under maintenance</template>", 500    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.put("/users/block/<user_pk>")
def user_block(user_pk):
    try:        
        if not "admin" in session.get("user").get("roles"): return redirect(url_for("view_login"))
        user_pk = x.validate_uuid4(user_pk)
        user_blocked_at = int(time.time())
        db, cursor = x.db()
        q = 'UPDATE users SET user_blocked_at = %s WHERE user_pk = %s'
        cursor.execute(q, (user_blocked_at, user_pk))

        q="SELECT * FROM users WHERE user_pk = %s"
        cursor.execute(q, (user_pk,))

        user=cursor.fetchone()

        ic(user)

        if cursor.rowcount != 1: x.raise_custom_exception("cannot block user", 400)
        x.send_block_email(user["user_email"], "blocked", "account")
        db.commit()
        unblock=render_template("___btn_unblock_user.html", user=user)
        return f"""<template mix-target="#block-{user_pk}" mix-replace>{unblock}</template>"""
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.put("/items/block/<item_pk>")
def item_block(item_pk):
    try:
        if not "admin" in session.get("user").get("roles"):
            return redirect(url_for("view_login"))
        
        item_pk = x.validate_uuid4(item_pk)
        item_blocked_at = int(time.time())
        
        db, cursor = x.db()
        
        # Update the item as blocked
        q = 'UPDATE items SET item_blocked_at = %s WHERE item_pk = %s'
        cursor.execute(q, (item_blocked_at, item_pk))
        
        # Join items and users to get the user's email
        q = '''
        SELECT users.user_email 
        FROM items 
        JOIN users ON items.item_user_fk = users.user_pk 
        WHERE items.item_pk = %s
        '''
        cursor.execute(q, (item_pk,))
        
        # Fetch the user's email
        item_with_email = cursor.fetchone()
        
        # Verify the item exists and was blocked
        if cursor.rowcount != 1:
            x.raise_custom_exception("cannot block user", 400)
        
        x.send_block_email(item_with_email['user_email'], "blocked", "item")
        
        db.commit()
        
        unblock = render_template("___btn_unblock_item.html", item=item_with_email)
        return f"""<template mix-target="#block-{item_pk}" mix-replace>{unblock}</template>"""
    
    except Exception as ex:
        ic(ex)
        if "db" in locals():
            db.rollback()
        
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500
        
        return "<template>System under maintenance</template>", 500
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

##############################
@app.put("/users/unblock/<user_pk>")
def user_unblock(user_pk):
    try:
        if not "admin" in session.get("user").get("roles"): return redirect(url_for("view_login"))
        user_pk = x.validate_uuid4(user_pk)
        user_blocked_at = 0
        db, cursor = x.db()
        q = 'UPDATE users SET user_blocked_at = %s WHERE user_pk = %s'
        cursor.execute(q, (user_blocked_at, user_pk))

        q="SELECT * FROM users WHERE user_pk = %s"
        cursor.execute(q, (user_pk,))

        user=cursor.fetchone()
        if cursor.rowcount != 1: x.raise_custom_exception("cannot unblock user", 400)
        x.send_block_email(user["user_email"], "unblocked", "account")
        db.commit()
        block=render_template("___btn_block_user.html", user=user)
        return f"""<template mix-target="#unblock-{user_pk}" mix-replace>{block}</template>"""
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.put("/restaurant-profile/delete")
def delete_restaurant():
    try:
        if not session.get("user"):
            return redirect(url_for("view_login"))
        if not "restaurant" in session.get("user").get("roles"): 
            return redirect(url_for("view_login"))
        
        user_pk = session.get("user").get("user_pk")
        user_email = session.get("user").get("user_email")
        
        password = x.validate_user_password()

        if not password:
            x.raise_custom_exception("password is required", 400)


        db, cursor = x.db()
        cursor.execute("SELECT user_password FROM users WHERE user_pk = %s", (user_pk,))
        user = cursor.fetchone()
        if not user:
            x.raise_custom_exception("user not found", 404)

        if not check_password_hash(user["user_password"], password):
            x.raise_custom_exception("invalid password", 401)
        
        user_deleted_at = int(time.time())
        q = 'UPDATE users SET user_deleted_at = %s WHERE user_pk = %s'
        cursor.execute(q, (user_deleted_at, user_pk))
        if cursor.rowcount != 1:
            x.raise_custom_exception("cannot delete restaurant", 400)
        

        db.commit()
        x.send_deletion_email(user_email)
        session.pop("user", None)
        return f"""
        <template mix-redirect="/login"></template>
"""
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): return ex.message, ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "Database under maintenance", 500        
        return "System under maintenance", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()






##############################
@app.put("/items/unblock/<item_pk>")
def item_unblock(item_pk):
    try:
        if not "admin" in session.get("user").get("roles"): 
            return redirect(url_for("view_login"))
        
        item_pk = x.validate_uuid4(item_pk)
        item_blocked_at = 0
        
        db, cursor = x.db()
        
        # Update the item as unblocked
        q = 'UPDATE items SET item_blocked_at = %s WHERE item_pk = %s'
        cursor.execute(q, (item_blocked_at, item_pk))

        # Query to get both item and user email
        q = '''
        SELECT items.*, users.user_email 
        FROM items 
        JOIN users ON items.item_user_fk = users.user_pk 
        WHERE items.item_pk = %s
        '''
        cursor.execute(q, (item_pk,))

        # Fetch the item and user details
        item_with_email = cursor.fetchone()
        
        if cursor.rowcount != 1: 
            x.raise_custom_exception("cannot unblock user", 400)
        
        x.send_block_email(item_with_email["user_email"], "unblocked", "item")
        
        db.commit()
        
        block = render_template("___btn_block_item.html", item=item_with_email)
        return f"""<template mix-target="#unblock-{item_pk}" mix-replace>{block}</template>"""
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): 
            db.rollback()
        
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        
        return "<template>System under maintenance</template>", 500  
    
    finally:
        if "cursor" in locals(): 
            cursor.close()
        if "db" in locals(): 
            db.close()


##############################
@app.put("/items/<item_pk>/edit")
@x.no_cache
def update_item(item_pk):
    try:
        # Ensure the user is logged in
        if not session.get("user", ""): 
            return redirect(url_for("view_login"))
        
        # Ensure the user has the 'restaurant' role
        if not "restaurant" in session.get("user").get("roles", ""):
            return redirect(url_for("view_login"))
        
        # Validate the item title, description, and price
        item_title = x.validate_item_title()
        item_description = x.validate_item_description()
        item_price = x.validate_item_price()
        
        # Validate the image
        file, item_image_name = x.validate_item_image()
        file.save(os.path.join(x.UPLOAD_ITEM_FOLDER, item_image_name))
        if not item_image_name:
            x.raise_custom_exception("Cannot save image", 500)
        
        # Update the item in the database
        db, cursor = x.db()
        q = """
            UPDATE items
            SET item_title = %s, item_description = %s, item_price = %s, item_image = %s
            WHERE item_pk = %s
        """
        cursor.execute(q, (item_title, item_description, item_price, item_image_name, item_pk))
        if cursor.rowcount != 1:
            x.raise_custom_exception("Cannot update item", 400)
        db.commit()
        
        # Return a success message
        toast = render_template("___toast_success.html", message="Item updated")
        return f"""
        <template mix-target="#toast" mix-bottom>{toast}</template>
        """
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500
        return "<template>System under maintenance</template>", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################

@app.put("/profile/edit")
def update_profile():
    try:
        user = session.get("user")
        if not user:
            x.raise_custom_exception("Please log in to edit your profile", 401)

        user_pk = user.get("user_pk")

        # Get form data
        user_name = x.validate_user_name()
        user_email = x.validate_user_email()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")


        db, cursor = x.db()
        # Fetch current user data
        cursor.execute("""
            SELECT user_password, user_email, user_name
            FROM users
            WHERE user_pk = %s
        """, (user_pk,))
        user_data = cursor.fetchone()

        if not user_data:
            x.raise_custom_exception("User not found", 404)

        # Validate and update email
        if user_email != user_data['user_email']:
            if not x.validate_email(user_email):
                x.raise_custom_exception("Invalid email address", 400)
            # Check if email is already taken
            cursor.execute("SELECT user_pk FROM users WHERE user_email = %s", (user_email,))
            if cursor.fetchone():
                x.raise_custom_exception("Email is already in use", 400)

        # Validate and update name

        # Update password if provided
        if new_password:
            if not current_password:
                x.raise_custom_exception("Current password is required to change your password", 400)
            if not check_password_hash(user_data['user_password'], current_password):
                x.raise_custom_exception("Current password is incorrect", 401)
            if new_password != confirm_password:
                x.raise_custom_exception("New passwords do not match", 400)
            if not x.validate_new_user_password(new_password):
                x.raise_custom_exception("Password does not meet requirements", 400)
            new_password_hash = generate_password_hash(new_password)
        else:
            new_password_hash = user_data['user_password']  # Keep the old password

        # Update user data in the database
        cursor.execute("""
            UPDATE users
            SET user_name = %s, user_email = %s, user_password = %s
            WHERE user_pk = %s
        """, (user_name, user_email, new_password_hash, user_pk))
        db.commit()

        # Update session data
        session['user']['user_name'] = user_name
        session['user']['user_email'] = user_email

        toast = render_template("___toast_success.html", message="Profile updated")
        return f"""
        <template mix-target="#toast" mix-bottom>{toast}</template>
"""

    except Exception as ex:
        if "db" in locals():
            db.rollback()
        x.ic(ex)
        
        return "Error updating profile", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()




##############################
##############################
##############################

def _________DELETE_________(): pass

##############################
##############################
##############################


@app.delete("/users/<user_pk>")
def user_delete(user_pk):
    try:
        # Check if user is logged
        if not session.get("user", ""): return redirect(url_for("view_login"))
        # Check if it is an admin
        if not "admin" in session.get("user").get("roles"): return redirect(url_for("view_login"))
        user_pk = x.validate_uuid4(user_pk)
        user_deleted_at = int(time.time())
        db, cursor = x.db()
        q = 'UPDATE users SET user_deleted_at = %s WHERE user_pk = %s'
        cursor.execute(q, (user_deleted_at, user_pk))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot delete user", 400)
        db.commit()
        session.pop("user", None)
        return """<template>user deleted</template>"""
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################

@app.delete("/items/<item_pk>")
def delete_item(item_pk):
    try:
        if not session.get("user"):
            return redirect(url_for("view_login"))
        if not "restaurant" in session.get("user").get("roles"): 
            return redirect(url_for("view_login"))
        item_pk = x.validate_uuid4(item_pk)
        db, cursor = x.db()
        q = 'DELETE FROM items WHERE item_pk = %s'
        cursor.execute(q, (item_pk,))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot delete item", 400)
        db.commit()
        return f"""
        <template mix-redirect="/restaurant/items"></template>"""
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): return ex.message, ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "Database under maintenance", 500        
        return "System under maintenance", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################



##############################
##############################
##############################

def _________BRIDGE_________(): pass

##############################
##############################
##############################
    




##############################
@app.get("/verify/<verification_key>")
@x.no_cache
def verify_user(verification_key):
    try:
        ic(verification_key)
        verification_key = x.validate_uuid4(verification_key)
        user_verified_at = int(time.time())

        db, cursor = x.db()
        q = """ UPDATE users 
                SET user_verified_at = %s 
                WHERE user_verification_key = %s"""
        cursor.execute(q, (user_verified_at, verification_key))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot verify account", 400)
        db.commit()
        return redirect(url_for("view_login", message="User verified, please login"))

    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): return ex.message, ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "Database under maintenance", 500        
        return "System under maintenance", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()    






