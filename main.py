from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
import psycopg2 as psql
import logging
import db_helpers 

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

def home_tab_view_signed(username, name, email, ssh_key):
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Nest Bot"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hey there, I'm Nest Bot! My main gig is simplifying the Nest registration process for you. Just provide your details, and I'll handle the rest.",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Your Tilde Username:* {username}",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": "edit_username",
                    "action_id": "edit_username",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Your Full Name is:* {name}",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": "edit_full_name",
                    "action_id": "edit_full_name",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Your E-Mail is:* {email}",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": "edit_email",
                    "action_id": "edit_email",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Your SSH public key is:* `{ssh_key}`",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": "edit_ssh_key",
                    "action_id": "edit_ssh_key",
                },
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Delete me!",
                            "emoji": True,
                        },
                        "style": "danger",
                        "value": "remove_me",
                        "action_id": "remove_me",
                    },
                ],
            },
        ],
    }


def home_tab_view_not_signed():
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Nest Bot"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hey there, I'm Nest Bot! My main gig is simplifying the Nest registration process for you. Just provide your details, and I'll handle the rest.",
                },
            },
            {
                "type": "divider",
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Register yourself!",
                            "emoji": True,
                        },
                        "style": "primary",
                        "value": "register_user",
                        "action_id": "register_user",
                    }
                ],
            },
        ],
    }


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
        # Checks if the user is already registered and publishes the view accordingly
        if name != None:
            client.views_publish(
                user_id=event["user"],
                view=home_tab_view_signed(
                    username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                    name=name,
                    email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                    ssh_key=db_helpers.get_email(cursor=cursor, user_id=user_id),
                ),
            )
        else:
            client.views_publish(
                user_id=event["user"],
                view=home_tab_view_not_signed(),
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
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "callback_id": "register_user",
            # "previous_view_id": f"{body['view'][;d"]}",
            "type": "modal",
            "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
            "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
            "title": {"type": "plain_text", "text": "Register for Nest", "emoji": True},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": f":wave: Hey {profile_name}!\n\nPlease enter the required details to register for Nest!",
                        "emoji": True,
                    },
                },
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "username",
                    "label": {
                        "type": "plain_text",
                        "text": "What is your username?",
                        "emoji": True,
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "username_input",
                    },
                },
                {
                    "type": "input",
                    "block_id": "name",
                    "label": {
                        "type": "plain_text",
                        "text": "What is your Full Name?",
                        "emoji": True,
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "name_input",
                    },
                },
                {
                    "type": "input",
                    "block_id": "email",
                    "label": {
                        "type": "plain_text",
                        "text": "What is your E-Mail?",
                        "emoji": True,
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "email_input",
                    },
                },
                {
                    "type": "input",
                    "block_id": "ssh_key",
                    "label": {
                        "type": "plain_text",
                        "text": "What is your public SSH Key?",
                        "emoji": True,
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "ssh_key_input",
                        "multiline": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "description",
                    "label": {
                        "type": "plain_text",
                        "text": "What will you use nest for?",
                        "emoji": True,
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "description_input",
                        "multiline": True,
                    },
                },
            ],
        },
    )


@app.view("register_user")
def handle_register_user(ack, body, client):
    """
    Handle user registration view submission.

    This function is called when a user submits their registration details through a Slack modal view.
    It inserts the provided details into the PostgreSQL server.
    """
    ack()
    insert_query = """
    INSERT INTO nest_bot.users (slack_user_id, name, email, tilde_username, ssh_public_key, description)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    slack_user_id = body["user"]["id"]
    username = body["view"]["state"]["values"]["username"]["username_input"]["value"]
    name = body["view"]["state"]["values"]["name"]["name_input"]["value"]
    email = body["view"]["state"]["values"]["email"]["email_input"]["value"]
    ssh_key = body["view"]["state"]["values"]["ssh_key"]["ssh_key_input"]["value"]
    description = body["view"]["state"]["values"]["description"]["description_input"][
        "value"
    ]
    try:
        cursor.execute(
            insert_query, (slack_user_id, name, email, username, ssh_key, description)
        )
        connection.commit()
        client.views_publish(
            user_id=slack_user_id,
            view=home_tab_view_signed(
                username=username, name=name, email=email, ssh_key=ssh_key
            ),
        )
    except psql.Error as e:
        error_handling(e)


@app.action("edit_full_name")
def edit_full_name(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "edit_full_name",
            "title": {"type": "plain_text", "text": "Nest Bot", "emoji": True},
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Edit Full Name",
                        "emoji": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "name_new",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "name_new_input",
                    },
                    "label": {"type": "plain_text", "text": "New Name", "emoji": True},
                },
            ],
            "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
            "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        },
    )


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
        client.views_update(
            view_id=home_ids[user_id],
            view=home_tab_view_signed(
                username=db_helpers.get_username(cursor=cursor, user_id=user_id),
                name=name_new,
                email=db_helpers.get_email(cursor=cursor, user_id=user_id),
                ssh_key=db_helpers.get_email(cursor=cursor, user_id=user_id),
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
        client.views_update(view_id=body["view"]["id"], view=home_tab_view_not_signed())
    except psql.Error as e:
        error_handling(e)


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()
