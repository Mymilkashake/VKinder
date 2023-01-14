with open('vk_group_token.txt', 'r') as file_object:
    vk_group_token = file_object.read().strip()

with open('vk_user_token.txt', 'r') as file:
    vk_user_token = file.readline()

"""
https://oauth.vk.com/authorize?client_id=51491947&display=page&scope=stats.offline.messages.status.photos&response_type=token&v=5.131

vk_user_token нужно обновлять, так как у него ограниченный срок жизни

"""