def get_username(cursor, user_id):
    cursor.execute(
        "SELECT tilde_username FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
    )
    username = cursor.fetchone()[0]
    if username != None:
        return str(username)
    else:
        return None


def get_full_name(cursor, user_id):
    cursor.execute(
        "SELECT name FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
    )
    name = cursor.fetchone()[0]
    if name != None:
        return str(name)
    else:
        return None


def get_email(cursor, user_id):
    cursor.execute(
        "SELECT email FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
    )
    email = cursor.fetchone()[0]
    if email != None:
        return str(email)
    else:
        return None


def get_ssh_key(cursor, user_id):
    cursor.execute(
        "SELECT ssh_key FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
    )
    ssh_key = cursor.fetchone()[0]
    if ssh_key != None:
        return str(ssh_key)
    else:
        return None