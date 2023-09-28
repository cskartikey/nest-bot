def get_username(cursor, user_id):
    try:
        cursor.execute(
            "SELECT tilde_username FROM nest_bot.users WHERE slack_user_id = %s",
            [user_id],
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        print(f"Error fetching full name: {e}")
        return None


def get_full_name(cursor, user_id):
    try:
        cursor.execute(
            "SELECT name FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        print(f"Error fetching full name: {e}")
        return None


def get_email(cursor, user_id):
    try:
        cursor.execute(
            "SELECT email FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        print(f"Error fetching full name: {e}")
        return None


def get_ssh_key(cursor, user_id):
    try:
        cursor.execute(
            "SELECT ssh_public_key FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        print(f"Error fetching full name: {e}")
        return None


def get_status(cursor, user_id):
    try:
        cursor.execute(
            "SELECT is_approved FROM nest_bot.users WHERE slack_user_id = %s", [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Error fetching full name: {e}")
        return None
