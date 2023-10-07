UPDATE nest_bot.users 
SET is_approved = true
WHERE slack_user_id = %s