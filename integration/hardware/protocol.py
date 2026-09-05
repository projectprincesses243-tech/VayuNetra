import json


def encode_message(data):
    """
    Convert dictionary to serial message
    """

    return json.dumps(data) + "\n"



def decode_message(message):
    """
    Convert received serial data
    into dictionary
    """

    return json.loads(
        message.strip()
    )



if __name__ == "__main__":

    test_message = {

        "type": "PING",

        "source": "RASPBERRY_PI",

        "id": 0

    }


    encoded = encode_message(
        test_message
    )

    print("Encoded:")
    print(encoded)


    decoded = decode_message(
        encoded
    )

    print("Decoded:")
    print(decoded)
