import eg, wx

eg.RegisterPlugin(
    name = "Spotify Web API",
    author = "Septik and yokel22",
    version = "0.1",
    kind = "other",
    description = "This plugin uses the Spotify Web API to perform various actions in Spotify.",
    icon = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAACNElEQVR42o2TbUhTYRTHfzc3bcuX"
    "EndpiUVvlIRIGjmHFUVFQRALhLIXpCIIghAbfpCiD6OwEX3pQ0ERBAq94IcIAitJwpJwZmVFqdnE"
    "QiWLLNfUuXXu7tQZd+GBh3Pufc7zP+f8n/+jkMCOnEdNtrBci8dH6b5WxaBRnvLvjwuP2ZdkolLC"
    "grj9iCxfeAKvewu3DQGO1jA310GthHv4v93pbOPQlQqCMwAuNlEvzsXs7G7lJkqnAGoeUWYyUxsa"
    "gy9d8K0PAr9kU3at6ZCVDXZhw5w8jRAOs9e9mVtKrHpbJMLas1L/9w/9oCVVfBL8ESCZHZMcXr0e"
    "SmTAlYVRDJ90sU7Zf5qFBVv5qnXT3a5XtOXIAfNUpWhHnT5obYDed3DiMizNI/K+BbtS7sGZt4Fm"
    "LbnnDTTWQX8PjPzUQTJskLMK1pRAbhEM9oK6GOZId10vcWoAxQLwTAPwC/qn15C9AuZlwEQIvvfD"
    "5w549QRSLHDMC5l2vTsBKFbKqrEVbmdAGyE0Dh1PYcAvJA7rVearsCwfFgmJ7Y3Cg0PA03VtvG1G"
    "nSSxRVzR8JCMIEpQl0DqAp28IWHnwwsIjsCBM3r7MXsuJDqjAOce4EqxRnWQ0Po+QlqmcJKlf8uV"
    "767axr14Id0Ud3CWQroh1Q/PUGKpG7NjF1clLDd6I3Fv4rrvIcfrPIQwSvTcZ4cljVMSbpQVUwNC"
    "L03BAN7qnTTE5yeqhOskVrk2jTJlbBR//SUCRnl/AbtOpXRdoA/cAAAAAElFTkSuQmCC"),
    )
    
import json, base64, requests, os, time, threading

class SpotifyWebAPI(eg.PluginBase):

    def __init__(self):

        self.client_id = 'Your Spotify client ID'
        self.client_secret = 'Your Spotify client secret'
        self.userName = 'Your Spotify username'
        self.AddAction(PrintUserName)
        self.AddAction(AddToPlaylist)
        self.AddAction(getFirstAccessToken)
        self.AddAction(PauseMusic)
        self.AddAction(PlayMusic)
        self.access_token = eg.plugins.Webserver.GetPersistentValue(u'spotify_access_token', False)
        self.refresh_token = access_token = eg.plugins.Webserver.GetPersistentValue(u'spotify_refresh_token', False)
    
    def Configure(
        self,
        client_id="",
        client_secret="",
        userName=""
        ):
        
        panel = eg.ConfigPanel()
        helpString = panel.StaticText(
            "Enter your Spotify credentials:"
        )

        spaceString = panel.StaticText("")
        client_idCtrl = panel.TextCtrl(client_id)
        client_secretCtrl = panel.TextCtrl(client_secret)
        userNameCtrl = panel.TextCtrl(userName)

        settingsBox = panel.BoxedGroup(
            "User Credentials",
            (u"Client ID:", client_idCtrl),
            (u"Client Secret:", client_secretCtrl),
            (u"Spotify user name:", userNameCtrl)
        )
        
        panel.sizer.Add(helpString, 0, wx.EXPAND)
        panel.sizer.Add(spaceString, 0, wx.EXPAND)
        panel.sizer.Add(settingsBox, 0, wx.EXPAND) 
        
        while panel.Affirmed():
            panel.SetResult(
                client_idCtrl.GetValue(),
                client_secretCtrl.GetValue(),
                userNameCtrl.GetValue()
                )
            self.client_id = client_idCtrl.GetValue()
            self.client_secret = client_secretCtrl.GetValue()
            self.userName = userNameCtrl.GetValue()
        
    def __start__(self, client_id, client_secret, userName):
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.userName = userName
        

class PrintUserName(eg.ActionBase):
    name = "Print user name"
    description = "For testing purposes."
    def __call__(self):
        print self.plugin.userName
        
class PauseMusic(eg.ActionBase):
    name = "Pause"
    description = "Pause music on current device."
    def __call__(self):
        access_token = eg.plugins.Webserver.GetPersistentValue(u'spotify_access_token', False)
        url = 'https://api.spotify.com/v1/me/player/pause'
        headers = {"Authorization": "Bearer " + access_token}
        
        r = requests.put(url, headers=headers)
        
class PlayMusic(eg.ActionBase):
    name = "Play"
    description = "Play (unpause) music on current device."
    def __call__(self):
        access_token = eg.plugins.Webserver.GetPersistentValue(u'spotify_access_token', False)
        url = 'https://api.spotify.com/v1/me/player/play'
        headers = {"Authorization": "Bearer " + access_token}
        
        r = requests.put(url, headers=headers)
    

class AddToPlaylist(eg.ActionBase):
    name = "Add current song to playlist"
    description = "Adds the currently playing song to a user-defined playlist."
    
    def __call__(self, playlistID):
        userName = self.plugin.userName
        access_token = eg.plugins.Webserver.GetPersistentValue(u'spotify_access_token', False)
        refresh_token = eg.plugins.Webserver.GetPersistentValue(u'spotify_refresh_token', False)
        
        if access_token is None:
            self.PrintError("No access token found.")
            access_token = self.refreshAccessToken(refresh_token)
            
        
        trackInfo = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers={"Authorization": "Bearer " + access_token})

        if trackInfo.status_code == 401:
            self.refreshAccessToken(self.refresh_token)
            access_token = eg.plugins.Webserver.GetPersistentValue(u'spotify_access_token', False)
            trackInfo = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers={"Authorization": "Bearer " + access_token})

        if trackInfo.status_code == 204:
            self.PrintError("No track info found!")
            return

        #Parse track info
        i=trackInfo.json()
        trackID=i['item']['id']
        trackName=i['item']['name']
        trackArtist=i['item']['album']['artists'][0]['name']
        
        #Get playlist info
        tracklist = requests.get("https://api.spotify.com/v1/users/" + userName + "/playlists/" + playlistID + "/tracks?fields=items(track.id),total", headers={"Accept": "application/json", "Authorization": "Bearer " + access_token + "\"" })
        t = tracklist.json()
        total = t['total']

        #Get playlist name
        playlist = requests.get("https://api.spotify.com/v1/users/" + userName + "/playlists/" + playlistID + "?fields=name", headers={"Authorization": "Bearer " + access_token})
        p = playlist.json()
        pname = p['name']

        print "Checking for duplicates..."
        
        offset = 100
        while (offset < total):
            tracklist = requests.get("https://api.spotify.com/v1/users/" + userName + "/playlists/" + playlistID + "/tracks?fields=items(track.id),total&offset=" + str(offset), headers={"Accept": "application/json", "Authorization": "Bearer " + access_token + "\"" })
            t = tracklist.json()
            for i, song in enumerate(t['items']):
                if song['track']['id'] == trackID:
                    print "Duplicate found! Track was not added to the playlist."
                    return
            offset +=100

        print "No duplicates found."

        #Add track to playlist
        add = requests.post("https://api.spotify.com/v1/users/" + userName + "/playlists/" + playlistID + "/tracks?uris=spotify%3Atrack%3A" + trackID, headers={"Accept": "application/json", "Authorization": "Bearer " + access_token + "\"" })

        #Create OSD object
        osd = eg.plugins.EventGhost.actions["ShowOSD"]()

        #Exit with error if song couldn't be added to playlist
        if add.status_code != 201:
            print ("POST ERROR: " + str(add.status_code) + " " + add.reason)
            osd("POST ERROR: " + str(add.status_code) + " " + add.reason)
            return


        #Show OSD if everything went well
        osd("'" + trackArtist + " - " + trackName + "'" + " added to playlist " + pname + ".", u'0;-16;0;0;0;700;0;0;0;0;3;2;1;34;Arial', (255, 255, 255), None, 3, (5, 37), 0, 3.0, True)
        print "\"" + trackArtist + " - " + trackName + "\" added to playlist \"" + pname + "\"."            
        
        return
        
    def Configure(self, playlist="", refresh_token=""):
       panel = eg.ConfigPanel()
       
       playlistCtrl = panel.TextCtrl(playlist)
       
       panel.AddLine(u"Playlist ID:", playlistCtrl)
        
       while panel.Affirmed():
           panel.SetResult(
               playlistCtrl.GetValue(),
               )
           self.playlist = playlistCtrl.GetValue()
           
    def refreshAccessToken(self, refresh_token):
        print "Refreshing access token..."
        
        # These should rather appear below the if statement but are
        # passed on to the waitForCode function to prevent an error.
        client_id = self.plugin.client_id
        client_secret = self.plugin.client_secret

        
        if refresh_token == None:
            self.PrintError("No refresh token found!")
            refresh_token = getFirstAccessToken.__call__(getFirstAccessToken(), client_id, client_secret)
        
        #client_id = self.plugin.client_id
        #client_secret = self.plugin.client_secret

        url = "https://accounts.spotify.com/api/token"
        payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        headers = {"Authorization": "Basic " + (base64.standard_b64encode(client_id + ":" + client_secret))}

        r = requests.post(url, payload, headers=headers)
        json_string = r.content
        parsed_json = json.loads(json_string)

        access_token = parsed_json['access_token']
        eg.plugins.Webserver.SetPersistentValue(u'spotify_access_token', str(access_token), False, False)
        
        return access_token
        
class getFirstAccessToken(eg.ActionBase):
    name = "Get initial access token"
    description = "Perform this once if you haven't acquired an access token yet."
    
    
    def waitForCode(self, client_id, client_secret):
        time_out = time.time() + 30
        accessCode = None
        
        print "Attempting to acquire access code..."
        
        while time_out > time.time():
            if eg.event.prefix == "HTTP":
                code = eg.event.suffix
                accessCode = code.split("code=", 1)
                break
                
        if accessCode == None:
            self.PrintError("Failed to retrieve access code!")
            return
        
        
        print "Acquiring access and refresh tokens..."
        #The commented out part below produces an error.
        #client_id = self.plugin.client_id
        #client_secret = self.plugin.client_secret
        url = 'https://accounts.spotify.com/api/token'
        redirect_uri = "http://localhost:8025"
        payload = {"grant_type": "authorization_code", "code": str(accessCode[1]), "redirect_uri": redirect_uri }
        headers = {"Authorization": "Basic " + (base64.standard_b64encode(client_id + ":" + client_secret))}
        
        r = requests.post(url, payload, headers=headers)
        json_string = r.content
        parsed_json = json.loads(json_string)

        #The next line produces an error, but access_token still prints shortly after! 
        access_token = parsed_json['access_token']
        print "access_token: " + str(access_token)
        refresh_token = parsed_json['refresh_token']
        print "refresh_token: " + str(refresh_token)
        
        eg.plugins.Webserver.SetPersistentValue(u'spotify_access_token', str(access_token), False, False)
        eg.plugins.Webserver.SetPersistentValue(u'spotify_refresh_token', str(refresh_token), False, False)
        
        print "Successfully retrieved access and refresh tokens!"
        
        return str(refresh_token)

    
    def __call__(self, client_id, client_secret):
        scope = "playlist-read-private%20playlist-modify-public%20playlist-modify-private%20user-read-currently-playing%20user-modify-playback-state"
        redirect_uri = "http://localhost:8025"
        url = 'https://accounts.spotify.com/authorize/?client_id=' + client_id + '&response_type=code&redirect_uri=' + redirect_uri + "&scope=" + scope
        threadWaitForCode = threading.Thread(target=self.waitForCode,args=(client_id, client_secret))
        output = threadWaitForCode.start()
        os.startfile(url)
        return output
