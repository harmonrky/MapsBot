#Config file for important reddit and sql access info. Do not leave fields blank!
r_client_id = ''
r_client_secret = ''
r_user_agent = ''
r_username = ''
r_password = ''
r_subreddit_name = ''
sql_host = ''
sql_port = 0
sql_user = ''
sql_password = ''
sql_db = ''

#The format of comments posted by the bot can be edited here
def comment_body(searchterm, url):
    return "**Google Maps search for:**\n\n[" + searchterm + "](" + url +")\n\nI am a bot in beta. If I get something wrong, please send me a PM. **BEEP BOOP.**"