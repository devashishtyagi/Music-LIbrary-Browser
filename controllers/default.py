# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a deafult controller
## - index is the default action controller. Performs the search functionality
## - album is used to render the release group page
## - artist is used to render the artist information page
## - release is used to render the information about a single release
## - playlist allows the user to add or delete playlists
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

import datetime
import httplib
import pprint
import json
import urllib2, urllib
from bs4 import BeautifulSoup
import csv
import os, stat
from gluon.debug import dbg

########### GETTING IMAGE LINK FOR MBID #############
def get_link(destination):
	try:
		proxy = urllib2.ProxyHandler({'http': 'http://cs5090240:phone01202767129@10.10.78.62:3128'})
		authentication = urllib2.HTTPBasicAuthHandler()
		opener = urllib2.build_opener(proxy, authentication, urllib2.HTTPHandler)
		urllib2.install_opener(opener)
		req = urllib2.Request(url=destination,data="")
		f = urllib2.urlopen(req)
		data =json.load(f)
		coverarturl = data['images'][0]['thumbnails']['small']
	except:
		coverarturl = URL('static','images/no_image_found.jpg')
	return coverarturl

def get_wiki_desc(url):
	try:
		proxy = urllib2.ProxyHandler({'http': 'http://cs5090240:phone01202767129@10.10.78.62:3128'})
		auth = urllib2.HTTPBasicAuthHandler()
		opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
		urllib2.install_opener(opener)

		req = urllib2.Request(url, headers={'User-Agent' : "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127 Firefox/2.0.0.11"}) 
		conn = urllib2.urlopen( req )

		data = conn.read()
		soup = BeautifulSoup(data)
		dic= soup.findAll('p')
		k=dic[0]
		for item in dic:
			if(len(item)<15):
				continue
			else:
				k=item
				break
		return k
	except:
		return "No wiki description"


########### INDEX CONTROLLER ##############
def index():
	"""
	Initializes reponse variables.
	Show the search bar which enables the user to search for music, artists,
	albums and records. On clicking the search tab, the user will be redirected
	to search action.
	This page also displays featured artists, albums, music.
	"""
	form = FORM('',
				INPUT(_name='search_term', requires = IS_NOT_EMPTY(), _class='input-large search-query', 
					_placeholder='Search for music', _autocomplete="off"),
				INPUT(_type='submit', _class='btn', _value='Search'), _class='form-search')
	if form.process().accepted:
		redirect(URL('search', vars=dict(search_term=request.vars.search_term)))
	featured_albums = db.executesql("select * from top_release_group;")
	groupinfo = []
	imagelink = []
	for row in featured_albums:
		groupinfo.append(row[0])
		if (row[2]):
			imagelink.append(row[2])
		else:
			imageurl = get_link("http://www.coverartarchive.org/release-group/"+row[1]);
			db.executesql("update top_release_group set url = '"+str(imageurl)+"' where id="+str(row[0])+";")
			imagelink.append(imageurl)
	return dict(form=form, groupinfo=groupinfo, imagelink=imagelink)

########### SEARCH CONTROLLER ##############
def search():
	"""
	Returns search results of the query obtained in request args. It Returns
	four seperate variables containing results for artists, music, albums and
	records.
	"""
	if not request.vars.search_term:
		redirect(URL('index'))
	term = request.vars.search_term
	origterm = term
	term = term.replace(' ','|')
	artists = db.executesql("select distinct(m1.id), m1.art_name, m1.artist_type, m1.country, m1.b_year,m1.b_month,m1.b_date,m1.e_year,m1.e_month,m1.e_day,ts_rank(to_tsvector(m1.art_name),to_tsquery('"+term+"')) rank from art_info m1 where to_tsvector('english',m1.art_name) @@ to_tsquery('"+term+"') order by rank desc limit 20;")
	albums = db.executesql("select distinct(m1.id),m2.name,m1.art_id,m1.art_name,m1.rel_type,m1.count,ts_rank(to_tsvector(m2.name),to_tsquery('"+term+"')) rank from rel_art m1, release_name m2, release_group m3 where m3.name = m2.id and m3.id = m1.id and to_tsvector('english',m2.name) @@ to_tsquery('"+term+"') order by rank desc limit 20;")
	songs = db.executesql("select m2.id, m1.name, m3.art_id, m3.art_name, m3.rel_id, m3.rel_name from track_name m1, recording m2, rec_rel_art m3 where m1.id = m2.name and m2.id = m3.rec_id and lower(m1.name) LIKE lower('%%"+origterm+"%%') limit 20;")
	return dict(songs=songs, albums=albums, artists=artists)

########### ALBUM CONTROLLER ##############
def album():
	"""
	This action is responsible for obtaining and returning all the information 
	related to a particular release group item. 
	"""
	if not request.vars.id:
		redirect(URL('index'))
	id = request.vars.id
	releasegroupname = db.executesql("select m1.name, m2.id from release_name as m1, release_group as m2 where m1.id = m2.name and m2.id = "+id+";")
	releasegroup = db.executesql("select distinct(m2.id),m3.name,m5.name,m7.track_count,m2.date_year,m2.date_month,m2.date_day,m6.name,m2.barcode from release_group m1,release m2,release_name m3,medium m4,medium_format m5, country m6, tracklist m7 where m5.id = m4.format and m4.release = m2.id and m2.name = m3.id and m2.release_group = m1.id and m2.country = m6.id and m4.tracklist = m7.id and m1.id = "+id+";")
	urls = db.executesql("select m2.url from l_release_group_url m1, url m2 where m1.entity1 = m2.id and m1.entity0 = "+id+";")
	mbid = db.executesql("select m1.gid from release_group m1 where m1.id = "+id+";")
	rating = db.executesql("select rating, count from release_group_rating_global where id = "+id+";")
	avg_rating = float(rating[0][0])/float(rating[0][1])
	if auth.user:
		urating = db.executesql("select rating from release_group_rating_local where id = "+str(id)+" and user_id = "+str(auth.user.id)+";")
		if urating:
			user_rating = urating[0][0]
		else:
			user_rating = 0
	else:
		user_rating = 0
	try:
		proxy = urllib2.ProxyHandler({'http': 'http://cs5090240:phone01202767129@10.10.78.62:3128'})
		authentication = urllib2.HTTPBasicAuthHandler()
		opener = urllib2.build_opener(proxy, authentication, urllib2.HTTPHandler)
		urllib2.install_opener(opener)
		destination = 'http://www.coverartarchive.org/release-group/'+mbid[0][0]
		#dbg.set_trace()
		req = urllib2.Request(url=destination,data="")
		f = urllib2.urlopen(req)
		#dbg.set_trace()
		data =json.load(f)
		#dbg.set_trace()
		coverarturl = data['images'][0]['image']
	except:
		coverarturl = URL('static','images/no_image_found.jpg')
	links = []
	wikiurl = ""
	for url in urls:
		if "wikipedia" in url[0]:
			wikiurl = url[0]
		else:
			links.append(url[0])
	if wikiurl:
		#wiki = get_wiki_desc(str(wikiurl)+"?printable=yes")
		wiki = "Description available at "+str(wikiurl)
	else:
		wiki = "No wiki description"
	return dict(releasegroupname=releasegroupname, releasegroup=releasegroup, links=links, wiki=wiki, wikiurl=wikiurl, coverarturl=coverarturl, avg_rating=avg_rating, user_rating=user_rating)

########### RELEASE CONTROLLER ##############
def release():
	"""
	This action is reponsible  for displaying the displaying the tracklist
	of a particular release
	"""
	if not request.vars.id:
		redirect(URL('index'))
	id = request.vars.id
	releasename = db.executesql("select m1.name from release_name as m1, release as m2 where m1.id = m2.name and m2.id = "+id+";")
	tracklist = db.executesql("select m4.id, m5.name, m4.position, m4.length from release m1,medium m2,tracklist m3,track m4,track_name m5 where m5.id = m4.name and m4.tracklist = m3.id and m3.id = m2.tracklist and m2.release = m1.id and m1.id = "+id+" order by m4.position;")
	urls = db.executesql("select m2.url from l_release_url m1, url m2 where m1.entity1 = m2.id and m1.entity0 = "+id+";")
	mbid = db.executesql("select m1.gid from release m1 where m1.id = "+id+";")
	try:
		proxy = urllib2.ProxyHandler({'http': 'http://cs5090240:phone01202767129@10.10.78.62:3128'})
		authentication = urllib2.HTTPBasicAuthHandler()
		opener = urllib2.build_opener(proxy, authentication, urllib2.HTTPHandler)
		urllib2.install_opener(opener)
		destination = 'http://www.coverartarchive.org/release/'+mbid[0][0]
		#dbg.set_trace()
		req = urllib2.Request(url=destination,data="")
		f = urllib2.urlopen(req)
		#dbg.set_trace()
		data =json.load(f)
		#dbg.set_trace()
		coverarturl = data['images'][0]['image']
	except:
		coverarturl = URL('static','images/no_image_found.jpg')
	links = []
	wiki = ""
	for url in urls:
		if "wikipedia" in url[0]:
			wiki = url[0]
		else:
			links.append(url[0])
	tracklist1 = []
	for row in tracklist:
		row1 = list(row)
		if (row1[3]):
			d = datetime.datetime.fromtimestamp(int(row1[3])//1000)
			row1[3] = str(d.hour)+":"+str(d.minute)
		else:
			row1[3] = 'N/A'
		tracklist1.append(row1)
	if auth.user:
		playlists = db(db.playlists.user_id == auth.user.id).select()
	else:
		playlists = None
	return dict(tracklist=tracklist1, releasename=releasename, wiki=wiki, links=links, playlists=playlists, coverarturl=coverarturl)

########### ARTIST CONTROLLER ##############
def artist():
	"""
	This action is reponsible for displaying all the information related 
	to an artist
	"""
	if not request.vars.id:
		redirect(URL('index'))
	id = request.vars.id
	artistname = db.executesql("select m1.name from artist_name as m1, artist as m2 where m1.id = m2.name and m2.id = "+id+";")
	urls = db.executesql("select distinct(m2.url) from l_artist_url m1, url m2 where m2.id = m1.entity1 and m1.entity0 = "+id+";")
	discography = db.executesql("select m4.name,m5.name,m3.id,m6.count from artist_credit_name m1, artist_credit m2,release_group m3,release_name m4, release_group_primary_type m5,rel_group_count m6 where m4.id = m3.name and m3.artist_credit = m2.id and m2.id = m1.artist_credit and m5.id = m3.type and m6.id = m3.id and m1.artist = "+id+";")
	links = []
	wiki = ""
	for url in urls:
		if "wikipedia" in url[0]:
			wiki = url[0]
		else:
			links.append(url[0])
	return dict(discography=discography, wiki=wiki, links=links, artistname=artistname)

########### PLAYLIST CONTROLLER ##############
@auth.requires_login()
def playlist():
	db.playlists.user_id.default = auth.user.id
	form =  SQLFORM(db.playlists, labels={'name':'Name', 'description':'Description', 'submit':'Add Playlist'})
	if form.process().accepted:
		response.flash = 'Your playlists has been added.'
	playlists = db(db.playlists.user_id == auth.user.id).select()
	return dict(playlists=playlists, form=form)

########### DELETE PLAYLIST ################
@auth.requires_login()
def deleteplaylist():
	if request.vars.id:
		db(db.playlists.id == request.vars.id).delete()
	return dict()

########## ADD TO PLAYLIST ################
@auth.requires_login()
def addtoplaylist():
	if request.vars:
		playlistid = str(request.vars.playlistid)
		trackid = str(request.vars.trackid)
		if not db.executesql("SELECT * FROM playlist_track where playlist_id="+playlistid+" AND track_id="+trackid+";"):
			db.executesql("INSERT INTO playlist_track VALUES(" + playlistid + "," + trackid + ");")
	return dict()

########## PLAYLIST HOME ################
def playlisthome():
	if not request.vars.id:
		redirect(URL('index'))
	id = request.vars.id
	recordings = db.executesql("select pr.playlist_id, pr.track_id, tn.name from playlist_track as pr, track as tk, track_name as tn where pr.playlist_id = "+id+" AND pr.track_id = tk.id AND tk.name = tn.id;")
	playlist_info = db.executesql("select * from playlists where id = "+id+";")
	return dict(recordings=recordings, playlist_info=playlist_info);

########## DELETE TRACK FROM PLAYLIST ###########
def delete_track_from_playlist():
	if not (request.vars.pid and request.vars.tid):
		redirect(URL('index'))
	pid = request.vars.pid
	tid = request.vars.tid
	db.executesql("DELETE FROM playlist_track WHERE playlist_id="+pid+" AND track_id="+tid+";")
	return dict()

########## MODIFY USER RATINGS ##############
def modifyreleasegrouprating():
	if not (request.vars.rgid and request.vars.uid and request.vars.score):
		redirect(URL('index'))
	rgid = request.vars.rgid
	uid = request.vars.uid
	score = request.vars.score
	if not db.executesql("select * from release_group_rating_local where id = "+rgid+" and user_id = "+uid+";"):
		db.executesql("insert into release_group_rating_local values("+rgid+","+uid+","+score+");")
	else:
		db.executesql("update release_group_rating_local set rating = "+score+" where id = "+rgid+" and user_id = "+uid+";")
	return dict()

########## EXPORT PLAYLIST TO CSV ############
def export():
	if not request.vars.id:
		redirect(URL('index'))
	id = request.vars.id
	recordings = db.executesql("select pr.track_id, tn.name from playlist_track as pr, track as tk, track_name as tn where pr.playlist_id = "+id+" AND pr.track_id = tk.id AND tk.name = tn.id;")
	filename = "plalist_id"+str(id)+".csv"
	with open(os.path.join(request.folder,'uploads',filename), "wb") as csvfile:
		csvwriter = csv.writer(csvfile)
		for row in recordings:
			csvwriter.writerow([str(row[0]), str(row[1])])
	response.stream(os.path.join(request.folder,'uploads',filename))


def user():
	"""
	exposes:
	http://..../[app]/default/user/login
	http://..../[app]/default/user/logout
	http://..../[app]/default/user/register
	http://..../[app]/default/user/profile
	http://..../[app]/default/user/retrieve_password
	http://..../[app]/default/user/change_password
	use @auth.requires_login()
		@auth.requires_membership('group name')
		@auth.requires_permission('read','table name',record_id)
	to decorate functions that need access control
	"""
	return dict(form=auth())


def download():
	"""
	allows downloading of uploaded files
	http://..../[app]/default/download/[filename]
	"""
	return response.download(request, db)


def call():
	"""
	exposes services. for example:
	http://..../[app]/default/call/jsonrpc
	decorate with @services.jsonrpc the functions to expose
	supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
	"""
	return service()


@auth.requires_signature()
def data():
	"""
	http://..../[app]/default/data/tables
	http://..../[app]/default/data/create/[table]
	http://..../[app]/default/data/read/[table]/[id]
	http://..../[app]/default/data/update/[table]/[id]
	http://..../[app]/default/data/delete/[table]/[id]
	http://..../[app]/default/data/select/[table]
	http://..../[app]/default/data/search/[table]
	but URLs must be signed, i.e. linked with
	  A('table',_href=URL('data/tables',user_signature=True))
	or with the signed load operator
	  LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
	"""
	return dict(form=crud())
