# -*- coding: utf-8 -*-
# Viewster Kodi Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

cache = StorageServer.StorageServer("plugin.video.viewster", 1) # (Your plugin name, Cache time in hours)

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.viewster')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

# 30032|30020|30021|30022|30023|30024
lang_lookup   = [ None, 'en', 'fr', 'de', 'es', 'ja' ]

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36'
defaultHeaders = {'User-Agent': USER_AGENT,
               'Referer': 'http://www.viewster.com/',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'en-US,en;q=0.8',
               'Accept': 'application/json, text/javascript, */*; q=0.01',
               'Connection': 'keep-alive'}

def getRequest(url, udata=None, headers = defaultHeaders):
   log("getRequest URL:"+str(url))
   req = urllib2.Request(url.encode(UTF8), udata, headers)
   try:
      response = urllib2.urlopen(req)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         log("Content Encoding == gzip")
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
   except:
      page = ""
   return(page)

def getToken():

    url = 'https://www.viewster.com/'
    udata = None
    headers = {'User-Agent': USER_AGENT,
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}
    headers['Host'] = 'www.viewster.com'
    headers['Upgrade-Insecure-Requests'] = '1'
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    headers['If-None-Match'] = 'W/"1db6-XP9MvSddVilh+ytjiBJpJw"'
    headers['If-Modified-Since'] = 'Wed, 09 Sep 2015 14:47:22 GMT'

    req = urllib2.Request(url, udata, headers)
    for i in [1,2,3,4,5,6,7,8,9]:
        try:
          response = urllib2.urlopen(req)
          break
        except:
          print 'Error retieving token, retry!'
          time.sleep(1)

    token = uqp(re.compile('api_token=(.+?);',re.DOTALL).search(str(response.info())).group(1))
    return token

def getSources(fanart):
    ilist = []
    url   = 'https://public-api.viewster.com/genres'
    headers = defaultHeaders
    headers['Auth-token'] = cache.cacheFunction(getToken)
    html = getRequest(url, None, headers)
    cats = json.loads(html)
    for list in cats:
       name = list['Name'].decode(UTF8)
       url = str(list['Id'])
       img  =   'http://divaag.vo.llnwd.net/o42/http_rtmpe/shared/Viewster_Artwork/internal_artwork/g%s_1280x720.jpg' % url
       mode = 'GC'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
    searches = [("/search/Movies#%s",__language__(30001)),("/search/TvShow#%s",__language__(30002))]
    for url,name in searches:
       url  = url % name
       lname = "[COLOR red]%s[/COLOR]" % name
       u = '%s?url=%s&name=%s&mode=DS' % (sys.argv[0],qp(url), qp(name))
       liz=xbmcgui.ListItem(lname, '',icon, None)
       ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def doSearch(osid):
        keyb = xbmc.Keyboard('', 'Search')
        keyb.doModal()
        if (keyb.isConfirmed()):
            search = urllib.quote_plus(keyb.getText())
            url = 'https://public-api.viewster.com/search/%s?pageSize=50&pageIndex=1' % uqp(search)
            headers = defaultHeaders
            headers['Auth-token'] = cache.cacheFunction(getToken)
            headers['X-Requested-With']= 'XMLHttpRequest'
            html = getRequest(url, None, headers)


def getCats(url, name):
    ilist = []
    img   = 'http://divaag.vo.llnwd.net/o42/http_rtmpe/shared/Viewster_Artwork/internal_artwork/g%s_1280x720.jpg' % url
    names = [('Movies', 'GM'), ('Tv-Series','GS')]
    for name, mode in names:
        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
        liz=xbmcgui.ListItem(name, '',None, img)
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getMovie(url, name):
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')

    ilist = []
    url   = 'https://public-api.viewster.com/movies?pageSize=200&pageIndex=1&genreId=%s' % url
    headers = defaultHeaders
    headers['Auth-token'] = cache.cacheFunction(getToken)
    html = getRequest(url, None, headers)
    try: a = json.loads(html)['Items']
    except: return
    for b in a:
       img    = 'http://image.api.viewster.com/movies/%s/image?width=196&height=279' % b['OriginId']
       name = b['Title']
       vid = b['Id']
       infoList = {}
       infoList['Title'] = name
       try: 
          infoList['Genre'] = ''
          for genre in b['Genres']: infoList['Genre'] += genre['Name']+','
       except: pass
       try: infoList['Plot']         = b['Synopsis']['Detailed']
       except: pass
       try: infoList['PlotOutline']  = b['Synopsis']['Short']
       except: pass
       try: infoList['Director']     = b['Directors']
       except: pass
       try:
           infoList['Cast']  = []
           for actor in b['Actors'].split(',') : infoList['Cast'].append(actor)
       except: pass
       try: infoList['Year']     = int(b['ReleaseDate'].split('-',1)[0])
       except: pass
       try: infoList['premiered']= b['ReleaseDate'].split('T')[0]
       except: pass
       try: infoList['Duration'] = b['Duration']
       except: pass

       dub_lang = None
       sub_lang = None
       i_max = 128
       try:
           for l in b['LanguageSets']:
              sub_this_language = "true"
              try: sub_this_language = addon.getSetting('sub_'+l['Audio'])
              except: pass

              if sub_this_language == "false":
                 dub_lang = l['Audio']
                 sub_lang = None
                 # We found a language the user has marked he understands!
                 # This seems to be a perfect match no need to search any further
                 break;

              for i in [1,2,3,4]:
                 if i >= i_max: # no improvement on subtitle rank possible anymore
                    break;

                 if lang_lookup[ int(addon.getSetting('sub_'+str(i))) ] == l['Subtitle']:
                    dub_lang = l['Audio']
                    sub_lang = l['Subtitle']
                    i_max = i
       except: pass

       u = '%s?url=%s&mode=GV&dub=%s&sub=%s' % (sys.argv[0], vid, dub_lang, sub_lang)
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.addStreamInfo('video', { 'codec': 'avc1',
                         'width' : 856,
                         'height' : 480,
                         'aspect' : 1.78 })
       liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : dub_lang, 'channels': 2})

       if sub_lang != None: # Skip adding subtitle info if not set
         liz.addStreamInfo('subtitle', { 'language' : sub_lang})

       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.addStreamInfo('video', { 'codec': 'avc1', 
                         'width' : 856, 
                         'height' : 480, 
                         'aspect' : 1.78 })
       liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
       liz.addStreamInfo('subtitle', { 'language' : 'en'})
       liz.setProperty('fanart_image', addonfanart)
       liz.setProperty('IsPlayable', 'true')
       ilist.append((u, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('movies_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

          
def getEpisodes(url, catname):
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

    ilist = []
    url   = 'https://public-api.viewster.com/series/%s/episodes' % url
    headers = defaultHeaders
    headers['Auth-token'] = cache.cacheFunction(getToken)
    html = getRequest(url, None, headers)
    try: a = json.loads(html)
    except: return

    for b in a:
       img    = 'http://image.api.viewster.com/movies/%s/image?width=196&height=279' % b['OriginId']
       name = b['Title']
       vid = b['Id']
       infoList = {}
       infoList['Title'] = name
       infoList['TVShowTitle'] = uqp(catname)
       infoList['Season'] = 1
       infoList['Episode'] = 0
       try: 
          infoList['Genre'] = ''
          for genre in b['Genres']: infoList['Genre'] += genre['Name']+','
       except: pass
       try: infoList['Plot']         = b['Synopsis']['Detailed']
       except: pass
       try: infoList['PlotOutline']  = b['Synopsis']['Short']
       except: pass
       try: infoList['Director']     = b['Directors']
       except: pass
       try:
           infoList['Cast']  = []
           for actor in b['Actors'].split(',') : infoList['Cast'].append(actor)
       except: pass
       try: infoList['Year']     = int(b['ReleaseDate'].split('-',1)[0])
       except: pass
       try: infoList['premiered']= b['ReleaseDate'].split('T')[0]
       except: pass
       try: infoList['Duration'] = b['Duration']
       except: pass

       dub_lang = None
       sub_lang = None
       i_max = 128
       try:
           for l in b['LanguageSets']:
              sub_this_language = "true"
              try: sub_this_language = addon.getSetting('sub_'+l['Audio'])
              except: pass

              if sub_this_language == "false":
                 dub_lang = l['Audio']
                 sub_lang = None
                 # We found a language the user has marked he understands!
                 # This seems to be a perfect match no need to search any further
                 break;

              for i in [1,2,3,4]:
                 if i >= i_max: # no improvement on subtitle rank possible anymore
                    break;

                 if lang_lookup[ int(addon.getSetting('sub_'+str(i))) ] == l['Subtitle']:
                    dub_lang = l['Audio']
                    sub_lang = l['Subtitle']
                    i_max = i
       except: pass

       u = '%s?url=%s&mode=GV&dub=%s&sub=%s' % (sys.argv[0], vid, dub_lang, sub_lang)
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.addStreamInfo('video', { 'codec': 'avc1', 
                         'width' : 856, 
                         'height' : 480, 
                         'aspect' : 1.78 })
       liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : dub_lang, 'channels': 2})

       if sub_lang != None: # Skip adding subtitle info if not set
         liz.addStreamInfo('subtitle', { 'language' : sub_lang})

       liz.setProperty('fanart_image', addonfanart)
       liz.setProperty('IsPlayable', 'true')
       ilist.append((u, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
              

def getShow(url, catname):
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

    ilist = []
    url   = 'https://public-api.viewster.com/series?pageSize=200&pageIndex=1&genreId=%s' % url
    headers = defaultHeaders
    headers['Auth-token'] = cache.cacheFunction(getToken)
    html = getRequest(url, None, headers)
    try: a = json.loads(html)['Items']
    except: return
    for b in a:
       img    = 'http://image.api.viewster.com/movies/%s/image?width=196&height=109' % b['OriginId']
       name = b['Title']
       vid = b['Id']
       infoList = {}
       infoList['TVShowTitle'] = name
       try: 
          infoList['Genre'] = ''
          for genre in b['Genres']: infoList['Genre'] += genre['Name']+','
       except: pass
       try: infoList['Plot']         = b['Synopsis']['Detailed']
       except: pass
       try: infoList['PlotOutline']  = b['Synopsis']['Short']
       except: pass
       try: infoList['Director']     = b['Directors']
       except: pass
       try:
           infoList['Cast']  = []
           for actor in b['Actors'].split(',') : infoList['Cast'].append(actor)
       except: pass
       try: infoList['Year']     = int(b['ReleaseDate'].split('-',1)[0])
       except: pass
       try: infoList['premiered']= b['ReleaseDate'].split('T')[0]
       except: pass
       u = '%s?url=%s&name=%s&mode=GE' % (sys.argv[0], vid, qp(name.encode(UTF8)))
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.addStreamInfo('video', { 'codec': 'avc1', 
                         'width' : 856, 
                         'height' : 480, 
                         'aspect' : 1.78 })
       liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
       liz.addStreamInfo('subtitle', { 'language' : 'en'})
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('shows_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getVideo(sid, name, dub, sub):

#    url = 'https://public-api.viewster.com/movies/'+sid+'/video?mediaType=application%2Ff4m%2Bxml'
#    url = 'https://public-api.viewster.com/movies/'+sid+'/video'
#    url = 'https://public-api.viewster.com/movies/'+sid+'/video?mediaType=video%2Fmp4&language=en&subtitle='

    url = 'https://public-api.viewster.com/movies/'+sid+'/video?mediaType=video%2Fmp4'
    if dub != 'None':
       url += '&language=' + dub

    if sub != 'None':
       url += '&subtitle=' + sub

    headers = defaultHeaders
    headers['Auth-token'] = cache.cacheFunction(getToken)
    headers['X-Requested-With']= 'XMLHttpRequest'

    html = getRequest(url, None, headers)
    a = json.loads(html)
    url = a['Uri']
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))



# MAIN EVENT PROCESSING STARTS HERE

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
      try:    parms[key] = urllib.unquote_plus(parms[key]).decode(UTF8)
      except: pass
except:
    parms = {}

p = parms.get

mode = p('mode',None)

if mode==  None:  getSources(p('fanart'))
elif mode=='GC':  getCats(p('url'), p('name'))
elif mode=='GS':  getShow(p('url'),p('name'))
elif mode=='GM':  getMovie(p('url'),p('name'))
elif mode=='GE':  getEpisodes(p('url'),p('name'))
elif mode=='GV':  getVideo(p('url'),p('name'),p('dub'),p('sub'))
elif mode=='DS':  doSearch(p('url'))





