import serial
import time


class STM32Serial:

    def __init__(
        self,
        port="/dev/ttyACM0",
        baudrate=115200
    ):

        self.connection = serial.Serial(
            port,
            baudrate,
            timeout=1
        )

        time.sleep(2)


    def send(self, message):

        self.connection.write(
            (
                message + "\n"
            ).encode()
        )


    def receive(self):

        if self.connection.in_waiting:

            data = (
                self.connection.readline()
                .decode()
                .strip()
            )

            return data

        return None


    def close(self):

        self.connection.close()



if __name__ == "__main__":

    print("Connecting STM32...")

    stm = STM32Serial()

    print("STM32 Port Open")

    stm.send(
        '{"type":"PING","source":"RASPBERRY_PI"}'
    )

    time.sleep(1)

    response = stm.receive()

    print(
        "Response:",
        response
    )

    stm.close()
