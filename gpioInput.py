import RPi.GPIO as GPIO

class GpioInput():
	GPIO.setmode(GPIO.BCM)

	windowWidth = 0

	SPICLK = 11
	SPIMISO = 9
	SPIMOSI = 10
	SPICS = 8

	BUTTON = 7
	# set up the SPI interface pins
	GPIO.setup(SPIMOSI, GPIO.OUT)
	GPIO.setup(SPIMISO, GPIO.IN)
	GPIO.setup(SPICLK, GPIO.OUT)
	GPIO.setup(SPICS, GPIO.OUT)

	GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	# 10k trim pot connected to adc #0
	potentiometer_adc = 0
	# END POT INSERT

	def __init__(self, wdw):
		self.windowWidth = wdw

	def readButton(self):
		return GPIO.input(self.BUTTON) == False

	def getPotPosition(self):
		trim_pot = self.readadc(self.potentiometer_adc, self.SPICLK, self.SPIMOSI, self.SPIMISO, self.SPICS)
		trim_pot * self.windowWidth / 1023.0

		return trim_pot

	# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
	def readadc(self, adcnum, clockpin, mosipin, misopin, cspin):

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