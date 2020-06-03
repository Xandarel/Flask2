import os
from flask import (
    Blueprint,
    request,
    session,
    send_file)
from flask.views import MethodView
from src.database import db
from src.config import Config
bp = Blueprint('images', __name__)


class ImagesView(MethodView):
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
                return 'вы не являетесь продавцом', 401

        else:
            return 'вы не авторизованы', 401
        if 'file' in request.files:
            request_file = request.files['file']
        else:
            return 'нет изображения', 409
        filename = request_file.filename
        filename = filename[0: -1]
        print(filename)
        up_level_path = os.getcwd()
        request_file.save(os.path.join(up_level_path, Config.UPLOAD_FOLDER, filename))
        return os.path.join(up_level_path, Config.UPLOAD_FOLDER, filename), 201


class ImageView(MethodView):
    def get(self, filename):
        jpg = '.jpg'
        up_level_path = os.getcwd()
        file = os.path.join(up_level_path, Config.UPLOAD_FOLDER, filename + jpg)
        if file:
            return send_file(file), 200
        else:
            return '', 404


bp.add_url_rule('', view_func=ImagesView.as_view('download_image'))
bp.add_url_rule('/<filename>', view_func=ImageView.as_view('get_image'))
