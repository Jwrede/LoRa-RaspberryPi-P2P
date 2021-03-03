from time import sleep
import RPi.GPIO as GPIO
import spidev
import controller


GPIO.setmode(GPIO.BCM)

try:
    GPIO.cleanup()
except Exception as e:
    print(e)


class Controller:
    class Mock:
        pass

    ON_BOARD_LED_PIN_NO = 47  # RPi's on-board LED
    ON_BOARD_LED_HIGH_IS_ON = True
    GPIO_PINS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,)

    # LoRa config
    PIN_ID_FOR_LORA_RESET = 22

    PIN_ID_FOR_LORA_SS = 8
    PIN_ID_SCK = 11
    PIN_ID_MOSI = 10
    PIN_ID_MISO = 9

    PIN_ID_FOR_LORA_DIO0 = 5
    PIN_ID_FOR_LORA_DIO1 = 6
    PIN_ID_FOR_LORA_DIO2 = None
    PIN_ID_FOR_LORA_DIO3 = None
    PIN_ID_FOR_LORA_DIO4 = None
    PIN_ID_FOR_LORA_DIO5 = None

    def __init__(self,
                 pin_id_led=ON_BOARD_LED_PIN_NO,
                 on_board_led_high_is_on=ON_BOARD_LED_HIGH_IS_ON,
                 pin_id_reset=PIN_ID_FOR_LORA_RESET,
                 blink_on_start=(2, 0.5, 0.5)):

        self.pin_led = self.prepare_pin(pin_id_led)
        self.on_board_led_high_is_on = on_board_led_high_is_on
        self.pin_reset = self.prepare_pin(pin_id_reset)
        self.reset_transceivers()
        self.spi = self.prepare_spi(self.get_spi())
        self.transceivers = {}
        self.blink_led(*blink_on_start)

    def add_transceiver(self,
                        transceiver,
                        pin_id_ss=PIN_ID_FOR_LORA_SS,
                        pin_id_RxDone=PIN_ID_FOR_LORA_DIO0,
                        pin_id_RxTimeout=PIN_ID_FOR_LORA_DIO1,
                        pin_id_ValidHeader=PIN_ID_FOR_LORA_DIO2,
                        pin_id_CadDone=PIN_ID_FOR_LORA_DIO3,
                        pin_id_CadDetected=PIN_ID_FOR_LORA_DIO4,
                        pin_id_PayloadCrcError=PIN_ID_FOR_LORA_DIO5):

        transceiver.transfer = self.spi.transfer
        transceiver.blink_led = self.blink_led

        transceiver.pin_ss = self.prepare_pin(pin_id_ss)
        transceiver.pin_RxDone = self.prepare_irq_pin(pin_id_RxDone)
        transceiver.pin_RxTimeout = self.prepare_irq_pin(pin_id_RxTimeout)
        transceiver.pin_ValidHeader = self.prepare_irq_pin(pin_id_ValidHeader)
        transceiver.pin_CadDone = self.prepare_irq_pin(pin_id_CadDone)
        transceiver.pin_CadDetected = self.prepare_irq_pin(pin_id_CadDetected)
        transceiver.pin_PayloadCrcError = self.prepare_irq_pin(
            pin_id_PayloadCrcError)

        transceiver.init()
        self.transceivers[transceiver.name] = transceiver
        return transceiver

    def prepare_pin(self, pin_id, in_out=GPIO.OUT):
        if pin_id is not None:
            GPIO.setup(pin_id, in_out)
            new_pin = Controller.Mock()
            new_pin.pin_id = pin_id

            if in_out == GPIO.OUT:
                new_pin.low = lambda: GPIO.output(pin_id, GPIO.LOW)
                new_pin.high = lambda: GPIO.output(pin_id, GPIO.HIGH)
            else:
                new_pin.value = lambda: GPIO.input(pin_id)

            return new_pin

    def prepare_irq_pin(self, pin_id):
        pin = self.prepare_pin(pin_id, GPIO.IN)
        if pin:
            pin.set_handler_for_irq_on_rising_edge = \
                lambda handler: GPIO.add_event_detect(pin.pin_id,
                                                      GPIO.RISING,
                                                      callback=handler)
            pin.detach_irq = lambda: GPIO.remove_event_detect(pin.pin_id)
            return pin

    def get_spi(self):
        spi = None

        try:
            spi = spidev.SpiDev()
            bus = 0
            device = 0
            spi.open(bus, device)
            spi.max_speed_hz = 10000000
            spi.mode = 0b00
            spi.lsbfirst = False

        except Exception as e:
            print(e)
            GPIO.cleanup()
            if spi:
                spi.close()
                spi = None

        return spi

    def prepare_spi(self, spi):
        if spi:
            new_spi = Controller.Mock()

            def transfer(pin_ss, address, value=0x00):
                response = bytearray(1)

                pin_ss.low()
                response.append(spi.xfer2([address, value])[1])
                pin_ss.high()

                return response

            new_spi.transfer = transfer
            new_spi.close = spi.close
            return new_spi

    def led_on(self, on=True):
        self.pin_led.high() if self.on_board_led_high_is_on == on else self.pin_led.low()

    def blink_led(self, times=1, on_seconds=0.1, off_seconds=0.1):
        for i in range(times):
            self.led_on(True)
            sleep(on_seconds)
            self.led_on(False)
            sleep(off_seconds)

    def reset_pin(self, pin, duration_low=0.05, duration_high=0.05):
        pin.low()
        sleep(duration_low)
        pin.high()
        sleep(duration_high)

    def reset_transceivers(self):
        self.reset_pin(self.pin_reset)

    def __exit__(self):
        GPIO.cleanup()
        self.spi.close()
