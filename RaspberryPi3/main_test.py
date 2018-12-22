# sf, bwを変えながら移動端末から受信する
#
# LoRaモジュールから1行読み、rssi、panid、srcid、msgに分解
# さらにmsgが'TemHumPre=(Tem,Hum,Pre)'という形式なので、'(Tmp,Hum,Pre)'部分をTupleに変換
# rssiを保存し、Ambientに送信
#
#

import lora
import ast
import time
import struct
import sys
import ambient

# (bw, sf, timeout)
bw = 3
sf = 12
time_out = 5

channelId1 = チャネルID1
writeKey1 = 'ライトキー1'

am1 = ambient.Ambient(channelId1, writeKey1)

lr = lora.LoRa()

def printable(l):
    x = struct.unpack(str(len(l)) + 'b', l)
    y = ''
    for i in range(len(x)):
        if x[i] >= 0:
            y = y + chr(x[i])
    return y

def sendcmd(cmd):
    # print(cmd)
    lr.write(cmd)
    t = time.time()
    while (True):
        if (time.time() - t) > 5:
            print('panic: %s' % cmd)
            exit()
        line = lr.readline()
        if 'OK' in printable(line):
            # print(line)
            return True
        elif 'NG' in printable(line):
            # print(line)
            return False

def setMode(bw, sf):
    lr.write('config\r\n')
    lr.s.flush()
    time.sleep(0.2)
    lr.reset()
    time.sleep(1.5)

    line = lr.readline()
    while not ('Mode' in printable(line)):
        line = lr.readline()
        if len(line) > 0:
            print(line)

    sendcmd('2\r\n')
    sendcmd('node 1\r\n') //親機に設定
    sendcmd('ownid 0000\r\n') //自ノードアドレスを0に
    sendcmd('rssi 1\r\n')
    sendcmd('rcvid 1\r\n')
    sendcmd('bw %d\r\n' % bw)
    sendcmd('sf %d\r\n' % sf)
    sendcmd('q 2\r\n')
    sendcmd('w\r\n')

    lr.reset()
    print('LoRa module set to new mode')
    time.sleep(1)
    sys.stdout.flush()


print('setMode(bw: %d, sf: %d)' % (bw, sf))
setMode(bw, sf)

while (True):
    rssi = None
    Test = ()

    t = None #or time_out
    timeout = False
    start = time.time()
    while (True):
        while (True):
            line = lr.readline(t)
            # print(line)
            # sys.stdout.flush()
            if len(line) == 0: # TIMEOUT
                timeout = True
                break
            if len(line) >= 14: # 'rssi(4bytes),pan id(4bytes),src id(4bytes),\r\n'で14バイト
                break
        if timeout == True:
            rssi = None
            print('TIMEOUT')
            break;
        data = lr.parse(line)  # 'rssi(4bytes),pan id(4bytes),src id(4bytes),TemHumPre=(12バイト,12バイト,12バイト)\r\n', ペイロード34バイト
        print(data)
        if 'res=' in data[3]:
            res = ast.literal_eval(data[3].split('=')[1])
            rssi = data[0]
            Test = res
            s = time_out - (time.time() - start)
            # print('sleep: ' + str(s))
            if s > 0:
                time.sleep(s)
            break

    print(rssi)
    print(Test)
    sys.stdout.flush()

    am1.send({'d1': rssi, 'd2': Test[0], 'd3': Test1], 'd4': Test[2]})
