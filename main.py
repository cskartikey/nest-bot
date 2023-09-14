from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
import psycopg2 as psql

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
)

cursor = connection.cursor()


def home_tab_view_signed(username, ssh_key):
    return {
        "type": "home",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hey there, I'm Nest Bot! My main gig is simplifying the Nest registration process for you. Just provide your username and public SSH key, and I'll handle the rest, ensuring a smooth and secure entry into Nest.",
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
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hey there, I'm Nest Bot! My main gig is simplifying the Nest registration process for you. Just provide your username and public SSH key, and I'll handle the rest, ensuring a smooth and secure entry into Nest.",
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
    select_query = """
    SELECT * FROM nest_bot.users
    WHERE slack_user_id = %s;
    """
    cursor.execute(select_query, (user_id,))
    result = cursor.fetchone()
    # Checks if the user is already registered and publishes the view accordingly
    if result != None:
        client.views_publish(
            user_id=event["user"],
            view=home_tab_view_signed(username=result[2], ssh_key=result[3]),
        )
    else:
        client.views_publish(
            user_id=event["user"],
            view=home_tab_view_not_signed(),
        )


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
    INSERT INTO nest_bot.users (slack_user_id, tilde_username, ssh_public_key)
    VALUES (%s, %s, %s);
    """
    slack_user_id = body["user"]["id"]
    username = body["view"]["state"]["values"]["username"]["username_input"]["value"]
    ssh_key = body["view"]["state"]["values"]["ssh_key"]["ssh_key_input"]["value"]
    cursor.execute(insert_query, (slack_user_id, username, ssh_key))
    connection.commit()

@app.view("delete_user")
def handle_delete_user(ack, body, client):
    """
    Delete user view submission

    Called when a user submits a delete request and removes user from PostgreSQL Server
    """
    ack()
    # check if user exists

    user_id = body["user"]["id"]
    select_query = """
    SELECT * FROM nest_bot.users
    WHERE slack_user_id = %s;
    """
    cursor.execute(select_query, (user_id,))
    result = cursor.fetchone()

    if result is None:
        delete_query = """
            DELETE FROM nest_bot.users WHERE slack_user_id=%s
        """
        cursor.execute(delete_query, (user_id))
        connection.commit()
    else:
        # show an error, dont know how to do that yet
        pass

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()
