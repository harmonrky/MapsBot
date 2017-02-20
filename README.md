# MapsBot
I wanted to work on my Python and MySQL skills so I decided to create a reddit bot. The bot's functionality isn't really all that useful
as it only saves a few keystrokes but the I think the search algorithm used is rather interesting and may be useful in future projects.
I created the bot with the intention of using it on subreddits such as "r/cityporn" (just skyline pics, no obsenities!) where the names of locations
are often used in post titles. The bot's goal is to take a submission's title and compare it with a database of populated global locations. If a 
location is found, a google maps link is generated using the location as a search term. For example, if the post title is "The wonderful
beaches of Los Angeles, CA", the bot would generate the search term "Los Angeles, California" and would reply to the post with 
https://google.com/maps/search/los+angeles+california.

Based on my testing, the bot works rather well with only occational incorrect results. This current build, however, has the limitation of 
only returning one location. This means that if a title contains multiple location names, only the most specific location (city name, region name)
or most populous location will be returned. While not ideal, this functionality can be fixed in the future by adding a bit more complexity 
to the search algorithm.

As stated before, this reddit bot isn't all that useful. However, the ability to identify a location given a string of text could be rather 
useful in other projects.

The database used with the bot can be found at https://drive.google.com/open?id=0B_Ofjq44vQ3vNlF3OE5zam9PU0E. This database contains edited 
data derived from the information available at http://www.geonames.org/ and http://corpus.byu.edu/
