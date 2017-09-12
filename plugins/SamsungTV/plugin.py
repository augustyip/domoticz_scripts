#           Samsung TV Python Plugin for Domoticz
#
#           keys code : https://wiki.samygo.tv/index.php?title=D-Series_Key_Codes
#           Dev. Platform : Win10 x64 & Py 3.5.3 x86
#
#           Author:     zak45, 2017
#           1.0.0:  initial release
#           2.0.0:  Added Remote control Kodi like (customizable)
#

# Below is what will be displayed in Domoticz GUI under HW
#
"""
<plugin key="SamsungTV" name="Samsung TV with Kodi Remote" author="zak45" version="2.0.0" wikilink="http://www.domoticz.com/wiki/plugins/SamsungTV.html" externallink="https://github.com/Ape/samsungctl">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="40px" required="true" default="55000"/>
        <param field="Mode1" label="Method" width="150px" required="true" default="legacy">
            <options>
                <option label="Legacy" value="legacy"/>
                <option label="Websocket" value="websocket"/>                
            </options>
        </param>
        <param field="Mode2" label="Name" width="100px" required="true" default="samsungctl"/>            
        <param field="Mode3" label="ID" width="75px" default=""/>
        <param field="Mode4" label="Timeout (wake up)" width="75px" default="5"/>
        <param field="Mode5" label="Wake UP Command (HTTP or Shell)" width="400px" default=""/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="True" />
            </options>
        </param>
    </params>
</plugin>
"""
#
# Main Import
import Domoticz
import base64
import socket
import configparser

#
# Caution : this value should not be higher than heartbeat
socket.setdefaulttimeout(10)
#
# Required to import samsungctl, path is OS dependent
# Python framework in Domoticz do not include OS dependent path
#
import sys
import os 

if sys.platform.startswith('linux'):
    # linux specific code here
    sys.path.append(os.path.dirname(os.__file__) + '/diste-packages')
elif sys.platform.startswith('darwin'):
    # mac
    sys.path.append(os.path.dirname(os.__file__) + '/site-packages')
elif sys.platform.startswith('win32'):
    #  win specific
    sys.path.append(os.path.dirname(os.__file__) + '\site-packages')

#
import samsungctl

# Connection Status
isConnected = False
KEY = ''

# Volume switch On/Off
numberMute = 0

# Delay (9) before switch off device
DelayNumber = 0

#
RemoteCommand = ()
remoteKEY =()
remotetoSEND= ()

# Domoticz call back functions
#

# Executed once at HW creation/ update. Can create up to 255 devices.
def onStart():
    global config, numberMute

    if Parameters["Mode6"] == "Debug":
        Domoticz.Debugging(1)
    if (len(Devices) == 0):
        Domoticz.Device(Name="Status",  Unit=1, Type=17, Image=2, Switchtype=17).Create()
        Options =   {   "LevelActions"  :"||||" , 
                        "LevelNames"    :"Off|TV|HDMI|HDMI1|HDMI2" ,
                        "LevelOffHidden":"true",
                        "SelectorStyle" :"0"
                     }        
        Domoticz.Device(Name="Source",  Unit=2, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
        Options =   {   "LevelActions"  :"||||" , 
                        "LevelNames"    :"Off|VOL+|VOL-" ,
                        "LevelOffHidden":"false",
                        "SelectorStyle" :"0"
                     }        
        Domoticz.Device(Name="Volume",  Unit=3, TypeName="Selector Switch", Switchtype=18, Image=8, Options=Options).Create()
        Options =   {   "LevelActions"  :"||||" , 
                        "LevelNames"    :"Off|SOURCE|ANYNET|ENTER" ,
                        "LevelOffHidden":"true",
                        "SelectorStyle" :"0"
                     }        
        Domoticz.Device(Name="Input",  Unit=4, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()        
        Domoticz.Log("Devices created.")
    
    DumpConfigToLog()
    Domoticz.Heartbeat(15)

    config = {
            "name"       :  Parameters["Mode2"]     ,
            "description":  "Domoticz"              ,
            "id"         :  Parameters["Mode3"]     ,
            "host"       :  Parameters["Address"]   ,
            "port"       :  int(Parameters["Port"]) ,
            "method"     :  Parameters["Mode1"]     ,
            "timeout"    :  int(Parameters["Mode4"]),
    }

    Domoticz.Log("Connecting to: "+Parameters["Address"]+":"+Parameters["Port"])

    isAlive()

    if (isConnected == True):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("Devices are connected - Initialisation")   
        TurnOn()
        SamsungSend("KEY_VOLDOWN",3,20)
        SamsungSend("KEY_VOLUP",3,10)        

    genRemote()

    return True

# executed each time we click on device thru domoticz GUI
def onCommand(Unit, Command, Level, Hue):
    global isConnected, numberMute

    Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + ", Connected: " + str(isConnected))

    Command = Command.strip()
    action, sep, params = Command.partition(' ')
    action = action.capitalize()

    if (isConnected == False):
        if (Command == 'On'):
            if (Unit == 1):  # Status
                PowerOn()
        Domoticz.Error("Not Connected")    
    else:        
        if (Command == 'On'):
            if (Unit == 1):  # Status
                PowerOn()
        elif (Command == 'Set Level'):            
            if (Unit == 2):  # Source selector                    
                if (Level == 10): SamsungSend("KEY_TV",Unit,Level)
                if (Level == 20): SamsungSend("KEY_HDMI",Unit,Level)
                if (Level == 30): SamsungSend("KEY_HDMI1",Unit,Level)
                if (Level == 40): SamsungSend("KEY_HDMI2",Unit,Level)
            elif (Unit == 3):   # Volume control                    
                if Devices[Unit].nValue == 0:
                    numberMute += 1
                if (Level == 10): SamsungSend("KEY_VOLUP",Unit,Level)
                if (Level == 20): SamsungSend("KEY_VOLDOWN",Unit,Level)
            elif (Unit == 4): # Source input selector                    
                if (Level == 10): SamsungSend("KEY_SOURCE",Unit,Level)
                if (Level == 20): SamsungSend("KEY_ANYNET",Unit,Level)                    
                if (Level == 30): SamsungSend("KEY_ENTER",Unit,Level)
            else:
                Domoticz.Error( "Unknown Unit number in command "+str(Unit)+".")        
        elif (Command == 'Off'):
            if (Unit == 1):  
               SamsungSend("KEY_POWEROFF",Unit,0)
               TurnOff()
            elif (Unit == 3):  # Volume control
                SamsungSend("KEY_MUTE",Unit,0)                
                manageMute()
                if Parameters["Mode6"] == "Debug":
                    Domoticz.Log("Number of Mute activation: " + str(numberMute))                 
            else:
                Domoticz.Error( "Unknown Unit number in command "+str(Unit)+".")        
        else:
            if (Unit == 1):
                if remoteSend(Command,Unit):
                    UpdateDevice(Unit,1,Command)
                else:
                    UpdateDevice(Unit,1,'undefined')
            else:
                # unknown 
                Domoticz.Error('Unknown key...!!! ???')

    return True

# execution depend of Domoticz.Heartbeat(x) x in seconds
def onHeartbeat():
    global isConnected, DelayNumber

    isAlive()

    if ((isConnected == True) and ((Devices[1].nValue == 0) or (Devices[2].nValue == 0))):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("Devices connected - re-init")   
        TurnOn()

    return True

def onDisconnect():
    global isConnected, numberMute, DelayNumber

    isConnected = False
    if Parameters["Mode6"] == "Debug":
        Domoticz.Log("Device has disconnected - Maybe PowerOff")    
    TurnOff()
    numberMute = 0
    DelayNumber = 0

    return

# executed once when HW updated/removed
def onStop():
    Domoticz.Log("onStop called")
    return True

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

# Update Device into DB
def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

# Turn devices on in Domoticz
def TurnOn():
    global numberMute, isConnected, DelayNumber

    for Key in Devices:
        if Key == 1:        
            UpdateDevice(Key, 1, 'Samsung On')
        else:
            UpdateDevice(Key, 10, '10')        
    
    numberMute = 0
    isConnected = True
    DelayNumber = 0

    return

# Turn devices off in Domoticz
def TurnOff():
    global isConnected   
    
    for Key in Devices:
        if Key == 1:
            UpdateDevice(Key, 0, 'Samsung Off')
        else:
            UpdateDevice(Key, 0, '0')

    isConnected = False

    return

# Send the command to Samsung TV and update data
def SamsungSend(KEY,Unit,Level):
    # Send command Key to Samsung TV
    with samsungctl.Remote(config) as remote:
         remote.control(KEY)
    
    if Parameters["Mode6"] == "Debug":
        Domoticz.Log("Send key : %s " % KEY)

    if KEY != "KEY_MUTE" and Unit != 1:
        UpdateDevice(Unit,Level,Level)

    if KEY == "KEY_TV":
        UpdateDevice(1,1,"TV")
    elif KEY == "KEY_HDMI":
        UpdateDevice(1,1,"HDMI")
    elif KEY == "KEY_HDMI1":
        UpdateDevice(1,1,"HDMI1")
    elif KEY == "KEY_HDMI2":
        UpdateDevice(1,1,"HDMI2")
    elif KEY == "KEY_SOURCE":
        UpdateDevice(1,1,"SOURCE")
    elif KEY == "KEY_ANYNET":
        UpdateDevice(1,1,"ANYNET")    
    elif Unit == 1:
        UpdateDevice(1,1,Level)   
 
    return

# Check if Samsung TV is On and connected to Network
# Need to do in this way as TV accept connection and disconnect immediately
def isAlive():
    global isConnected, DelayNumber
    socket.setdefaulttimeout(1)    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((config["host"], config["port"]))
        isConnected = True
    except socket.error as e:
        isConnected = False
        if DelayNumber > 9:
            onDisconnect()
        else:
            DelayNumber += 1
            if Parameters["Mode6"] == "Debug":
                Domoticz.Log('Delaynumber : ' + str(DelayNumber))    

    s.close()
    if Parameters["Mode6"] == "Debug":
            Domoticz.Log("isAlive status :" +str(isConnected))
        
    return

# Determine way to wake UP: if param 5 contains HTTP so.. else just switch On
def PowerOn():
    global DelayNumber

    if Parameters["Mode5"]:
   
        if  Parameters["Mode5"].startswith('http://'):
            PowerOnHTTP()
        else:
            PowerOnShell()
            Domoticz.Log('Shell called')
    else:

        Devices[1].Update(nValue=1, sValue='SamSung')
        DelayNumber = 0

    return

#Command to send power on to TV : via HTTP Url
def PowerOnHTTP():
    import urllib.request

    html=urllib.request.urlopen(Parameters["Mode5"], timeout=int(Parameters["Mode4"]))
    Response=html.read()
    if Parameters["Mode6"] == "Debug":
        Domoticz.Log(str(Response))    

    return

#Command to send power on to TV : via Shell script
def PowerOnShell():
    import subprocess

    try:
        subprocess.check_call(Parameters["Mode5"], shell=True, timeout=int(Parameters["Mode4"]))
    except subprocess.CalledProcessError as e:
        Domoticz.Error(str(e.returncode))
        Domoticz.Error(str(e.cmd))
        Domoticz.Error(str(e.output))


    return

def remoteSend(Command,Unit):
    global numberMute
    
    if Command in remoteKEY:
        k = remoteKEY.index(Command) 
        try:
            SamsungSend(str(remotetoSEND[k]),Unit,Command)
        except IndexError:
            Domoticz.Error('Send error or Remote command not set in ini file: ' + Command)                     
            return False        
        if Command == "Mute":            
            manageMute()
        elif Command == "VolumeUp" or Command == "VolumeDown":
            if Devices[3].nValue == 0:
                    Devices[3].Update(nValue=10, sValue='10')  
                    numberMute += 1
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log('Remote send: ' + str(k + 1) + " " + str(remotetoSEND[k]))            
    else:
        Domoticz.Error('Remote command not defined: ' + Command)
        return False
    
    return True

# get config ini file
def get_remoteconfig():
    global RemoteCommand

    name = Parameters["HomeFolder"] + "plugin_remote_"+ str(Parameters["HardwareID"]) + ".ini"

    if os.path.isfile(name):
        try:
            with open(name) as f: # No need to specify 'r': this is the default.                    
                        config = configparser.ConfigParser()
                        config.read(name)
                        RemoteCommand = config.get("Custom", "Command")                        
        except IOError as exc:
            Domoticz.Error('error : ' + str(exc))        
            raise # Propagate other kinds of IOErro

        if Parameters["Mode6"] == "Debug":
            Domoticz.Log( "ini file read...." + name)    
            Domoticz.Log( "Custom Remote Commands: " + RemoteCommand)    
    else:
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log( "No ini file :" + name)    
            Domoticz.Log( "Custom Commands for Remote not managed")
            
    return

# generate tuple for remote
def genRemote():
    global remoteKEY, remotetoSEND

    from ast import literal_eval as make_tuple

    get_remoteconfig()

    if RemoteCommand:        
        remotetoSEND = make_tuple(RemoteCommand)
    else:
        remotetoSEND=(  "KEY_GUIDE",                    
                        "KEY_UP",
                        "KEY_INFO",
                        "KEY_LEFT",
                        "KEY_ENTER",
                        "KEY_RIGHT",
                        "KEY_RETURN",
                        "KEY_DOWN",
                        "KEY_MENU",
                        "KEY_CHUP",
                        "KEY_TOOLS",
                        "KEY_VOLUP",
                        "KEY_CH_LIST",
                        "KEY_SOURCE",
                        "KEY_MUTE",
                        "KEY_CHDOWN",                    
                        "KEY_STOP",                    
                        "KEY_VOLDOWN"
                    )

    remoteKEY=( "Home",
                "Up",
                "Info",                
                "Left",
                "Select",
                "Right",
                "Back",
                "Down",                
                "ContextMenu",
                "ChannelUp",
                "FullScreen",
                "VolumeUp",
                "Channels",
                "ShowSubtitles",
                "Mute",
                "ChannelDown",                
                "Stop",                
                "VolumeDown",
                "BigStepBack",
                "Rewind",
                "PlayPause",
                "FastForward",
                "BigStepForward"
                )

    return

def manageMute():
    global numberMute

    numberMute += 1

    if ((numberMute % 2) == 0):
                    #update device
        Devices[3].Update(nValue=10, sValue='10')  
    else:
        Devices[3].Update(nValue=0, sValue='0')   

    return
