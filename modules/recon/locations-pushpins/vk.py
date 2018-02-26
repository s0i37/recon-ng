from recon.core.module import BaseModule
from datetime import datetime
import json

class Module(BaseModule):

	meta = {
		'name': 'VKontakte Geolocation Search',
		'author': 'Soier Z (@s0i37)',
		'description': 'Searches vkontakte for media in the specified proximity to a location.',
		'comments': (
			'Radius must be greater than zero and less than 50000 meters.',
		),
		'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
		'options': (
			('radius', 50, True, 'radius in meters'),
			('start_time', 0, False, 'start time (d.m.Y H:M:S)'),
			('end_time', 0, False, 'end time (d.m.Y H:M:S)')
		),
	}

	def module_run(self, points):
		url = 'https://api.vk.com/method/photos.search.json'
		rad = self.options['radius']
		start_time = datetime.strptime(self.options['start_time'], '%d.%m.%Y %H:%M:%S').strftime("%s") if self.options['start_time'] else 0
		end_time = datetime.strptime(self.options['end_time'], '%d.%m.%Y %H:%M:%S').strftime("%s") if self.options['end_time'] else 0
		for point in points:
			self.heading(point, level=0)
			lat = point.split(',')[0]
			lon = point.split(',')[1]
			offset = 0
			while True:
				payload = {'lat': lat, 'long': lon, 'radius': rad, 'count': 100, 'offset': offset, 'start_time': start_time, 'end_time': end_time }
				resp = self.request(url, payload=payload)
				jsonobj = json.loads(resp.text)
				count = jsonobj["response"][0]
				if not jsonobj["response"][1:]:
					break
				for pushpin in jsonobj["response"][1:]:
					offset += 1
					source = "VK"
					screen_name = pushpin.get('pid')
					profile_name = pushpin.get('owner_id')
					profile_url = "https://vk.com/id%d" % profile_name
					for size in ['src_xxxbig','src_xxbig', 'src_xbig', 'src_big']:
						if pushpin.get(size):
							media_url = pushpin.get(size)
							break
					thumb_url = pushpin.get('src')
					message = pushpin.get('text') or ''
					latitude = pushpin.get('lat') or ''
					longitude = pushpin.get('long') or ''
					try:
						time = datetime.fromtimestamp( pushpin.get('created') )
					except ValueError:
						time = datetime(1970, 1, 1)
					if latitude and longitude:
						self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)