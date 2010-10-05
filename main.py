# -*- coding: utf-8 -*-
###################################################################
## this module is the main one, which contains the game class
###################################################################

from direct.showbase.ShowBase import ShowBase
from pandac.PandaModules import * #Load all PandaModules
import settings
import inputdevice
import player
import splitscreen
import trackgen3d
from playercam import PlayerCam
from text3d import Text3D
import gettext
from menu import Menu

# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------

class Game(ShowBase):
    '''
    '''
    def __init__(self):
        '''
        '''
        ShowBase.__init__(self)
        #PStatClient.connect() #activate to start performance measuring with pstats
        base.setFrameRateMeter(True) #Show the Framerate
        base.camNode.setActive(False) #disable default cam 
        self.disableMouse() #disable manual camera-control
        
        # load the settings
        self.settings = settings.Settings()
        self.settings.loadSettings("user/config.ini")
        gettext.install("ragetrack", "data/language")#, unicode=True) #installs the system language
        #trans = gettext.translation("ragetrack", "data/language", ["de"]) #installs choosen language
        #trans.install() #usage: print _("Hallo Welt") 
        
        # initialize the input devices
        self.devices = inputdevice.InputDevices(self.settings.getInputSettings())
        print self.devices
        taskMgr.add(self.devices.fetchEvents, "fetchEvents")
        
        #Initialize needed variables and objects
        self.players = [] #holds the player objects
        self.TRACK_GRIP = 0.5
        self.LINEAR_FRICTION = 0.9
        self.ANGULAR_FRICTION = 0.9
        self.splitscreen = splitscreen.SplitScreen(0)
        
        #Initialize Physics (ODE)
        self.world = OdeWorld()
        self.world.setGravity(0, 0, -9.81)
        self.deltaTimeAccumulator = 0.0 #this variable is necessary to track the time for the physics
        self.stepSize = 1.0 / 900.0 # This stepSize makes the simulation run at 60 frames per second

        #Initialize Collisions (ODE)
        self.space = OdeSimpleSpace()
        #Initialize the surface-table, it defines how objects interact with each other
        self.world.initSurfaceTable(1)
        self.world.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        self.space.setAutoCollideWorld(self.world) 
        self.contactgroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactgroup)
        
        #set up the collision event
        self.space.setCollisionEvent("ode-collision")
        base.accept("ode-collision", self.onCollision) 
        
        #Initialize the first player
        #self.addPlayer(self.devices.devices[0]) ##pass the device for the first player (probably the keyboard)
        
        # try to read the ini-file. If it fails the settings class
        # automatically contains default values
        self.settings = settings.Settings()
        try:
            self.settings.loadSettings("user/config.ini")
        except:
            pass    # so here is nothing to do
        
        # Add the main menu (though this is only temporary:
        # the menu should me a member-variable, not a local one)
        #m = menu3D.Menu()
                
        #LICHT
        plight = PointLight('plight')
        plight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        plnp = render.attachNewNode(plight)
        plnp.setPos(100, 100, 0)
        render.setLight(plnp)
        
        #m.addOption("NewGame", self.newGame)
        #m.addOption("AddPlayer", self.addPlayer)
        
        #Start the Game for testing purpose
        #self.menu = Menu(self.newGame, self.players[0].getDevice())    #if one player exist
        self.menu = Menu(self.newGame, self.devices.devices[0])         #if no player exist)
        print self.devices.getCount()
        self.menu.menuMain()
        

    # -----------------------------------------------------------------

    def addPlayer(self, device):
        '''
        creates a new player object, initializes it and sorts the cameras on the screen
        '''
        screen = self.splitscreen.addCamera()
        camera = PlayerCam(screen)
        
        #Create a new player object
        self.players.append(player.Player(len(self.players),self.world, self.space, device, camera))


    # -----------------------------------------------------------------

    def removePlayer(self, number):
        '''
        deletes a player object and sorts the cameras on the screem
        '''

        #delete the player
        for player in self.players:
            if player.getNumber() == number:
                self.players.remove(player) ##all objects must be deleted!

        #sort the cameras

    # -----------------------------------------------------------------

    def newGame(self):
        '''
        starts the game or goes to the next menu
        '''
        #Create the Track
        self.track = trackgen3d.Track3d(1000, 800, 600, 200)
        nodePath = self.render.attachNewNode(self.track.createMesh())
        tex = loader.loadTexture('data/textures/street.png')
        nodePath.setTexture(tex)
        nodePath.setTwoSided(True)
        #base.toggleWireframe()
        
        
        self.addPlayer(self.devices.devices[0])
        #Load the Map
        self.map = self.loader.loadModel("data/models/Track01")
        self.map.reparentTo(self.render)
        self.map.setScale(10, 10, 10)
        self.map.setPos(0, 10, -7)

        #add collision with the map
        #OdeTriMeshGeom(self.space, OdeTriMeshData(self.map, True))
        groundGeom = OdePlaneGeom(self.space, Vec4(0, 0, 1, -7))
        groundGeom.setCollideBits(0)
        groundGeom.setCategoryBits(3)

        #Load the Players
        ##probably unnecessary because the players are already initialized at this point

        #Load the Lights
        ambilight = AmbientLight('ambilight')
        ambilight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        render.setLight(render.attachNewNode(ambilight))

        #start the gametask
        taskMgr.add(self.gameTask, "gameTask")
        self.world.setGravity(0, 0, -1.81)



    # -----------------------------------------------------------------
    
    def onCollision(self, entry):
        '''
        Handles Collision-Events
        '''

        geom1 = entry.getGeom1()
        geom2 = entry.getGeom2()
        body1 = entry.getBody1()
        body2 = entry.getBody2()
        
        #Handles the collision-rays from the players
        for player in self.players:
            for ray in player.vehicle.collision_rays:
                if geom1 == ray or geom2 == ray:
                    normal = entry.getContactGeom(0).getNormal()
                    player.vehicle.physics_model.setGravityMode(0) #disable gravity if on the track
                    force_pos = ray.getPosition()
                    contact = entry.getContactPoint(0)
                    force_dir = force_pos - contact
                    acceleration = (ray.getLength()/2-force_dir.length())#calculate the direction
                    if acceleration > 0:
                        force_dir.normalize()
                        force_dir = Vec3(force_dir[0]*acceleration,force_dir[1]*acceleration,force_dir[2]*acceleration)
                        player.vehicle.physics_model.addForceAtPos(force_dir, force_pos)
                        #print "up:", acceleration
                        #testcode
                        #print normal
                        dir = player.vehicle.collision_model.getQuaternion().xform(Vec3(-1,0,0))
                        force_dir = Vec3(normal[0]*acceleration,normal[1]*acceleration,normal[2]*acceleration)
                        player.vehicle.hit_ground = True
                    else:
                        force_dir.normalize()
                        force_dir = Vec3(normal[0]*acceleration,normal[1]*acceleration,normal[2]*acceleration)
                        player.vehicle.physics_model.addForce(force_dir)
                    #player.vehicle.physics_model.setTorque(player.vehicle.physics_model.getAngularVel()*0.01) 
                    #player.vehicle.physics_model.addTorque(player.vehicle.physics_model.getAngularVel()*-1)
 # -----------------------------------------------------------------
             
    def gameTask(self, task):
        '''
        this task runs once per second if the game is running
        '''
        #calculate the physics
        #self.space.autoCollide() # Setup the contact joints

        self.deltaTimeAccumulator += globalClock.getDt()  
        while self.deltaTimeAccumulator > self.stepSize: # Step the simulation
            self.space.autoCollide() # Setup the contact joints  
            for player in self.players:  
                player.doStep() #refresh player specific things (rays) 
                
                #get the player input and set the forces
                if player.device.boost:
                    player.vehicle.setBoost()
                if player.device.directions[0] != 0 or player.device.directions[1] != 0:
                    player.vehicle.direction = player.device.directions
                
                linear_velocity = player.vehicle.physics_model.getLinearVel()
                angular_velocity = player.vehicle.physics_model.getAngularVel()               
                
                #calculate airresistance to get energy out of the ode-system
                player.vehicle.physics_model.addForce(linear_velocity*-self.LINEAR_FRICTION)  
                player.vehicle.physics_model.addTorque(angular_velocity*-self.ANGULAR_FRICTION)    
                
                
            self.deltaTimeAccumulator -= self.stepSize # Remove a stepSize from the accumulator until the accumulated time is less than the stepsize
            #self.space.autoCollide() # Setup the contact joints            
            self.world.quickStep(self.stepSize)
            self.contactgroup.empty() # Clear the contact joints
            #player.vehicle.hit_ground = False
            
        for player in self.players: # set new positions
            player.updatePlayer()
        return task.cont
    # -----------------------------------------------------------------

    def menuTask(self, task):
        '''
        this task runs once per second if we are in game menu
        '''
        pass

    # -----------------------------------------------------------------

# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------

game = Game()
game.run()




