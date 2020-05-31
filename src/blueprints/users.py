import sqlite3
import datetime

from flask import (
    Blueprint,
    jsonify,
    request,
    session
)
from flask.views import MethodView
from werkzeug.security import generate_password_hash

from src.database import db


bp = Blueprint('users', __name__)


class UsersView(MethodView):

    def post(self):
        request_json = request.json
        email = request_json.get('email')
        password = request_json.get('password')
        first_name = request_json.get('first_name')
        last_name = request_json.get('last_name')
        is_seller = request_json.get('is_seller')
        if is_seller:
            phone = request_json.get('phone')
            zip_code = request_json.get('zip_code')
            city_id = request_json.get('city_id')
            street = request_json.get('street')
            home = request_json.get('home')

        if not email or not password or \
           not first_name or not last_name:
            return '', 400

        password_hash = generate_password_hash(password)

        with db.connection as con:
            try:
                cursor = con.cursor()
                cursor.execute(
                    'INSERT INTO account (first_name, last_name, email, password) '
                    'VALUES (?, ?, ?, ?)',
                    (first_name, last_name, email, password_hash),
                )
                con.commit()
                account_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                return '', 409

            if is_seller:
                try:
                    cursor = con.cursor()
                    cursor.execute(f"""
                            SELECT zip_code
                            FROM zipcode
                            WHERE zip_code = {zip_code}
                    """)
                    if cursor.fetchone():
                        cursor.execute(f"""
                        INSERT INTO seller (zip_code, street, home, phone, account_id)
                        VALUES (?,?,?,?,?)""",
                        (zip_code, street, home, phone, account_id)
                        )
                        con.commit()
                    else:
                        cursor.execute("""
                        INSERT INTO zipcode(zip_code, city_id)
                        VALUES (?, ?)""",
                        (zip_code,city_id)
                        )
                        con.commit()

                        cursor.execute("""
                        INSERT INTO seller (zip_code, street, home, phone, account_id)
                        VALUES (?,?,?,?,?)""",
                        (zip_code, street, home, phone, account_id)
                        )
                        con.commit()

                except sqlite3.IntegrityError:
                    return '', 409

        return request_json, 201


class UserView(MethodView):
    def get(self, user_id):
        if session['id'] is not None:
            return '', 401
        with db.connection as con:
            cur = con.execute(
                'SELECT account.id, first_name, last_name '
                'FROM account '
                'WHERE account.id = ?',
                (user_id,),
            )
            user = cur.fetchone()
            user = dict(user)

            cur = con.execute("""
                SELECT zipcode.zip_code, street, home, phone, city_id
                FROM seller
                JOIN zipcode ON zipcode.zip_code = seller.zip_code
                WHERE account_id = ?
            """,
            (user_id,),
            )
            is_seller=cur.fetchone()
            if is_seller:
                user['is_seller'] = True
                user.update(dict(is_seller))
            else:
                user['is_seller'] = False
        if user is None:
            return '', 404
        return jsonify(dict(user))

    def patch(self, user_id):
        if user_id != session['id']:
            return '', 401

        request_json = request.json
        update_acc ='UPDATE account '
        set = 'SET '
        where = 'WHERE id=?'
        value = list()
        first_name = request_json.get('first_name')
        if first_name:
            set += 'first_name = ?'
            value.append(first_name)

        last_name = request_json.get('last_name')
        if last_name:
            set += ', last_name = ?'
            value.append(last_name)

        value.append(user_id)
        with db.connection as con:
            con.execute(update_acc + set + where,tuple(value))
            con.commit()

        is_seller = request_json.get('is_seller')
        phone = request_json.get('phone')
        street = request_json.get('street')
        zip_code = request_json.get('zip_code')
        city_id = request_json.get('city_id')
        home = request_json.get('home')

        if is_seller is not None:
            if not is_seller:
                with db.connection as con:
                    con.execute("""
                    DELETE FROM seller
                    WHERE account_id = ?
                    """,
                    (user_id,)
                    )
                    con.commit()
            else:
                with db.connection as con:
                    cur = con.execute("""
                    SELECT id
                    FROM seller
                    WHERE account_id =?
                    """,
                    (user_id,)
                    )
                    seller = cur.fetchone()

                if seller:
                    update_acc = 'UPDATE seller '
                    set = 'SET '
                    value.clear()

                    if phone:
                        set += 'phone = ?'
                        value.append(phone)

                    if street:
                        set += ', street = ?'
                        value.append(street)

                    if home:
                        set += ', home = ?'
                        value.append(home)

                    if zip_code:
                        set += ', zip_code = ?'
                        value.append(zip_code)

                    value.append(user_id)
                    with db.connection as con:
                        con.execute(update_acc + set + where, tuple(value))
                        con.commit()
                else:
                    with db.connection as con:
                        con.execute("""
                            INSERT INTO seller (zip_code, street, home, phone, account_id)
                            VALUES (?,?,?,?,?)
                        """,
                        (zip_code, street, home, phone, user_id)
                        )
                        con.commit()

        if zip_code and city_id:
            with db.connection as con:
                cur = con.execute(
                    'SELECT zip_code, city_id '
                    'FROM zipcode '
                    'WHERE zip_code = ? AND city_id = ?',
                    (zip_code, city_id),
                )
                element = cur.fetchone()
            if not bool(element):
                con.execute(
                    'INSERT INTO zipcode (zip_code, city_id)'
                    'VALUES (?,?) ',
                    (zip_code, city_id),
                )
                con.commit()

        with db.connection as con:
            cur = con.execute(
                'SELECT account.id, first_name, last_name '
                'FROM account '
                'WHERE account.id = ?',
                (user_id,),
            )
            user = cur.fetchone()
            user = dict(user)

            cur = con.execute("""
                SELECT zipcode.zip_code, street, home, phone, city_id
                FROM seller
                JOIN zipcode ON zipcode.zip_code = seller.zip_code
                WHERE account_id = ?
            """,
            (user_id,),
            )
            is_seller=cur.fetchone()
            if is_seller:
                user['is_seller'] = True
                user.update(dict(is_seller))
            else:
                user['is_seller'] = False

        return jsonify(dict(user)), 200


 # недоделано
# class UserAds(MethodView):
#     def get(self,user_id):
#         if user_id != session['id']:
#             return '', 401
#         request_json = request.json
#         tags = request_json.get('tags')
#         make = request_json.get('make')
#         model = request_json.get('model')
#
#         with db.connection as con:
#             cur = con.execute("""
#                 SELECT id, seller_id, title, date
#                 FROM ad
#                 WHERE seller_id = ?
#             """,
#             (user_id,)
#             )
#             ad_info = cur.fetchall()


class AddAds(MethodView):
    def post(self,user_id):
        if user_id != session['id']:
            return '', 401

        with db.connection as con:
            cur = con.execute("""
                SELECT id
                FROM SELLER
                WHERE account_id = ?
            """,
            (user_id,)
            )
            seller_id = cur.fetchone()
        if not seller_id:
            return '', 403

        request_json = request.json
        title = request_json.get('title')
        tags = request_json.get('tags')

        car = jsonify(request_json.get('car')).json
        make = car.get('make')
        model = car.get('model')
        colors = car.get('colors')
        mileage = car.get('mileage')
        num_owners = car.get('num_owners')

        if not num_owners:
            num_owners = 1
        reg_number = car.get('reg_number')

        images = car.get('images')

        with db.connection as con:
            cur = con.execute("""
                INSERT INTO car (make, model, mileage, num_owners, reg_number)
                VALUES (?, ?, ?, ?, ?)
            """,
            (make, model, mileage, num_owners, reg_number)
            )
            con.commit()
            car_id = cur.lastrowid

        for color_id in colors:
            with db.connection as con:
                con.execute("""
                    INSERT INTO carcolor (color_id, car_id)
                    VALUES (?, ?)
                """,
                (color_id, car_id)
                )
                con.commit()
        for image in images:
            im = jsonify(image).json
            im_title = im.get('title')
            url = im.get('url')
            with db.connection as con:
                con.execute("""
                    INSERT INTO image (title, url, car_id)
                    VALUES (?, ?, ?)
                    """,
                    (im_title, url, car_id)
                )
                con.commit()

        with db.connection as con:
            now = int(datetime.datetime.today().timestamp())
            cur = con.execute("""
                INSERT INTO ad (title, date, seller_id, car_id)
                VALUES (?, ?, ?, ?)
            """,
            (title, now, seller_id, car_id)
            )
            con.commit()
            ad_id = cur.lastrowid()

            cur = con.execute(f"""
                SELECT date
                FROM ad
                WHERE seller_id ={seller_id}
            """)
            date = cur.fetchone()

        tags_id = list()
        for tag in tags:
            with db.connection as con:
                cur = con.execute(""" 
                    SELECT id
                    FROM tag
                    WHERE name = ?
                    """,
                    (tag,)
                )
                tags_id.append(cur.fetchone())

        for tag_id in tags_id:
            with db.connection as con:
                cur = con.execute(""" 
                    INSERT INTO adtag (tag_id, ad_id)
                    VALUES (?, ?)
                """,
                (tag_id, ad_id)
                )
                con.commit()

        color_list = list()
        for color in colors:
            with db.connection as con:
                cur = con.execute(f""" 
                    SELECT name, hex
                    FROM color
                    WHERE id = {color}
                """)
                ans = cur.fetchone().json
                color_list.append({'id':color, 'name':ans['name'], 'hex':ans['hex']})

        response = {'id': user_id, 'seller_id': seller_id, 'title': title, 'date': date, 'tags': tags,
                    'car': {'make': make, 'model': model, 'color': color_list, 'mileage': mileage, 'num_owners': num_owners,
                            'reg_number': reg_number,'images': images
                           }
                    }
        return jsonify(response), 200


bp.add_url_rule('', view_func=UsersView.as_view('users'))
bp.add_url_rule('/<int:user_id>', view_func=UserView.as_view('user'))
bp.add_url_rule('/<int:user_id>/ads', view_func=AddAds.as_view('user_add_ads'))
