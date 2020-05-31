from flask import (
    Blueprint,
    jsonify,
    request,
    session
)

from flask.views import MethodView

from src.database import db
from src.services.ads import AdsService

bp = Blueprint('cities', __name__)

class Cities(MethodView):
    def get(self):
        with db.connection as con:
            cur = con.execute("""
                SELECT *
                FROM city
            """)
            city = cur.fetchall()
            city_list = list()
            for c in city:
                city_list.append({'id': c[0], 'name': c[1]})
        return jsonify(city_list), 200


bp.add_url_rule('', view_func = Cities.as_view('cities'))
