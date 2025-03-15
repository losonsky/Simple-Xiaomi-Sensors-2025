#!/usr/bin/python3 -u

import asyncio
import struct
from Cryptodome.Cipher import AES
from bleak import BleakScanner

import paho.mqtt.client as mqtt
# bash
import subprocess

# MQTT broker details
broker = "192.168.1.10"
port = 1883
username = "test01"
password = "123"


XIAOMI_DEVICES = {
    "A4:C1:38:74:38:7A": {
        "alias": "MI_0",
        "dev_type": "LYWSD03MMC",
        "bind_key": bytes.fromhex("6c9725e5358e137580d063a68c4a05ea")  # 16-byte AES key
    }
    ,
    "A4:C1:38:D4:75:50": {
        "alias": "MI_1",
        "dev_type": "LYWSD03MMC",
        "bind_key": bytes.fromhex("1daa6055aa6fc2e17abddab555d63c78")  # 16-byte AES key
    }
    # ,
    # "A4:C1:38:C6:11:02": {
    #     "alias": "MI_2",
    #     "dev_type": "MHO-C401",
    #     "bind_key": bytes.fromhex("425291f9922c618494f7bdd4564ebdf5")  # 16-byte AES key
    #     # "bind_key": bytes.fromhex("d1f73801ef999872ff8b0c0b9fcb1e5d")  # 16-byte AES key
    #     # "bind_key": bytes.fromhex("bdda814f40f1517d1116594af6ac141c")  # 16-byte AES key
    # }
    ,
    "A4:C1:38:5E:EB:EB": {
        "alias": "MI_3",
        "dev_type": "LYWSD03MMC",
        "bind_key": bytes.fromhex("56a20342f366da96036cab9b87cc98cb")  # 16-byte AES key
    }
    ,
    "A4:C1:38:6D:3B:2B": {
        "alias": "MI_4",
        "dev_type": "LYWSD03MMC",
        "bind_key": bytes.fromhex("9955608fe7c9cff55dc919a9eefd0a30")  # 16-byte AES key
    }
}



# 📡 Received Encrypted Data from MI_0 (A4:C1:38:74:38:7A): 5858 5b05 75 7a387438c1a4 cdf655af5d5e0000ae831e70
# 📡 Received Encrypted Data from MI_0 (A4:C1:38:74:38:7A): 5858 5b05 76 7a387438c1a4 f52309574f5e0000bb1c9510
# 📡 Received Encrypted Data from MI_0 (A4:C1:38:74:38:7A): 5858 5b05 88 7a387438c1a4 f8999856cb5e00001bc2f839
# 📡 Received Encrypted Data from MI_0 (A4:C1:38:74:38:7A): 5858 5b05 da 7a387438c1a4 f5c16f85045e0000c9627de3


def decrypt_xiaomi_data(advertisement_data, bind_key, alias):
    """Decrypts Xiaomi BLE encrypted advertisement data."""
    if len(advertisement_data) < 15:
        print(f"❌ Invalid payload length for {alias}: {advertisement_data.hex()}")
        # subprocess.run(["expect", "/usr/local/bin/losonewble.sh", "A4:C1:38:C6:11:02", "1"], check=True)
        subprocess.run(["expect", "/usr/local/bin/losonewble.sh", "A4:C1:38:C6:11:02"], check=True)
        return None

    crypto_payload = advertisement_data[11:-7] # without Header, Counter and MIC
    mic = advertisement_data[-4:]
    nonce = bytes([ *advertisement_data[5:11], *advertisement_data[2:4], advertisement_data[4], *advertisement_data[-7:-4]])

    # print(f"advertisement_data: {advertisement_data.hex()}, nonce: {nonce.hex()}, mic: {mic.hex()}")
    cipher = AES.new(bind_key, AES.MODE_CCM, nonce=nonce, mac_len=4)
    cipher.update(b"\x11")

    try:
        decrypted = cipher.decrypt_and_verify(crypto_payload, mic)  # Decrypt + Verify MIC
        return decrypted
    except ValueError:
        print(f"❌ Decryption failed for {alias}, check bind key or nonce!")
        return None

def detection_callback(device, advertisement_data):
    if device.address in XIAOMI_DEVICES:
        alias = XIAOMI_DEVICES[device.address]["alias"]
        dev_type = XIAOMI_DEVICES[device.address]["dev_type"]
        bind_key = XIAOMI_DEVICES[device.address]["bind_key"]

        service_data = advertisement_data.service_data.get("0000fe95-0000-1000-8000-00805f9b34fb")
        if service_data:
            # print(f"📡 Received Encrypted Data from {alias} ({device.address}): {service_data.hex()} {bind_key.hex()}")
            decrypted_data = decrypt_xiaomi_data(service_data, bind_key, alias)
            if decrypted_data:
                print(f"alias: {alias}, decrypted_data: {decrypted_data.hex()}")
                if len(decrypted_data) == 5:
                    msg, tmp0, tmp1, value = struct.unpack("<BBBh", decrypted_data)
                    # temp, humi, batt, volt, rssi = struct.unpack("<BBBBB", decrypted_data)
                    # temp, humi, batt, volt, rssi = struct.unpack("<hBB", decrypted_data[:4])
                    # temp, hum = struct.unpack("<hH", decrypted_data)
                    # print(f"alias: {alias}, temp: {temp}, humi: {humi}, batt: {batt}, volt: {volt}, rssi: {rssi}")
                    # print(f"🌡 {alias} - Temp: {temp / 10:.1f}°C, Humidity: {hum / 10:.1f}%")
                    if msg == 4:
                        # temp = 0.1 * (256 * decrypted_data[4] + decrypted_data[3])
                        temp = 0.1 * value
                        print(f"alias: {alias}, temp: {temp:.1f}°C")
                        topic = f"{alias}/tx/{dev_type}/temperature"
                        client = mqtt.Client(client_id="orangepizero3", clean_session=True)
                        client.username_pw_set(username, password)
                        client.connect(broker, port, 60)
                        client.publish(topic, temp)
                        client.loop_start()
                        client.disconnect()
                    if msg == 6:
                        # humi = 0.1 * (256 * decrypted_data[4] + decrypted_data[3])
                        humi = 0.1 * value
                        print(f"alias: {alias}, humi: {humi:.1f}%")
                        topic = f"{alias}/tx/{dev_type}/humidity"
                        client = mqtt.Client(client_id="orangepizero3", clean_session=True)
                        client.username_pw_set(username, password)
                        client.connect(broker, port, 60)
                        client.publish(topic, humi)
                        client.loop_start()
                        client.disconnect()
                if len(decrypted_data) == 4:
                    msg, tmp0, tmp1, value = struct.unpack("<BBBB", decrypted_data)
                    if msg == 10:
                        # humi = 0.1 * (256 * decrypted_data[4] + decrypted_data[3])
                        batt = 1.0 * value
                        print(f"alias: {alias}, batt: {batt:.1f}%")
                        # topic = f"{alias}/tx/{dev_type}/humidity"
                        # client = mqtt.Client(client_id="orangepizero3", clean_session=True)
                        # client.username_pw_set(username, password)
                        # client.connect(broker, port, 60)
                        # client.publish(topic, humi)
                        # client.loop_start()
                        # client.disconnect()
                    if msg == 13:
                        print(f"alias: {alias}, tehu: XYZ")


async def scan_xiaomi_sensors():
    scanner = BleakScanner(detection_callback)
    await scanner.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping scan...")
    finally:
        await scanner.stop()

asyncio.run(scan_xiaomi_sensors())

