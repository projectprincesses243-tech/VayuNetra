import serial.tools.list_ports


def list_devices():

    devices = []

    ports = serial.tools.list_ports.comports()

    for port in ports:

        device = {
            "port": port.device,
            "description": port.description,
            "manufacturer": port.manufacturer
        }

        devices.append(device)

    return devices


if __name__ == "__main__":

    devices = list_devices()

    print("\nDetected devices:\n")

    for d in devices:
        print("----------------")
        print("PORT:", d["port"])
        print("DESCRIPTION:", d["description"])
        print("MANUFACTURER:", d["manufacturer"])
