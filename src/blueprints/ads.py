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


bp = Blueprint('ads', __name__)


class AdsView(MethodView):
    def get(self):
        request_dict = dict(request.args)
        with db.connection as con:
            service = AdsService(con)
            ads = service.get_ads(request_dict)
            return jsonify(ads)

    @auth_required
    def post(self, user):#переписать
        user_id = user['id']
        request_json = request.json
        title = request_json.get('title')

        if not title:
            return '', 400

        with db.connection as con:
            con.execute(
                'INSERT INTO ad (title, user_id) '
                'VALUES (?, ?)',
                (title, user_id),
            )
            con.commit()

            cur = con.execute(
                'SELECT * '
                'FROM ad '
                'WHERE user_id = ? AND title = ?',
                (user_id, title),
            )
            ad = cur.fetchone()
        return jsonify(dict(ad)), 201


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
