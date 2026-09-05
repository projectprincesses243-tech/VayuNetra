import serial
import time


class ESP32Radio:


    def __init__(
        self,
        port="/dev/ttyUSB0",
        baudrate=115200
    ):

        self.connection = serial.Serial(
            port,
            baudrate,
            timeout=1
        )

        time.sleep(2)



    def send(self,message):

        self.connection.write(
            (
                message+"\n"
            ).encode()
        )



    def receive(self):

        if self.connection.in_waiting:

            return (
                self.connection.readline()
                .decode()
                .strip()
            )

        return None



    def close(self):

        self.connection.close()



if __name__=="__main__":

    print("Connecting ESP32...")

    radio = ESP32Radio()

    print("ESP32 Port Open")

    radio.send(
        '{"type":"PING","source":"RASPBERRY_PI"}'
    )

    time.sleep(1)

    print(
        "Response:",
        radio.receive()
    )

    radio.close()
