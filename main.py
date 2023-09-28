from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
import psycopg2 as psql
import logging
import db_helpers
import json

load_dotenv()

slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_app_token = os.environ.get("SLACK_APP_TOKEN")

app = App(token=slack_bot_token)
logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

severity_to_logging_level = {
    "NOTSET": 0,
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

connection = psql.connect(
    database=os.environ.get("SQL_DATABASE"),
    host=os.environ.get("SQL_HOST"),
    user=os.environ.get("SQL_USER"),
    password=os.environ.get("SQL_PASSWORD"),
    port=os.environ.get("SQL_PORT"),
    # sslmode='require' # comment it if you run it on localhost though
)

cursor = connection.cursor()

home_ids = {}


def error_handling(e: psql.Error):
    severity = getattr(e.diag, "severity", "UNKNOWN")
    if isinstance(e, psql.InterfaceError):
        logging.log(
            level=int(severity_to_logging_level[str(severity)]),
            msg=f"DatabaseError: InterfaceError occurred.\nMessage:{e.diag.message_primary}",
        )
    elif isinstance(e, psql.DatabaseError):
        if isinstance(e, psql.DataError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: DataError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.OperationalError):
            lpogging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: OperationalError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.IntegrityError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: IntegrityError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.InternalError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: InternalError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.ProgrammingError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: ProgrammingError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.NotSupportedError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: NotSupportedError occurred.\nMessage:{e.diag.message_primary}",
            )
        else:
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError occurred of no particular type.\nMessage:{e.diag.message_primary}",
            )
    elif isinstance(e, psql.Warning):
        logging.log(
            level=int(severity_to_logging_level[str(severity)]),
            msg=f"Warning occured occurred.\nMessage:{e.diag.message_primary}",
        )
    else:
        logger.log(f"Other error occurred: {type(e)}")


def approved_home(username, name, email, ssh_key):
    with open("json/approved_home.json", "r") as read_file:
        data = json.load(read_file)
    data["blocks"][3]["text"]["text"] = data["blocks"][3]["text"]["text"].format(
        username=username
    )
    data["blocks"][5]["text"]["text"] = data["blocks"][5]["text"]["text"].format(
        name=name
    )
    data["blocks"][7]["text"]["text"] = data["blocks"][7]["text"]["text"].format(
        email=email
    )
    data["blocks"][9]["text"]["text"] = data["blocks"][9]["text"]["text"].format(
        ssh_key=ssh_key
    )
    return data


def unapproved_home(username, name, email, ssh_key):
    with open("json/unapproved_home.json", "r") as read_file:
        data = json.load(read_file)
    data["blocks"][3]["text"]["text"] = data["blocks"][3]["text"]["text"].format(
        username=username
    )
    data["blocks"][5]["text"]["text"] = data["blocks"][5]["text"]["text"].format(
        name=name
    )
    data["blocks"][7]["text"]["text"] = data["blocks"][7]["text"]["text"].format(
        email=email
    )
    data["blocks"][9]["text"]["text"] = data["blocks"][9]["text"]["text"].format(
        ssh_key=ssh_key
    )
    return data


def unsigned_home():
    with open("json/unsigned_home.json", "r") as read_file:
        data = json.load(read_file)
    return data


@app.event("app_home_opened")
def initial_home_tab(client, event, logger):
    """
    Handle the app home tab opening event.

    This function is triggered when a user opens the app's home tab. It checks whether the user
    is already registered and publishes the appropriate view (signed or not signed) accordingly.
    """
    user_id = event["user"]
    username = client.users_profile_get(user=user_id)["profile"]["display_name"]
    home_ids[user_id] = event["view"]["id"]
    try:
        name = db_helpers.get_full_name(cursor=cursor, user_id=user_id)
        status = db_helpers.get_status(cursor=cursor, user_id=user_id)
        # Checks if the user is already registered and publishes the view accordingly
        if name != None and status:
            client.views_publish(
                user_id=event["user"],
                view=approved_home(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=name,
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_email(cursor=cursor, user_id=user_id),
                ),
            )
        elif name != None and not status:
            client.views_publish(
                user_id=event["user"],
                view=unapproved_home(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=name,
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_email(cursor=cursor, user_id=user_id),
                ),
            )
        else:
            client.views_publish(
                user_id=event["user"],
                view=unsigned_home(),
            )

    except psql.Error as e:
        error_handling(e)


@app.action("register_user")
def register_user(ack, body, client, logger):
    """
    Open a registration modal for unregistered users to sign up for Nest.

    This function is triggered when a user clicks the "Register Yourself" button. It acknowledges
    the action, retrieves the user's Slack display name, and opens a modal for them to enter their
    registration details (tilde username and SSH key).
    """
    ack()
    slack_user_id = body["user"]["id"]
    profile_name = (client.users_profile_get(user=slack_user_id))["profile"][
        "display_name"
    ]
    with open("json/register_user.json", "r") as read_file:
        data = json.load(read_file)
    data["blocks"][0]["text"]["text"] = data["blocks"][0]["text"]["text"].format(
        profile_name=profile_name
    )
    client.views_open(trigger_id=body["trigger_id"], view=data)


@app.view("register_user")
def handle_register_user(ack, body, client):
    """
    Handle user registration view submission.

    This function is called when a user submits their registration details through a Slack modal view.
    It inserts the provided details into the PostgreSQL server.
    :todo: SSH Key validation
    """

    insert_query = """
    INSERT INTO nest_bot.users (slack_user_id, name, email, tilde_username, ssh_public_key, description)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    errors = {}
    slack_user_id = body["user"]["id"]
    username = body["view"]["state"]["values"]["username"]["username_input"]["value"]
    name = body["view"]["state"]["values"]["name"]["name_input"]["value"]
    email = body["view"]["state"]["values"]["email"]["email_input"]["value"]
    ssh_key = body["view"]["state"]["values"]["ssh_key"]["ssh_key_input"]["value"]
    description = body["view"]["state"]["values"]["description"]["description_input"][
        "value"
    ]

    if username is not None:
        cursor.execute(
            "SELECT tilde_username FROM nest_bot.users WHERE tilde_username=%s",
            [username],
        )
        result = cursor.fetchone()
        if result is not None and result[0] == username:
            errors["username"] = "The username is taken. Please choose another username"
            ack(response_action="errors", errors=errors)
            return
    if description is not None and len(description) < 10:
        errors["description"] = "The description should be larger than 10 characters."
        ack(response_action="errors", errors=errors)
        return
    ack()
    try:
        cursor.execute(
            insert_query, (slack_user_id, name, email, username, ssh_key, description)
        )
        connection.commit()
        client.views_publish(
            user_id=slack_user_id,
            view=unapproved_home(
                username=username, name=name, email=email, ssh_key=ssh_key
            ),
        )
    except psql.Error as e:
        error_handling(e)


@app.action("edit_full_name")
def edit_full_name(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    with open("json/edit_full_name.json", "r") as read_file:
        data = json.load(read_file)
    client.views_open(trigger_id=body["trigger_id"], view=data)


@app.action("edit_username")
def edit_full_name(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    with open("json/edit_username.json", "r") as read_file:
        data = json.load(read_file)
    client.views_open(trigger_id=body["trigger_id"], view=data)


@app.action("edit_email")
def edit_full_name(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    with open("json/edit_email.json", "r") as read_file:
        data = json.load(read_file)
    client.views_open(trigger_id=body["trigger_id"], view=data)


@app.view("edit_full_name")
def handle_edit_full_name(ack, body, client, logger):
    ack()
    update_query = """
    UPDATE nest_bot.users 
    SET name = %s
    WHERE slack_user_id = %s
    """
    user_id = body["user"]["id"]
    name_new = body["view"]["state"]["values"]["name_new"]["name_new_input"]["value"]
    try:
        cursor.execute(
            update_query,
            (
                name_new,
                user_id,
            ),
        )
        connection.commit()
        status = db_helpers.get_status(cursor=cursor, user_id=user_id)
        if status:
            client.views_update(
                view_id=home_ids[user_id],
                view=approved_home(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=name_new,
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
        else:
            client.views_update(
                view_id=home_ids[user_id],
                view=unapproved_home(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=name_new,
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
    except psql.Error as e:
        error_handling(e)


@app.view("edit_username")
def handle_username(ack, body, client, logger):
    ack()
    update_query = """
    UPDATE nest_bot.users 
    SET tilde_username = %s
    WHERE slack_user_id = %s
    """
    user_id = body["user"]["id"]
    username_new = body["view"]["state"]["values"]["username_new"][
        "username_new_input"
    ]["value"]
    try:
        cursor.execute(
            update_query,
            (
                username_new,
                user_id,
            ),
        )
        connection.commit()
        status = db_helpers.get_status(cursor=cursor, user_id=user_id)
        if status:
            client.views_update(
                view_id=home_ids[user_id],
                view=approved_home(
                    username=username_new,
                    name=db_helpers.get_full_name(cursor=cursor, user_id=user_id),
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
        else:
            client.views_update(
                view_id=home_ids[user_id],
                view=unapproved_home(
                    username=username_new,
                    name=db_helpers.get_full_name(cursor=cursor, user_id=user_id),
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
    except psql.Error as e:
        error_handling(e)


@app.view("edit_email")
def handle_edit_email(ack, body, client, logger):
    ack()
    update_query = """
    UPDATE nest_bot.users 
    SET email = %s
    WHERE slack_user_id = %s
    """
    user_id = body["user"]["id"]
    email_new = body["view"]["state"]["values"]["email_new"]["email_new_input"]["value"]
    try:
        cursor.execute(
            update_query,
            (
                email_new,
                user_id,
            ),
        )
        connection.commit()
        status = db_helpers.get_status(cursor=cursor, user_id=user_id)
        if status:
            client.views_update(
                view_id=home_ids[user_id],
                view=approved_home(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=db_helpers.get_full_name(cursor=cursor, user_id=user_id),
                    email=email_new,
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
        else:
            client.views_update(
                view_id=home_ids[user_id],
                view=unapproved_home(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=db_helpers.get_full_name(cursor=cursor, user_id=user_id),
                    email=email_new,
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
    except psql.Error as e:
        error_handling(e)


@app.action("remove_me")
def handle_delete_user(ack, body, client):
    """
    Delete user view submission

    Called when a user submits a delete request and removes user from PostgreSQL Server
    """
    ack()
    user_id = body["user"]["id"]
    delete_query = """
        DELETE FROM nest_bot.users WHERE slack_user_id=%s
    """
    try:
        cursor.execute(delete_query, (user_id,))
        connection.commit()
        client.views_update(view_id=body["view"]["id"], view=unsigned_home())
    except psql.Error as e:
        error_handling(e)


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()
