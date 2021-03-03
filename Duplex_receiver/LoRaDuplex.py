import time


def millisecond(): return time.time() * 1000


msgCount = 0  # count of outgoing messages
INTERVAL = 2000  # interval between sends
INTERVAL_BASE = 2000  # interval between sends base


def duplex(lora):
    print("LoRa Duplex")
    f = open("/home/R2B", "w")
    do_loop(lora, f)


def do_loop(lora, f):
    global msgCount

    lastSendTime = 0
    interval = 0

    while True:
        now = millisecond()
        if now < lastSendTime:
            lastSendTime = now

        if (now - lastSendTime > interval):
            lastSendTime = now  # timestamp the message
            interval = (lastSendTime % INTERVAL) + INTERVAL_BASE  # 2-3 seconds

            message = "{} {}".format("RPi", msgCount)
            sendMessage(lora, message)  # send message
            msgCount += 1

            # parse for a packet, and call onReceive with the result:
        receive(lora, f)


def sendMessage(lora, outgoing):
    lora.println(outgoing)
    print("Sending message:\n{}\n".format(outgoing))


def receive(lora, f):
    if lora.receivedPacket():
        lora.blink_led()

        try:
            payload = lora.read_payload()
            f.write(payload.decode() + "\n")
        except Exception as e:
            print(e)
        print("with RSSI {}\n".format(lora.packetRssi()))
