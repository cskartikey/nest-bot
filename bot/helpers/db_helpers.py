from pathlib import Path
from utils import error_handling

def read_sql_query(sql_path: Path) -> str:
    return Path(sql_path).read_text()


def get_username(cursor, user_id) -> str:
    try:
        cursor.execute(
            read_sql_query("sql/selectUser.sql"),
            [user_id],
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        error_handling(e)
        return None


def get_full_name(cursor, user_id):
    try:
        cursor.execute(
            read_sql_query("sql/selectName.sql"), [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        error_handling(e)
        return None


def get_email(cursor, user_id):
    try:
        cursor.execute(
            read_sql_query("sql/selectEmail.sql"), [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        error_handling(e)
        return None


def get_ssh_key(cursor, user_id):
    try:
        cursor.execute(
            read_sql_query("sql/selectKey.sql"), [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return str(result[0])
        else:
            return None
    except Exception as e:
        error_handling(e)
        return None


def get_status(cursor, user_id):
    try:
        cursor.execute(
            read_sql_query("sql/getStatus.sql"), [user_id]
        )
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            return result[0]
        else:
            return None
    except Exception as e:
        error_handling(e)
        return None
