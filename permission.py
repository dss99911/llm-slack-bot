PERMISSION_NO = 0
PERMISSION_USE = 1
PERMISSION_SQL = 2
PERMISSION_ALL = 3


def get_user_permission(user_id):
    if user_id == 'U09DPGC0P':
        return PERMISSION_ALL
    else:
        return PERMISSION_NO