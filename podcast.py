from rastadb import config_db, podcast_db
import os
import requests
import re
from discord import Activity, ActivityType


def get_image(url):
	img_data = requests.get(url).content
	return img_data


def download_image(url, name):
	os.chdir('/home/runner/RastaBot/all_images/')
	img_data = get_image(url)
	print('Downloaded {}'.format(name))
	with open(name, 'wb') as handler:
		handler.write(img_data)
		print('Wrote {}'.format(name))
	return img_data


def check_new():
	channel = "https://www.youtube.com/c/TheGrowFromYourHeartPodcast"
	html = requests.get(channel + "/videos").text
	index = html.find("{\"videoId\":\"") + 12
	try:
		title = re.search('(?<={"text":").*?(?="})', html).group()
	except:
		return None, None, None
	url = 'https://www.youtube.com/watch?v={}'.format(html[index:index + 11])
	number = int(title[1:4])

	if number <= int(podcast_db.get_current('number')):
		return None, None, None

	return title, url, number


async def auto_status(client, irie_guild):
	if podcast_db.get_auto_status():
		name, url, num = check_new()
		if num:
			podcast_db.new_podcast(num, name, url)
			bot_channel = irie_guild.get_channel(config_db.bot_channel_id)
			gfyh_podcast_channel = irie_guild.get_channel(podcast_db.podcast_channel_id)
			await bot_channel.send('Found a new podcast. Updating')
			await gfyh_podcast_channel.send("Episode {} of the Grow From Your Heart ({}) podcast has been posted! \n {}".format(num, name, url))
			print('New podcast found: {} at {}'.format(num, url))
		await client.change_presence(activity = Activity(type = ActivityType.streaming, name='GFYH Podcast #{}'.format(num, url=url)))

print('Loaded podcast.py')