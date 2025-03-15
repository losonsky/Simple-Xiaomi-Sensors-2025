#!/usr/bin/expect -f

# set device "A4:C1:38:74:38:7A";
# set device "A4:C1:38:D4:75:50";
# set device "A4:C1:38:C6:11:02"; # eInk
set device [lindex $argv 0];

# set characteristic "0x0038";
set characteristic "ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6";

set debug_flag 0;
log_user 0;

if { $argc > 1 } {
        set debug_flag [lindex $argv 1];
        puts "debug_flag = $debug_flag";
        if { $debug_flag > 0 } {
                log_user 1;
        }
}

spawn bluetoothctl;
expect "# ";

# send "power on\r";
# expect "# ";

proc fresh_connect {} {
        global device;

        set timeout 1;
        send "menu scan\r";
        expect "# ";
        
        send "clear\r";
        expect "# ";
        
        send "transport le\r";
        expect "# ";
        
        send "back\r";
        expect "# ";
        
        set timeout 60;
        send "scan on\r";
        expect {
                "Device $device" {};
                timeout {
                        puts "❌ Timeout occurred at scan $device. Exiting...";
                        set timeout 10;
                        send "scan off\r";
                        expect "# ";
                        exit 1;
                }
        }
        
        set timeout 10;
        send "scan off\r";
        expect "Discovery stopped";
        
        set timeout 20;
        send "connect $device\r";
        expect {
                "Connection successful" {};
                "$device type LE Public disconnected" {
                        puts "❌ Device $device type LE Public disconnected. Exiting...";
                        exit 1;
                }
                "LE Public connect failed" {
                        puts "❌ Device $device LE Public connect failed. Exiting...";
                        exit 1;
                }
                "Device $device Connected: no" {
                        puts "❌ Device $device Connected: no. Exiting...";
                        exit 1;
                }
                timeout {
                        puts "❌ Timeout occurred at connection $device. Exiting...";
                        set timeout 10;
                        send "disconnect $device\r";
                        # expect "# Successful disconnected";
                        exit 1;
                }
        }
}

set timeout 10;
send "connect $device\r";
expect {
        "Connection successful" {};
        "Device $device not available" {
                fresh_connect        
        }
        timeout {
                fresh_connect        
        }
}

set timeout 30;
expect "Device $device ServicesResolved: yes";

set timeout 1;
send "menu gatt\r";
expect "# ";

set timeout 10;
send "select-attribute $characteristic\r";
expect "char003\[25\]]*# ";

# for {set i 0} {$i < 12} {incr i} {
for {set i 0} {$i < 1} {incr i} {
        set timeout 10;
        send "notify on\r";
        expect "Notify started";
        set timeout 60;
        expect {
        -re {^.*\[.*char003[25]\].*\#\s+([0-9a-fA-F\s]+)} {
                set btmessage $expect_out(1,string);
                # puts "🔔 $device $i $btmessage";
                set output [exec /usr/local/bin/newbledecode.sh $device $i $btmessage];
                puts "$output";
                set timeout 10;
                send "notify off\r";
                expect "Notify stopped";
            }
                timeout {
                        puts "❌ Timeout occurred at listen $device. Exiting...";
                        set timeout 10;
                        send "back\r";
                        expect "# ";
                        set timeout 10;
                        send "disconnect $device\r";
                        expect "Successful disconnected";
                        exit 1;
                }
        }
        # puts "sleeping";
        # sleep 298;
}

set timeout 10;
send "back\r";
expect "# ";
set timeout 10;
send "disconnect $device\r";
expect {
        "Successful disconnected" {};
        timeout {
                puts "❌ Timeout occurred at disconnect after listen $device. Exiting...";
                set timeout 10;
                send "disconnect $device\r";
                expect "Successful disconnected";
                exit 1;
        }
}

