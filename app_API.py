from flask import Flask, request, jsonify

from DataModels.CartProduct import CartProduct
from Enums.LogLevels import LogLevel
from Enums.ProductStatus import ProductStatus
from Global import Global_methods
from DataModels.Product import Product
from DataModels.User import User
from MongoDbManager.MongoDbSingleton import MongoDbSingleton
from Models.Writer import Writer

app_api = Flask(__name__)
path = r'C:\Users\User\Projects\Logs'
log_file = 'Product_Logs.log'


@app_api.route('/add_product', methods = ['POST'])
def add_product():
    data = request.get_json()
    product_data = data['form']
    user_id = data['user_id']
    try:
        MongoDbSingleton.reinitialize()
        dictionary = MongoDbSingleton('E_Commerce', 'Users').find_one_by_key_value('_id', user_id)
        user = User.from_dict(dictionary)
        owner_id = product_data['owner_id']
        title = product_data['title']
        price = product_data['price']
        section = product_data['section']
        description = product_data['description']
        available_for_sale = product_data['available_for_sale']
        product_status = product_data['product_status']
        pictures = product_data['pictures']
        if pictures == '':
            pictures = None
        product = Product(owner_id, price,
                          title,
                          section, description,
                          available_for_sale,
                          product_status,
                          pictures)
        product_id = str(product.internal_id)
        product.internal_id = product_id
        new_sections = []
        if isinstance(product.section, list):
            for section in product.section:
                modified_section = str(section)
                new_sections.append(modified_section)
            product.section = new_sections

        else:
            new_sections.append(product.section)
        if user.products_for_sell is None:
            user.products_for_sell = list()
        user.products_for_sell.append(product.internal_id)
        MongoDbSingleton.reinitialize()
        MongoDbSingleton('E_Commerce', 'Users').replace_member(user)
        MongoDbSingleton.reinitialize()
        MongoDbSingleton('E_Commerce', 'Products').insert(product)
        MongoDbSingleton.reinitialize()

        return jsonify(), 201

    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


@app_api.route('/delete_product', methods = ['DELETE'])
async def delete_product():
    data = request.get_json()
    product_id = data['product_id']
    user_id = data['user_id']
    try:
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton('E_Commerce', 'Users')
        dictionary = db_manager.find_one_by_key_value('_id', user_id)
        user = User.from_dict(dictionary)
        user.products_for_sell = [p for p in user.products_for_sell if p != product_id]
        db_manager.replace_member(user)

        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton('E_Commerce', 'Products')
        await db_manager.delete_by_id(product_id)
        MongoDbSingleton.reinitialize()

        return jsonify(), 200

    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        MongoDbSingleton.reinitialize()

        return jsonify(), 500


@app_api.route('/my_store', methods = ['POST'])
def my_store():
    data = request.get_json()
    user_id = data['user_id']
    try:
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton('E_Commerce', 'Products')
        products_id_list = db_manager.find_by_key_value('owner_id', user_id)
        return jsonify(products_id_list), 200
    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


@app_api.route('/search_products', methods=['POST']) # Returns a list of products that are not owned by the searcher.
def search_products():
    data = request.get_json()
    user_id = data['user_id']
    form = data['form']
    keys_words = form['search_query']
    try:
        MongoDbSingleton.reinitialize()
        db_manager = MongoDbSingleton('E_Commerce', 'Products')
        products_dict = db_manager.find_all()
        products_list = list()
        keys_list = Product.initialize_search_keys(keys_words)
        for item in products_dict:
            products_list.append(Product.from_dict(item))
        filtered_list = [product for product in products_list if product.owner_id != user_id and product.product_status == ProductStatus.DISPLAY and Global_methods.compare_lists(keys_list, product.search_keys)]

        if len(products_list) > 1:
            products_list.sort(key = lambda x: x.section)
        serialized_products = [product.to_dict() for product in filtered_list]

        return jsonify(serialized_products), 200
    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


@app_api.route('/add_product_to_cart', methods=['POST'])
def add_product_to_cart():
    data = request.get_json()
    user_id = data['user_id']
    form = data['form']
    product_id = form['item_internal_id']
    count = form['quantity']
    try:
        dictionary = MongoDbSingleton('E_Commerce', 'Users').find_one_by_key_value('_id', user_id)
        user = User.from_dict(dictionary)
        if user.cart is None:
            user.cart = list()
        user.clear_list()
        for item in user.cart:
            if item.product_id == product_id:
                user.cart.remove(item)
                user.cart.append(CartProduct(product_id, count))
                MongoDbSingleton('E_Commerce', 'Users').replace_member(user)
                return jsonify(), 200

        user.cart.append(CartProduct(product_id, count))
        # MongoDbSingleton('E_Commerce', 'User').update_member(user_id, 'cart', user.cart)
        MongoDbSingleton.reinitialize()
        MongoDbSingleton('E_Commerce', 'Users').replace_member(user)
        return jsonify(), 200

    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


@app_api.route('/my_cart', methods=['POST'])
def my_cart():
    data = request.get_json()
    user_id = data['user_id']
    try:
        MongoDbSingleton.reinitialize()
        dictionary = MongoDbSingleton('E_Commerce', 'Users').find_one_by_key_value('_id', user_id)
        user = User.from_dict(dictionary)
        if user.cart is None or len(user.cart) == 0:
            return jsonify(), 200
        MongoDbSingleton.reinitialize()
        products_list = []
        for item in user.cart:
            products_list.append(Product.from_dict(MongoDbSingleton('E_Commerce', 'Products').find_by_id(item.product_id)))

        return jsonify(products_list), 200
    except Exception as e:
        Writer(path=path, file_name=log_file).write_log(str(e), level=LogLevel.ERROR)
        return jsonify(), 500


if __name__ == '__main__':
    app_api.run(port = 9997, debug = True)

