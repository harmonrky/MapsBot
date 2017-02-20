import praw
import time
import re
import pymysql
import config

# Get reddit instance using registered bot credentials
reddit = praw.Reddit(client_id=config.r_client_id, client_secret=config.r_client_secret, user_agent=config.r_user_agent,
                     username=config.r_username, password=config.r_password)

# Seperate list of locations into two categories, cities and regions, and add label_id
def filter_locations(locations, cities, regions):

    # Label_id is used to keep a city and region of the same word from pairing. e.g. the word
    # "Los Angeles" will produce the city "Los Angeles" and the region "Los Angeles County". These
    # may be paired up later as "Los Angeles, Los Angeles County" which may not be intended
    label_id = 0;
    for word in locations:
        for location in word:
            if (location[6] == "A"):
                loc_list = list(location)
                loc_list.append(label_id)
                regions.append(loc_list)
            else:
                loc_list = list(location)
                loc_list.append(label_id)
                cities.append(loc_list)
        label_id += 1

# Helper function for searching database
def find_locationsb(word, word_list, cursor):
    # Execute sql command using word
    cursor.execute(
        "SELECT * FROM populatedplaces WHERE geonamid IN (SELECT `primary reference` FROM altnames WHERE name = '" + word + "' || name LIKE '" + word + " %') || name = '" + word + "' || name LIKE '" + word + " %' ORDER BY population DESC LIMIT 1;")
    results = cursor.fetchall()

    # If not results found, then return empty list
    if (len(results) == 0):
        return results

    # If a possible location is found, make a search command for the current word + the next word in the list
    if len(word_list) != 0:
        next_word = word_list.pop(0)
        new_word = word + " " + next_word

        # Recurse through words until the string of words returns no results in database
        results = find_locationsb(new_word, word_list, cursor)

        # Head back up recursive calls
        if (len(results) != 0):
            return results
        else:
            word_list.insert(0, next_word)

    # Check if word is found in a set of common words. If so, the word most likely is not referring to a place and
    # therefore should not be used as a location
    cursor.execute("SELECT * FROM commonwords WHERE word = '" + word + "' LIMIT 1;")
    false_local = cursor.fetchall()

    if (len(false_local) != 0):
        return []

    # Conduct an EXACT search for word. Prior searches may have returned similiarly named but not exact locations
    cursor.execute(
        "SELECT * FROM populatedplaces WHERE geonamid IN (SELECT `primary reference` FROM altnames WHERE name = '" + word + "') || name = '" + word + "' ORDER BY population DESC;")
    results = cursor.fetchall()
    return results

# Search database for locations
def find_locations(word_list, cursor):
    locations_list = []
    # Iterate over word_list and process each word
    while len(word_list) != 0:
        word = word_list.pop(0)
        location = find_locationsb(word, word_list, cursor)

        # Add location to list if word was found in database
        if (len(location) != 0):
            locations_list.append(location)

    return locations_list


# Search given list of words for populated locations
def location_search(word_list):
    # Connect to database and create cursor
    db = pymysql.connect(host=config.sql_host, port=config.sql_port, user=config.sql_user, passwd=config.sql_password,
                         db=config.sql_db)
    cursor = db.cursor()

    # Search database for matching locations in word_list
    results = find_locations(word_list, cursor)

    # No mathes found, return black string
    if (len(results) == 0):
        return ""

    # Seperate list of locations into two categories: cities and regions
    cities = []
    regions = []
    filter_locations(locations=results, cities=cities, regions=regions)
    del results

    # Sort lists by location populations in descending order
    regions = sorted(regions, key=lambda location: location[14], reverse=True)
    cities = sorted(cities, key=lambda location: location[14], reverse=True)

    # If only city locations are found, return name of most populated city in list
    if len(regions) == 0:
        return cities[0][1]

    # If only region locations are found, return name of most populated region in list
    if (len(cities) == 0):
        return regions[0][1]

    # Check for matches between cities and regions and pair accordingly e.g. city of "Los Angeles"
    # and state of "California" would be paired as "Los Angeles, California" before being returned
    for city in cities:
        for region in regions:
            # Check if city and region have matching country codes but do not have matching word ID's
            if (region[8] == city[8]) and (region[19] != city[19]):
                # Check if city and region have state codes (only used for us cities/regions)
                if (not region[10].isnumeric() or not city[10].isnumeric()):
                    if (region[10] == city[10]):
                        return city[1] + ", " + region[1]
                else:
                    return city[1] + ", " + region[1]

    # Return most populated city by default
    return cities[0][1]


# Funcion for reformatting title name and call on location_search
def parse_title(title):
    # Split string into an array of words
    word_list = title.split()
    temp_word_list = []

    # Strip out unwanted special characters
    for word in word_list:
        word = re.sub('[(\[\].,!?/;:%"]', '', word)
        word = re.sub("'s", '', word)
        word = re.sub("'", "\\'", word)

        temp_word_list.append(word)
    word_list = temp_word_list

    # Search for location using formatted words
    return location_search(word_list)


# Function for commenting on submission
def post_comment(submission, searchterm):
    # Replace spaces with '+" and strip out commas
    formatted_searchterm = re.sub(' ', '+', searchterm)
    formatted_searchterm = re.sub(',', '', formatted_searchterm)

    # Generate link using google maps url parameters
    url = "http://google.com/maps/search/" + formatted_searchterm

    # Generate comment
    comment_body = config.comment_body(searchterm, url)

    # Post comment to submission
    submission.reply(comment_body)


if __name__ == "__main__":
    # Keep track of which submissions the bot has processed and commented on
    id_list = []

    # Bot will run every 30 minutes. Can be changed using time.sleep() function at end of loop
    while 1:
        # Get subreddit instance
        subreddit = reddit.subreddit(config.r_subreddit_name)

        # List of submissions to be processed
        sub_list = []
        for submission in subreddit.new():
            # Check if submission has already been processed
            if submission.id not in id_list:
                sub_list.append(submission)
                # Add subreddit id to list once added to sub_list
                id_list.insert(0, submission.id)

                # subreddit.new() returns a maximum of 100 newest posts. Therefore, it is safe to keep the queue at only 100 elements
                if len(id_list) > 100:
                    id_list.pop(100)
        # Iterate over submissions
        for submission in sub_list:
            # Find location referred to in submission and return the name as a string
            searchterm = parse_title(title=submission.title)
            print(searchterm)
            # Don't post comment if not location was found
            if (searchterm != ""):
                # Use searchterm found in parse_title to post a comment on given submission
                post_comment(submission, searchterm)
        time.sleep(1800)
