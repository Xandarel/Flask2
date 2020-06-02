from src.exceptions import ServiceError


class AdsServiceError(ServiceError):
    service = 'ads'


class AdDoesNotExistError(AdsServiceError):
    pass


class AdsService:
    def __init__(self, connection):
        self.connection = connection

    def get_ads(self, request_dict=None, id_user=None):
        query = ("""
        SELECT ALL ad.id, ad.seller_id, ad.title, ad.date, (SELECT DISTINCT GROUP_CONCAT(tag.name)
            FROM tag, adtag
            WHERE ad.id = adtag.ad_id AND tag.id = adtag.tag_id) as tags 
        FROM ad, seller, account
        JOIN car ON ad.car_id=car.id
        """)
        where = 'WHERE '
        group = " GROUP BY ad.id"
        params = list()
        if id_user is not None:
            where += 'account.id = ? AND account.id=seller.account_id AND ad.seller_id=seller.id AND'
            params.append(id_user)
        if request_dict is not None:
            for rd in request_dict:
                if rd == 'tags':
                    where += f' {rd} like ? AND'
                    params.append('%' + request_dict[rd] + '%')
                else:
                    where += f' {rd} = ? AND'
                    params.append(request_dict[rd])
        where = ' '.join(where.split()[:-1])
        print(query + where + group)
        cur = self.connection.execute(query + where + group, tuple(params))
        ads = cur.fetchall()
        ads = [dict(ad) for ad in ads]

        for a in ads:
            query = ("""
                SELECT car.*
                FROM car, ad
                WHERE ad.id = ? AND car.id = ad.car_id
            """)
            params = (a['id'],)
            cur = self.connection.execute(query,params)
            car = dict(cur.fetchone())

            query = ("""
            SELECT color.*
            FROM color, carcolor,car
            WHERE car.id= ? AND carcolor.car_id=car.id AND carcolor.color_id=color.id""")
            params = (car['id'],)
            cur = self.connection.execute(query, params)
            color =[dict(c) for c in cur.fetchall()]
            car['color'] = color

            query = ("""
            SELECT title, url
            FROM image, car
            WHERE car.id = ? AND car.id=image.car_id
            """)
            params = (car['id'],)
            cur = self.connection.execute(query, params)
            image = [dict(im) for im in cur.fetchall()]
            car['image'] = image
            del car['id']
            a['car'] = car
        return ads

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
