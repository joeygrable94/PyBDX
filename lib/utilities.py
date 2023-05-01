import unicodedata
import re
from phpserialize import *


def getDict( object ):
	# as dict
	tmp_dict = {}
	data_attrs = [a for a in dir( object ) if not a.startswith('_') and not callable(getattr( object, a ))]
	for attribute in data_attrs:
		if getattr( object, attribute ):
			tmp_attr = getattr( object, attribute )
			if type(tmp_attr) is list:
				tmp_dict[attribute] = dumps( tmp_attr ).decode("utf-8")
			else:
				tmp_dict[attribute] = tmp_attr
	return tmp_dict

def unpackOrderedDict(dictionary):
	# take an input OrderedDict object
	items = {}
	# order dict of items how they arrived
	for index, ddata in dictionary.items():
		items[index] = ddata
	# return a dictionary of items
	return items

def tab(num):
	# return a tabbed string X times
	return '\t'*num

def trimEndSpaces( string ):
	tmp = string
	if tmp[0] == ' ' or tmp[-1] == ' ':
		if tmp[0] == ' ':
			tmp = tmp[1:]
		if tmp[-1] == ' ':
			tmp = tmp[:-1]
		return trimEndSpaces(tmp)
	else:
		return tmp

def slugify(value, allow_unicode=False):
	# Slugify => https://github.com/django/django/blob/master/django/utils/text.py
	value = str(value)
	if allow_unicode:
		value = unicodedata.normalize('NFKC', value)
	else:
		value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
	value = re.sub(r'[^\w\s-]', '', value.lower())
	return re.sub(r'[-\s]+', '-', value).strip('-_')

def sumDictKeyValues( dictionary ):
	total = 0
	for key in dictionary.keys():
		total += int( dictionary[key] )
	return str(total)

def filterName( filter_list, name ):
	for rm_str in filter_list:
		name = ''.join(name.split( rm_str ))
	if '- ' in name:
		name = re.sub(r'- ', ' ', name)
	if ' -' in name:
		name = re.sub(r' -', ' ', name)
	return name

def formatImageData( key, slug, data_list ):
	output = []
	img_num = 0
	for item in data_list:
		img_num += 1
		title = item.attrs['Title'] if item.attrs.get('Title') else ''
		cap = item.attrs['Caption'] if item.attrs.get('Caption') else ''
		if '' != title or '' != cap:
			output.append( {
				'type': key,
				'src': item.text,
				'slug': '%s-%s' % (slug, img_num),
				'title': title,
				'caption': cap
			} )
	if len(output) > 0:
		return output
	else:
		return [{}]

def BDXgetMatchingWPID( needle, haystack ):
	# if matching BDX slug indexed
	if needle in haystack:
		# return this BDX slug's WP ID
		return haystack[needle]
	else:
		# search the needle substrings
		needles = needle.split('-')
		for straw in needles:
			# in the haystack keys
			for barrel in haystack.keys():
				if straw in barrel:
					# return this BDX slug's WP ID
					return haystack[barrel]
		# return no ID found
		return -1
