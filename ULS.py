import praw
import webbrowser
import time
import string
import OAuth2Util
import datetime
from twitch.api import v3 as twitch

# REDDIT SETTINGS

SUBREDDIT = "UndergroundLolSociety"
UPDATE_SIDEBAR_TIME = 180
UPDATE_LIST_LOOPS = 5


user_agent = "windows:Underground LoL Society Automod:1.1.2 (by /u/evanc1411)"

r = praw.Reddit(user_agent=user_agent)

# OLD OAUTH

# r.set_oauth_app_info(client_id="client_id",
#                      client_secret="client_secret",
#                      redirect_uri="http://127.0.0.1:65010/authorize_callback")

o = OAuth2Util.OAuth2Util(r)

# TO FIX USER AUTHENTICATION

# url = r.get_authorize_url('_key_', 'identity modconfig modwiki wikiedit', True)
# webbrowser.open(url)

# info = r.get_access_information("reddit_info_key")
# print (ainfo)

# r.set_access_credentials(**ainfo)

running = True

SUBREDDIT = r.get_subreddit(SUBREDDIT)

# STREAMERS AND REDDITORS

streams = []
redditors = []

def updateStreamerListFromWiki():
    wiki = r.get_wiki_page(SUBREDDIT, "Streamerlist").content_md
    listStart = string.find(wiki, "---") + 5;  listEnd = string.rfind(wiki, "---") + 5
    lines = wiki[listStart:listEnd].splitlines()
    updatedstreams = []
    updatedredditors = []
    num = 0
    errored = False

    for entry in lines:
        if entry != "" and entry != "---" and not errored:
            modified = entry.split(":")
            try:
                updatedredditors.insert(num, modified[0])
                updatedstreams.insert(num, modified[1])
                num += 1
            except ValueError:
                print "Streamer list entry invalid. (Entry #" + num + ")\n"
                errored = True

    if len(updatedstreams) != len(updatedredditors):
        print "Error! Not the same number of redditors and streams.\n"
        errored = True

    if errored:
        print "Error updating streamer list. Will use the last known streamer list.\n"

    else:
        return updatedredditors, updatedstreams

def checkStreamOnline(name):
    try:
        stream_by_channel = twitch.streams.by_channel(name)
        if stream_by_channel.get('stream') is None:
            return False
        else:
            return True
    except:
        print "Error! Channel could not be found for channel: " + name + ".\n"
        return False

# template: [](/offlineindic) twitch.tv/evancg17 ^*/u/evancg17*: Offline
# template: [](/onlineindic) [twitch.tv/naturesbf](http://twitch.tv/naturesbf) ^*/u/naturesbfLoL*: Online!

def formatStreamStatus(redditor, stream):
    if checkStreamOnline(stream):
        return "[](/onlineindic) [\/u\/" + redditor + "](http://twitch.tv/" + stream + "): Online!\n\n"
    else:
        return "[](/offlineindic) /u/" + redditor + " : Offline.\n\n"

def getEditableSidebarIndices(sidebar):
    start = string.find(sidebar, "[](/BEGINSTREAMLIST)")
    end = string.find(sidebar, "[](/ENDSTREAMLIST)")
    return [start, end]

def getEditableSidebarText(sidebar):
    [start, end] = getEditableSidebarIndices(sidebar)
    return sidebar[start:end]

def getSidebarText():
    return SUBREDDIT.get_settings()['description']

def updateSidebar():
    currentsidebar = getSidebarText()
    currentarea = getEditableSidebarText(currentsidebar)
    [start, end] = getEditableSidebarIndices(currentsidebar)
    beforeeditable = currentsidebar[:start]
    aftereditable = currentsidebar[end:]
    newarea = "[](/BEGINSTREAMLIST)\n\n"

    for num in range(0, streams.__len__()):
        redditor = redditors[num]
        stream = streams[num]
        newarea += formatStreamStatus(redditor, stream)

    time = "\n^(*Last updated: " + str(datetime.datetime.now())
    time = time[:string.find(time, ".")] + " MST*)\n\n"

    if currentarea != newarea:
        newarea += time
        updatedsidebar = beforeeditable + newarea + aftereditable
        r.update_settings(SUBREDDIT, description=updatedsidebar)
        print ("Sidebar updated.")
    else:
        r.update_settings(SUBREDDIT, description=beforeeditable+currentarea+time+aftereditable)
        print ("Sidebar up to date.")


o.refresh()
me = r.get_me()
print ("Authenticated as " + me.name + ".")

print "Bot starting."
loop = 0

while running:
    o.refresh()
    print "Updating sidebar contents in 3..."
    time.sleep(3)
    if loop % UPDATE_LIST_LOOPS == 0:
        print "Updating stream list from wiki page..."
        redditors, streams = updateStreamerListFromWiki()
        print "Stream list updated."
    updateSidebar()
    loop += 1
    time.sleep(UPDATE_SIDEBAR_TIME - 3)
