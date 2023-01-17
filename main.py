import config
from random import randrange
import time
import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_agent import VkAgent
from data_base import set_favorite, show_favorite, create_table

token = config.vk_group_token
user_token = config.vk_user_token
# user_token = input('Введи свой персональный токен (token) для профиля ВКонтакте: ')

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)
vk_upload = vk_api.VkUpload(vk)
vk_user = VkAgent(user_token)


def write_msg(user_id, message, keyboard=None):
    params = {
        'user_id': user_id,
        'message': message,
        'random_id': randrange(10 ** 7)
    }
    if keyboard is not None:
        params['keyboard'] = keyboard.get_keyboard()
    vk.method('messages.send', params)


def write_message_with_photo(user_id, list_of_ids, owner_id):
    for item in list_of_ids:
        params = {
            'user_id': user_id,
            'attachment': f'photo{owner_id}_{item}',
            'random_id': randrange(10 ** 7)
        }
        vk.method('messages.send', params)


search_params_all_user = {}
search_result_partner_id = None


def main():
    create_table()
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower()
                    if request == "привет":
                        if event.user_id in search_params_all_user:
                            write_msg(event.user_id, 'Привет, привет!')
                            continue
                        else:
                            search_params_all_user[event.user_id] = vk_user.get_default_params(event.user_id)

                        if search_params_all_user[event.user_id][0] == 0:
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button('Параметры\пол', color=VkKeyboardColor.PRIMARY)
                            keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                            write_msg(event.user_id, 'Для корректного поиска необходимо указать ваш пол.', keyboard)
                        if search_params_all_user[event.user_id][2] == 0:
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button('Параметры\возраст', color=VkKeyboardColor.PRIMARY)
                            write_msg(event.user_id, 'Для корректного поиска необходимо указать ваш возраст.', keyboard)
                        else:
                            if vk_user.get_client_name(event.user_id):
                                write_msg(event.user_id, f'Привет, {vk_user.get_client_name(event.user_id)}')
                                write_msg(event.user_id, 'Мы будем подбирать партнера на основании данных твоей анкеты.'
                                                         ' Чтобы задать параметры поиска отправь команду: '
                                                         '"Параметры"')
                                keyboard = VkKeyboard(inline=True)
                                keyboard.add_button('Найти партнера', color=VkKeyboardColor.PRIMARY)
                                keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                write_msg(event.user_id, f'Погнали?', keyboard)
                            else:
                                write_msg(event.user_id, 'Ой, кажется возникла проблема.'
                                                         'Специалисты уже работают над ее устранением.')

                    elif request == 'найти партнера' or request == 'дальше' or request == 'искать' or request == \
                            'искать дальше':
                        photo_param = vk_user.get_photo(search_params_all_user[event.user_id], event.user_id)
                        search_result_partner_id = photo_param[0]
                        partner = vk.method("users.get", {"user_ids": search_result_partner_id})
                        partner_name = partner[0]['first_name'] + ' ' + partner[0]['last_name']
                        write_msg(event.user_id, f'Привет, меня зовут {partner_name}')
                        write_message_with_photo(event.user_id, photo_param[1], photo_param[0])
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button('Избранное', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('Дальше', color=VkKeyboardColor.PRIMARY)
                        write_msg(event.user_id, f"Добавим {partner[0]['first_name']} в Избранное?", keyboard)

                    elif request == 'избранное':
                        set_favorite(search_result_partner_id, event.user_id)
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button('Дальше', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('Показать избранное', color=VkKeyboardColor.PRIMARY)
                        write_msg(event.user_id, 'Пользователь добавлен в Избранное', keyboard)

                    elif request == 'показать избранное':
                        user_list = show_favorite(event.user_id)
                        if len(user_list) < 1:
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                            write_msg(event.user_id,
                                      'Список "Избранное" пуст!\nДавай поскорее найдем кого-нибудь',
                                      keyboard)
                        else:
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button('Искать дальше', color=VkKeyboardColor.PRIMARY)
                            write_msg(event.user_id,
                                      'Список твоих любимчиков:', keyboard)
                            for user in user_list:
                                write_msg(event.user_id, f'{vk_user.get_client_name(user)} '
                                                         f'- vk.com/id{user}')

                    elif request == 'пока':
                        write_msg(event.user_id, 'До новых встреч!')

                    elif request == 'параметры':
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button('1', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('2', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('3', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('4', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('Помощь', color=VkKeyboardColor.PRIMARY)
                        write_msg(event.user_id, 'Что изменим в поиске?\n1 - Пол\n2 - Семейное положение'
                                                 '\n3 - Возраст\n4 - Город\nТы можешь посмотреть список доступных'
                                                 'из Параметров команд, отравив команду "Помощь".', keyboard)
                        vk_user.clear_search_params(event.user_id)

                        for event in longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW:
                                if event.to_me:
                                    request = event.text.lower()

                                    if request == '1':
                                        keyboard = VkKeyboard(inline=True)
                                        keyboard.add_button('Мужской', color=VkKeyboardColor.PRIMARY)
                                        keyboard.add_button('Женский', color=VkKeyboardColor.NEGATIVE)
                                        write_msg(event.user_id, 'Выберите пол избранника?', keyboard)
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text.lower()
                                                    if request == 'женский':
                                                        search_params_all_user[event.user_id][0] = 1
                                                    else:
                                                        search_params_all_user[event.user_id][0] = 2
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, 'Готово!\nИщем или еще меняем параметры?',
                                                              keyboard)
                                                    break
                                        break

                                    if request == '2':
                                        keyboard = VkKeyboard(inline=True)
                                        keyboard.add_button('1', color=VkKeyboardColor.SECONDARY)
                                        keyboard.add_button('2', color=VkKeyboardColor.SECONDARY)
                                        keyboard.add_button('3', color=VkKeyboardColor.SECONDARY)
                                        keyboard.add_button('4', color=VkKeyboardColor.SECONDARY)
                                        write_msg(event.user_id, 'Выберите семейное положение (по умолчанию задано '
                                                                 '"В активном поиске"):')
                                        write_msg(event.user_id, '1 - Не женат (Не замужем)\n 2 - В активном поиске\n'
                                                                 '3 - Женат (Замужем)\n4 - Все сложно', keyboard)
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text.lower()
                                                    if request == '1':
                                                        search_params_all_user[event.user_id][1] = 1
                                                    elif request == '2':
                                                        search_params_all_user[event.user_id][1] = 6
                                                    elif request == '3':
                                                        search_params_all_user[event.user_id][1] = 4
                                                    elif request == '4':
                                                        search_params_all_user[event.user_id][1] = 5
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, 'Готово!\nИщем или еще меняем параметры?',
                                                              keyboard)
                                                    break
                                        break

                                    if request == '3':
                                        write_msg(event.user_id, 'Укажите возраст избранника (один вариант):')
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text.lower()
                                                    search_params_all_user[event.user_id][2] = request
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, 'Готово!\nИщем или еще меняем параметры?',
                                                              keyboard)
                                                    break
                                        break

                                    if request == '4':
                                        write_msg(event.user_id, 'В каком городе продолжим поиск?')
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text
                                                    search_params_all_user[event.user_id][3] = request
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, f'Готово!\nИщем в городе {request} или еще'
                                                                             f' меняем параметры?', keyboard)
                                                    break
                                        break

                                    elif request == 'привет':
                                        write_msg(event.user_id, 'Привет, привет! Выбирай Параметры или отправь '
                                                                 'команду "Искать"')
                                        break
                                    elif request == 'помощь' or request == 'help' or request == 'нужна помощь':
                                        write_msg(event.user_id, 'Отправь команду "Искать" для поиска пары.\n')
                                        break
                                    else:
                                        write_msg(event.user_id, 'Введите команду "Помощь" для просмотра списка '
                                                                 'доступных команд.')
                                        break
                    else:
                        write_msg(event.user_id, 'Привет! Хочешь найти свою вторую половинку? Отправь мне команду '
                                                 '"привет"')
    except requests.exceptions.RequestException:
        time.sleep(10)


if __name__ == '__main__':
    main()