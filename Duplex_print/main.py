import LoRaDuplex
from controller import Controller
import sx127x
import gc


def main():
    controller = Controller()

    lora = controller.add_transceiver(sx127x.SX127x(name='LoRa'),
                                      pin_id_ss=Controller.PIN_ID_FOR_LORA_SS,
                                      pin_id_RxDone=Controller.PIN_ID_FOR_LORA_DIO0)

    LoRaDuplex.duplex(lora)


if __name__ == '__main__':
    gc.collect()
    main()
