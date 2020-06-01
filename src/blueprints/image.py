import os
import sqlite3
from flask import (
    Blueprint,
    jsonify,
    request,
    session)
from werkzeug.utils import secure_filename
from flask.views import MethodView
from src.database import db
from src.config import Config
bp = Blueprint('images', __name__)


class ImageView(MethodView):
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

        request_file = request.files['file']
        filename = request_file.filename
        print(filename)
        up_level_path = os.getcwd()
        request_file.save(os.path.join(up_level_path, Config.UPLOAD_FOLDER, filename))
        return os.path.join(up_level_path, Config.UPLOAD_FOLDER, filename)


bp.add_url_rule('', view_func=ImageView.as_view('images'))
