
class Buzzer:
    def __init__(self, GPIO, pin):
        self.__pin = pin
        self.__GPIO = GPIO
        self.__GPIO.setup(self.__pin, self.__GPIO.OUT)
    
    def turn(self, state):
        if state :
            self.__GPIO.output(self.__pin, self.__GPIO.HIGH)
            print("Beep {}".format(self.__pin))
        else :
            self.cleanup()
            print("No Beep")
        return self
    
    def cleanup(self) :
        self.__GPIO.output(self.__pin, self.__GPIO.LOW)
        print("Cleanup")
        return self
