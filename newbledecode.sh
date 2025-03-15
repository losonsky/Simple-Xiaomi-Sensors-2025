#!/bin/bash

DEBUG=1;

MQTT_SERVER="192.168.1.10";

MAC_ADDRESS="$1";
DEVICE_TYPE="LYWSD03MMC";
DEVICE_NAME="MI_X";

if [ "$MAC_ADDRESS" == "A4:C1:38:74:38:7A" ]; then
    DEVICE_NAME="MI_0";
fi

if [ "$MAC_ADDRESS" == "A4:C1:38:D4:75:50" ]; then
    DEVICE_NAME="MI_1";
fi

if [ "$MAC_ADDRESS" == "A4:C1:38:C6:11:02" ]; then
    DEVICE_TYPE="MHO-C401";
    DEVICE_NAME="MI_2";
fi

BT_MESSAGE="$3 $4 $5 $6 $7";
if [ $DEBUG -gt 1 ]; then
    echo "BT_MESSAGE = $BT_MESSAGE";
fi

if [ ${#BT_MESSAGE} -lt 10 ]; then
    echo "Error: BT_MESSAGE empty";
    exit 0;
fi

TMPHEX=$(echo $BT_MESSAGE | awk -F ' ' '{print $2$1}' | tr [:lower:] [:upper:]);
HUMHEX=$(echo $BT_MESSAGE | awk -F ' ' '{print   $3}' | tr [:lower:] [:upper:]);
BATHEX=$(echo $BT_MESSAGE | awk -F ' ' '{print $5$4}' | tr [:lower:] [:upper:]);

if [ $DEBUG -gt 1 ]; then
    echo "$TMPHEX";
    echo "$HUMHEX";
    echo "$BATHEX";
fi

TEMPERATURE=$(echo "ibase=16; $TMPHEX" | bc | awk '{ printf "%0.2f", 0.01  * $1 }');
HUMIDITY=$(   echo "ibase=16; $HUMHEX" | bc                                       );
BAT=$(        echo "ibase=16; $BATHEX" | bc | awk '{ printf "%0.2f", 0.001 * $1 }');

if [ $DEBUG -gt 0 ]; then
    echo "$0: $DEVICE_NAME, mac: $MAC_ADDRESS, num: $2, time:        $(date)";
    echo "$0: $DEVICE_NAME, mac: $MAC_ADDRESS, num: $2, temperature: ${TEMPERATURE}°C";
    echo "$0: $DEVICE_NAME, mac: $MAC_ADDRESS, num: $2, humidity:    ${HUMIDITY}%";
    echo "$0: $DEVICE_NAME, mac: $MAC_ADDRESS, num: $2, battery:     ${BAT}V";
fi 

mosquitto_pub -h $MQTT_SERVER -u test01 -P 123 -m $TEMPERATURE -t $DEVICE_NAME/tx/$DEVICE_TYPE/temperature;
mosquitto_pub -h $MQTT_SERVER -u test01 -P 123 -m $HUMIDITY -t $DEVICE_NAME/tx/$DEVICE_TYPE/humidity;
mosquitto_pub -h $MQTT_SERVER -u test01 -P 123 -m $BAT -t $DEVICE_NAME/tx/$DEVICE_TYPE/voltage;

