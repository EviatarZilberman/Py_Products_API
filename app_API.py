from flask import Flask, request, jsonify

from Enums.LogLevels import LogLevel
from Global import Global_methods
from DataModels.Product import Product
from DataModels.User import User
from MongoDbManager.MongoDbSingleton import MongoDbSingleton
from Models.Writer import Writer

app_api = Flask(__name__)
path = r'C:\Users\User\Projects\Logs'
log_file = 'Product_Logs.log'


@app_api.route("/add_product", methods = ['POST'])
def add_product():
    data = request.get_json()
    product_data = data["form"]
    user_id = data["user_id"]
    try:
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton("E_Commerce", "Users")
        dictionary = db_manager.find_one_by_key_value("_id", user_id)
        user = User.from_dict(dictionary)
        product = Product.from_dict(product_data)
        product_id = str(product.internal_id)
        product.internal_id = product_id
        new_sections = []
        if isinstance(product.section, list):
            for section in product.section:
                modified_section = section.name
                new_sections.append(modified_section)
            product.m_section = new_sections

        else:
            new_sections.append(product.section)
        if user.products_for_sell is None:
            user.products_for_sell = list()
        user.products_for_sell.append(product.internal_id)
        db_manager.replace_member(user)
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton("E_Commerce", "Products")

        db_manager.insert(product)
        MongoDbSingleton.reinitialize()

        return jsonify(), 201

    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


@app_api.route("/delete_product", methods = ['DELETE'])
async def delete_product():
    data = request.get_json()
    product_id = data["product_id"]
    user_id = data["user_id"]
    try:
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton("E_Commerce", "Users")
        dictionary = db_manager.find_one_by_key_value("_id", user_id)
        user = User.from_dict(dictionary)
        user.products_for_sell = [p for p in user.products_for_sell if p != product_id]
        db_manager.replace_member(user)

        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton("E_Commerce", "Products")
        await db_manager.delete_by_id(product_id)
        MongoDbSingleton.reinitialize()

        return jsonify(), 200

    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        MongoDbSingleton.reinitialize()

        return jsonify(), 500


@app_api.route("/my_store", methods = ['POST'])
def my_store():
    data = request.get_json()
    user_id = data["user_id"]
    try:
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton("E_Commerce", "Products")
        products_id_list = db_manager.find_by_key_value("owner_id", user_id)
        return jsonify(products_id_list), 200
    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


@app_api.route("/search_products", methods=['POST']) # Returns a list of products that are not owned by the searcher.
def search_products():
    data = request.get_json()
    user_id = data["user_id"]
    form = data["form"]
    keys_words = form["search_query"]
    try:
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton("E_Commerce", "Products")
        products_dict = db_manager.find_all()
        products_list = list()
        keys_list = Product.initialize_search_keys(keys_words)
        for item in products_dict:
            products_list.append(Product.from_dict(item))

        for product in products_list:
            if product.owner_id == user_id:
                products_list.remove(product)
            try:
                if not Global_methods.compare_lists(keys_list, product.search_keys):
                    products_list.remove(product)
            except:
                continue
        if len(products_list) > 1:
            products_list.sort(key = lambda x: x.section)
        serialized_products = [product.to_dict() for product in products_list]

        return jsonify(serialized_products), 200
    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


# @app_api.route("/my_cart", methods = ['POST'])
# def my_cart():
#     data = request.get_json()
#     user_id = data["user_id"]
#     try:
#         MongoDbSingleton.reinitialize()
#         user = User.from_dict(MongoDbSingleton("E_Commerce", "User").find_one_by_key_value('_id', user_id))
#         products_id_list =
#
#             db_manager.find_by_key_value("owner_id", user_id)
#         return jsonify(products_id_list), 200
#     except Exception as e:
#         Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
#         return jsonify(), 500


@app_api.route("/add_product_to_cart", methods=['POST'])
def add_product_to_cart():
    data = request.get_json()
    user_id = data["user_id"]
    product_id = data["product_id"]
    try:
        MongoDbSingleton.reinitialize()
        user = User.from_dict(MongoDbSingleton('E_Commerce', 'User').find_one_by_key_value('_id', user_id))
        if user.cart is None:
            user.cart = list()
        user.cart.append(product_id)
        # MongoDbSingleton('E_Commerce', 'User').update_member(user_id, 'cart', user.cart)
        MongoDbSingleton('E_Commerce', 'User').replace_member(user)
        return jsonify(), 200

    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


if __name__ == "__main__":
    app_api.run(port = 9997, debug = True)

