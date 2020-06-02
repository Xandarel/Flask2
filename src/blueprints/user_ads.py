from flask import (
    Blueprint,
    jsonify,
    request
)
from flask.views import MethodView

from src.database import db
from src.services.ads import AdsService


bp = Blueprint('user_ads', __name__)


class UserAdsView(MethodView):
    def get(self, user_id):
        request_dict = dict(request.args)
        with db.connection as con:
            service = AdsService(con)
            ads = service.get_ads(request_dict=request_dict, id_user=user_id)
            return jsonify(ads)


bp.add_url_rule('/<int:user_id>/ads', view_func=UserAdsView.as_view('user_ads'))
