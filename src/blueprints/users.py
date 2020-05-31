import sqlite3

from flask import (
    Blueprint,
    jsonify,
    request,
    session
)
from flask.views import MethodView
from werkzeug.security import generate_password_hash

from src.auth import auth_required
from src.database import db


bp = Blueprint('users', __name__)


class UsersView(MethodView):
    def get(self):
        with db.connection as con:
            cur = con.execute(
                'SELECT id, email '
                'FROM account'
            )
            rows = cur.fetchall()
        return jsonify([dict(row) for row in rows])

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
        if session['id'] != user_id:
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
            value.append('first_name')

        last_name = request_json.get('last_name')
        if last_name:
            set += ', last_name = ?'
            value.append('first_name')

        value.append(user_id)
        with db.connection as con:
            con.execute(update_acc + set + where,tuple(value))
            con.commit()

        is_seller = request_json.get('is_seller')
        phone = request_json.get('phone')
        street = request_json.get('street')
        zip_code = request_json.get('zip_code')
        city_id = request_json.get('city_id')
        home = request_json('home')

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
                    (zip_code,street,home,phone,user_id,)
                    )
                    con.execute()

        if zip_code and city_id:
            with db.connection as con:
                cur = con.execute(
                    'SELECT zip_code, city_id '
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


bp.add_url_rule('', view_func=UsersView.as_view('users'))
bp.add_url_rule('/<int:user_id>', view_func=UserView.as_view('user'))
