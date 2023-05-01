# ---------------------------------------------------------------------------
# IMPORTS
import os, shutil, json, csv
from datetime import datetime
import paramiko
import pandas as pd
from ftplib import FTP
from zipfile import ZipFile
from urllib.request import urlretrieve
from .constants import *
from .DataSoup import BDXDataSoup



class DataFile():

	def __init__( self, file ):
		filebase = file.split('.')
		fileparts = filebase[0].split('-')
		self.file = file
		self.name = filebase[0]
		self.ext = filebase[-1]
		self.client_id = fileparts[0]
		self.type = fileparts[1]
		self.src = f'{DATA_PATH}/{fileparts[0]}'
		self.date = self.stamp_date( fileparts )

	def __repr__( self ):
		return f"<DataFile name='{self.client_id} {self.type.capitalize()}'>"

	def dataframe( self ):
		# create a dictionary
		data = {}
		if os.path.exists( f'{self.src}/{self.file}' ):
			# df = pd.read_csv( f'{self.src}/{self.file}' )
			# return df
			# Open a csv reader called DictReader
			with open( f'{self.src}/{self.file}', encoding='utf-8') as csvf:
				csvReader = csv.DictReader(csvf)
				# Convert each row into a dictionary
				# and add it to data
				count = 0
				for rows in csvReader:
					data[count] = rows
					count += 1
		# return the data
		return data

	@staticmethod
	def stamp_date( str_parts ):
		if str_parts[-1] == 'current':
			filedate = datetime.today().strftime('%Y-%m-%d')
		else:
			filedate = f'{str_parts[-3]}-{str_parts[-2]}-{str_parts[-1]}'
		return filedate



class DataFileHandler():

	data = set()
	groups = []

	def __init__( self, key, filetype='' ):
		self.client_key = key
		self.filetype = filetype
		for file in os.listdir( f'{DATA_PATH}/{key}' ):
			if not file[0] in ['_','.'] and file.split('.')[-1] == filetype:
				self.add( file )

	def __repr__( self ):
		return f"<DataFileHandler client='{self.client_key}' n='{len(self.data)}'>"

	def add( self, file ):
		is_current = ( file.split('.')[0].split('-')[-1] == 'current' )
		is_source = ( file.split('.')[0].split('-')[-1] == self.client_key )
		if not is_current and not is_source:
			dfile = DataFile( file )
			self.data.add( dfile )

	def sort( self ):
		# sort data set by the data file data attr
		self.data = sorted( list(self.data),
			key=lambda k: datetime.strptime(k.date, '%Y-%m-%d'),
			reverse=True )
		# break files into groups by date
		group = []
		last_date = None
		date_changed = False
		for item in self.data:
			if type(last_date) is str:
				date_changed = ( not last_date == item.date ) if True else False
			last_date = item.date
			if date_changed:
				self.groups.append( group )
				group.clear()
			group.append( item )

	def latest( self ):
		try:
			latest_file = self.groups[0]
			latest_data = dict()
			# loop each index and 
			for index in range( 0, len(latest_file) ):
				latest_data[latest_file[index].type] = latest_file[index]
			return latest_data
		except Exception as e:
			return exit( e )

	def previous( self, n=1):
		try:
			previous_file = self.groups[n]
			previous_data = dict()
			# loop each index and set previous data dict
			for index in range( 0, len(previous_file) ):
				previous_data[previous_file[index].type] = previous_file[index]
			return previous_data
		except Exception as e:
			return exit( e )



# ----------------------------------------------------------------------------------------
# PYTHON BDX DATA FEED WRANGLER
class PyBDX():
	data_files = []
	xml_files = None
	csv_files = None
	data = None

	def __repr__( self ):
		return 'PyBDX key=%s' % ( self.key )

	def __init__( self, client, download=False, analyze=False, convert=False, upload=False ):
		self.client = client
		self.key = client.BDX_FEED_XML_FILE_ID
		self.client_data_path = '%s/%s' % ( DATA_PATH, client.BDX_FEED_XML_FILE_ID )
		self.checkDataDirectories()
		self.formatFileNames()
		# download new datafiles
		if download:
			zip_download = self.downloadDataFromBDX()
			self.data_files = self.decompressDataFiles( zip_download )
			self.key = self.data_files[0].split('.')[:-1][0]
		# copy latest file to a current copy to manipulate
		resource = self.makeCurrentDataFiles()
		# data wrangling (the magic ✨)
		if analyze:
			preload_data = BDXDataSoup( resource, client )
			print(preload_data)
			# if converting data to update CSV import files
			if convert:
				# iterate each json list to convert to csv
				for data_key in preload_data.json:
					self.saveDataToAllImportCSV(
						data_key = data_key,
						json_data = preload_data.json[data_key],
						upload = upload )
		# compiling csv data
		# self.csv_files = self.getClientDataCSV()
		self.xml_files = self.getClientDataXML()

	@staticmethod
	def print( obj: object, keys: list) -> None:
		display = [ getattr(obj, pkey) for pkey in keys if hasattr(obj, pkey) ]
		print('\n'.join(display))

	@staticmethod
	def ReheatSoup( resource, client ):
		warm_soup = None
		# if a data file exists
		if os.path.isfile( resource ):
			warm_soup = BDXDataSoup( resource, client )
		return warm_soup

	def loadDataFromCsv( self, key='plans', datafile=None ):
		# get pandas dataframe
		if datafile is not None:
			key_data = datafile[key].dataframe()
			all_items = []
			for row in key_data:
				raw_data = {}
				for node in key_data[row].keys():
					raw_data[node] = key_data[row][node]
				all_items.append(raw_data)
			return all_items

	def getClientDataXML( self ):
		xml_archive = DataFileHandler( self.key, 'xml' )
		xml_archive.sort()
		return xml_archive

	def getClientDataCSV( self ):
		csv_archive = DataFileHandler( self.key, 'csv' )
		csv_archive.sort()
		return csv_archive

	@staticmethod
	def findMatchingCPT( needle, haystack=[] ):
		if type(needle) is list and len(needle) > 0:
			needle = needle[0]
		for check in haystack:
			if needle == check.wp_cpt_id:
				return check
		return None

	@staticmethod
	def findMatchingPlan( needle, haystack=[] ):
		for check in haystack:
			if needle.name == check.name \
				and needle.builder == check.builder \
				and needle.subdiv  == check.subdiv:
				return check
		return None

	@staticmethod
	def calcPlanPricing( previous, current ):
		# if we have previous plan data
		# and the previous plan price is different than current
		if previous is not None:
			if current.actual_price != previous.actual_price:
				plan_diff = float(current.actual_price) - float(previous.actual_price)
				plan_diff_str = '+' + str(int(plan_diff)) if plan_diff > 0 else str(int(plan_diff))
				plan_price = f'$ { current.actual_price } ({ current.base_price }) —> Δ { plan_diff_str }'
			else:
				plan_price = f'$ { current.actual_price } ({ current.base_price })'
		else:
			plan_price = f'$ { current.actual_price } ({ current.base_price })'
		return plan_price

	def checkDataDirectories( self ):
		if not os.path.exists( self.client_data_path ):
			os.mkdir( self.client_data_path )
		return True

	def formatFileNames( self ):
		# format the data file names and paths
		now = datetime.now()
		year = '{:02d}'.format(now.year)
		month = '{:02d}'.format(now.month)
		day = '{:02d}'.format(now.day)
		# todays date as a string
		self.todaystr = '{}-{}-{}'.format(year, month, day)
		self.xml_file_today = '%s-%s.xml' % ( self.key, self.todaystr )
		self.xml_file_current = '%s-%s.xml' % ( self.key, 'current' )

	def downloadDataFromBDX( self ):
		# connect to host, and download ZIP data files
		ftp = FTP( self.client.BDX_SERVERHOST )
		ftp.login(
			user = self.client.BDX_USERNAME,
			passwd = self.client.BDX_PASSWORD )
		files = []
		download_path = ''
		# loop files in BDX FTP source
		for file in ftp.nlst():
			download_path = self.client.BDX_SERVER_PATH + ftp.pwd()
			# only grab the zip file
			if 'zip' == file.split( '.' )[-1].lower():
				download_path = '%s/%s' % ( download_path, file )
			# download the file
			download_zip = os.path.join( DATA_PATH, self.key, file )
			loc_file = open(download_zip, "wb")
			ftp.retrbinary( "RETR " + file, loc_file.write, 8*1024 )
			loc_file.close()
			# track the files downloaded
			files.append( download_zip )
		# return the list of files downloaded
		return files

	def decompressDataFiles( self, zip_files ):
		# list of xml files in zip
		xmlfiles = []
		# loop provided files
		for file in zip_files:
			# opening the zip file in READ mode
			zipf = ZipFile( file, 'r' )
			# extracting all the files
			zipf.extractall( '%s/%s' % ( DATA_PATH, self.key ) )
			xmlfiles = zipf.namelist()
			# delete the zip file
			os.remove( file )
		# return the list of xml files
		return xmlfiles

	def makeCurrentDataFiles( self ):
		# src file exists but today's
		if os.path.isfile( '%s/%s/%s.xml' % ( DATA_PATH, self.key, self.key ) ) and not os.path.isfile( '%s/%s/%s' % ( DATA_PATH, self.key, self.xml_file_today ) ):
			# copy the src file and rename it with today's date
			shutil.copy( '%s/%s/%s.xml' % ( DATA_PATH, self.key, self.key ), '%s/%s/%s' % ( DATA_PATH, self.key, self.xml_file_today ) )
		# today's data exists
		if os.path.isfile( '%s/%s/%s' % ( DATA_PATH, self.key, self.xml_file_today ) ):
			# copy today's data file and rename it with the "current" tag
			shutil.copy( '%s/%s/%s' % ( DATA_PATH, self.key, self.xml_file_today ), '%s/%s/%s' % ( DATA_PATH, self.key, self.xml_file_current ) )
		# return a bool, and the path to the current data file
		return '%s/%s/%s' % ( DATA_PATH, self.key, self.xml_file_current )

	def saveDataToAllImportCSV( self, data_key, json_data, upload ):
		csv_file_today = '%s-%s-%s.csv' % ( self.key, data_key, self.todaystr )
		csv_file_current = '%s-%s-current.csv' % ( self.key, data_key )
		# save Today's json data to a csv file
		self._saveJSONtoCSV( data=json_data, file_name=csv_file_today )
		# save Current the json data to a csv file
		self._saveJSONtoCSV( data=json_data, file_name=csv_file_current )
		# if requested to upload this data file to the server
		if upload and os.path.isfile( '%s/%s/%s' % ( DATA_PATH, self.key, csv_file_current ) ):
			# upload the csv file to the remote server for web use
			if self._uploadFileToServer( csv_file_today ):
				print('=> PyBDX Data successfully uploaded to server.')

	def _saveJSONtoCSV( self, data, file_name ):
		# open the file to save data in
		data_file = open( '%s/%s/%s' % ( DATA_PATH, self.key, file_name ), 'w' )
		# create the csv writer object
		csv_writer = csv.writer( data_file )
		# counter variable used for writing headers
		count = 0
		for row in data:
			if count == 0:
				# write CSV file headers
				header = row.keys()
				csv_writer.writerow( header )
				count += 1
			# write CSV file data
			csv_writer.writerow( row.values() )
		data_file.close()
		return True

	def _uploadFileToServer( self, file_name ):
		# uploading data files to the RI data folder
		file_src = '%s/%s/%s' % ( DATA_PATH, self.key, file_name )
		file_dst = '%s/%s' % ( self.client.SITE_DUMP_PATH, file_name )
		ssh = paramiko.SSHClient() 
		ssh.load_host_keys( os.path.expanduser(os.path.join('~','.ssh','known_hosts')) )
		ssh.connect(
			self.client.SITE_IP,
			username=self.client.SSH_USER,
			password=self.client.SSH_PASS,
			banner_timeout=self.client.SSH_TIMEOUT_MS
		)
		sftp = ssh.open_sftp()
		sftp.put( file_src, file_dst )
		sftp.close()
		ssh.close()
		return True

	@staticmethod
	def downloadImages( obj: object, kind: str ) -> None:
		# download the image locally
		data = None
		if hasattr(obj, kind):
			data = getattr(obj, kind)
		elif hasattr(obj, f'_{kind}'):
			data = getattr(obj, f'_{kind}')
		if data:
			for item in data:
				if item.get('slug'):
					slug = item['slug']
					file_parts = item['src'].split('.')
					file_ext = file_parts[-1]
					filename = f'{obj.wp_slug}-{slug}-{kind}.{file_ext}'
					if kind == 'floorplans':
						save_to = '%s/%s' % (IMG_FLRP, filename)
					elif kind == 'elevations':
						save_to = '%s/%s' % (IMG_ELV, filename)
					elif kind == 'images':
						save_to = '%s/%s' % (IMG_PLN, filename)
					elif kind == 'interiors':
						save_to = '%s/%s' % (IMG_INT, filename)
					if not os.path.isfile(save_to):
						urlretrieve( item['src'], save_to )
