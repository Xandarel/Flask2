from flask import (
    Blueprint,
    jsonify,
    request,
    session
)
from flask.views import MethodView

from src.auth import auth_required
from src.database import db
from src.services.ads import (
    AdDoesNotExistError,
    AdsService,
)
import datetime
import sqlite3

bp = Blueprint('ads', __name__)


class AdsView(MethodView):
    def get(self):
        request_dict = dict(request.args)
        with db.connection as con:
            service = AdsService(con)
            ads = service.get_ads(request_dict)
            return jsonify(ads)

    @auth_required
    def post(self):
        if session['id']:
            with db.connection as con:
                cur = con.execute("""
                SELECT id
                FROM seller
                WHERE account_id = ?
                """,
                (session['id'],)
                )
                is_seller = cur.fetchone()
            is_seller = dict(is_seller)
            if not bool(is_seller['id']):
                return '', 403
        else:
            return '', 401

        with db.connection as con:
            cur = con.execute("""
                SELECT id
                FROM SELLER
                WHERE account_id = ?
            """,
            (session['id'],)
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
            (title, now, dict(seller_id)['id'], car_id)
            )
            con.commit()
            ad_id = cur.lastrowid

            cur = con.execute("""
                SELECT date
                FROM ad
                WHERE seller_id =?
            """,
            (dict(seller_id)['id'],)
            )
            date = cur.fetchone()

        tags_id = list()
        for tag in tags:
            try:
                with db.connection as con:
                    cur = con.execute("""
                        INSERT INTO tag (name)
                        VALUES (?)
                    """,
                    (tag,)
                    )
                    con.commit()
                    tags_id.append(cur.lastrowid)
            except sqlite3.IntegrityError:
                with db.connection as con:
                    cur = con.execute(""" 
                        SELECT id
                        FROM tag
                        WHERE name = ?
                        """,
                        (tag,)
                    )
                    tags_id.append(dict(cur.fetchone())['id'])
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
                ans = dict(cur.fetchone())
                color_list.append({'id': color, 'name': ans['name'], 'hex': ans['hex']})

        response = {'id': session['id'], 'seller_id': dict(seller_id)['id'], 'title': title, 'date': now, 'tags': tags,
                    'car': {'make': make, 'model': model, 'color': color_list, 'mileage': mileage, 'num_owners': num_owners,
                            'reg_number': reg_number, 'images': images
                           }
                    }
        return jsonify(response), 200


class AdView(MethodView):
    def get(self, ad_id):
        with db.connection as con:
            service = AdsService(con)
            try:
                ad = service.get_ad(ad_id)
            except AdDoesNotExistError:
                return '', 404
            else:
                return jsonify(ad), 200

    def patch(self, ad_id):
        if session['id']:
            with db.connection as con:
                cur = con.execute("""
                SELECT id
                FROM seller
                WHERE account_id = ?
                """,
                (session['id'],)
                )
                is_seller = cur.fetchone()
            seller_id = dict(is_seller)
            if not bool(seller_id['id']):
                return '', 403
        else:
            return '', 401
        with db.connection as con:
            cur = con.execute("""
            SELECT id
            FROM ad
            WHERE ad.id=? AND seller_id=?
            """,
            (ad_id, seller_id)
            )
            ad = cur.fetchone()
        if not bool(ad):
            return '', 412

        request_json = request.json
        title = request_json.get('title')
        tags = request_json.get('tags')
        car = request_json.get('car')

        make = car.get('make')
        model = car.get('model')
        colors = car.get('colors')
        mileage = car.get('mileage')
        num_owners = car.get('num_owners')
        reg_number = car.get('reg_number')
        images = car.get('images')
        if title:
            with db.connection as con:
                con.execute(""" 
                UPDATE ad
                SET title = ?
                WHERE id = ?
                """,
                (title, ad_id)
                )
                con.commit()

        if tags:
            title_id = list()
            for t in title:
                with db.connection as con:
                    cur = con.execute("""
                    SELECT id 
                    FROM tag
                    WHERE name = ?
                    """,
                    (t,)
                    )
                    title_id.append(dict(cur.fetchone())['id'])

            with db.connection as con:
                con.execute("""
                    DELETE FROM adtags
                    WHERE ad_id = ?
                """,
                (ad_id,)
                )
                con.commit()

            for t_id in title_id:
                with db.connection as con:
                    con.execute(""" 
                        INSERT INTO adtag (tag_id, ad_id)
                        VALUES (?, ?)
                        """,
                    (t_id, ad_id)
                    )
                    con.commit()

        if car:
            update_car = 'UPDATE car '
            set = 'SET '
            where = 'WHERE ad.id = ? AND ad.car_id = car.id'
            values = list()
            values.append(ad_id)
            if make:
                set += 'make = ?,'
                values.append(make)
            if model:
                set += 'model = ?,'
                values.append(model)
            if mileage:
                set += 'mileage = ?,'
                values.append(mileage)
            if num_owners:
                set += 'num_owners = ?,'
                values.append(num_owners)
            if reg_number:
                set += 'reg_number = ?,'
                values.append(reg_number)
            set = set[:-1]
            with db.connection as con:
                con.execute(set + where, values)

        with db.connection as con:
                    cur = con.execute(""" 
                        SELECT id
                        FROM car
                        WHERE ad.id = ? AND ad.car_id = car.id
                    """,
                    (ad_id)
                    )
                    car_id = dict(cur.fetchone())['id']

        if colors:
            for col in colors:
                try:
                  with db.connection as con:
                        con.execute(""" 
                            INSERT INTO carcolor (color_id, car_id)
                            VALUES (?, ?)
                        """,
                        (col, car_id)
                        )
                        con.commit()
                except sqlite3.IntegrityError:
                    pass

        if images:
            try:
                for im in images:
                    im_title = im.get('title')
                    url = im.get('url')
                    with db.connection as con:
                        con.execute(""" 
                            INSERT INTO image (title, url, car_id)
                            VALUES (?, ?, ?)
                        """,
                        (im_title,url, car_id)
                        )
                        con.commit()
            except sqlite3.IntegrityError:
                pass






    def delete(self, ads_id):
        with db.connection as con:
            cur = con.execute(f"""
            SELECT account_id
            FROM seller
            JOIN ad ON ad.id ={ads_id}
            WHERE ad.seller_id=seller.id
            """)
            user_id = cur.fetchone()

        if user_id != session['id']:
            return '', 401

        with db.connection as con:
            con.execute(f"""
            DELETE FROM ad WHERE id = {ads_id}
            """)
            con.commit()
        return '', 200


bp.add_url_rule('', view_func=AdsView.as_view('ads'))
bp.add_url_rule('/<int:ad_id>', view_func=AdView.as_view('ad'))
