# coding=utf-8
from enigma import *
from ServiceReference import ServiceReference
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from Screens.ChannelSelection import *
from Components.Pixmap import *
from Components.Label import Label
from Components.MenuList import MenuList
from Components.config import *
from Components.ConfigList import ConfigList
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.HTMLComponent import *
from Components.GUIComponent import *
from Tools.NumericalTextInput import *
from Tools.Directories import *
from Tools.LoadPixmap import LoadPixmap
from Plugins.Plugin import PluginDescriptor
from threading import Thread
import os, sys, string, time, datetime
plugin_path = ''
VERSION = '0.32'

class fanzone(Screen):
    skin = '<screen position="0,0" size="1280,720" title=" " backgroundColor="#FF000000" >\
    <widget name="fzhd" pixmap="~/png/curs.png" position="0,0" size="250,30" />\
    <widget name="exit" position="0,640" size="1280,80" valign="center" halign="center" zPosition="2" font="Regular;48" transparent="1" foregroundColor="yellow" />\
    <widget name="warn" position="290,80" size="700,560" valign="center" halign="center" zPosition="3" font="Regular;48" foregroundColor="yellow" backgroundColor="black" />\
    <widget name="audiosel" position="0,0" size="1280,80" valign="center" halign="center" zPosition="2" font="Regular;48" transparent="1" foregroundColor="yellow" /></screen>'

    def __init__(self, session, args = None):					
        global plugin_path
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self['actions'] = ActionMap(['OkCancelActions', 'NumberActions', 'ColorActions', 'DirectionActions'], {'ok': self.ok,
         '1': self.k1,
         '2': self.k2,
         '3': self.k3,
         '4': self.k4,
         '5': self.k5,
         '6': self.k6,
         '7': self.k7,
         '8': self.k8,
         '0': self.positionen,
         'cancel': self.cancel,
         'left': self.links,
         'right': self.rechts,
         'up': self.rechts,
         'down': self.links,
         'red': self.konf1,
         'green': self.konf2,
         'yellow': self.audioeinzel,
         'blue': self.sender}, -1)
        self['fzhd'] = Pixmap()							
        self['fzhd'].hide()							
        self.pxmap = self['fzhd']
        self['exit'] = Label()
        self['exit'].hide()
        self.exit = self['exit']								
        self.exit.setText(_('"OK / Exit" zurück zu "FanZone"'))					
        self['warn'] = Label()
        self['warn'].hide()
        self.warn = self['warn']
        self.warn.setText(_('Warnung'))
        self['audiosel'] = Label()
        self['audiosel'].hide()
        self.audsel = self['audiosel']
        self.startch = eServiceReference()					
        self.startch = self.session.nav.getCurrentlyPlayingServiceReference()
        self.buli = []
        self.sport = []
        chafile = open('/usr/lib/enigma2/python/Plugins/SystemPlugins/SkyFanZone/cha.cfg', 'r')	
        for line in chafile:
            row = line.rstrip().split(',')
            if "FanZone" in str(row[0]):
            	self.fzmc = row
            elif ("Buli" in str(row[0])) and ("FanZone" not in str(row[0])):
            	self.buli.append(row)
            elif "Sport" in str(row[0]):
            	self.sport.append(row)
            else:
            	row = row[1]
            	row = row.split(':')
            	self.audkom = str(row[1]).strip('[]').replace(" ","")
            	startdelay = int(row[2].strip())
        chafile.close()							
        if str(self.audkom) == 'Stereo':
        	self.audkom = 0
        	self.audsel.setText(_('Kommentar Stereo'))
        elif str(self.audkom) == 'Stadion':
        	self.audkom = 2
        	self.audsel.setText(_('Stadion'))
        else:
        	self.audkom = 1
        	self.audsel.setText(_('Kommentar Dolby'))
        self.session.nav.playService(eServiceReference(self.fzmc[1]))				
        self.events = []
        self.konferenz = []							
        self.step = 1										
        self.aud = 0
        self.level = 0
        self.audioTimer = eTimer()								
        self.audioTimer.timeout.get().append(self.audiosel)
        self.hideTimer = eTimer()
        self.hideTimer.timeout.get().append(self.hide)
        self.audselTimer =eTimer()
        self.audselTimer.timeout.get().append(self.hide)
        self.warnTimer =eTimer()
        self.warnTimer.timeout.get().append(self.hide)
        self.startTimer = eTimer()
        self.startTimer.timeout.get().append(self.startup)
        self.startTimer.start(startdelay)
        
    def startup(self):
        self.startTimer.stop()									
        self.audioTimer.start(200)
        self.sender()
	self.positionen()
        if (len(self.events) != 0) and (self.track > 1):
        	self.ksp = 0
        	posy = self.pos[self.step - 1]					
       		posx = self.pos[self.step + self.track]
        	self.pxmap.setPosition(posx, posy)
        	self.pxmap.show()
        elif len(self.events) == 0:
        	self.events.append(self.fzkf[1])
		self.ksp = 1
		self.warn.setText(_('Keine Spiele gefunden\nNeue Suche mit "Blau"'))
		self.warnTimer.start(5000)
		self.warn.show()
	else:
		self.ksp = 1
		self.warn.setText(_('Momentan keine Übertragung\nNeuzuordnung mit "0"'))
		self.warnTimer.start(5000)
		self.warn.show()
				        			        	
    def sender(self):
    	epg = eEPGCache.getInstance()						
	searchevent = str(epg.lookupEvent(['E' , (self.fzmc[1], 0, -1)])).strip().strip('[]').strip('()').strip(',').replace(" ","")
	searchtitel = str(epg.lookupEvent(['T' , (self.fzmc[1], 0, -1)])).strip().strip('[]').strip('()').strip(',').replace(" ","")
	searchevent2 = str(epg.lookupEvent(['E' , (self.fzmc[1], 1, -1)])).strip().strip('[]').strip('()').strip(',').replace(" ","")
	searchtitel2 = str(epg.lookupEvent(['T' , (self.fzmc[1], 1, -1)])).strip().strip('[]').strip('()').strip(',').replace(" ","")
	if searchtitel != "'SkyHDFanZone'":					
		search = searchevent
	elif searchtitel2 != "'SkyHDFanZone'":
		search = searchevent2
	else:
		search = "ihhgrktnm68998"
	if 'ChampionsLeague' in search:
		fanevent = 'CL:'
		self.sender = self.sport
	else:
		fanevent = "BL:"
		self.sender = self.buli
	self.fzkf = self.sender[0]
	for aktive in self.sender:						
            partie = "jb+#äü(/&%"
            geg1 = "v-+?%&"							
	    geg2 ="htfdgkhj=$6(68/$"
	    title = str(epg.lookupEvent(['T' , (aktive[1], 0, -1)])).strip().replace(" ","")
	    title2 = str(epg.lookupEvent(['T' , (aktive[1], 1, -1)])).strip().replace(" ","")
	    subtitle = str(epg.lookupEvent(['S' , (aktive[1], 0, -1)])).strip().strip('[]').strip('()').strip(',').replace(" ","")
	    subtitle2 = str(epg.lookupEvent(['S' , (aktive[1], 1, -1)])).strip().strip('[]').strip('()').strip(',').replace(" ","")
	    if (subtitle == "'MomentankeinProgramm'") or ("Live" not in title):
		title = title2
		subtitle = subtitle2
	    if (str(fanevent).strip('[]') in title) and (',' in title) and ('-' in title): 
	    	title = title.split(str(fanevent).strip('[]'))							
		title = str(title[1])
		title = title.split(',')							
		title = str(title[0])
		partie = title.strip('[]').replace(" ","")
		title = title.split('-')
		geg1 = str(title[0]).strip('[]').replace(" ","")
		geg2 = str(title[1]).strip('[]').replace(" ","")
	    if geg1 == "FCBayernMünchen":
	    	geg1 ="BayernMünchen"
	    if geg1 == "BorussiaM'Gladbach":
	    	geg1 = "BorussiaMönchengladbach"
	    if geg1 == "FCSchalke04":
	    	geg1 = "Schalke04"
	    if geg1 == "FCIngolstadt04":
	    	geg1 = "FCIngolstadt"
	    if geg1 == "SCPaderborn07":
	    	geg1 = "FCPaderborn"
	    if geg2 == "FCBayernMünchen":
	    	geg2 ="BayernMünchen"
	    if geg2 == "BorussiaM'Gladbach":
	    	geg2 = "BorussiaMönchengladbach"
	    if geg2 == "FCSchalke04":
	    	geg2 = "Schalke04"
	    if geg2 == "FCIngolstadt04":
	    	geg2 = "FCIngolstadt"
	    if geg2 == "SCPaderborn07":
	    	geg2 = "FCPaderborn"
	    if (partie in search) or (geg1 in search) or (geg2 in search):  
		self.events.append(aktive[1])
	    if ('Konferenz' in title):
	    	self.konferenz.append(aktive[1])
				   
    def positionen(self):
    	pos = []
        posfile = open('/usr/lib/enigma2/python/Plugins/SystemPlugins/SkyFanZone/pos.cfg', 'r')
        for line in posfile:
            row = line.rstrip().split(',')
            pos.append(row)
        posfile.close()
        self.track = self.session.nav.getCurrentService().audioTracks().getNumberOfTracks()	
	if self.track == 8:				
		posu = pos[7]
	elif self.track == 7:
		posu = pos[6]
	elif self.track == 6:
	    	posu = pos[5]
	elif self.track == 5:
	    	posu = pos[4]
	elif self.track == 4:
	    	posu = pos[3]
	elif self.track == 3:
	    	posu = pos[2]
	elif self.track == 2:
	    	posu = pos[1]
	else:
		posu = pos[0]
	self.pos = []
        self.pos.append(int(posu[1].strip()))
        self.pos.append(int(posu[2].strip()))
        if self.track == 2:
            	self.pos.append(int(posu[2].strip()))
        if self.track > 2:
            	self.pos.append(int(posu[3].strip()))
        if self.track == 3:
            	self.pos.append(int(posu[3].strip()))
        if self.track > 3:
            	self.pos.append(int(posu[4].strip()))
        if self.track == 4:
            	self.pos.append(int(posu[4].strip()))
        if self.track > 4:
            	self.pos.append(int(posu[5].strip()))
        if self.track == 5:
            	self.pos.append(int(posu[5].strip()))
        if self.track > 5:
           	self.pos.append(int(posu[6].strip()))
        if self.track == 6:
            	self.pos.append(int(posu[6].strip()))
        if self.track > 6:
            	self.pos.append(int(posu[7].strip()))
        if self.track == 7:
            	self.pos.append(int(posu[7].strip()))
        if self.track > 7:
        	self.pos.append(int(posu[8].strip()))
        if self.track == 8:
            	self.pos.append(int(posu[8].strip()))
        if self.track > 8:
            	self.pos.append(int(posu[9].strip()))
            	self.pos.append(int(posu[10].strip()))
            	self.pos.append(int(posu[11].strip()))
        self.pos.append(int(posu[1+self.track].strip()))
        self.pos.append(int(posu[2+self.track].strip()))
        if self.track == 2:
            	self.pos.append(int(posu[2+self.track].strip()))
        if self.track > 2:
            	self.pos.append(int(posu[3+self.track].strip()))
        if self.track == 3:
            	self.pos.append(int(posu[3+self.track].strip()))
        if self.track > 3:
            	self.pos.append(int(posu[4+self.track].strip()))
        if self.track == 4:
            	self.pos.append(int(posu[4+self.track].strip()))
        if self.track > 4:
            	self.pos.append(int(posu[5+self.track].strip()))
        if self.track == 5:
            	self.pos.append(int(posu[5+self.track].strip()))
        if self.track > 5:
            	self.pos.append(int(posu[6+self.track].strip()))
        if self.track == 6:
            	self.pos.append(int(posu[6+self.track].strip()))
        if self.track > 6:
            	self.pos.append(int(posu[7+self.track].strip()))
        if self.track == 7:
        	self.pos.append(int(posu[7+self.track].strip()))
        if self.track > 7:
            	self.pos.append(int(posu[8+self.track].strip()))
        if self.track == 8:
            	self.pos.append(int(posu[8+self.track].strip()))
        if self.track > 8:
            	self.pos.append(int(posu[9+self.track].strip()))
            	self.pos.append(int(posu[10+self.track].strip()))
            	self.pos.append(int(posu[11+self.track].strip()))
        if len(self.events) > 0:
        	self.ksp = 0
    	
    def cancel(self):
        self.hide()
        if self.level == 1:						
            self.level = 0
            self.session.nav.playService(eServiceReference(self.fzmc[1]))
            self.audioTimer.start(800)
            self.pxmap.show()
        else:								
            self.hide()
            self.esc()							

    def esc(self):
        if self.startch is not None:					
            self.session.nav.playService(self.startch)
        self.close()
        return
    
    def hide(self):
        self.hideTimer.stop()					
        self.exit.hide()						
        self.warn.hide()
        self.audsel.hide()
        self.pxmap.hide()

    def ok(self):							
        if self.level == 0:						
            self.level = 1						
            self.hide()						
            if (len(self.events) < self.step) or (self.ksp == 1):				
                self.warn.setText(_('Spiel nicht gefunden\nSchalte auf Konferenz'))
        	self.warnTimer.start(3000)
        	self.warn.show()
                self.session.nav.playService(eServiceReference(self.fzkf[1]))
            else:							
            	self.session.nav.playService(eServiceReference(self.events[self.step -1]))
            self.trackselect = int(self.audkom) + 1
            self.exit.show()							
            self.hideTimer.start(3000)				
            self.audioTimer.start(800)					
        else:								
            self.cancel()

    def cursor(self):
    	posy = self.pos[self.step - 1]					
        posx = self.pos[self.step + self.track]
        self.pxmap.setPosition(posx, posy)				
        self.aud = self.step -1						
        if self.aud < 0:						
        	self.aud = self.aud + self.track
        self.session.nav.getCurrentService().audioTracks().selectTrack(self.aud) 
        self.pxmap.show()						
    
    def audiosel(self):						
        self.audioTimer.stop()						
        if self.level == 1:
        	self.session.nav.getCurrentService().audioTracks().selectTrack(self.audkom)
        else:
        	self.session.nav.getCurrentService().audioTracks().selectTrack(self.aud)
        	       
    def audioeinzel(self):
    	if self.level == 0:
    		return
    	else:
    		tracks = self.session.nav.getCurrentService().audioTracks().getNumberOfTracks()
    		if self.trackselect < tracks:
    			self.trackselect += 1
    		else:
    			self.trackselect = 1
    	self.session.nav.getCurrentService().audioTracks().selectTrack(self.trackselect - 1)
    	trackname = self.session.nav.getCurrentService().audioTracks().getTrackInfo(self.trackselect - 1).getLanguage()
    	self.audsel.setText(_(trackname))
    	self.audsel.show()
    	self.audselTimer.start(2500)
       
    def links(self):
        if self.level == 1:						
            return
        if self.step > 1:						
            self.step -= 1						
        else:
            self.step = self.track					
        self.hide()
        self.cursor()						
                
    def rechts(self):							
    	if self.level == 1:						
            return
        if self.step < self.track:
            self.step += 1
        else:
            self.step = 1    
        self.hide()
        self.cursor()
    
    def oben(self):
    	return
    	
    def unten(self):
    	return
    	
    def konf1(self):
    	if (len(self.konferenz) > 0) and (self.level == 0):
    		self.hide()
    		self.level = 1
    		self.session.nav.playService(eServiceReference(self.konferenz[0]))
    	else:
    		return
    
    def konf2(self):
    	if (len(self.konferenz) > 1) and (self.level == 0):
    		self.hide()
    		self.level = 1
    		self.session.nav.playService(eServiceReference(self.konferenz[1]))
    	else:
    		return
    
    def k1(self):
    	if self.level == 1 or self.track < 1:
    		return
    	else:
    		self.step = 1
    		self.cursor()
        
    def k2(self):
    	if self.level == 1 or self.track < 2:
    		return
    	else:
    		self.step = 2
    		self.cursor()

    def k3(self):
    	if self.level == 1 or self.track < 3:
    		return
    	else:
    		self.step = 3
    		self.cursor()
    		
    def k4(self):
    	if self.level == 1 or self.track < 4:
    		return
    	else:
    		self.step = 4
    		self.cursor()
    		
    def k5(self):
    	if self.level == 1 or self.track < 5:
    		return
    	else:
    		self.step = 5
    		self.cursor()
    		
    def k6(self):
    	if self.level == 1 or self.track < 6:
    		return
    	else:
    		self.step = 6
    		self.cursor()
    		
    def k7(self):
    	if self.level == 1 or self.track < 7:
    		return
    	else:
    		self.step = 7
    		self.cursor()
    		
    def k8(self):
    	if self.level == 1 or self.track < 8:
    		return
    	else:
    		self.step = 8
    		self.cursor()

def FZMain(session, servicelist = 0):
    session.open(fanzone)


def Plugins(path, **kwargs):
    global plugin_path
    plugin_path = path
    return PluginDescriptor(name='Sky Fan-Zone Plugin', description='Sky Fan-Zone Plugin based on F1-Plugin', icon='png/FZ.png', where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=FZMain)
