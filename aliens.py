import pygame, sys, random, math
import pygame.locals as GAME_GLOBALS
import pygame.event as GAME_EVENTS
import pygame.time as GAME_TIME
import ships

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):

	if ((adcnum > 7) or (adcnum < 0)):
		return -1
	GPIO.output(cspin, True)

	GPIO.output(clockpin, False)  # start clock low
	GPIO.output(cspin, False)     # bring CS low

	commandout = adcnum
	commandout |= 0x18  # start bit + single-ended bit
	commandout <<= 3    # we only need to send 5 bits here
	for i in range(5):
		if (commandout & 0x80):
			GPIO.output(mosipin, True)
		else:
			GPIO.output(mosipin, False)
		commandout <<= 1
		GPIO.output(clockpin, True)
		GPIO.output(clockpin, False)

	adcout = 0
	# read in one empty bit, one null bit and 10 ADC bits
	for i in range(12):
		GPIO.output(clockpin, True)
		GPIO.output(clockpin, False)
		adcout <<= 1
		if (GPIO.input(misopin)):
			adcout |= 0x1

	GPIO.output(cspin, True)

	adcout >>= 1       # first bit is 'null' so drop it
	return adcout

SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# 10k trim pot connected to adc #0
potentiometer_adc = 0;
# END POT INSERT


windowWidth = 800
windowHeight = 480

pygame.init()
pygame.font.init()
# surface = pygame.display.set_mode((windowWidth,windowHeight), pygame.FULLSCREEN)
surface = pygame.display.set_mode((windowWidth,windowHeight))

pygame.display.set_caption('Alien\'s Are Gonna Kill Me!')
textFont = pygame.font.SysFont("monospace", 50)

gameStarted = False
gameStartedTime = 0
gameFinishedTime = 0
gameOver = False

# Mouse variables
mousePosition = (0,0)
mouseStates = None
mouseDown = False

# Image variables
startScreen = pygame.image.load("assets/start_screen.png")
background = pygame.image.load("assets/background.png")

# Ships
ship = ships.Player(windowWidth / 2, windowHeight, pygame, surface)
enemyShips = []

lastEnemyCreated = 0
enemyInterval = random.randint(1000, 2500)

# Sound setup
pygame.mixer.init()

def updateGame():
	global mouseDown, gameOver

	if mouseStates[0] is 1 and mouseDown is False:
		ship.fire()
		mouseDown = True
	elif mouseStates[0] is 0 and mouseDown is True:
		mouseDown = False

	ship.setPosition(pot_position)

	enemiesToRemove = []

	for idx, enemy in enumerate(enemyShips):
		if enemy.y < windowHeight:
			enemy.move()
			enemy.tryToFire()
			shipIsDestroyed = enemy.checkForHit(ship)
			enemyIsDestroyed = ship.checkForHit(enemy)

			if enemyIsDestroyed is True:
				enemiesToRemove.append(idx)

			if shipIsDestroyed is True:
				gameOver = True
				print "\n\n\nYou Died\n\n\n"
				pygame.mouse.set_visible(True)
				# TODO I think gameFinishedTime should be set here
				# TODO This should display GAME OVER screen, not quit the game, right? 
				# quitGame()

		else:
			enemiesToRemove.append(idx)

	for idx in enemiesToRemove:
		del enemyShips[idx]

def drawGame():
	surface.blit(background, (0,0))
	ship.draw()
	ship.drawBullets()

	for enemy in enemyShips:
		enemy.draw()
		enemy.drawBullets()

def quitGame():
	pygame.quit()
	sys.exit()

# MAIN LOOP
while True:
	timeTick = GAME_TIME.get_ticks()
	mousePosition = pygame.mouse.get_pos()
	mouseStates = pygame.mouse.get_pressed()
	trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
	pot_position = trim_pot * (windowWidth / 1024)

	if gameStarted is True and gameOver is False:
		updateGame()
		drawGame()

	elif gameStarted is False and gameOver is False:
		surface.blit(startScreen, (0,0))
		if mouseStates[0] is 1:
			# TODO change for varying screen sizes
			# print "x: " + str(mousePosition[0]) + " y: " + str(mousePosition[1])
			if mousePosition[0] > 350 and mousePosition[0] < 450 and mousePosition[1] > 350 and mousePosition[1] < 400:
				# TODO I think that gameStartedTime should be set here
				pygame.mouse.set_visible(False)
				gameStarted = True
		elif mouseStates[0] is 0 and mouseDown is True:
			mouseDown = False

	elif gameStarted is True and gameOver is True:
		surface.blit(startScreen, (0,0))
		timeLasted = (gameFinishedTime - gameStartedTime) / 1000

	# Handle user and system events
	for event in GAME_EVENTS.get():
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				quitGame()

		if event.type == GAME_GLOBALS.QUIT:
			quitGame()

	if GAME_TIME.get_ticks() - lastEnemyCreated > enemyInterval and gameStarted is True:
		enemyShips.append(ships.Enemy(random.randint(0, windowWidth), -60, pygame, surface, 1))
		lastEnemyCreated = GAME_TIME.get_ticks()

	pygame.display.update()