from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
import psycopg2 as psql
from utils import error_handling
import helpers.db_helpers as db_helpers
import json
import re
import httpx
from datetime import datetime, timezone


load_dotenv()

slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_app_token = os.environ.get("SLACK_APP_TOKEN")

app = App(token=slack_bot_token)
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


def populate_users():
    try:
        url = "http://127.0.0.1:41896/check_conflict"
        response = httpx.get(url=url)
        users = response.json()
        slack_user_id = 0
        insert_query = db_helpers.read_sql_query("sql/register_user.sql")
        description = "Populated by populate_users() function"
        epoch_start = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        for user in users:
            username = user.get("username")
            name = user.get("name")
            email = user.get("email")
            sshKey = (
                user["attributes"].get("sshPublicKey") if "attributes" in user else None
            )
            if sshKey is None:
                sshKey = "None supplied by populate_users()"
            slack_user_id = slack_user_id - 1
            cursor.execute(
                insert_query,
                (
                    slack_user_id,
                    name,
                    email,
                    username,
                    sshKey,
                    description,
                    epoch_start,
                ),
            )
            connection.commit()
    except Exception as e:
        print(e)


def authorize(slack_user_id):
    url = "http://127.0.0.1:41896/register_user"
    selectUser = db_helpers.read_sql_query("sql/selectUserFromSlackID.sql")
    cursor.execute(
        selectUser,
        [slack_user_id],
    )
    result = cursor.fetchone()
    username = result[2]
    name = result[3]
    email = result[4]
    attributes = {"sshPublicKey": result[5]}
    dataInDict = {
        "username": username,
        "name": name,
        "email": email,
        "attributes": attributes,
        # Optionals
        "pk": None,
        "is_active": None,
        "last_login": None,
        "is_superuser": None,
        "groups": None,
        "avatar": None,
        "uid": None,
        "path": None,
        "type": None,
    }
    try:
        response = httpx.post(url=url, data=json.dumps(dataInDict))
        password = json.loads(response.text)
        if response.status_code == 200:
            return password.get("password")
        else:
            return False
    except Exception as e:
        pass


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


def send_message(client, user_id, name, username, email, ssh_key, description):
    with open("json/send_message.json", "r") as read_file:
        data = json.load(read_file)
    details = {
        "name": name,
        "username": username,
        "email": email,
        "ssh_key": ssh_key,
        "description": description,
    }
    data[0]["text"]["text"] = data[0]["text"]["text"].format(slack_user=user_id)

    data[1]["text"]["text"] = data[1]["text"]["text"].format(**details)
    client.chat_postMessage(
        channel="C05VBD1B7V4",  # the private nest-registration channel ID
        blocks=data,
        text=f"<@{user_id}> is requesting an approval for Nest",
    )


@app.event("app_home_opened")
def initial_home_tab(client, event, logger):
    """
    Handle the app home tab opening event.

    This function is triggered when a user opens the app's home tab. It checks whether the user
    is already registered and publishes the appropriate view (signed or not signed) accordingly.
    """

    try:
        user_id = event["user"]
        username = client.users_profile_get(user=user_id)["profile"]["display_name"]
        # home_ids[user_id] = event["view"]["id"]
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
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
        elif name != None and not status:
            client.views_publish(
                user_id=event["user"],
                view=unapproved_home(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=name,
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_ssh_key(cursor=cursor, user_id=user_id),
                ),
            )
        else:
            client.views_publish(
                user_id=event["user"],
                view=unsigned_home(),
            )

    except Exception as e:
        print(e)
        # error_handling(e)


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
    """

    insert_query = db_helpers.read_sql_query("sql/register_user.sql")
    errors = {}
    slack_user_id = body["user"]["id"]
    username = body["view"]["state"]["values"]["username"]["username_input"]["value"]
    name = body["view"]["state"]["values"]["name"]["name_input"]["value"]
    email = body["view"]["state"]["values"]["email"]["email_input"]["value"]
    ssh_key = body["view"]["state"]["values"]["ssh_key"]["ssh_key_input"]["value"]
    description = body["view"]["state"]["values"]["description"]["description_input"][
        "value"
    ]
    current_utc_time = datetime.now(timezone.utc)
    selectUser = db_helpers.read_sql_query("sql/selectUser.sql")
    if username is not None:
        cursor.execute(
            selectUser,
            [username],
        )
        result = cursor.fetchone()
        if result is not None and result[0] == username:
            errors["username"] = "The username is taken. Please choose another username"
            ack(response_action="errors", errors=errors)
            return
    if email is not None:
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.match(email_pattern, email):
            errors["email"] = "Invalid email"
            ack(response_action="errors", errors=errors)
            return
    if ssh_key is not None:
        ssh_pattern = r"ssh-(ed25519|rsa|dss|ecdsa) AAAA(?:[A-Za-z0-9+\/]{4})*(?:[A-Za-z0-9+\/]{2}==|[A-Za-z0-9+\/]{3}=|[A-Za-z0-9+\/]{4})( [^@]+@[^@]+)?"
        if not re.match(ssh_pattern, ssh_key):
            errors["ssh_key"] = "Invalid ssh_key"
            ack(response_action="errors", errors=errors)
            return
    if description is not None and len(description) < 10:
        errors["description"] = "The description should be larger than 10 characters."
        ack(response_action="errors", errors=errors)
        return
    ack()
    try:
        cursor.execute(
            insert_query,
            (
                slack_user_id,
                name,
                email,
                username,
                ssh_key,
                description,
                current_utc_time,
            ),
        )
        connection.commit()
        send_message(client, slack_user_id, name, username, email, ssh_key, description)
        client.views_publish(
            user_id=slack_user_id,
            view=unapproved_home(
                username=username, name=name, email=email, ssh_key=ssh_key
            ),
        )
        client.chat_postMessage(
            channel=slack_user_id,
            text="Keep an eye out in your DMs -  you'll recieve a notification within 24 hours about your approval status!",
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
    update_query = db_helpers.read_sql_query("sql/update_full_name.sql")
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


@app.view("edit_email")
def handle_edit_email(ack, body, client, logger):
    update_query = db_helpers.read_sql_query("sql/update_email.sql")
    user_id = body["user"]["id"]
    email_new = body["view"]["state"]["values"]["email_new"]["email_new_input"]["value"]
    errors = {}
    if email_new is not None:
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.match(email_pattern, email_new):
            errors["email_new"] = "Invalid email"
            ack(response_action="errors", errors=errors)
            return
    ack()
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


# Disabled in production
# @app.action("remove_me")
# def handle_delete_user(ack, body, client):
#     """
#     Delete user view submission

#     Called when a user submits a delete request and removes user from PostgreSQL Server
#     """
#     ack()
#     user_id = body["user"]["id"]
#     delete_query = db_helpers.read_sql_query("sql/delete_user.sql")
#     try:
#         cursor.execute(delete_query, (user_id,))
#         connection.commit()
#         client.views_update(view_id=body["view"]["id"], view=unsigned_home())
#     except psql.Error as e:
#         error_handling(e)


@app.action("approve_action")
def handle_approve_action(ack, body, client):
    ack()
    update_query = db_helpers.read_sql_query("sql/update_status.sql")
    admin_user_id = body["user"]["id"]
    thread_ts = body["container"]["message_ts"]
    channel_id = body["container"]["channel_id"]
    block = body["message"]["blocks"]
    new_text = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Approved by <@{admin_user_id}>",
        },
    }
    user_id = re.findall(r"<@(\w+)>", block[0]["text"]["text"])[0]
    block[2] = new_text
    client.chat_postMessage(
        channel=user_id,
        text=f"Your request to get access to Nest has been approved!",
    )
    client.chat_update(
        channel=channel_id,
        ts=thread_ts,
        blocks=block,
        text=f"Approved by <@{admin_user_id}>",
    )
    client.chat_postMessage(
        channel=channel_id, thread_ts=thread_ts, text=f"Approved by <@{admin_user_id}>"
    )
    try:
        password = authorize(user_id)
        if password != False:
            with open("json/markdown_message.json", "r") as read_file:
                pwd_blocks = json.load(read_file)
            pwd_blocks[0]["text"][
                "text"
            ] = f"Your password for your Nest account is `{password}`. Please continue through our Quickstart guide at https://guides.hackclub.app/index.php/Quickstart#Creating_an_Account."
            client.chat_postMessage(
                channel=user_id,
                blocks=pwd_blocks,
                text="Your password for your Nest account is {password}. Please continue through our Quickstart guide at https://guides.hackclub.app/index.php/Quickstart#Creating_an_Account.",
            )
        cursor.execute(update_query, (user_id,))
        connection.commit()

    except psql.Error as e:
        error_handling(e)


@app.action("deny_action")
def handle_deny_action(ack, body, client):
    ack()
    delete_query = db_helpers.read_sql_query("sql/delete_user.sql")
    admin_user_id = body["user"]["id"]
    thread_ts = body["container"]["message_ts"]
    channel_id = body["container"]["channel_id"]
    block = body["message"]["blocks"]
    new_text = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Denied by <@{admin_user_id}>",
        },
    }
    user_id = re.findall(r"<@(\w+)>", block[0]["text"]["text"])[0]
    block[2] = new_text
    client.chat_postMessage(
        channel=user_id,
        text=f"Your request to get access to Nest has been denied. Please DM <@{admin_user_id}> for more information.",
    )
    client.chat_update(
        channel=channel_id,
        ts=thread_ts,
        blocks=block,
        text=f"Denied by <@{admin_user_id}>",
    )
    client.chat_postMessage(
        channel=channel_id, thread_ts=thread_ts, text=f"Denied by <@{admin_user_id}>"
    )
    try:
        cursor.execute(delete_query, (user_id,))
        connection.commit()
    except psql.Error as e:
        error_handling(e)


# Start your app
if __name__ == "__main__":
    # populate_users()
    SocketModeHandler(app, slack_app_token).start()
