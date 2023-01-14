import random
from datetime import date
from pprint import pprint
import requests
import data_base


class VkAgent:
    def __init__(self, token: str, api_version: str = '5.131', base_url: str = "https://api.vk.com/"):
        self.token = token
        self.list_of_partner_ids = {}
        self.search_params = {}
        self.offset_count = {}
        self.search_count = 100
        self.api_version = api_version
        self.base_url = base_url
        self.params = {
            'access_token': self.token,
            'v': self.api_version
        }

    def get_response(self, method, params):
        return requests.get(f"{self.base_url}{method}", params={**params, **self.params}).json()

    # @staticmethod
    # def get_response(url, params):
    #     response = requests.get(url, params=params)
    #     if response.status_code == 200:
    #         return response.json()
    #     else:
    #         return False

    @staticmethod
    def get_link(response, photo_index):
        """
        Получить url ссылку на скачивание фото максимального размера из профиля пользователя VK
        """
        return response['response']['items'][photo_index]['sizes'][-1]['url']

    def make_list_of_partner_ids(self, search_params, client_id):
        """
        Создать список id пользователей исходя из параметров поиска: sort — сортировка результатов (1 — по дате
        регистрации, 0 — по популярности); status — семейное положение (1 — неженат (не замужем), 2 — встречается,
        3 — помолвлен(-а), 4 — женат (замужем), 5 — всё сложно, 6 — в активном поиске, 7 — влюблен(-а),
        8 — в гражданском браке); has_photo — учитывать ли наличие фото (1 — искать только пользователей с фотографией,
        0 — искать по всем пользователям); hometown — название города строкой.
        """
        list_of_partner_ids = []
        method = '/method/users.search'
        params = {
            'sort': 0,
            'count': self.search_count,
            'offset': self.offset_count[client_id],
            'sex': search_params[0],
            'status': search_params[1],
            'age_from': search_params[2],
            'age_to': int(search_params[2]) + 10,
            'is_closed': False,
            'has_photo': 1,
            'hometown': search_params[3]
        }
        response = self.get_response(method, params)
        # pprint(response_find_user)
        if response:
            for item in response['response']['items']:
                if not item['is_closed']:
                    list_of_partner_ids.append(item['id'])
                else:
                    continue
            self.list_of_partner_ids[client_id] = list_of_partner_ids

    def select_id(self, list_of_partner_ids, client_id):
        """
        Получить рандомный id из списка поисковой выдачи пользователей
        """
        try:
            if len(list_of_partner_ids) != 0:
                partner_id = random.choice(list_of_partner_ids)
                list_of_partner_ids.remove(partner_id)
                if data_base.record_user(partner_id, client_id):
                    return partner_id
                else:
                    return self.select_id(list_of_partner_ids, client_id)
            else:
                return False
        except Exception:
            return False

    def get_photo(self, search_params, client_id):
        """
        Получить id 3-х самых популярных фото пользователя, если фото меньше, то получить имеющееся количество
        """
        if client_id not in self.search_params:
            self.search_params[client_id] = search_params
        if client_id not in self.offset_count:
            self.offset_count[client_id] = 0
        if client_id in self.list_of_partner_ids:
            if len(self.list_of_partner_ids[client_id]) == 0:
                self.make_list_of_partner_ids(self.search_params[client_id], client_id)
                self.offset_count[client_id] += self.search_count
        else:
            self.list_of_partner_ids[client_id] = []

        method = '/method/photos.get'
        user_id = self.select_id(self.list_of_partner_ids[client_id], client_id)
        if user_id:
            params = {
                'owner_id': user_id,
                'album_id': 'profile',
                'extended': '1',
                'photo_sizes': '1',
                'rev': '1'
            }
            response = self.get_response(method, params)
            # pprint(response)
            if response:
                count_photo = len(response['response']['items'])
                # owner_id = response['response']['items'][0]['owner_id']
                if count_photo >= 3:  # если больше 3 фото, то самые популярные выбираем как сумма лайков и комментов
                    photo_dict = {}
                    for item in range(count_photo):
                        likes_count = response['response']['items'][item]['likes']['count']
                        comments_count = response['response']['items'][item]['comments']['count']
                        photo_dict[likes_count + comments_count] = response['response']['items'][item]['id']
                    sorted_dict = sorted(photo_dict.items(), reverse=True)
                    # print(sorted_dict)
                    list_of_photo_ids = []
                    for n in range(3):
                        list_of_photo_ids.append(sorted_dict[n][1])
                    return [user_id, list_of_photo_ids]
                else:  # если меньше 3 фото, то только их и берем
                    list_of_photo_ids = []
                    for item in range(count_photo):
                        list_of_photo_ids.append(response['response']['items'][item]['id'])
                    return [user_id, list_of_photo_ids]
            else:
                return False
        else:
            self.make_list_of_partner_ids(self.search_params[client_id], client_id)
            return self.get_photo(self.search_params[client_id], client_id)

    def get_client_name(self, user_id):
        """
        Получить имя пользователя из профиля VK по id
        """
        method = '/method/users.get'
        params = {
            'user_ids': user_id
        }
        response = self.get_response(method, params)
        if response:
            return response['response'][0]['first_name']
        else:
            return False

    def get_default_params(self, user_id):
        """
        Получить информацию о пользователе (пол, дата рождения, город) из профиля VK по id,
        затем сохранить списком параметры для автоматического подбора пары: [0] противоположный пол (по умолчанию пол:
        1 - женский, 2 - мужской, 0 - без указания пола), статус по умолчанию, возраст, город.
        """
        method = '/method/users.get'
        params = {
            'user_ids': user_id,
            'fields': 'sex, bdate, city'
        }
        response = self.get_response(method, params)
        # pprint(response)
        if response:
            search_params = []
            if response['response'][0]['sex'] == 1:
                search_params.append(2)  # ищем противоположный пол - если девочка, то запишем мальчик и наоборот
            elif response['response'][0]['sex'] == 2:
                search_params.append(1)
            else:
                search_params.append(response['response'][0]['sex'])
            search_params.append(6)  # 6 = по умолчанию 'в активном поиске'
            today = date.today()
            try:
                user_bdate = response['response'][0]['bdate'].split('.')
                # print(user_bdate)
            except Exception:  # по умолчанию = сегодня, если возраст скрыт
                user_bdate = today.strftime("%d.%m.%Y").split('.')
            age = today.year - int(user_bdate[2]) - (
                    (today.month, today.day) < (int(user_bdate[1]), int(user_bdate[0])))
            search_params.append(age)
            search_params.append(response['response'][0]['city']['title'])
            return search_params
        else:
            return False

    def clear_search_params(self, client_id):
        self.list_of_partner_ids[client_id] = []