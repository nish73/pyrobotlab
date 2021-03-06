# TODO
# way to dynamically add actuators & controllers
# http://www.blender.org/api/blender_python_api_2_60_6/bpy.ops.logic.html
import bge # blender game engine
import bpy  # blender python interface
import math
import mathutils
import sys
from os.path import expanduser
import socket
import threading
import socketserver
import json
import traceback

# FIXES
# bge dynamic import or absolute? path info ???
# clean/complete shutdown
# out of bge mode and back in - should still work - removal of all globals
# already started .... on start 
# BGE - restart does not work !!!
# when "run script" bge does not exist
# BGE - restarted - and sockets left running - everything reconnects fine BUT GRAPHICS DONT MOVE !!

# MRL is disconnected - BGE terminates then restarts - connections look normal but mouth does not move !

# WORKS
# when MRL is terminated and BGE is left running - can connect multiple times & threads appear to die as expected
# regular start/stop appears to work 

home = expanduser("~")
print (home)
print (sys.version)
print (sys.path)

controlPort = 8989
serialPort  = 9191

readyToAttach = None # must I remove this too ?

#-------- obj begin ---------------
# ['__class__', '__contains__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__','__hash__', '__init__', '__le__', '__lt__', '__ne__', '__new__', '__reduce__','__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', 'actuators', 'addDebugProperty', 'alignAxisToVect', 'angularVelocity', 'applyForce', 'applyImpulse', 'applyMovement', 'applyRotation', 'applyTorque', 'attrDict', 'children', 'childrenRecursive', 'collisionCallbacks','color', 'controllers', 'debug', 'debugRecursive', 'disableRigidBody', 'enableRigidBody', 'endObject', 'get', 'getActionFrame', 'getAngularVelocity', 'getAxisVect', 'getDistanceTo', 'getLinearVelocity', 'getPhysicsId', 'getPropertyNames','getReactionForce', 'getVectTo', 'getVelocity', 'groupMembers', 'groupObject', 'invalid', 'isPlayingAction', 'life', 'linVelocityMax', 'linVelocityMin', 'linearVelocity', 'localAngularVelocity', 'localInertia', 'localLinearVelocity', 'localOrientation', 'localPosition', 'localScale', 'localTransform', 'mass', 'meshes','name', 'occlusion', 'orientation', 'parent', 'playAction', 'position', 'rayCast', 'rayCastTo', 'record_animation', 'reinstancePhysicsMesh', 'removeParent', 'replaceMesh', 'restoreDynamics', 'scaling', 'scene', 'sendMessage', 'sensors', 'setActionFrame', 'setAngularVelocity', 'setCollisionMargin', 'setLinearVelocity','setOcclusion', 'setParent', 'setVisible', 'state', 'stopAction', 'suspendDynamics', 'timeOffset', 'visible', 'worldAngularVelocity', 'worldLinearVelocity', 'worldOrientation', 'worldPosition', 'worldScale', 'worldTransform']-------- obj end ---------------

print("-------- scene begin ---------------")
scene = bge.logic.getCurrentScene()
# help(scene)
print(dir(scene))
print("-------- scene end ---------------")

"""
obj = scene.objects["i01.head.jaw"]
print("-------- obj begin ---------------")
print(dir(obj))
print("-------- obj end ---------------")
print("localOrientation", obj.localOrientation)
print("localPosition", obj.localPosition)
print("----- actuator begin ----")
print(dir(obj.actuators["i01.head.jaw"]))
print("----- actuator end ----")
actuator = obj.actuators["i01.head.jaw"]
print("dRot", actuator.dRot)
print("angV", actuator.angV)

obj.applyRotation([ 0.1, 0.0, 0.0], True)

print("localOrientation", obj.localOrientation)

# euler rotations
xyz = obj.localOrientation.to_euler()
xyz[0] = math.radians(10)
obj.localOrientation = xyz.to_matrix()

# create a rotation matrix
mat_rot = mathutils.Matrix.Rotation(math.radians(10.0), 4, 'X')
print("mat_rot", mat_rot)
# mat_rot = mathutils.Matrix.Rotation(math.radians(10.0), 3, 'X')

# extract components back out of the matrix
#loc, rot, sca = obj.localOrientation.decompose()
#print(loc, rot, sca)
#obj.applyRotation(mat_rot)
#obj.localTransform = mat_rot

#obj.localOrientation = mat_rot.to_3x3()

"""

# TODO - derive from json object - so we can control correct encoding
# http://stackoverflow.com/questions/3768895/python-how-to-make-a-class-json-serializable
class MyRobotLab:
  """the MyRobotLab class - mrl manages the control and serial servers which the middleware interfaces with"""
  def __init__(self):
    self.control = None
    self.controlServer = None
    self.serialServer = None
    self.virtualDevices = {}
    self.blenderObjects = {}
    self.version = "0.9"
    self.pos = 0.0
    
  def toJson(self):
    ret = "{'control': "
    ret += "'initialized'" if (self.control != None) else "'None'"
    ret += ", 'controlServer': "
    ret += "'initialized'" if (self.controlServer != None) else "'None'"
    ret += ", 'serialServer': "
    ret += "'initialized'" if (self.serialServer != None) else "'None'"
    ret += ", 'virtualDevices': ["
    
    vdJson = []
   
    print(self.virtualDevices)
    for vd in self.virtualDevices:
      print("virtual device [" + vd + "]")
      #vdJson.append("'" + vd + "': " + self.virtualDevices[vd])
      #vdJson.append("'" + vd + "': '" + vd + "'")
    
    ret += ",".join(self.virtualDevices)
    ret += "]"
    
    ret += "}"
    return ret
    
def toJson():
  return bpy.mrl.toJson();
    
# bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0

if (not hasattr(bpy, "mrl")):
    print("initializing MyRobotLab")
    bpy.mrl = MyRobotLab()
else:
    print("MyRobotLab already initialized")

class Message:
  """an MRL message definition in Python"""
  def __init__(self):
    self.msgID = 0
    self.timeStamp = 0
    self.name = ""
    self.sender = ""
    self.method = ""
    self.sendingMethod = ""
    self.data = []
    self.historyList = []
    #def __init__(self, j):
      #self.__dict__ = json.loads(j)
      
class VirtualDevice:
  """a virtual device Servo, Arduino, Lidar, etc"""
  def __init__(self, name, type):
    self.name = name
    self.type = type
    self.serialHandler = None
    self.service = None
   
  def toJson(self):
    ret = "{'name':'" + self.name + "', 'type':'" + self.type + "',"
    ret += "'serialHandler': '"
    ret += "'initialized'" if (self.serialHandler != None) else "'None'"
    ret += "'service': '"
    ret += "'initialized'" if (self.service != None) else "'None'"
    ret += "}"

def getVersion():
  print("version is ", bpy.mrl.version)
  return bpy.mrl.version


def Cube():
    global a
    #print ("cube ", a)
    scene = bge.logic.getCurrentScene()     #Locate current device
    cont = bge.logic.getCurrentController()
    own = cont.owner   
 
    xyz = own.localOrientation.to_euler()   #Extract the Rotation Data    
    xyz[0] = math.radians(a)                #PreLoad your RX data
                                            #xyz[0] x Rotation axis
                                            #xyz[1] y Rotation axis
                                            #xyz[2] z Rotation axis
    own.localOrientation = xyz.to_matrix()  #Apply your rotation data
  
def createJsonMsg(method, data):
  msg = Message()
  msg.name = "blender"
  msg.method = method
  msg.sendingMethod = method
  msg.data.append(data)
  retJson = json.dumps(msg.__dict__)
  # FIXME - better terminator ?
  retJson = retJson + "\n"
  return retJson.encode()

def onError(msg):
  print(msg)
  request = bpy.mrl.control.request
  request.sendall(createJsonMsg("onError", msg))
    
def stopServer():
    print ("stopping controlServer")
    controlServer = bpy.mrl.controlServer
    
    if (controlServer != None):
        controlServer.shutdown()
    else:
        print("controlServer already stopped")
    bpy.mrl.controlServer = None
    
    print ("stopping serialServer")
    
    serialServer = bpy.mrl.serialServer
    
    if (serialServer != None):
        serialServer.shutdown()
    else:
        print("serialServer already stopped")
    bpy.mrl.serialServer = None
    
    #for controlHandler in controlHandlers
    #    print (controlHandler)
    #controlHandlers[controlHandler].listening = False  
    
def startServer():
    global controlPort
    controlServer = bpy.mrl.controlServer
    if (controlServer ==  None):
      ##### control server begin ####
      controlServer = ThreadedTCPServer(("localhost", controlPort), ControlHandler)
      bpy.mrl.controlServer = controlServer
      ip, port = controlServer.server_address

      # Start a thread with the controlServer -- that thread will then start one
      # more thread for each request
      controlThread = threading.Thread(target=controlServer.serve_forever)
      # Exit the controlServer thread when the main thread terminates
      controlThread.daemon = True
      controlThread.start()
      print ("control server loop running in thread: ", controlThread.name, " port ", controlPort)
      ##### control server end ####
      ##### serial server begin ####
      serialServer = ThreadedTCPServer(("localhost", serialPort), SerialHandler)
      bpy.mrl.serialServer = serialServer
      ip, port = serialServer.server_address

      # Start a thread with the serialServer -- that thread will then start one
      # more thread for each request
      serialThread = threading.Thread(target=serialServer.serve_forever)
      # Exit the serialServer thread when the main thread terminates
      serialThread.daemon = True
      serialThread.start()
      print ("serial server loop running in thread: ", serialThread.name, " port ", serialPort)
      ##### serial server end ####
    else:
      print ("servers already started")
        

# attach a device - control message comes in and sets up
# name and type - next connection on the serial port will be
# the new device
# FIXME - catch throw on class not found
def attach(name, type):
  global readyToAttach
  # adding name an type to new virtual device
  newDevice = VirtualDevice(name, type)
  # constructing the correct type
  newDevice.service = eval(type + "('" + name + "')")
  bpy.mrl.virtualDevices[name] = newDevice
  readyToAttach = name
  print("onAttach " + str(name) + " " + str(type) + " SUCCESS - ready for serial connection")
  # print("<--- sending control onAttach(" + str(name) + ")")
  # control.request.sendall(createJsonMsg("onAttach", name))
  return name

    
class ControlHandler(socketserver.BaseRequestHandler):
    listening = False
    
    def handle(self):
        bpy.mrl.control = self
        #data = self.request.recv(1024).decode()
        myThread = threading.current_thread()
        
        print("---> client connected to control socket thread {} port {}".format(myThread.name, controlPort))
        
        buffer = ''
        
        listening = True

        while listening:
            try:
                # Try to receive som data
                # data = self.request.recv(1024).decode()
                # TODO - refactor to loading Message object
                controlMsg = json.loads(self.request.recv(1024).decode().strip())
                
                print("---> control: controlMsg ", controlMsg)
                method = controlMsg["method"]
                
                #### command processing begin ####
                command = method + "("
                cnt = 0
                
                # unload parameter array
                data = controlMsg["data"]
                if (len(data) > 0):
                  for param in data:
                    cnt += 1
                    
                    if isinstance(param, int):
                      command = command + str(param)
                    else:
                      command = command + "'" + param + "'"
                      
                    if (len(data) != cnt):
                      command = command + ","
                
                command = command + ")"
                
                print ("*** command " , command, " ***")
                
                ret = eval(command)
                retMsg = Message()
                retMsg.name = "blender"
                retMsg.method = "on" + method[0:1].capitalize() + method[1:]
                retMsg.sendingMethod = controlMsg["method"]
                retMsg.data.append(ret)
                
                retJson = json.dumps(retMsg.__dict__)
                
                print ("<--- control: ret" , retJson)
                
                self.request.sendall(retJson.encode())
                # TODO - better way to send full json message ? better way to parse it?
                self.request.sendall("\n".encode())
                #### command processing end ####
            
            except Exception as e:  
                print ("control handler error: ", e)
                print (traceback.format_exc())
                #run_main_loop = False
                listening = False
        
        print("terminating control handler", myThread.name, controlPort)


class SerialHandler(socketserver.BaseRequestHandler):
      listening = False
      service = None
      name = ""
      
      def handle(self):
          global readyToAttach
          
          myThread = threading.current_thread()
          
          if (readyToAttach in bpy.mrl.virtualDevices):
            print("++++attaching " + str(readyToAttach) + " serial handler++++ thread {} port {}".format(myThread.name, serialPort))
            bpy.mrl.virtualDevices[readyToAttach].serialHandler = self
            service = bpy.mrl.virtualDevices[readyToAttach].service
            self.name = readyToAttach
          else:
            print("could not attach serial device")
            # ERROR - we need a name to attach
            onError("XXXX incoming serial connection but readyToAttach [" + str(readyToAttach) + "] XXXX")
            return           
          
          listening = True
  
          while listening:
            try:
              data = self.request.recv(1024)
              service.handle(data)

            except Exception as e:  
                print ("serial handler error: ", e)
                print (traceback.format_exc())
                #run_main_loop = False
                listening = False
        
          print("terminating serial handler", myThread.name, serialPort)
         
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
        
class Arduino:
  def __init__(self, name):
    print("creating new Arduino ", name)
    self.name = name
    self.servos = {}
    self.msgByteCount = 0
    self.msgSize = 0
    self.method = 0
    self.params = []
    self.version = 20
    
  def sendMRLCOMMMsg(self, method, value):
    socket = bpy.mrl.virtualDevices[self.name].serialHandler.request
    print("sending bytes")
    print(bytes([170, method, 1, value]))
    # MRLCOMM PROTOCOL
    # MAGIC_NUMBER|NUM_BYTES|FUNCTION|DATA0|DATA1|....|DATA(N)
    #              NUM_BYTES - is the number of bytes after NUM_BYTES to the end
    
    socket.sendall(bytes([170, 2, method, value]))

  def handle(self, byteArray):
    newByteCnt = len(byteArray)
    # print (self.name + " recvd " + str(newByteCnt) + " bytes")
    # print(byteArray)
    
    # parse MRL Msg
    for newByte in byteArray: 
      self.msgByteCount += 1
      # print("byte ", newByte, " byteCount  ", self.msgByteCount, " size ", self.msgSize)
      # check magic
      if (self.msgByteCount == 1):
        if (newByte != 170):
          print("ERROR message does not begin with MAGIC")
          self.msgByteCount = 0
          self.msgSize = 0
      elif (self.msgByteCount == 2):      
        # print command - TODO error checking > 64        
        self.msgSize = newByte
        # print("MRLCOMM msg size is " + str(self.msgSize))
      elif (self.msgByteCount == 3):  
        # print("MRLCOMM method is " + str(newByte))
        self.method = newByte
      elif (self.msgByteCount > 3 and self.msgByteCount - 3 < self.msgSize):  
        # print("MRLCOMM datablock")
        self.params.append(newByte)
      elif (self.msgByteCount > 3 and self.msgByteCount - 3 > self.msgSize):  
        print("MRLCOMM ERROR STATE - resetting ")
        self.msgSize = 0
        self.msgByteCount = 0
        self.params = []

      # now we have a full valid message
      if (self.msgByteCount - 2 == self.msgSize and self.msgSize != 0):
        
        # GET_VERSION
        if (self.method == 26):
          print("GET_MRLCOMM_VERSION")
          self.sendMRLCOMMMsg(26, self.version)          
        elif (self.method == 6):
          print("SERVO_ATTACH", self.params)
          # create "new" servo if doesnt exist
          # attach to this Arduino's set of servos
          params = self.params
          servoIndex = params[0]
          servoPin = params[1]
          
          servoName = ""
          for x in range(3, params[2]+3):
            servoName += chr(params[x])
          print ("servo index", servoIndex, "pin", servoPin, "name", servoName)
          print("servo index")
          self.servos[servoIndex] = servoName
          bpy.mrl.blenderObjects[servoName] = 0 # rest position? 90 ?
        elif (self.method == 7):
          print("SERVO_WRITE", self.params)
          #moveTo(self.params[1])
          # FIXME - not necessary to put in blenderObject[] on attach !!!
          servoIndex = self.params[0]
          pos = self.params[1]
          servoName = self.servos[servoIndex]
#          print("blender object ", servoName, "position", pos)
          bpy.mrl.blenderObjects[servoName] = pos
        elif (self.method == 8):
          print("SERVO_SET_MAX_PULSE", self.params)
        elif (self.method == 9):
          print("SERVO_DETACH", self.params)
        elif (self.method == 12):
          print("SET_SERVO_SPEED", self.params)
        elif (self.method == 28):
          print("SERVO_WRITE_MICROSECONDS", self.params)
        else:
          print ("UNKNOWN METHOD ", self.method, self.params)
        
        #print("MRLCOMM msg done ")
        self.msgSize = 0
        self.msgByteCount = 0
        self.params = []
          
      # do command

# TODO - REMOVE
def moveTo():

    # iterate through all current actuator points
    for name in bpy.mrl.blenderObjects:
      # set each
      scene = bge.logic.getCurrentScene()        
      #object = scene.objects["Servo_Jaw_Drive_shaft"]
      object = scene.objects[name]
      xyz = object.localOrientation.to_euler()
      # orientation a problem?
      pos = bpy.mrl.blenderObjects[name]
      xyz[0] = math.radians(pos/8)
      object.localOrientation = xyz.to_matrix()
    
    """
    scene = bge.logic.getCurrentScene()
    cont = bge.logic.getCurrentController()
    own = cont.owner   
    #print (a)    
    xyz = own.localOrientation.to_euler()
    xyz[0] = math.radians(bpy.mrl.pos/8)
    own.localOrientation = xyz.to_matrix()
    """

tick = 0
    
def frameTick():
  """Always block will drive this to update all data which would effect the scene"""
  global tick
  tick += 1
  # iterate through global containers
  # if data different than last time - update scene
  # this method should be quick 
  if (tick == 1):
    print("frame tick")
    
  scene = bge.logic.getCurrentScene()        
    
  # iterate through all "attached" blender objects
  for name in bpy.mrl.blenderObjects:
    if (name not in scene.objects):
      #print("did not find", name, "in blender objects - need to define objects and actuators?")
      continue
      
    # grab object of the same name as MRL service
    obj = scene.objects[name]
    # for that object - grab it's actuator with the same name
    # actuator = obj.actuators[name]
    actuator = obj.actuators[0]

    # apply the rotation for that actuator locally
    # print("local ", obj.localOrientation)
    # print(actuator.dRot)
    # xyz = obj.localOrientation.to_euler()
    # orientation a problem?
    pos = bpy.mrl.blenderObjects[name]
    xyz = obj.localOrientation.to_euler()
    
    # find actuators rotation axis based on dRot
    av = actuator.dRot
    axis = 3
    if (av[0] != 0):
      axis = 0 # x
    elif (av[1] != 0):
      axis = 2 # y
    elif (av[2] != 0):
      axis = 1 # z
    else:
      print("ERROR UNKNOWN AXIS")
      return
      
    # FIXME - should just do matrix multiplications
    # but since rotations are so simple at the moment
    # using Euler conversions
    
    # print ("av", av, "axis", axis, "pos", pos)
    # nice debugging prints out "working" position & axis & object
    # print(name, "axis", axis, "pos", pos)
    
    xyz = obj.localOrientation.to_euler()
    # depending on mechanical amplification
    # this unit (if not accurately modeled) could
    # be different for each joint
    # xyz[axis] = math.radians(pos/8)
    xyz[axis] = math.radians(pos/2)
    obj.localOrientation = xyz.to_matrix()
    
    # print("pos", pos, obj.localOrientation, obj.localOrientation.to_euler())
      
    # Euler cheating way - because I don't know
    # how to apply "absolute" matrix
    
    #    cont = bge.logic.getCurrentController()
    #    own = cont.owner   

    
""" GONNA USE EULER SINCE ONLY ROT ON 1 AXIS
    xyz = obj.localOrientation.to_euler()
    xyz[0] = math.radians(pos/8)
    obj.localOrientation = xyz.to_matrix()
"""  
  

def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(message)
        response = sock.recv(1024).encode
        print ("Received: {}".format(response))
    finally:
        sock.close()
    
def endcomm():
    print("endcomm")
    bge.logic.endGame()    
    
    
startServer()
    
# mrl = MyRobotLab()
# print(mrl.toJson())