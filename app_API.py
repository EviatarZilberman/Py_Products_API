from flask import Flask, request, jsonify
from DataModels.Product import Product
from DataModels.User import User
from MongoDbManager import MongoDbSingleton

app_api = Flask(__name__)
path = r'C:\Users\User\Projects\Py_Products_API\logs'
log_file = 'Products.log'


@app_api.route("/add_product", methods = ['POST'])
def add_product():
    data = request.get_json()
    product_data = data["form"]
    user_id = data["user_id"]
    try:
        db_manager = MongoDbSingleton.MongoDbSingleton("E_Commerce", "Users")
        dictionary = db_manager.find_one_by_key_value("_id", user_id)
        user = User.from_dict(dictionary)
        product = Product.from_dict(product_data)
        product_id = str(product.m_internal_id)
        product.m_internal_id = product_id
        new_sections = []
        for section in product.m_section:
            modified_section = section.name
            new_sections.append(modified_section)
        product.m_section = new_sections
        if user.m_products_for_sell is None:
            user.m_products_for_sell = list()

        user.m_products_for_sell.append(product.m_internal_id)
        db_manager.replace_member(user)
        MongoDbSingleton.MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton.MongoDbSingleton("E_Commerce", "Products")

        db_manager.insert(product)
        MongoDbSingleton.MongoDbSingleton.reinitialize()

        return jsonify(), 201

    except Exception as e:
        print(str(e))
        return jsonify(), 500


@app_api.route("/delete_product", methods = ['POST'])
def delete_product():
    data = request.get_json()
    product_data = data["form"]
    user_id = data["user_id"]
    try:
        db_manager = MongoDbSingleton.MongoDbSingleton("E_Commerce", "Users")
        dictionary = db_manager.find_one_by_key_value("_id", user_id)
        user = User.from_dict(dictionary)
        product = Product.from_dict(product_data)
        for product_id in user.m_products_for_sell:
            if product_id == product:
                user.m_products_for_sell.pop()
        db_manager.replace_member(user)

        MongoDbSingleton.MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton.MongoDbSingleton("E_Commerce", "Products")
        db_manager.delete_by_id(product)
        return jsonify(), 200

    except:
        # writer = Writer(r'C:\Users\User\Projects\Logs', 'Products.log')
        # writer.write_log(str(e), 'f')
        return jsonify(), 500


@app_api.route("/my_store", methods = ['POST'])
def my_store():
    data = request.get_json()
    user_id = data["user_id"]
    try:
        db_manager = MongoDbSingleton.MongoDbSingleton("E_Commerce", "Products")
        products_id_list = db_manager.find_by_key_value("owner_id", user_id)
        return jsonify(products_id_list), 200
    except:
        return jsonify(), 500


if __name__ == "__main__":
    app_api.run(port = 9997, debug = True)

