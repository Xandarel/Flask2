from src.exceptions import ServiceError


class AdsServiceError(ServiceError):
    service = 'ads'


class AdDoesNotExistError(AdsServiceError):
    pass


class AdsService:
    def __init__(self, connection):
        self.connection = connection

    def get_ads(self, user_id=None):
        query = (
            'SELECT * '
            'FROM ad '
        )
        params = ()
        if user_id is not None:
            query += 'WHERE user_id = ?'
            params = (user_id,)
        cur = self.connection.execute(query, params)
        ads = cur.fetchall()
        return [dict(ad) for ad in ads]

    def get_ad(self, ad_id):
        query = (
            'SELECT * '
            'FROM ad '
            'WHERE id = ?'
        )
        params = (ad_id,)
        cur = self.connection.execute(query, params)
        ad = cur.fetchone()
        if ad is None:
            raise AdDoesNotExistError(ad_id)
        get_tags = (f"""
            SELECT name
            FROM tag, adtag
            WHERE adtag.ad_id = ? AND tag.id = adtag.tag_id
        """)
        cur = self.connection.execute(get_tags, params)
        tags = cur.fetchall()
        ad = dict(ad)
        ad['tags'] = list(tag[0] for tag in tags)

        get_car = ("""
        SELECT *
        FROM car, ad
        WHERE ad.id = ? and ad.car_id = car.id""")
        cur = self.connection.execute(get_car, params)
        car = dict(cur.fetchone())

        get_color = ("""
            SELECT color.id, color.hex, color.name
            FROM color, carcolor
            WHERE carcolor.car_id = ? 
            AND carcolor.color_id = color.id
        """)
        cur = self.connection.execute(get_color, (car['id'],))
        color = cur.fetchall()
        color_list =list()
        for col in color:
            color_dic = {'id': col[0], 'name': col[2], 'hex': col[1]}
            color_list.append(color_dic)
        car['color'] = color_list

        get_images = ("""
            SELECT image.title, image.url
            FROM image
            WHERE image.car_id = ?
        """)
        cur = self.connection.execute(get_images, (car['id'],))
        images = cur.fetchall()
        image_list = list()
        for im in images:
            image_list.append({'title': im[0], 'url': im[1]})
        car['images'] = image_list
        ad['car'] = car
        return ad
