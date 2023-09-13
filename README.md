# Nest Bot - Slack Bot for Nest Registration

Nest Bot is a Slack bot designed to simplify the Nest registration process for users. It allows users to register for Nest using their Slack username and public SSH key.

## Installation and Deployment

Follow these steps to deploy Nest Bot in your environment:

### Prerequisites

- Python 3.8+
- PostgreSQL Database
- Slack App and Bot Token

### Setup the Database

1. Create a PostgreSQL database and schema for Nest Bot:

   ```sql
   CREATE SCHEMA nest_bot;
   ```

2. Create the `users` table to store user registration data:

   ```sql
   CREATE TABLE nest_bot.users (
       id SERIAL PRIMARY KEY,
       slack_user_id VARCHAR(255) UNIQUE NOT NULL,
       tilde_username VARCHAR(255) UNIQUE NOT NULL,
       ssh_public_key TEXT NOT NULL
   );
   ```

3. Grant usage on the `nest_bot` schema to your PostgreSQL user:

   ```sql
   GRANT USAGE ON SCHEMA nest_bot TO your_postgresql_user;
   ```

### Environment Variables

Create a `.env` file in your project's root directory and add the following environment variables:

```dotenv
SLACK_BOT_TOKEN=your_slack_bot_token
SQL_DATABASE="your_database_name"
SQL_HOST="your_database_host"
SQL_USER="your_database_user"
SQL_PASSWORD="your_database_password"
SQL_PORT="your_database_port"
SLACK_APP_TOKEN=your_slack_app_token
```

Replace `your_slack_bot_token`, `your_database_name`, `your_database_host`, `your_database_user`, `your_database_password`, `your_database_port`, and `your_slack_app_token` with your specific values.

### Install Dependencies

Install the required Python dependencies using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Running Nest Bot

Start Nest Bot using the following command:

```bash
python your_app_filename.py
```

Replace `your_app_filename.py` with the name of the Python script where your Nest Bot code is located.
