#!/usr/bin/env python
import matplotlib
matplotlib.interactive(True)
matplotlib.use('WXAgg')

import os
import sys, time
import serial
import serial.tools.list_ports
from pprint import pprint
import wx
import wx.lib.scrolledpanel
import wx.lib.agw.knobctrl as kc
import wx.lib.agw.peakmeter as pm
import threading
import configparser
import pyaudio
import sounddevice as sd
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np

default_configs = {'win': {'winfo_width': '1100','winfo_height': '586','winfo_x': '1222','winfo_y': '254'},
                   'rig': {'serialdevice': 'COM8','baudrate': '38400','mic': 'a', 'speaker': 'b'},
                   'com0com': {'serialdevice': 'COM4','baudrate': '38400'}
                  }

path_current_dir = os.path.dirname(sys.argv[0])
config_file = os.path.join(path_current_dir, 'ft991cat.ini')
icon_file = os.path.join(path_current_dir, 'ft991cat.ico')

#config_file = os.path.join(os.path.dirname(__file__), 'ft991cat.ini')

baudrate = ['4800','9600','19200','38400']
mic_lists = []
speaker_lists = []
combo_mic_lists = []
combo_speaker_lists = []
N =2048            # FFT用のサンプル数
fs = 44100            # 音声データのサンプリング周波数

port = b''

bandlists = [
 ['00','  1.8MHz(160m)','  1.8MHz','160m',1.8,1.9125]
,['01','  3.5MHz(80m)' ,'  3.5MHz','80m',3.5,3.805]
,['02','  5MHz(60m)'   ,'  5MHz','60m',5.18,5.24]
,['03','  7MHz(40m)'   ,'  7MHz','40m',7.0,7.2]
,['04',' 10MHz(30m)'   ,' 10MHz','30m',10.1,10.15]
,['05',' 14MHz(20m)'   ,' 14MHz','20m',14.0,14.35]
,['06',' 18MHz(17m)'   ,' 18MHz','17m',18.068,18.168]
,['07',' 21MHz(15m)'   ,' 21MHz','15m',21.0,21.45]
,['08',' 24.5MHz(12m)' ,' 24.5MHz','12m',24.89,24.99]
,['09',' 28MHz(10m)'   ,' 28MHz','10m',28.0,29.7]
,['10',' 50MHz(6m)'    ,' 50MHz','6m',50.0,54.0]
,['15','144MHz(2m)'    ,'144MHz','2m',144.0,146.0]
,['16','430MHz(70m)'   ,'430MHz','70m',430.0,440.0]
,['11','GEN()'         ,'GEN','',0.0,0.0]
,['12','MW()'          ,'MW','',0.0,0.0]
,['14','AIR()'         ,'AIR','',0.0,0.0]
,['13','----()'        ,'----','',0.0,0.0]
]

combo_bandlists = [
 '  1.8MHz(160m)'
,'  3.5MHz(80m)' 
,'  5MHz(60m)'   
,'  7MHz(40m)'   
,' 10MHz(30m)'   
,' 14MHz(20m)'   
,' 18MHz(17m)'   
,' 21MHz(15m)'   
,' 24.5MHz(12m)' 
,' 28MHz(10m)'   
,' 50MHz(6m)'    
,'144MHz(2m)'    
,'430MHz(70m)'   
,'GEN()'         
,'MW()'          
,'AIR()'         
,'----()'        
]

modelists = [
 ['01','LSB',          'SSB']
,['02','USB',          'SSB']
,['03','CW-U',         'CW']
,['04','FM',           'FM']
,['05','AM',           'AM']
,['06','RTTY-LSB',     'DATA']
,['07','CW-R',         'CW']
,['08','DATA-LSB',     'DATA']
,['09','RTTY-USB',     'DATA']
,['0A','DATA-FM',      'DATA']
,['0B','FM-N',         'FM']
,['0C','DATA-USB',     'DATA']
,['0D','AM-N',         'AM']
,['0E','C4FM',         'FM']
]

combo_modelists = ['LSB','USB','CW-U','FM','AM','RTTY-LSB','CW-R','DATA-LSB','RTTY-USB','DATA-FM','FM-N','DATA-USB','AM-N','C4FM']

bandwidthlists = [
 ['99','    Off','    Off','   Off','    Off','   Off','   Off','Off']
,['00','1500 Hz','2400 Hz','500 Hz','2400 Hz','300 Hz',' 500 Hz','Off']
,['01',' 200 Hz','       ',' 50 Hz','       ',' 50 Hz','   ','Off']
,['02',' 400 Hz','       ','100 Hz','       ','100 Hz','   ','Off']
,['03',' 600 Hz','       ','150 Hz','       ','150 Hz','   ','Off']
,['04',' 850 Hz','       ','200 Hz','       ','200 Hz','   ','Off']
,['05','1100 Hz','       ','250 Hz','       ','250 Hz','   ','Off']
,['06','1350 Hz','       ','300 Hz','       ','300 Hz','   ','Off']
,['07','1500 Hz','       ','350 Hz','       ','350 Hz','   ','Off']
,['08','1650 Hz','       ','400 Hz','       ','400 Hz','   ','Off']
,['09','1800 Hz','1800 Hz','450 Hz','       ','450 Hz','   ','Off']
,['10','       ','1950 Hz','500 Hz',' 500 Hz','500 Hz',' 500 Hz','Off']
,['11','       ','2100 Hz','      ',' 800 Hz','      ',' 800 Hz','Off']
,['12','       ','2200 Hz','      ','1200 Hz','      ','1200 Hz','Off']
,['13','       ','2300 Hz','      ','1400 Hz','      ','1400 Hz','Off']
,['14','       ','2400 Hz','      ','1700 Hz','      ','1700 Hz','Off']
,['15','       ','2500 Hz','      ','2000 Hz','      ','2000 Hz','Off']
,['16','       ','2600 Hz','      ','2400 Hz','      ','2400 Hz','Off']
,['17','       ','2700 Hz','      ','3000 Hz','      ','3000 Hz','Off']
,['18','       ','2800 Hz','      ','       ','      ','   ','Off']
,['19','       ','2900 Hz','      ','       ','      ','   ','Off']
,['20','       ','3000 Hz','      ','       ','      ','   ','Off']
,['21','       ','3200 Hz','      ','       ','      ','   ','Off']
]

bandwidth2lists = [
 [' 200 Hz',' 400 Hz',' 600 Hz',' 850 Hz','1100 Hz','1350 Hz','1500 Hz','1650 Hz','1800 Hz']
,['1800 Hz','1950 Hz','2100 Hz','2200 Hz','2300 Hz','2400 Hz','2500 Hz','2600 Hz','2700 Hz','2800 Hz','2900 Hz','3000 Hz','3200 Hz']
,[' 50 Hz','100 Hz','150 Hz','200 Hz','250 Hz','300 Hz','350 Hz','400 Hz','450 Hz','500 Hz']
,[' 500 Hz',' 800 Hz','1200 Hz','1400 Hz','1700 Hz','2000 Hz','2400 Hz','3000 Hz']
,[' 50 Hz','100 Hz','150 Hz','200 Hz','250 Hz','300 Hz','350 Hz','400 Hz','450 Hz','500 Hz']
,[' 500 Hz',' 800 Hz','1200 Hz','1400 Hz','1700 Hz','2000 Hz','2400 Hz','3000 Hz']
,['Off']
]

catcmds = [
 ['AB','VFO-A TO VFO-B',' [VFO A ⇒ VFO B] 動作','',1,0,0,0]
,['AC','ANTENNA TUNER CONTROL','アンテナチューナー動作開始・停止','000: チューナー“OFF”001: チューナー“ON”002: チューニングスタート / ストップ',1,1,1,1]
,['AG','AF GAIN','AF GAIN の設定と読み出し','',1,1,1,1]
,['AI','AUTO INFORMATION','オートインフォメーションの設定と読み出し','0: オートインフォメーション“OFF”1: オートインフォメーション“ON”',1,1,1,0]
,['AM','VFO-A TO MEMORY CHANNEL','[A ＞ M] キー動作','',1,0,0,0]
,['BA','VFO-B TO VFO-A',' [VFO B ⇒ VFO A] 動作','',1,0,0,0]
,['BC','AUTO NOTCH',' オートノッチの設定と読み出し','00: オートノッチ“OFF”01: オートノッチ“ON”',1,1,1,1]
,['BD','BAND DOWN','バンドダウンスイッチの動作を行う','',1,0,0,0]
,['BI','BREAK-IN','ブレークインの設定と読み出し','0: ブレークイン“OFF”1: ブレークイン“ON”',1,1,1,1]
,['BP','MANUAL NOTCH','マニュアルノッチの設定と読み出し','00000: マニュアルノッチ“OFF” 00001: マニュアルノッチ“ON” 01001-01320 (NOTCH 周波数設定 : x 10 Hz )',1,1,1,1]
,['BS','BAND SELECT','[BAND] キー動作','00:1.8MHz 01:3.5MHz 02:5MHz 03:7MHz 04:10MHz 05:14MHz 06:18MHz 07:21MHz 08:24.5MHz 09:28MHz 10:50MHz 11:GEN 12:MW 13:- 14:AIR 15:144MHz 16:430MHz',1,0,0,0]
,['BU','BAND UP','バンドアップスイッチの動作を行う','',1,0,0,0]
,['BY','BUSY','BUSY 状態の読み出し','00: RX BUSY“OFF”10: RX BUSY“ON”',0,1,1,1]
,['CH','CHANNEL UP/DOWN','メモリーチャンネルのアップ・ダウン','0: メモリーチャンネル“UP” 1: メモリーチャンネル“DOWN”',1,0,0,0]
,['CN','CTCSS/DCS NUMBER','CTCSS 周波数 /DCS コード設定と読み出し','00: CTCSS 000-049: トーン周波数番号 01: DCS 000-103: DCS コード番号',1,1,1,1]
,['CO','CONTOUR','CONTOUR の状態の設定と読み出し','000000:CONTOUR“OFF” 000001:CONTOUR“ON” 010010-013200:CONTOUR周波数:10～3200Hz 020000:APF“OFF” 020001:APF“ON”030000-030050:APF周波数:-250～250Hz',1,1,1,1]
,['CS','CW SPOT','SPOT の設定と読み出し','0: OFF 1: ON',1,1,1,1]
,['CT','CTCSS','CTCSS の状態の設定と読み出し','00: CTCSS “OFF” 01: CTCSS ENC/DEC 02: CTCSS ENC 03: DCS ENC/DEC 04: DCS ENC',1,1,1,1]
,['DA','DIMMER',' ディマーの設定と読み出し','00: （固定値） 01-02: LED インジケーターの明るさ調整 00-15: TFT ディスプレイの明るさ調整',1,1,1,0]
,['DN','DOWN','マイクの DOWN キー動作を行う','',1,0,0,0]
,['DT','DATE AND TIME','時刻の設定と読み出し','0yyyymmdd:日付 1hhmmss:時刻（UTC）2: 補正（TIME ZONE）',1,1,1,0]
,['ED','ENCODER DOWN','エンコーダ DOWN','0:MAINエンコーダー 1:SUBエンコーダー 8:MULTIエンコーダー 01-99:周波数ステップ 01:（固定値）ステップ（周波数以外）',1,0,0,0]
,['EK','ENT KEY','[ENT] キー動作','',1,0,0,0]
,['EU','ENCODER UP',' エンコーダ U P','0:MAINエンコーダー 1:SUBエンコーダー 8:MULTIエンコーダー 01-99:周波数ステップ 01:（固定値） ステップ（周波数以外）',1,0,0,0]
,['EX','MENU','MENU の設定と読み出し','001-153 ( メニュー番号 ) 設定値',1,1,1,1]
,['FA','FREQUENCY VFO-A','VFO-A の周波数の設定と読み出し','000030000-470000000 (Hz) ',1,1,1,1]
,['FB','FREQUENCY VFO-B','VFO-B の周波数の設定と読み出し','000030000-470000000 (Hz) ',1,1,1,1]
,['FS','FAST STEP','FAST ステップの設定と読み出し','0:VFO-A FASTキー“OFF” 1:VFO-A FASTキー“ON”',1,1,1,1]
,['FT','FUNCTION TX','送信 VFO の設定と読み出し','2:VFO-A Band Transmitter: TX 3:VFO-B Band Transmitter: TX 0:VFO-A Band Transmitter: TX 1:VFO-B Band Transmitter: TX',1,1,1,1]
,['GT','AGC FUNCTION','AGC の時定数の設定と読み出し','0:（固定値） 0: AGC “OFF” 1: AGC “FAST”2: AGC “MID”3: AGC “SLOW” 4: AGC “AUTO-FAST”5: AGC “AUTO-MID” 6: AGC “AUTO-SLOW”',1,1,1,1]
,['ID','IDENTIFICATION',' 無線機 ID の読み出し','0570:FT-991',0,1,1,0]
,['IF','INFORMATION','VFO-A の状態を読み出す','001-117(メモリーチャンネル) P2 VFO-A 周波数 (Hz) P3 クラリファイアオフセット+プラスシフトマイナスシフトクラリファイア周波数:0000-9999(Hz) P4 0:RXクラリファイア“OFF” 1:RXクラリファイア“ON” P5 0:TXクラリファイア“OFF”1:TXクラリファイア“ON” P6 MODE 1:LSB 2:USB 3:CW 4:FM 5:AM 6:RTTY-LSB 7:CW-R 8:DATA-LSB 9:RTTY-USB A:DATA-FM B:FM-N C:DATA-USB D:AM-N E:C4FM P7 0:VFO 1:メモリー 2:メモリーチューン 3:クイックメモリーバンク(QMB) 4:QMB-MT 5:PMS 6:HOME P8 0:CTCSS“OFF”1:CTCSS ENC/DEC 2:CTCSS ENC 3:DCS ENC/DEC 4:DCS ENC P9 00:（固定値） P10 0:シンプレックス 1:プラスシフト 2:マイナスシフト ',0,1,1,1]
,['IS','IF-SHIFT','IF-SHIFT の設定と読み出し','0 --1200 ~ +1200 Hz (20 Hz ステップ ) ',1,1,1,1]
,['KM','KEYER MEMORY','キーヤーメモリーの設定と読み出し','1-5:キーヤーメモリーチャンネル番号 メッセージテキスト ',1,1,1,0]
,['KP','KEY PITCH','キーイングピッチの設定と読み出し','00: 300 Hz ~ 75: 1050 Hz (10 Hz ステップ )',1,1,1,1]
,['KR','KEYER','キーヤーの設定と読み出し','0:キーヤー“OFF”1:キーヤー“ON”',1,1,1,1]
,['KS','KEY SPEED','キーイングスピードの設定と読み出し','004-060 (WPM)',1,1,1,1]
,['KY','CW KEYING','メッセージキーヤーやキーヤーメモリーの再生','1:KeyerMemory“1”再生 6:MessageKeyer“1”再生 2:KeyerMemory“2”再生 7:MessageKeyer“2”再生 3:KeyerMemory“3”再生 8:MessageKeyer“3”再生 4:KeyerMemory“4”再生 9:MessageKeyer“4”再生 5:KeyerMemory“5”再生 A:MessageKeyer“5”再生',1,0,0,0]
,['LK','LOCK','LOCK 状態の設定と読み出し','0:VFO-Aダイアルロック“OFF” 1:VFO-Aダイアルロック“ON”',1,1,1,1]
,['LM','LOAD MESSEGE','音声録音の録音','00:DVS( 録音 停止 ) 01:DVS(CH“1”録音 開始／停止) 2:DVS(CH“2”録音 開始／停止) 3:DVS(CH“3”録音 開始／停止) 4:DVS(CH“4”録音 開始／停止) 5:DVS(CH“5”録音 開始／停止)',1,1,1,0]
,['MA','MEMORY CHANNEL TO VFO-A','[MEMORY ⇒ VFO A] 動作','',1,0,0,0]
,['MC','MEMORY CHANNEL',' メモリーチャンネルの設定と読み出し','001-099:通常メモリーチャンネル 100:P-1L 101:P-1U 116: P-9L 117: P-9U',1,1,1,0]
,['MD','MODE','モードの設定と読み出し','P1 0: MAIN RX P2 MODE 1: LSB 2: USB 3: CW-U 4: FM 5: AM 6: RTTY-LSB  7: CW-R 8: DATA-LSB 9: RTTY-USB A: DATA-FM   B: FM-N C: DATA-USB D: AM-N E: C4FM',1,1,1,1]
,['MG','MIC GAIN','マイクゲインの設定と読み出し','000 ~ 100',1,1,1,1]
,['ML','MONITOR LEVEL','モニターレベルの設定と読み出し','P1 0: モニター “ON/OFF” 1: モニターレベル P2 P1=0 の時  000: モニター “OFF”  001: モニター “ON” P1=1 の時  000 - 100',1,1,1,1]
,['MR','MEMORY READ','メモリーチャンネルの読み出し','P0 001-117 ( 呼び出したいメモリーチャンネル )P1 001-117 ( 現在のメモリーモードに設定されているメモリーチャンネル ) P2 周波数 (Hz) ※ P3 クラリファイアオフセット +: プラスシフト --: マイナスシフト クラリファイア周波数 : 0000 - 9999 (Hz) P4 0: RX クラリファイア “OFF” 1: RX クラリファイア “ON” P5 0: TX クラリファイア “OFF” 1: TX クラリファイア “ON” P6 MODE 1: LSB 2: USB 3: CW 4: FM 5: AM 6: RTTY-LSB  7: CW-R 8: DATA-LSB 9: RTTY-USB A: DATA-FM  B: FM-N C: DATA-USB D: AM-N E: C4FM P7 0: VFO 1: メモリー P8 0: CTCSS “OFF” 1: CTCSS ENC/DEC 2: CTCSS ENC 3: DCS ENC/DEC 4: DCS ENC P9 00: （固定値） P10 0: シンプレックス 1: プラスシフト 2: マイナスシフト ',0,1,1,0]
,['MS','METER SW','METER SW の設定と読み出し',' 0: COMP1: ALC 2: PO 3: SWR 4: ID 5: VDD',1,1,1,1]
,['MT','MEMORY WRITE/TAG','メモリーチャンネルとメモリータグの設定と読み出し','P1 メモリーチャンネル (001 ~ 117) P2 周波数 (Hz)P3 クラリファイアオフセット +: プラスシフト--: マイナスシフト クラリファイア周波数 : 0000 - 9999 (Hz) P4 0: RX クラリファイア “OFF” 1: RX クラリファイア “ON” P5 0: TX クラリファイア “OFF” 1: TX クラリファイア “ON” P6 MODE 1: LSB 2: USB 3: CW 4: FM  5: AM 6: RTTY-LSB 7: CW-R 8: DATA-LSB  9: RTTY-USB A: DATA-FM B: FM-NC: DATA-USB  D: AM-N E: C4FM P7 Set 時 0: （固定値） / Read 時 0: VFO 1: Memory P8 0: CTCSS “OFF” 1: CTCSS ENC/DEC 2: CTCSS ENC 3: DCS ENC/DEC 4: DCS ENC P9 00:（固定値） P10 0: シンプレックス1: プラスシフト2: マイナスシフト P11 0:（固定値） P12: メモリータグ (ASII コード ):（最大 12 文字',1,1,1,0]
,['MW','MEMORY WRITE','メモリーチャンネルの書き込み','P1 メモリーチャンネル (001 ~ 117) P2 周波数 (Hz)P3 クラリファイアオフセット +: プラスシフト --: マイナスシフト クラリファイア周波数 : 0000 - 9999 (Hz) P4 0: RX クラリファイア “OFF” 1: RX クラリファイア “ON” P5 0: TX クラリファイア “OFF” 1: TX クラリファイア “ON” P6 MODE 1: LSB 2: USB 3: CW 4: FM 5: AM 6: RTTY-LSB  7: CW-R 8: DATA-LSB 9: RTTY-USB A: DATA-FM  B: FM-N C: DATA-USB D: AM-N E: C4FM P7 0:（固定値） P8 0: CTCSS “OFF” 1: CTCSS ENC/DEC 2: CTCSS ENC 3: DCS ENC/DEC 4: DCS ENC P9: 00:（固定値） P10 0: シンプレックス 1: プラスシフト 2: マイナスシフト',1,0,0,0]
,['MX','MOX SET','MOX の設定と読み出し','0: MOX “OFF” 1: MOX “ON”',1,1,1,1]
,['NA','NARROW',' ナローの設定と読み出し','P1 0:（固定値） P2 0: OFF 1: ON',1,1,1,1]
,['NB','NOISE BLANKER','ノイズブランカーの設定と読み出し','P1 0:（固定値） P2 0: ノイズブランカー “OFF” 1: ノイズブランカー “ON”',1,1,1,1]
,['NL','NOISE BLANKER LEVEL','ノイズブランカーレベルの設定と読み出し','P1 0:（固定値） P2 000 ~ 010',1,1,1,1]
,['NR','NOISE REDUCTION','ノイズリダクションの設定と読み出し','P1 0:（固定値） P2 0: ノイズリダクション “OFF” 1: ノイズリダクション “ON”',1,1,1,1]
,['OI','OPPOSITE BAND INFORMATION','VFO-B の状態を読み出す','P1 001-117 ( メモリーチャンネル ) P2 VFO-B 周波数 (Hz)※P3 クラリファイアオフセット +: プラスシフト --: マイナスシフト クラリファイア周波数 : 0000 - 9999 (Hz) P4 0: RX クラリファイア “OFF” 1: RX クラリファイア “ON” P5 0: TX クラリファイア “OFF” 1: TX クラリファイア “ON” P6 MODE 1: LSB 2: USB 3: CW 4: FM 5: AM 6: RTTY-LSB  7: CW-R 8: DATA-LSB 9: RTTY-USB A: DATA-FM  B: FM-N C: DATA-USB D: AM-N E: C4FM P7 0: VFO 1: メモリー P8 0: CTCSS “OFF” 1: CTCSS ENC/DEC 2: CTCSS ENC 3: DCS ENC/DEC 4: DCS ENC P9 00: （固定値） P10 0: シンプレックス 1: プラスシフト 2: マイナスシフト',0,1,1,1]
,['OS','OFFSET (Repeater Shift)','レピーターシフトの設定と読み出し','P1 0:（固定値）P2 0: シンプレックス 1: プラスシフト 2: マイナスシフト',1,1,1,1]
,['PA','PRE-AMP (IPO)','IPO の設定と読み出し','P1 0: （固定値） P2 0: IPO 1: AMP 1 2: AMP 2',1,1,1,1]
,['PB','PLAY BACK','音声録音の再生','P1 0:（固定値） P2 0: DVS ( 再生停止 )  1: DVS (CH “1” 再生 )  2: DVS (CH “2” 再生 )  3: DVS (CH “3” 再生 )  4: DVS (CH “4” 再生 )  5: DVS (CH “5” 再生 )',1,1,1,0]
,['PC','POWER CONTROL','送信出力の設定と読み出し','005 ~ 100',1,1,1,1]
,['PL','SPEECH PROCESSOR LEVEL',' コンプレッションレベルの設定と読み出し','000 ~ 100',1,1,1,1]
,['PR','SPEECH PROCESSOR','スピーチプロセッサーの ON/OFF 設定と読み出し','P1 0: スピーチプロッセッサー 1: パラメトリックマイクイコライザー P2 1: “OFF” 2: “ON',1,1,1,1]
,['PS','POWER SWITH','電源 ON/OFF 設定と読み出し','0: 電源 “OFF” 1: 電源 “ON” ',1,1,1,0]
,['QI','QMB STORE','STO 動作','',1,0,0,0]
,['QR','QMB RECALL','RCL 動作','',1,0,0,0]
,['QS','QUICK SPLIT','クイック SPLIT の設定','',1,0,0,0]
,['RA','RF ATTENUATOR',' アッテネータの設定と読み出し','P1 0:（固定値） P2 0: OFF 1: ON',1,1,1,1]
,['RC','CLAR CLEAR','クラリファイアのクリア','',1,0,0,0]
,['RD','CLAR DOWN',' クラリファイア DOWN','0000 ~ 9999 (Hz)',1,0,0,0]
,['RG','RF GAIN','RF ゲインの設定と読み出し','P1 0:（固定値） P2 000 ~ 255',1,1,1,1]
,['RI','RADIO INFORMATION',' 無線機の情報読み出し','P1 0: Hi-SWR P2 0: OFF 3: REC 1: ON 4: PLAY 5: VFO-A TX 6: VFO-B TX 7: VFO-A RX A: TX LED',0,1,1,1]
,['RL','NOISE REDUCTION LEVEL',' ノイズリダクションレベルの設定と読み出し','P1 0:（固定値） P2 01 - 15',1,1,1,1]
,['RM','READ METER','METER の読み出し','P1 0: 選択している METER による 5: PO 1: S 6: SWR 2: 選択している METER による 7: ID （PO / COMP /ALC /SWR /ID /VDD） 8: VDD 3: COMP  4: ALC  P2 0 - 255',0,1,1,1]
,['RS','RADIO STATUS','無線機の状態読み出し',' 0: 通常状態 1: メニューモード中',0,1,1,0]
,['RT','CLAR','クラリファイアの ON/OFF 設定と読み出し',' 0: RX クライファイア “OFF” 1: RX クライファイア “ON”',1,1,1,1]
,['RU','CLAR UP','クラリファイア UP','0000 ~ 9999 (Hz)',1,0,0,0]
,['SC','SCAN','スキャンの設定と読み出し','0: スキャン “OFF” （スキャンを停止） 1: スキャン “ON” (UP 方向にスキャンを開始 ) 2: スキャン “ON” (DOWN 方向にスキャンを開始 )',1,1,1,1]
,['SD','SEMI BREAK-IN DELAY TIME','セミブレークインのディレータイムの設定と読み出し','0030 ~ 3000 msec',1,1,1,1]
,['SH','WIDTH',' WIDTH の設定と読み出し','P1 0:（固定値） P2 00 ( 表４参照 ',1,1,1,1]
,['SM','S METER','S メーター値の読み出し','P1 0:（固定値） P2 000 ~ 255',0,1,1,0]
,['SQ','SQUELCH LEVEL',' スケルチレベルの設定と読み出し','P1 0:（固定値） P2 000 ~ 100',1,1,1,1]
,['SV','SWAP VFO','[A/B] キー動作','',1,0,0,0]
,['TS','TXW','[TXW] キー動作',' 0: TXW “OFF” 1: TXW “ON”',1,1,1,1]
,['TX','TX SET','送信状態の設定と読み出し','0: RADIO TX “OFF” CAT TX “OFF” 1: RADIO TX “OFF” CAT TX “ON” 2: RADIO TX “ON” CAT TX “OFF” ( 応答 )',1,1,1,1]
,['UL','UNLOCK','PLL のロック状態の読み出し','0: PLL “Lock” 1: PLL “Unlock”',0,1,1,1]
,['UP','UP',' マイクの UP キー動作を行う','',1,0,0,0]
,['VD','VOX DELAY TIME','VOX ディレータイムの設定と読み出し','0030 ~ 3000 msec (10 msec ステップ ) メニューモードの 142 VOX SELECT が、 “MIC”の時 : VOX DELAY TIME “DATA”の時 : DATA DELAY TIME ',1,1,1,1]
,['VG','VOX GAIN','VOX GAIN の設定と読み出し','000 ~ 100',1,1,1,1]
,['VM','[V/M] KEY FUNCTION','[V/M] キー動作','',1,0,0,0]
,['VX','VOX','VOX の設定と読み出し','0: VOX “OFF” 1: VOX “ON',1,1,1,1]
,['XT','TX CLAR','送信クラリファイアの設定と読み出し','0: TX クラリファイア “OFF” 1: TX クラリファイア “ON”',1,1,1,1]
,['ZI','ZERO IN','CW AUTO ZERO IN 動作','',1,0,0,0]
]

ft8_cw_rtty_setting_cmd = [
 ['EX062','1','OTHERS','DATA MODE']
,['EX064','+1500','1500 Hz','OTHER DISP(SSB)']
,['EX065','+1500','1500 Hz','OTHER SHIFT(SSB)']
,['EX066','01','100 Hz','DATA LCUT FREQ']
,['EX068','47','3000 Hz','DATA HCUT FREQ'] # 01: 700 Hz ~ 67: 4000 Hz (50 Hz ステップ ) 
,['EX070','1','REAR','DATA IN SELECT']
,['EX071','1','RTS','DATA PTT SELECT']
,['EX072','2','USB','DATA PORT SELECT']
,['EX073','050','50','DATA OUT LEVEL']
,['EX059','0','DIRECT FREQ','CW FREQ DISPLAY']
,['EX060','3','DTR','PC KEYING']
,['EX096','1','DTR','RTTY SHIF PORT']
]

rtty_setting_cmd = [
 ['MD','06','RTTY-LSB','OPERATING MODE']
#,['PC','050','50W','POWER CONTROL']
,['PC','020','20W','POWER CONTROL']
,['EX097','1','NORNAL','RTTY POLARITY-RX']
,['EX098','1','NORNAL','RTTY POLARITY-RY']
,['EX100','1','170Hz','RTTY SHIFT FREQ']
,['EX101','2','2125Hz','RTTY MARK FREQ']
,['EX108','2','DTR','SSB PTT SELECT']
,['EX109','1','USB','SSB PORT SELECT']
]

ft8_setting_cmd = [
 ['MD','0C','DATA-USB','OPERATING MODE']
,['PC','020','20W','POWER CONTROL']
,['GT','00','OFF','AGC FUNCTION']
,['NA','00','OFF','NARROW']
,['PA','01','AMP1','PRE-AMP (IPO)']
,['SH','017','3000Hz','WIDTH']
,['EX102','01','100Hz','SSB LCUT FREQ']
,['EX104','51','3200Hz','SSB HCUT FREQ']
,['EX106','1','REAR ','SSB MIC SELECT']
,['EX109','1','USB','SSB PORT SELECT']
,['EX110','0','50-3000Hz','SSB TX BPF']
]

cw_setting_cmd = [
 ['MD','07','CW-R','OPERATING MODE']
#,['PC','050','50W','POWER CONTROL']
,['PC','020','20W','POWER CONTROL']
,['KR','1','ON','KEYER']
,['GT','04','AGC AUTO','AGC FUNCTION']
,['NA','01','ON','NARROW']
,['PA','01','AMP1','PRE-AMP (IPO)']
,['RA','00','OFF','RF ATTENUATOR']
,['SH','000','500Hz','WIDTH']
,['KP','30','600Hz','KEY PITC']
,['SD','0300','300ms','CW BREAK-IN DELAY TIME']
,['EX012','2','ELEKEY-A','KEYER TYPE']
,['EX056','0','SEMI BREAK-IN','CW BK-IN TYPE']
]

def comlist(devices,descriptions):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        devices.append(p.device)
        descriptions.append(p.description)

def comopen(device,baudrate):
    try:
        port = serial.Serial(port=device, baudrate=baudrate, write_timeout=0.05)
    except:
        print("Error: %s can't open." % device)
        return -1
    return port

def saveconfig(event):
    global note
    global devices
    global descriptions
    global mic_lists
    global speaker_lists
    global combo_mic_lists
    global combo_speaker_lists

    pos = frame.GetScreenPosition()
    size = frame.GetSize()

    config = configparser.ConfigParser()
    config.read_dict(default_configs)
    config.read(config_file)
    config['win'] = {}
    config['win']['winfo_width'] = str(size[0])
    config['win']['winfo_height'] = str(size[1])
    config['win']['winfo_x'] = str(pos[0])
    config['win']['winfo_y'] = str(pos[1])

    selected_value = note.com_port_setting_tab.frm1.combobox1r1.GetValue()
    config['rig'] = {}
    config['rig']['serialdevice'] = devices[descriptions.index(selected_value)]
    config['rig']['baudrate'] = note.com_port_setting_tab.frm1.combobox1r2.GetValue()
    config['rig']['mic'] = note.com_port_setting_tab.frm1.combobox2r1.GetValue()
    config['rig']['speaker'] = note.com_port_setting_tab.frm1.combobox2r2.GetValue()

    selected_value = note.com_port_setting_tab.frm1.combobox1c1.GetValue()
    config['com0com'] = {}
    config['com0com']['serialdevice'] = devices[descriptions.index(selected_value)]

    with open(config_file, 'w') as f:
        config.write(f)
    
    wx.MessageBox('保存しました', 'Setting')

def rig_raw2val(rawval,cal_table):
    fval = 0.0
#    print(rawval)
    for i in range(len(cal_table)):
        if rawval < cal_table[i][0]:
            break
    if i == 0:
        fval = cal_table[i][1]
    elif rawval == cal_table[i-1][0]:
        fval = cal_table[i-1][1]
    else:
        interpolation = ((cal_table[i][0] - rawval)* (cal_table[i][1] - cal_table[i-1][1]))/(cal_table[i][0] - cal_table[i-1][0])
        fval = cal_table[i][1] - interpolation
#    if i <= 10:
#        return i,i
#    return i,((i-10)+1)*10
#    print(fval)
    return i,10.0+(fval/6.0)


#    fval = 0.0
#    for i in range(len(cal_table)):
#        if rawval < cal_table[i][0]:
#            break
#    if rawval == cal_table[i-1][0]:
#        return cal_table[i-1][1]
#    if i == 0:
#        fval = cal_table[i][1]
#    elif i == len(cal_table):
#        fval = cal_table[i-1][1]
#    else:
#        interpolation = ((cal_table[i][0] - rawval)* (cal_table[i][1] - cal_table[i-1][1]))/(cal_table[i][0] - cal_table[i-1][0])
#        fval = cal_table[i][1] - interpolation
#    return fval

def rig_raw2val_float(rawval,cal_table):
    fval = 0.0
    for i in range(len(cal_table)):
        if rawval < cal_table[i][0]:
            break
    if i == 0:
        fval = cal_table[i][1]
    elif i == len(cal_table):
        fval = cal_table[i-1][1]
    else:
        interpolation = ((cal_table[i][0] - rawval)* (cal_table[i][1] - cal_table[i-1][1]))/(cal_table[i][0] - cal_table[i-1][0])
        fval = cal_table[i][1] - interpolation
    return fval

def view_disp_thread(note,data):
    global config
    global view_disp_thread_run
    global cmode
    global cnallow
    global btuner
    global bcwbkin
    global bpreamp
    global bband
    global bmode
    global bagc
    global bnallow
    global bbandwidth
    global bbandwidthno
    global tx_flag


    view_disp_thread_run  = 1
    sdata = data.split(';')
    for rdata in sdata:
        if rdata[0:2] == 'TX':
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = False
            widget[1].Hide()
            if rdata[2:] == '0':
                widget[1].SetForegroundColour('#ffffff')
                widget[1].SetBackgroundColour('#696969')
                tx_flag = False
            else:
                tx_flag = True
                widget[1].SetForegroundColour('blue')
                widget[1].SetBackgroundColour('green')
            widget[1].Show()
            continue
        if rdata[0:2] == 'RS' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            widget[1].Hide()
            if rdata[2:] == '0':
                widget[1].SetForegroundColour('#ffffff')
                widget[1].SetBackgroundColour('#696969')
            else:
                widget[1].SetForegroundColour('blue')
                widget[1].SetBackgroundColour('green')
            widget[1].Show()
            continue
        if rdata[0:2] == 'BY' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            widget[1].Hide()
            if rdata[2:] == '00':
                widget[1].SetForegroundColour('#ffffff')
                widget[1].SetBackgroundColour('#696969')
            else:
                widget[1].SetForegroundColour('blue')
                widget[1].SetBackgroundColour('green')
            widget[1].Show()
            continue
        if rdata[0:3] == 'RI0' and len(rdata)>3:
            if rdata[0:3] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:3])]
            else:
                continue
            widget[1].Hide()
            if rdata[3:] == '0':
                widget[1].SetForegroundColour('#ffffff')
                widget[1].SetBackgroundColour('#696969')
            else:
                widget[1].SetForegroundColour('white')
                widget[1].SetBackgroundColour('red')
            widget[1].Show()
            continue
        if rdata[0:2] == 'FS' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            widget[1].Hide()
            if rdata[2:] == '0':
                widget[1].SetForegroundColour('#ffffff')
                widget[1].SetBackgroundColour('#696969')
            else:
                widget[1].SetForegroundColour('blue')
                widget[1].SetBackgroundColour('green')
            widget[1].Show()
            continue
        if rdata[0:2] == 'LK' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            widget[1].Hide()
            if rdata[2:] == '0':
                widget[1].SetForegroundColour('#ffffff')
                widget[1].SetBackgroundColour('#696969')
            else:
                widget[1].SetForegroundColour('blue')
                widget[1].SetBackgroundColour('green')
            widget[1].Show()
            continue
        if rdata[0:3] == 'RM1' and len(rdata)>3 and (not tx_flag):
            if 'SM' in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index('SM')]
            else:
                continue
            FT991_STR_CAL = [[0, -54],[12,-48],[27,-42],[40,-36],[55,-30],[65,-24],[80,-18],[95,-12],[112,-6],[130,0],[150,10],[172,20],[190,30],[220,40],[240,50],[255,60]]
            yaesu_default_str_cal = [[0, -54], [26, -42], [ 51, -30], [ 81, -18], [105, -9], [130, 0], [157, 12], [186, 25], [203, 35], [237, 50],[ 255, 60]]
            try:
                pi,fval = rig_raw2val(float(rdata[3:]),FT991_STR_CAL)
                widget[2].SetLabel(("%1.2f" % (fval)))
                if peakmeter_start:
                    widget[3].SetData([int(fval*50/20)], 0, 1)
            except Exception as e:
                print(rdata)
                print(e)
                pass
            continue
        if rdata[0:3] == 'RM5' and len(rdata)>3 and tx_flag:
            if 'PO' in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index('PO')]
            else:
                continue
            FT991_RFPOWER_METER_CAL = [[0.0, 0.0], [10.0, 0.8], [50.0, 8.0], [100.0, 26.0], [150.0, 54.0], [200.0, 92.0], [250.0, 140.0]]
            fval = rig_raw2val_float(float(rdata[3:]),FT991_RFPOWER_METER_CAL)
            widget[2].SetLabel(str(int(fval)))
            if peakmeter_start:
                widget[3].SetData([int(fval*50/50)], 0, 1)
            continue
        if rdata[0:3] == 'RM4' and len(rdata)>3 and tx_flag:
            if 'ALC' in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index('ALC')]
            else:
                continue
            yaesu_default_alc_cal = [[0,0.0],[64,1.0]]
            fval = rig_raw2val_float(float(rdata[3:]),yaesu_default_alc_cal)
            widget[2].SetLabel(("%1.2f" % (fval*10.0)))
            if peakmeter_start:
                widget[3].SetRangeValue(int(0.5*50/2.0),int(0.9*50/2.0),int(1.0*50/1.0))
                widget[3].SetData([int(fval*50/2.0)], 0, 1)
            continue
        if rdata[0:3] == 'RM6' and len(rdata)>3 and tx_flag:
            if 'SWR' in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index('SWR')]
            else:
                continue
            yaesu_default_swr_cal = [[12,1.0],[39,1.35],[65,1.5],[89,2.0],[242,5.0]]
            fval = rig_raw2val_float(float(rdata[3:]),yaesu_default_swr_cal)
            widget[2].SetLabel(("%1.2f" % (fval)))
            if peakmeter_start:
                widget[3].SetRangeValue(int(1.5*50/6),int(2.5*50/6),50)
                widget[3].SetData([int((fval-0.8)*50/6)], 0, 1)
            continue
        if rdata[0:2] == 'FA' and len(rdata)>2:
            if 'FA' in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index('FA')]
            else:
                continue
            fval = float(rdata[2:])/1000000
            widget[1].SetLabel("{: >10.6f}".format(fval))
            if 'BS' in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index('BS')]
            else:
                continue
            for ti in range(len(bandlists)):
                if fval>=bandlists[ti][4] and fval<=bandlists[ti][5]:
                    if bband != ti:
                        bband = ti
                        widget[3].SetSelection(ti)
                    break
            continue
        if rdata[0:2] == 'PA' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = rdata[2:]
            if val in widget[1]:
                ti = widget[1].index(val)
                if bpreamp != ti:
                    bpreamp = ti
                    widget[3].SetSelection(ti)
            continue
        if rdata[0:2] == 'NA' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            cnallow = -1
            val = rdata[2:]
            if val in widget[1]:
                ti = widget[1].index(val)
                if bnallow != ti:
                    bnallow = ti
                    widget[3].SetSelection(ti)
                cnallow = ti
            continue
        if rdata[0:2] == 'MD' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = rdata[2:]
            cmode = -1
            if val in widget[1]:
                ti = widget[1].index(val)
                if bmode != ti:
                    bmode = ti
                    widget[3].SetSelection(ti)
                cmode = ti
            continue
        if rdata[0:2] == 'GT' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = rdata[2:]
            if val in widget[1]:
                ti = widget[1].index(val)
                if bagc != ti:
                    bagc = ti
                    widget[3].SetSelection(ti)
            continue
        if rdata[0:2] == 'SH' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            if cnallow < 0 or cmode < 0:
                cbandwidth = 6
            else:
                cbandwidth = 0
                if modelists[cmode][2] == 'SSB':
                    if cnallow == 0:
                        cbandwidth = 1
                    else:
                        cbandwidth = 0
                elif modelists[cmode][2] == 'CW':
                    if cnallow == 0:
                        cbandwidth = 3
                    else:
                        cbandwidth = 2
                elif modelists[cmode][2] == 'DATA':
                    if cnallow == 0:
                        cbandwidth = 5
                    else:
                        cbandwidth = 4
                else:
                    cbandwidth = 6
            if bbandwidth != cbandwidth:
                widget[3].Clear()
                widget[3].AppendItems(bandwidth2lists[cbandwidth])
                bbandwidth = cbandwidth
            cbandwidthno = -1
            if cbandwidth > 5:
                cbandwidthno = 0
            else:
                val = rdata[3:]
                for i in range(len(bandwidthlists)):
                    if bandwidthlists[i][0] == val:
                        if len(bandwidthlists[i][cbandwidth+1].strip()) > 0:
                            cbandwidthno = bandwidth2lists[cbandwidth].index(bandwidthlists[i][cbandwidth+1])
                        else:
                            cbandwidthno = 0
                        break
            if bbandwidthno != cbandwidthno:
                widget[3].SetSelection(cbandwidthno)
                bbandwidthno = cbandwidthno
            continue
            
        if rdata[0:5] == 'EX141' and len(rdata)>5:
            if rdata[0:5] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:5])]
            else:
                continue
            val = rdata[5:]
            if val in widget[1]:
                ti = widget[1].index(val)
                if btuner != ti:
                    btuner = ti
                    widget[3].SetSelection(ti)
            continue
        if rdata[0:5] == 'EX056' and len(rdata)>5:
            if rdata[0:5] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:5])]
            else:
                continue
            val = rdata[5:]
            if val in widget[1]:
                ti = widget[1].index(val)
                if bcwbkin != ti:
                    bcwbkin = ti
                    widget[3].SetSelection(ti)
            continue
        if rdata[0:2] == 'PC' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = int(rdata[2:])
            widget[1].SetValue(val)
            widget[2].SetLabel("{: >5d}W".format(val))
            continue
        if rdata[0:2] == 'AG' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = int(rdata[2:])
            widget[1].SetValue(val)
            widget[2].SetLabel("{: >5d}".format(val))
            continue
        if rdata[0:2] == 'SQ' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = int(rdata[2:])
            widget[1].SetValue(val)
            widget[2].SetLabel("{: >5d}".format(val))
            continue
        if rdata[0:2] == 'RG' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = int(rdata[2:])
            widget[1].SetValue(val)
            widget[2].SetLabel("{: >5d}".format(val))
            continue
        if rdata[0:2] == 'AC' and len(rdata)>2:
            if 'AC0' in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index('AC0')]
            else:
                continue
            val = False
            if rdata[4:] == '0':
                val = False
            else:
                val = True
            widget[1].SetValue(val)
            continue
        if rdata[0:2] == 'BP' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = False
            if rdata[6:] == '0':
                val = False
            else:
                val = True
            widget[1].SetValue(val)
            continue
        if rdata[0:2] == 'NB' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = False
            if rdata[3:] == '0':
                val = False
            else:
                val = True
            widget[1].SetValue(val)
            continue
        if rdata[0:2] == 'NR' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = False
            if rdata[3:] == '0':
                val = False
            else:
                val = True
            widget[1].SetValue(val)
            continue
        if rdata[0:2] == 'BI' and len(rdata)>2:
            if rdata[0:2] in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(rdata[0:2])]
            else:
                continue
            val = False
            if rdata[2:] == '0':
                val = False
            else:
                val = True
            widget[1].SetValue(val)
            continue
    view_disp_thread_run = 0
    return

def view_port_read(note,port):
    global view_disp_thread_run

#    if view_disp_thread_run == 1:
#        return b''
    data = port.read_all()
    if data != b'':
        ddata = data.decode(errors='ignore')
        if len(ddata) > 0:
#            print(ddata)
            th = threading.Thread(target=view_disp_thread, args=(note,ddata), daemon=True)
            th.start()
    return data

snd_cmd = ['BY;','SM0;','TX;RM1;RM4;RM5;RM6;','RS;','PC;','PA0;','EX141;','MD0;NA0;SH0;','GT0;','BP00;','NB0;','NR0;','BC0;','AG0;','RG0;','SQ0;','EX056;','RI0;','FS;','LK;','BI;']

def view_thread(note,dummy):
    global port
    global Receiving
    global config
    global view_disp_thread_run
    global cmode
    global cnallow
    global btuner
    global bcwbkin
    global bpreamp
    global bband
    global bmode
    global bagc
    global bnallow
    global bbandwidth
    global bbandwidthno
    global tx_flag

    cmode = -1
    cnallow = -1
    btuner = -1
    bcwbkin = -1
    bpreamp = -1
    bband = -1
    bmode = -1
    bagc = -1
    bnallow = -1
    bbandwidth = -1
    bbandwidthno = -1


    timeoutm = 0.01
    timeoutw = 0.05
    view_disp_thread_run = 0
    com0com = note.view_tab.frm1.checkbuttonc1.IsChecked()
    try:
        port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))
        print(type(port))
        pprint(port)
        if isinstance(port, serial.serialwin32.Serial):
            pprint(port.is_open)
            if not port.is_open:
                return
        else:
            return

        if com0com:
            port0 = comopen(config['com0com']['serialdevice'],int(config['rig']['baudrate']))
            port.write(str.encode('FA;AC;BY;SM0;TX;RM1;RM4;RM5;RM6;RS;MD0;PC;PA0;EX141;NA0;SH0;GT0;BP00;NB0;NR0;BC0;AG0;RG0;SQ0;EX056;RI0;FS;LK;BI;'))
            time.sleep(timeoutm)
            view_port_read(note,port)
        else:
            port.write(str.encode('AI1;TX;RM1;RM4;RM5;RM6;FA;AC;BY;MD0;PC;PA0;EX141;NA0;SH0;GT0;BP00;NB0;NR0;BC0;AG0;RG0;SQ0;EX056;RI0;FS;LK;BI;'))
            time.sleep(timeoutm)
            view_port_read(note,port)

        peakmeter_start = False

        mtsndcmd = ['SM','PO','ALC','SWR']
        for sndcmd in mtsndcmd:
            if sndcmd in note.view_tab.frm2.sndcmd:
                widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(sndcmd)]
                while widget[3].IsStarted():
                    time.sleep(0.1)
                widget[3].ResetControl()

        peakmeter_start = True

        timeoutc = 0.0
        snd_cmd_no = 0
        while 1:
            if Receiving == 0:
                break
            if com0com:
                data = port0.read_all()
                if data != b'':
                    port.write(data)
                    time.sleep(timeoutm)
                    timeoutc = timeoutc + timeoutm
                    data = view_port_read(note,port)
                    if data != b'':
                        port0.write(data)
                else:
                    if snd_cmd_no < len(snd_cmd):
                        port.write(str.encode(snd_cmd[snd_cmd_no]))
                        time.sleep(timeoutm)
                        timeoutc = timeoutc + timeoutm
                        view_port_read(note,port)
                        snd_cmd_no = snd_cmd_no + 1
                    else:
                        if timeoutc >= timeoutw:
                            snd_cmd_no = 0
                            timeoutc = 0.0
            else:
                view_port_read(note,port)
                time.sleep(timeoutm)
                timeoutc = timeoutc + timeoutm
                if timeoutc >= timeoutw:
                    port.write(str.encode('SM0;TX;RM1;RM4;RM5;RM6;RS;EX141;NA0;EX056;RI0;'))
                    time.sleep(timeoutm)
                    timeoutc = timeoutm
                    view_port_read(note,port)
            time.sleep(timeoutm)
            timeoutc = timeoutc + timeoutm
#            pprint(timeoutc)

        if not com0com:
            port.write(str.encode('AI0;'))

        port.close()
        if com0com:
            port.close()

    except serial.serialutil.SerialTimeoutException:
        pass

    return

def view(event):
    global Receiving
    global note
    global tx_flag
    
    if note.view_tab.frm1.button1.GetLabel() == 'Start':
        tx_flag = False
        Receiving = 1
        note.view_tab.frm1.button1.SetLabel('Stop')
        note.view_tab.frm1.button1.SetBackgroundColour('green')
        th = threading.Thread(target=view_thread, args=(note,''), daemon=True)
        th.start()
    else:
        tx_flag = False
        Receiving = 0
        note.view_tab.frm1.button1.SetLabel('Start')
        note.view_tab.frm1.button1.SetBackgroundColour('wx.NullColour')

    return

def peakmeter_widget_set(frm,col,row,columnspan,rowspan,cmd):
#    global style

    val = '000'
    widget = []
    widget.append(cmd)

    widget.append(wx.StaticText(frm, -1, cmd))
    frm.layout.Add(widget[len(widget)-1], (row,col), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + 1

    widget.append(wx.StaticText(frm, -1, ""))
    frm.layout.Add(widget[len(widget)-1], (row,col), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + 1

    widget.append(pm.PeakMeterCtrl(frm, -1, agwStyle=pm.PM_HORIZONTAL, size=(200,20)))
    widget[len(widget)-1].SetMeterBands(1, 50)
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL)
    widget[len(widget)-1].SetData([0], 0, 1)
    widget[len(widget)-1].SetFalloffEffect(False)
    widget[len(widget)-1].ShowGrid(False)

    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def progressbar_widget_set(frm,col,row,columnspan,rowspan,cmd):
#    global style

    val = '000'
    widget = []
    widget.append(cmd)

    widget.append(wx.StaticText(frm, -1, cmd))
    frm.layout.Add(widget[len(widget)-1], (row,col), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + 1

    widget.append(wx.StaticText(frm, -1, "{: >3d}".format(10)))
    frm.layout.Add(widget[len(widget)-1], (row,col), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + 1

    widget.append(wx.Gauge(frm, -1, range=100))
    widget[len(widget)-1].SetValue(10)
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL)

    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def togglebutton_widget_command(event,widget,no,cmd):
    global port

    if isinstance(port, serial.serialwin32.Serial):
        if not port.is_open:
            return
    else:
        return

    SNDCMD = ''
    val = widget[no][1].GetValue()
    print(val)
    if val:
        widget[no][1].SetBackgroundColour('green')
    else:
        widget[no][1].SetBackgroundColour('wx.NullColour')
    if cmd == 'BP':
        if val:
            SNDCMD = cmd + '00001' + ';'
        else:
            SNDCMD = cmd + '00000' + ';'
    elif cmd == 'NB':
        if val:
            SNDCMD = cmd + '01' + ';'
        else:
            SNDCMD = cmd + '00' + ';'
    elif cmd == 'NR':
        if val:
            SNDCMD = cmd + '01' + ';'
        else:
            SNDCMD = cmd + '00' + ';'
    elif cmd == 'BC':
        if val:
            SNDCMD = cmd + '01' + ';'
        else:
            SNDCMD = cmd + '00' + ';'
    elif cmd == 'BI':
        if val:
            SNDCMD = cmd + '1' + ';'
        else:
            SNDCMD = cmd + '0' + ';'

    if len(SNDCMD):
        print(SNDCMD)
        try:
            port.write(str.encode(SNDCMD))
        except serial.serialutil.SerialTimeoutException:
            pass

    return

def togglebutton_widget_set(frm,col,row,columnspan,rowspan,cmd,txt):
    widget = []
    widget.append(cmd)

    widget.append(wx.ToggleButton(frm, -1, txt))
    cno = len(frm.widget)
    widget[len(widget)-1].Bind(wx.EVT_TOGGLEBUTTON, lambda e:togglebutton_widget_command(e,frm.widget,cno,cmd))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL)

    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def button_widget_command(event,widget,no,cmd):
    global port

    if isinstance(port, serial.serialwin32.Serial):
        if not port.is_open:
            return
    else:
        return

    SNDCMD = ''
    if cmd == 'AC2':
        SNDCMD = 'AC002;'
    elif cmd == 'ZI':
        SNDCMD = cmd + ';'

    if len(SNDCMD):
        print(SNDCMD)
        try:
            port.write(str.encode(SNDCMD))
        except serial.serialutil.SerialTimeoutException:
            pass

    return

def button_widget_set(frm,col,row,columnspan,rowspan,cmd,txt):
    widget = []
    widget.append(cmd)

    widget.append(wx.Button(frm, -1, txt))
    cno = len(frm.widget)
    widget[len(widget)-1].Bind(wx.EVT_BUTTON, lambda e:button_widget_command(e,frm.widget,cno,cmd))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL)

    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def checkbutton_widget_command(event,widget,no,cmd):
    global port

    if isinstance(port, serial.serialwin32.Serial):
        if not port.is_open:
            return
    else:
        return

    SNDCMD = ''
    if cmd == 'AC0':
        if event.IsChecked():
            SNDCMD = 'AC001;'
        else:
            SNDCMD = 'AC000;'

    if len(SNDCMD):
        print(SNDCMD)
        try:
            port.write(str.encode(SNDCMD))
        except serial.serialutil.SerialTimeoutException:
            pass

    return

def checkbutton_widget_set(frm,col,row,cmd,txt):
    widget = []
    widget.append(cmd)

    widget.append(wx.CheckBox(frm, -1, txt))
    cno = len(frm.widget)
    widget[len(widget)-1].Bind(wx.EVT_CHECKBOX, lambda e:checkbutton_widget_command(e,frm.widget,cno,cmd))
    frm.layout.Add(widget[len(widget)-1], (row,col), (1,1), flag=wx.SHAPED | wx.ALIGN_CENTER)

    col = col + 1
    row = row + 1
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def vscale_widget_command(event,widget,no,cmd):
    global port

    if isinstance(port, serial.serialwin32.Serial):
        if not port.is_open:
            return
    else:
        return

    obj = event.GetEventObject()
    val = obj.GetValue()
    widget[no][2].SetLabel("{: >3d}".format(val))

    SNDCMD = ''
    if cmd == 'PC':
        SNDCMD = 'PC' + "{:0>3d}".format(val) + ';'
    elif cmd == 'AG':
        SNDCMD = 'AG0' + "{:0>3d}".format(val) + ';'
    elif cmd == 'RG':
        SNDCMD = 'RG0' + "{:0>3d}".format(val) + ';'
    elif cmd == 'SQ':
        SNDCMD = 'SQ0' + "{:0>3d}".format(val) + ';'

    if len(SNDCMD):
        print(SNDCMD)
        try:
            port.write(str.encode(SNDCMD))
        except serial.serialutil.SerialTimeoutException:
            pass

    return

def vscale_widget_set(frm,col,row,columnspan,rowspan,ifrom,ito,tickinterval,length,cmd,txt):
    widget = []
    widget.append(cmd)

    widget.append(wx.Slider(frm, -1, value=ifrom, minValue=ifrom, maxValue=ito, style=wx.SL_VERTICAL|wx.SL_INVERSE|wx.SL_MIN_MAX_LABELS|wx.SL_AUTOTICKS))
    widget[len(widget)-1].SetTickFreq(tickinterval)
    widget[len(widget)-1].SetPageSize(tickinterval)
    cno = len(frm.widget)
    widget[len(widget)-1].Bind(wx.EVT_SLIDER, lambda e:vscale_widget_command(e,frm.widget,cno,cmd))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL,   border=3)

    row = row + rowspan

    widget.append(wx.StaticText(frm, -1, "{: >3d}".format(ifrom)))
    frm.layout.Add(widget[len(widget)-1], (row,col), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    row = row + 1

    widget.append(wx.StaticText(frm, -1, txt))
    frm.layout.Add(widget[len(widget)-1], (row,col), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)

    col = col + columnspan
    row = row + 1
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def hscale_widget_command(event,widget,no,cmd):
    global port

    if isinstance(port, serial.serialwin32.Serial):
        if not port.is_open:
            return
    else:
        return

    obj = event.GetEventObject()
    val = obj.GetValue()
    freqstep = 1
    for i in range(val):
        freqstep = freqstep * 10
#    print(val)
    widget[no][2].SetLabel("{: >5d}Hz Step".format(freqstep))

#    SNDCMD = ''
#    if cmd == 'PC':
#        SNDCMD = 'PC' + "{:0>3d}".format(val) + ';'

#    if len(SNDCMD):
#        print(SNDCMD)
#        try:
#            port.write(str.encode(SNDCMD))
#        except serial.serialutil.SerialTimeoutException:
#            pass

    return

def hscale_widget_set(frm,col,row,columnspan,rowspan,columnspan2,rowspan2,ifrom,ito,tickinterval,length,cmd,txt):
    widget = []
    widget.append(cmd)
    widget.append(wx.Slider(frm, -1, value=2, minValue=ifrom, maxValue=ito, style=wx.SL_HORIZONTAL|wx.SL_INVERSE))
    widget[len(widget)-1].SetTickFreq(tickinterval)
    widget[len(widget)-1].SetPageSize(tickinterval)
    cno = len(frm.widget)
    widget[len(widget)-1].Bind(wx.EVT_SLIDER, lambda e:hscale_widget_command(e,frm.widget,cno,cmd))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + columnspan
    widget.append(wx.StaticText(frm, -1, "{: >5d}Hz Step".format(100)))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan2,columnspan2), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + columnspan2
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def vspinbutton_widget_command(event,frm,no,cmd,step):
    global port

    if isinstance(port, serial.serialwin32.Serial):
        if not port.is_open:
            return
    else:
        return

#    obj = event.GetEventObject()
#    val = obj.GetValue()
#    print(val)

    addfreq = 0
    freqstep = 1
    if 'XXX1' in frm.sndcmd:
        widgeti = frm.widget[frm.sndcmd.index('XXX1')]
        ti = widgeti[1].GetValue()
        freqstep = 1
        for i in range(ti):
            freqstep = freqstep * 10
        addfreq = step*freqstep
    if addfreq != 0:
        if 'FA' in frm.sndcmd:
            widgeti = frm.widget[frm.sndcmd.index('FA')]
            sfreq = widgeti[1].GetLabel()
            freq = int(float(sfreq)*1000000.0/float(freqstep)) * freqstep
            freq = freq + addfreq
            sfreq = "{:0>9d}".format(freq)
#            print(sfreq)
            SNDCMD = 'FA' + sfreq + ';'
            print(SNDCMD)
            try:
                port.write(str.encode(SNDCMD))
            except serial.serialutil.SerialTimeoutException:
                pass

def vspinbutton_widget_set(frm,col,row,columnspan,rowspan,cmd):
    widget = []
    widget.append(cmd)
    widget.append(wx.SpinButton(frm, style=wx.SP_VERTICAL))
    widget[len(widget)-1].SetMin(-1000000)
    widget[len(widget)-1].SetMax(1000000)
    cno = len(frm.widget)
    widget[len(widget)-1].Bind(wx.EVT_SPIN_UP, lambda e:vspinbutton_widget_command(e,frm,cno,cmd,1))
    widget[len(widget)-1].Bind(wx.EVT_SPIN_DOWN, lambda e:vspinbutton_widget_command(e,frm,cno,cmd,-1))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def color_label_widget_set(frm,col,row,columnspan,rowspan,cmd,txt):
    widget = []
    widget.append(cmd)
    widget.append(wx.StaticText(frm, -1, txt, style=wx.TE_CENTER))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetForegroundColour('#ffffff')
    widget[len(widget)-1].SetBackgroundColour('#696969')
    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def label_widget_set(frm,col,row,columnspan,rowspan,columnspan2,rowspan2,fontname,fontsize,cmd,txt):
    val = '  0.000000'
    widget = []
    widget.append(cmd)

    font = wx.Font(fontsize, fontname, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    widget.append(wx.StaticText(frm, -1, val))
    widget[len(widget)-1].SetFont(font)
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL,   border=3)

    col = col + columnspan
    if len(txt) > 0:
        widget.append(wx.StaticText(frm, -1, txt))
        widget[len(widget)-1].SetFont(font)
        frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan2,columnspan2), flag=wx.EXPAND | wx.ALL,   border=3)
        col = col + columnspan2
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def combobox_widget_command(event,widget,no,cmd,widget_descriptions,cmd_descriptions):
    global port

#    print(event.GetString())

    if isinstance(port, serial.serialwin32.Serial):
        if not port.is_open:
            return
    else:
        return

    SNDCMD = ''
    selected_value = event.GetString()
    if cmd == 'BS':
        bandlist = bandlists[combo_bandlists.index(selected_value)]
        SNDCMD = cmd + bandlist[0] + ';'
    elif cmd == 'MD':
        subcmd = cmd_descriptions[widget_descriptions.index(selected_value)]
        SNDCMD = cmd + subcmd + ';'
    elif cmd == 'GT':
        subcmd = cmd_descriptions[widget_descriptions.index(selected_value)]
        if int(subcmd) >= 4:
            subcmd = '04'
        SNDCMD = cmd + subcmd + ';'
    elif cmd == 'PA':
        subcmd = cmd_descriptions[widget_descriptions.index(selected_value)]
        SNDCMD = cmd + subcmd + ';'
    elif cmd == 'NA':
        subcmd = cmd_descriptions[widget_descriptions.index(selected_value)]
        SNDCMD = cmd + subcmd + ';'
    elif cmd == 'EX141':
        subcmd = cmd_descriptions[widget_descriptions.index(selected_value)]
        SNDCMD = cmd + subcmd + ';'
    elif cmd == 'EX056':
        subcmd = cmd_descriptions[widget_descriptions.index(selected_value)]
        SNDCMD = cmd + subcmd + ';'
    elif cmd == 'SH':
        if cnallow < 0 or cmode < 0:
            cbandwidth = 6
        else:
            cbandwidth = 0
            if modelists[cmode][2] == 'SSB':
                if cnallow == 0:
                    cbandwidth = 1
                else:
                    cbandwidth = 0
            elif modelists[cmode][2] == 'CW':
                if cnallow == 0:
                    cbandwidth = 3
                else:
                    cbandwidth = 2
            elif modelists[cmode][2] == 'DATA':
                if cnallow == 0:
                    cbandwidth = 5
                else:
                    cbandwidth = 4
            else:
                cbandwidth = 6
        if cbandwidth <= 5:
            for i in range(len(bandwidthlists)):
                if bandwidthlists[i][cbandwidth+1] == selected_value:
                    SNDCMD = cmd + '0' + bandwidthlists[i][0] + ';'
                    break
    if len(SNDCMD) > 0:
        print(SNDCMD)
        try:
            port.write(str.encode(SNDCMD))
        except serial.serialutil.SerialTimeoutException:
            pass

    return

def combobox_widget_set(frm,col,row,columnspan,rowspan,columnspan2,rowspan2,width,cmd,txt,widget_descriptions,cmd_descriptions):
    val = '  0.000000'
    widget = []
    widget.append(cmd)
    widget.append(cmd_descriptions)

    widget.append(wx.StaticText(frm, -1, txt))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan2,columnspan2), flag=wx.EXPAND | wx.ALL,   border=3)
    col = col + columnspan2

    widget.append(wx.ComboBox(frm, -1, u'選択', choices=widget_descriptions))
    cno = len(frm.widget)
    widget[len(widget)-1].Bind(wx.EVT_COMBOBOX, lambda e:combobox_widget_command(e,frm.widget,cno,cmd,widget_descriptions,cmd_descriptions))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND)
    widget[len(widget)-1].SetSelection(0)

    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

def knobctrl_widget_set(frm,col,row,columnspan,rowspan,ifrom,ito,tickinterval,length,cmd,txt):
    val = 10
    widget = []
    widget.append(cmd)

    widget.append(kc.KnobCtrl(frm, -1, size=(length, length)))
    frm.layout.Add(widget[len(widget)-1], (row,col), (rowspan,columnspan), flag=wx.EXPAND | wx.ALL,   border=3)

    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)
    return col,row

#def sdcallback(indata, frames, time, status):
#    global plotdata,downsample
#    print('sdcallback!')
#    data = indata[::downsample, 0]
#    shift = len(data)
#    plotdata = np.roll(plotdata, -shift, axis=0)
#    plotdata[-shift:] = data
    
#def update_graph(event):
#    print('Uppdate graph!')
#    update_plot(event)

#def update_plot(frame):
#    global note
#    global plotdata, window,line,downsample
#    x = plotdata[-N:] * window
#    F = np.fft.fft(x) # フーリエ変換
#    F = F / (N / 2) # フーリエ変換の結果を正規化
#    F = F * (N / sum(window)) # 窓関数による補正
#    Amp = np.abs(F) # 振幅スペクトル
#    line.set_ydata(Amp[:N // 2])
#    pprint(line)
#    note.view_tab.frm3.draw()
#    return line,

def view_tab_set(note):
    global config
    global plotdata, window,line,figure,downsample

    note.view_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.view_tab.SetAutoLayout(1)
    note.view_tab.SetupScrolling()
    note.view_tab.layout = wx.BoxSizer(wx.VERTICAL)

    note.view_tab.frm1 = wx.Panel(note.view_tab, wx.ID_ANY)
    note.view_tab.frm1.layout = wx.BoxSizer(wx.HORIZONTAL)

    note.view_tab.frm1.button1 = wx.ToggleButton(note.view_tab.frm1, label='Start')
    note.view_tab.frm1.button1.Bind(wx.EVT_TOGGLEBUTTON, view)
    note.view_tab.frm1.layout.Add(note.view_tab.frm1.button1, flag=wx.EXPAND | wx.ALL)

    note.view_tab.frm1.Label1 = wx.StaticText(note.view_tab.frm1, -1, u'com0com:')
    note.view_tab.frm1.layout.Add(note.view_tab.frm1.Label1, flag=wx.SHAPED | wx.ALIGN_CENTER)

    note.view_tab.frm1.checkbuttonc1 = wx.CheckBox(note.view_tab.frm1, -1, 'Enable')
    note.view_tab.frm1.layout.Add(note.view_tab.frm1.checkbuttonc1, flag=wx.SHAPED | wx.ALIGN_CENTER)

    note.view_tab.frm1.SetSizer( note.view_tab.frm1.layout)
    note.view_tab.frm1.layout.Fit(note.view_tab.frm1)
    note.view_tab.layout.Add(note.view_tab.frm1, 0, wx.GROW | wx.EXPAND | wx.ALL)

#    downsample = 1  # FFTするのでダウンサンプリングはしない
#    length = int(1000 * 44100 / (1000 * downsample))
#    plotdata = np.zeros((length))
#    window = signal.hann(N) # 窓関数
#    freq = np.fft.fftfreq(N, d=1 / fs) # 周波数スケール

#    figure = Figure(figsize=(6.4, 1.2))
#    figure.set_facecolor((0.9, 0.9, 1.))
#    figure.subplots_adjust(wspace = 0.1, hspace = 0.1, top=0.9, bottom = 0.20, right=0.92, left = 0.1)
#    subplot = figure.add_subplot(111)
#    line, = subplot.plot(freq[:N // 2], np.zeros(N // 2))    
#    subplot.set_ylim([0, 0.2])
#    subplot.set_xlim([0, 3000])
#    subplot.set_xlabel('Frequency [Hz]')
#    subplot.set_ylabel('Amplitude spectrum')
#    figure.tight_layout()

#    note.view_tab.frm3 = FigureCanvasWxAgg(note.view_tab, -1, figure)
#    note.view_tab.frm3.SetBackgroundColour(wx.Colour(100,255,255))
    
#    note.view_tab.frm3.layout = wx.BoxSizer(wx.VERTICAL)

#    note.view_tab.frm3.SetSizer( note.view_tab.frm3.layout)
#    note.view_tab.frm3.layout.Fit(note.view_tab.frm3)
#    note.view_tab.layout.Add(note.view_tab.frm3, 0, wx.EXPAND | wx.ALL)

    note.view_tab.frm2 = wx.Panel(note.view_tab, wx.ID_ANY)
    note.view_tab.frm2.layout = wx.GridBagSizer()

    note.view_tab.frm2.sndcmd = []
    note.view_tab.frm2.widget = []

    col = 0
    row = 0
    brow = row
    col,row = color_label_widget_set(note.view_tab.frm2,0,brow,1,1,'TX','TX')
    col,row = color_label_widget_set(note.view_tab.frm2,col,brow,1,1,'BY','BUSY')
    col,row = color_label_widget_set(note.view_tab.frm2,col,brow,1,1,'RS','MENU')
    col,row = color_label_widget_set(note.view_tab.frm2,col,brow,1,1,'FS','FAST')
    col,row = color_label_widget_set(note.view_tab.frm2,col,brow,1,1,'LK','LOCK')
    col,row = color_label_widget_set(note.view_tab.frm2,col,brow,1,1,'RI0','Hi-SWR')
    
    col,row = hscale_widget_set(note.view_tab.frm2,1,row,3,1,2,1,0,5,1,100,'XXX1','')

    brow = row
    col,nrow = label_widget_set(note.view_tab.frm2,0,brow,4,2,2,2,wx.FONTFAMILY_DEFAULT,24,'FA','MHz')
    bcol = col

    col,wrow = vspinbutton_widget_set(note.view_tab.frm2,col,brow,1,2,'XXX2')

    col,wrow = combobox_widget_set(note.view_tab.frm2,bcol+1,brow,3,1,1,1,15,'BS','Band',combo_bandlists,bandlists)
    col,wrow = combobox_widget_set(note.view_tab.frm2,bcol+1,wrow,3,1,1,1,10,'MD','Mode',['LSB','USB','CW-U','FM','AM','RTTY-LSB','CW-R','DATA-LSB','RTTY-USB','DATA-FM','FM-N','DATA-USB','AM-N','C4FM'],['01','02','03','04','05','06','07','08','09','0A','0B','0C','0D','0E'])

    col,w2row = combobox_widget_set(note.view_tab.frm2,bcol+5,brow,3,1,2,1,10,'PA','Pre AMP',['IPO','AMP 1','AMP 2'],['00','01','02'])
    col,w2row = combobox_widget_set(note.view_tab.frm2,bcol+5,w2row,3,1,2,1,10,'NA','NAR/WIDE',['WIDE','NARROW'],['00','01'])
    col,w2row = combobox_widget_set(note.view_tab.frm2,bcol+5,w2row,3,1,2,1,10,'SH','Band width',['Off'],['99'])
    col,w2row = combobox_widget_set(note.view_tab.frm2,bcol+5,w2row,3,1,2,1,10,'GT','AGC',['OFF','FAST','MID','SLOW','AUTO-FAST','AUTO-MID','AUTO-SLOW'],['00','01','02','03','04','05','06'])

    bcol = col
    col,row = combobox_widget_set(note.view_tab.frm2,bcol+3,brow,1,1,1,1,10,'EX141','TUNER',['OFF','INTERNAL','EXTERNAL','ATAS','LAMP'],['0','1','2','3','4'])
    col,row = checkbutton_widget_set(note.view_tab.frm2,bcol+4,row,'AC0','Enable Tune')
    zcol = bcol+4
    col,row = button_widget_set(note.view_tab.frm2,bcol+4,row,2,2,'AC2','Tune')

    row = nrow
    col,row = peakmeter_widget_set(note.view_tab.frm2,0,row,5,1,'SM')
    col,row = peakmeter_widget_set(note.view_tab.frm2,0,row,5,1,'PO')
    col,row = peakmeter_widget_set(note.view_tab.frm2,0,row,5,1,'ALC')
    col,row = peakmeter_widget_set(note.view_tab.frm2,0,row,5,1,'SWR')
#    col,row = progressbar_widget_set(note.view_tab.frm2,0,row,5,1,'SM')
#    col,row = progressbar_widget_set(note.view_tab.frm2,0,row,5,1,'PO')
#    col,row = progressbar_widget_set(note.view_tab.frm2,0,row,5,1,'ALC')
#    col,row = progressbar_widget_set(note.view_tab.frm2,0,row,5,1,'SWR')
    
    xcol = col

    col,wrow = vscale_widget_set(note.view_tab.frm2,2,row+1,1,10,5,100,5,200,'PC','PWR')
    col,wrow = vscale_widget_set(note.view_tab.frm2,col,row+1,1,10,0,255,20,200,'AG','AF')
    col,wrow = vscale_widget_set(note.view_tab.frm2,col,row+1,1,10,0,255,20,200,'RG','RF')
    col,wrow = vscale_widget_set(note.view_tab.frm2,col,row+1,1,10,0,100,10,200,'SQ','SQL')


    xrow = row
    col,wrow = togglebutton_widget_set(note.view_tab.frm2,xcol+1,xrow,2,2,'BC','DNF')
    col,wrow = togglebutton_widget_set(note.view_tab.frm2,col,xrow,2,2,'NB','NB')
    col,wrow = togglebutton_widget_set(note.view_tab.frm2,col,xrow,2,2,'NR','DNR')
    col,wrow = togglebutton_widget_set(note.view_tab.frm2,xcol+1,wrow,2,2,'BP','NOTCH')

    col,row = button_widget_set(note.view_tab.frm2,zcol,xrow,2,2,'ZI','CW ZERO IN')
    col,row = togglebutton_widget_set(note.view_tab.frm2,zcol,row,2,2,'BI','BREAK-IN')
    col,w2row = combobox_widget_set(note.view_tab.frm2,zcol-1,row,3,1,1,1,10,'EX056','CW BK-IN',['SEMI','FULL'],['0','1'])

    pprint(note.view_tab.frm2.widget)

    print("%d %d" % (note.view_tab.frm2.layout.GetCols(),note.view_tab.frm2.layout.GetRows()))
    
    for i in range(note.view_tab.frm2.layout.GetRows()):
        note.view_tab.frm2.layout.AddGrowableRow(i)
    for i in range(note.view_tab.frm2.layout.GetCols()):
        note.view_tab.frm2.layout.AddGrowableCol(i)

    note.view_tab.frm2.SetSizer( note.view_tab.frm2.layout)
    note.view_tab.frm2.layout.Fit(note.view_tab.frm2)
    note.view_tab.layout.Add(note.view_tab.frm2, 0, flag=wx.ALL | wx.EXPAND)

    note.view_tab.SetSizer(note.view_tab.layout)
    note.view_tab.layout.Fit(note.view_tab)

    note.AddPage(note.view_tab, u"View")

#    ani = FuncAnimation(figure, update_plot, interval=30, blit=True)
#    timer = wx.Timer(note.view_tab,1)
#    note.view_tab.Bind(wx.EVT_TIMER, update_graph, timer)
#    timer.Start(1000)

def auto_information_thread(note,dummy):
    global Receiving
    global config

    try:
        port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))
        pprint(port)
        port.write(str.encode('AI1;'))

        while 1:
            if Receiving == 0:
                break
            data = port.read_all()
#            pprint(data)
            if data != b'':
                sdata = data.decode(errors='ignore').split(';')
                print(sdata)
                for rdata in sdata:
                    if rdata[0:2] in note.auto_information_tab.frm2.sndcmd:
                        widget = note.auto_information_tab.frm2.widget[note.auto_information_tab.frm2.widget.index(rdata[0:2])]
                        if len(data) > 2:
                            widget[6].SetLabel(rdata[2:])
                note.auto_information_tab.frm2.layout.Fit(note.auto_information_tab.frm2)
            time.sleep(0.5)

        port.write(str.encode('AI0;'))
        port.close()
    except serial.serialutil.SerialTimeoutException:
        pass

    return

def auto_information(event):
    global note
    global Receiving
    
    if note.auto_information_tab.frm1.button1.GetLabel() == 'Start':
        Receiving = 1
        note.auto_information_tab.frm1.button1.SetLabel('Stop')
        th = threading.Thread(target=auto_information_thread, args=(note,''), daemon=True)
        th.start()
    else:
        Receiving = 0
        note.auto_information_tab.frm1.button1.SetLabel('Start')

    return

def auto_information_widget_set(frm,cmd,func,description):
    val = '000'
    widget = [cmd,func,val,description]
    row = len(frm.widget)
    widget.append(wx.StaticText(frm, -1, cmd))
    frm.layout.Add(widget[len(widget)-1], (row,0), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    widget.append(wx.StaticText(frm, -1, func + ': '))
    frm.layout.Add(widget[len(widget)-1], (row,1), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    widget.append(wx.StaticText(frm, -1, val))
    frm.layout.Add(widget[len(widget)-1], (row,2), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    widget.append(wx.StaticText(frm, -1, description))
    frm.layout.Add(widget[len(widget)-1], (row,3), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    frm.widget.append(widget)
    frm.sndcmd.append(cmd)

def auto_information_tab_set(note):
    global config

    note.auto_information_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.auto_information_tab.SetAutoLayout(1)
    note.auto_information_tab.SetupScrolling()
    note.auto_information_tab.layout = wx.BoxSizer(wx.VERTICAL)

    note.auto_information_tab.frm1 = wx.Panel(note.auto_information_tab, wx.ID_ANY)
    note.auto_information_tab.frm1.layout = wx.BoxSizer(wx.HORIZONTAL)

    note.auto_information_tab.frm1.button1 = wx.Button(note.auto_information_tab.frm1, label='Start')
    note.auto_information_tab.frm1.button1.Bind(wx.EVT_BUTTON, auto_information)
    note.auto_information_tab.frm1.layout.Add(note.auto_information_tab.frm1.button1, flag=wx.EXPAND | wx.ALL)

    note.auto_information_tab.frm1.SetSizer( note.auto_information_tab.frm1.layout)
    note.auto_information_tab.frm1.layout.Fit(note.auto_information_tab.frm1)
    note.auto_information_tab.layout.Add(note.auto_information_tab.frm1, 0, wx.GROW | wx.EXPAND | wx.ALL)

    note.auto_information_tab.frm2 = wx.Panel(note.auto_information_tab, wx.ID_ANY)
    note.auto_information_tab.frm2.layout = wx.GridBagSizer()

    note.auto_information_tab.frm2.sndcmd = []
    note.auto_information_tab.frm2.widget = []

    for catcmd in catcmds:
#        print(catcmd)
        if catcmd[7] == 1:
            auto_information_widget_set(note.auto_information_tab.frm2,catcmd[0],catcmd[1],catcmd[3])

    note.auto_information_tab.frm2.SetSizer( note.auto_information_tab.frm2.layout)
    note.auto_information_tab.frm2.layout.Fit(note.auto_information_tab.frm2)
    note.auto_information_tab.layout.Add(note.auto_information_tab.frm2, 0, flag=wx.ALL | wx.EXPAND)

    note.auto_information_tab.SetSizer(note.auto_information_tab.layout)
    note.auto_information_tab.layout.Fit(note.auto_information_tab)

    note.AddPage(note.auto_information_tab, u"Auto Information")

def com_port_setting_tab_set(note):
    global config
    global devices
    global descriptions
    global mic_lists
    global speaker_lists
    global combo_mic_lists
    global combo_speaker_lists

#    note.com_port_setting_tab = wx.Panel(note, wx.ID_ANY)
    note.com_port_setting_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.com_port_setting_tab.SetAutoLayout(1)
    note.com_port_setting_tab.SetupScrolling()
    note.com_port_setting_tab.layout = wx.BoxSizer(wx.VERTICAL)

#    note.com_port_setting_tab.frm1 = wx.ScrolledWindow(note.com_port_setting_tab, -1)
    note.com_port_setting_tab.frm1 = wx.Panel(note.com_port_setting_tab, wx.ID_ANY)
#    note.com_port_setting_tab.frm1 = wx.lib.scrolledpanel.ScrolledPanel(note.com_port_setting_tab, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
#    note.com_port_setting_tab.frm1.SetAutoLayout(1)
#    note.com_port_setting_tab.frm1.SetupScrolling()
    note.com_port_setting_tab.frm1.layout = wx.GridBagSizer()

    note.com_port_setting_tab.frm1.label1r0 = wx.StaticText(note.com_port_setting_tab.frm1, -1, u'Rig ')
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.label1r0, (0,0), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.label1r1 = wx.StaticText(note.com_port_setting_tab.frm1, -1, u'Serial Device: ')
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.label1r1, (1,1), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.combobox1r1 = wx.ComboBox(note.com_port_setting_tab.frm1, -1, u'選択', choices=descriptions)
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.combobox1r1, (1,2), (1,1), flag=wx.EXPAND)

    rig_serialdevice = config['rig']['serialdevice']
    if rig_serialdevice in devices:
        note.com_port_setting_tab.frm1.combobox1r1.SetSelection(devices.index(rig_serialdevice))
    else:
        note.com_port_setting_tab.frm1.combobox1r1.SetSelection(0)

    note.com_port_setting_tab.frm1.label1r2 = wx.StaticText(note.com_port_setting_tab.frm1, -1, u'Baud Rate: ')
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.label1r2, (1,3), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.combobox1r2 = wx.ComboBox(note.com_port_setting_tab.frm1, -1, u'選択', choices=baudrate)
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.combobox1r2, (1,4), (1,1), flag=wx.EXPAND)

    rig_baudrate = config['rig']['baudrate']
    if rig_baudrate in baudrate:
        note.com_port_setting_tab.frm1.combobox1r2.SetSelection(baudrate.index(rig_baudrate))
    else:
        note.com_port_setting_tab.frm1.combobox1r2.SetSelection(0)

    rig_mic = config['rig']['mic']
    rig_speaker = config['rig']['speaker']

    audio = pyaudio.PyAudio()
    
    mic_lists = []
    speaker_lists = []
    combo_mic_lists = []
    combo_speaker_lists = []
    
    for x in range(0, audio.get_device_count()):
        audio_device = audio.get_device_info_by_index(x)
        if audio_device['maxInputChannels'] > 0 and audio_device['hostApi'] == 0:
            mic_lists.append(audio_device)
            combo_mic_lists.append(audio_device['name'])
#            print("%d %s %f" % (audio_device['index'],audio_device['name'],audio_device['defaultSampleRate']))
        
    for x in range(0, audio.get_device_count()):
        audio_device = audio.get_device_info_by_index(x)
        if audio_device['maxOutputChannels'] > 0 and audio_device['hostApi'] == 0:
            speaker_lists.append(audio_device)
            combo_speaker_lists.append(audio_device['name'])
#            print("%d %s %f" % (audio_device['index'],audio_device['name'],audio_device['defaultSampleRate']))

    note.com_port_setting_tab.frm1.label2r1 = wx.StaticText(note.com_port_setting_tab.frm1, -1, u'Sound Device Input: ')
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.label2r1, (2,1), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.combobox2r1 = wx.ComboBox(note.com_port_setting_tab.frm1, -1, u'選択', choices=combo_mic_lists)
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.combobox2r1, (2,2), (1,1), flag=wx.EXPAND)

    if rig_mic in combo_mic_lists:
        note.com_port_setting_tab.frm1.combobox2r1.SetSelection(combo_mic_lists.index(rig_mic))
    else:
        note.com_port_setting_tab.frm1.combobox2r1.SetSelection(0)

    note.com_port_setting_tab.frm1.label2r2 = wx.StaticText(note.com_port_setting_tab.frm1, -1, u'Sound Device Output: ')
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.label2r2, (3,1), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.combobox2r2 = wx.ComboBox(note.com_port_setting_tab.frm1, -1, u'選択', choices=combo_speaker_lists)
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.combobox2r2, (3,2), (1,1), flag=wx.EXPAND)

    if rig_speaker in combo_speaker_lists:
        note.com_port_setting_tab.frm1.combobox2r2.SetSelection(combo_speaker_lists.index(rig_speaker))
    else:
        note.com_port_setting_tab.frm1.combobox2r2.SetSelection(0)


    note.com_port_setting_tab.frm1.label1c0 = wx.StaticText(note.com_port_setting_tab.frm1, -1, u'com0com ')
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.label1c0, (5,0), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.label1c1 = wx.StaticText(note.com_port_setting_tab.frm1, -1, u'Serial Device: ')
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.label1c1, (6,1), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.combobox1c1 = wx.ComboBox(note.com_port_setting_tab.frm1, -1, u'選択', choices=descriptions)
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.combobox1c1, (6,2), (1,1), flag=wx.EXPAND)

    com0com_serialdevice = config['com0com']['serialdevice']
    if com0com_serialdevice in devices:
        note.com_port_setting_tab.frm1.combobox1c1.SetSelection(devices.index(com0com_serialdevice))
    else:
        note.com_port_setting_tab.frm1.combobox1c1.SetSelection(0)
    
    note.com_port_setting_tab.frm1.button1 = wx.Button(note.com_port_setting_tab.frm1, label='保存')
    note.com_port_setting_tab.frm1.button1.Bind(wx.EVT_BUTTON, saveconfig)
    note.com_port_setting_tab.frm1.layout.Add(note.com_port_setting_tab.frm1.button1, (7,4), (1,1), flag=wx.EXPAND)

    note.com_port_setting_tab.frm1.layout.AddGrowableRow(0)
    note.com_port_setting_tab.frm1.layout.AddGrowableRow(1)
    note.com_port_setting_tab.frm1.layout.AddGrowableRow(2)
    note.com_port_setting_tab.frm1.layout.AddGrowableCol(0)
    note.com_port_setting_tab.frm1.layout.AddGrowableCol(1)
    note.com_port_setting_tab.frm1.layout.AddGrowableCol(2)
    note.com_port_setting_tab.frm1.SetSizer( note.com_port_setting_tab.frm1.layout)
    note.com_port_setting_tab.frm1.layout.Fit(note.com_port_setting_tab.frm1)
    note.com_port_setting_tab.layout.Add(note.com_port_setting_tab.frm1, 0, flag=wx.ALL | wx.EXPAND)

    note.com_port_setting_tab.SetSizer(note.com_port_setting_tab.layout)
    note.com_port_setting_tab.layout.Fit(note.com_port_setting_tab)

    note.AddPage(note.com_port_setting_tab, u"Setting")
    
def dump_thread(note,dummy):
    global Receiving
    global config

    com0com = note.dump_tab.frm1.checkbuttonc1.IsChecked()
    try:
        port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))
#        port.write(str.encode('AI1;'))

        if com0com:
            port0 = comopen(config['com0com']['serialdevice'],int(config['rig']['baudrate']))
        
        while 1:
            if Receiving == 0:
                break
            data = port.read_all()
            pprint('Rig:[')
            pprint(data)
            pprint(']')
            if data != b'':
                if len(data.decode(errors='ignore')) > 0:
                    note.dump_tab.frm2.text1.AppendText('Rig ->'+data.decode(errors='ignore')+'\n')
#                    pprint(data)
                    if com0com:
                        note.dump_tab.frm2.text1.AppendText('com0<-'+data.decode(errors='ignore')+'\n')
                        port0.write(data)
            if com0com:
                data = port0.read_all()
                pprint('com0com:[')
                pprint(data)
                pprint(']')
                if data != b'':
                    if len(data.decode(errors='ignore')) > 0:
                        note.dump_tab.frm2.text1.AppendText('com0->'+data.decode(errors='ignore')+'\n')
#                        pprint(data)
                        port.write(data)
                        note.dump_tab.frm2.text1.AppendText('Rig <-'+data.decode(errors='ignore')+'\n')
            time.sleep(0.1)

#        port.write(str.encode('AI0;'))

        port.close()
        if com0com:
            port.close()

    except serial.serialutil.SerialTimeoutException:
        pass

    return

def dump(event):
    global Receiving
    global note
    
    if note.dump_tab.frm1.button1.GetLabel() == 'Start':
        Receiving = 1
        note.dump_tab.frm1.button1.SetLabel('Stop')
        th = threading.Thread(target=dump_thread, args=(note,''), daemon=True)
        th.start()
    else:
        Receiving = 0
        note.dump_tab.frm1.button1.SetLabel('Start')

    return
    
def dump_tab_set(note):
#    note.dump_tab = wx.Panel(note, wx.ID_ANY)
    note.dump_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.dump_tab.SetAutoLayout(1)
    note.dump_tab.SetupScrolling()
    note.dump_tab.layout = wx.BoxSizer(wx.VERTICAL)

    note.dump_tab.frm1 = wx.Panel(note.dump_tab, wx.ID_ANY)
    note.dump_tab.frm1.layout = wx.BoxSizer(wx.HORIZONTAL)

    note.dump_tab.frm1.button1 = wx.Button(note.dump_tab.frm1, label='Start')
    note.dump_tab.frm1.button1.Bind(wx.EVT_BUTTON, dump)
    note.dump_tab.frm1.layout.Add(note.dump_tab.frm1.button1, flag=wx.EXPAND | wx.ALL)

    note.dump_tab.frm1.Label1 = wx.StaticText(note.dump_tab.frm1, -1, u'com0com:')
    note.dump_tab.frm1.layout.Add(note.dump_tab.frm1.Label1, flag=wx.SHAPED | wx.ALIGN_CENTER)

    note.dump_tab.frm1.checkbuttonc1 = wx.CheckBox(note.dump_tab.frm1, -1, 'Enable')
    note.dump_tab.frm1.layout.Add(note.dump_tab.frm1.checkbuttonc1, flag=wx.SHAPED | wx.ALIGN_CENTER)

    note.dump_tab.frm1.SetSizer( note.dump_tab.frm1.layout)
    note.dump_tab.frm1.layout.Fit(note.dump_tab.frm1)
    note.dump_tab.layout.Add(note.dump_tab.frm1, 0, wx.GROW | wx.EXPAND | wx.ALL)

    note.dump_tab.frm2 = wx.Panel(note.dump_tab, wx.ID_ANY)
    note.dump_tab.frm2.layout = wx.BoxSizer(wx.VERTICAL)

    note.dump_tab.frm2.text1 = wx.TextCtrl(note.dump_tab.frm2, -1,style=wx.TE_MULTILINE)
    note.dump_tab.frm2.layout.Add(note.dump_tab.frm2.text1, proportion=1, flag=wx.EXPAND | wx.ALL)

    note.dump_tab.frm2.SetSizer( note.dump_tab.frm2.layout)
    note.dump_tab.frm2.layout.Fit(note.dump_tab.frm2)
    note.dump_tab.layout.Add(note.dump_tab.frm2, proportion=1, flag=wx.EXPAND | wx.ALL)

    note.dump_tab.SetSizer(note.dump_tab.layout)
    note.dump_tab.layout.Fit(note.dump_tab)

    note.AddPage(note.dump_tab, u"Dump")
    
def ft8_cw_rtty_setting(event):
    global config
    global devices
    global descriptions

    port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))

    for catcmd in ft8_cw_rtty_setting_cmd:
        try:
            port.write(str.encode(catcmd[0]+catcmd[1]+';'))
            pprint(str.encode(catcmd[0]+catcmd[1]+';'))
            data = port.read_all()
            if data != b'':
                pprint(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    port.close()
    
    wx.MessageBox('設定しました', 'Setting')
    
    return

def ft8_cw_rtty_setting_widget_set(frm,catcmd,row):
    widget = catcmd
#    row = len(frm.widget)
    widget.append(wx.StaticText(frm, -1, catcmd[3]))
    frm.layout.Add(widget[len(widget)-1], (row,0), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    widget.append(wx.StaticText(frm, -1, catcmd[0]))
    frm.layout.Add(widget[len(widget)-1], (row,1), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    widget.append(wx.StaticText(frm, -1, catcmd[1]))
    frm.layout.Add(widget[len(widget)-1], (row,2), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    widget.append(wx.StaticText(frm, -1, catcmd[2]))
    frm.layout.Add(widget[len(widget)-1], (row,3), (1,1), flag=wx.EXPAND | wx.ALL,   border=3)
    widget[len(widget)-1].SetBackgroundColour('green')
    frm.widget.append(widget)
    frm.sndcmd.append(catcmd)
    row = row + 1
    return row

def ft8_cw_rtty_setting_tab_set(note):
    global config

#    note.ft8_cw_rtty_setting_tab = wx.Panel(note, wx.ID_ANY)
    note.ft8_cw_rtty_setting_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.ft8_cw_rtty_setting_tab.SetAutoLayout(1)
    note.ft8_cw_rtty_setting_tab.SetupScrolling()
    note.ft8_cw_rtty_setting_tab.layout = wx.BoxSizer(wx.VERTICAL)

    note.ft8_cw_rtty_setting_tab.frm1 = wx.Panel(note.ft8_cw_rtty_setting_tab, wx.ID_ANY)
    note.ft8_cw_rtty_setting_tab.frm1.layout = wx.BoxSizer(wx.HORIZONTAL)

    note.ft8_cw_rtty_setting_tab.frm1.button1 = wx.Button(note.ft8_cw_rtty_setting_tab.frm1, label='Set')
    note.ft8_cw_rtty_setting_tab.frm1.button1.Bind(wx.EVT_BUTTON, ft8_cw_rtty_setting)
    note.ft8_cw_rtty_setting_tab.frm1.layout.Add(note.ft8_cw_rtty_setting_tab.frm1.button1, flag=wx.EXPAND | wx.ALL)

    note.ft8_cw_rtty_setting_tab.frm1.SetSizer( note.ft8_cw_rtty_setting_tab.frm1.layout)
    note.ft8_cw_rtty_setting_tab.frm1.layout.Fit(note.ft8_cw_rtty_setting_tab.frm1)
    note.ft8_cw_rtty_setting_tab.layout.Add(note.ft8_cw_rtty_setting_tab.frm1, 0, wx.GROW | wx.EXPAND | wx.ALL)

    note.ft8_cw_rtty_setting_tab.frm2 = wx.Panel(note.ft8_cw_rtty_setting_tab, wx.ID_ANY)
    note.ft8_cw_rtty_setting_tab.frm2.layout = wx.GridBagSizer()

    note.ft8_cw_rtty_setting_tab.frm2.sndcmd = []
    note.ft8_cw_rtty_setting_tab.frm2.widget = []

    row = 0
    for catcmd in ft8_cw_rtty_setting_cmd:
        row = ft8_cw_rtty_setting_widget_set(note.ft8_cw_rtty_setting_tab.frm2,catcmd,row)

    note.ft8_cw_rtty_setting_tab.frm2.SetSizer( note.ft8_cw_rtty_setting_tab.frm2.layout)
    note.ft8_cw_rtty_setting_tab.frm2.layout.Fit(note.ft8_cw_rtty_setting_tab.frm2)
    note.ft8_cw_rtty_setting_tab.layout.Add(note.ft8_cw_rtty_setting_tab.frm2, 0, flag=wx.ALL | wx.EXPAND)

    note.ft8_cw_rtty_setting_tab.SetSizer(note.ft8_cw_rtty_setting_tab.layout)
    note.ft8_cw_rtty_setting_tab.layout.Fit(note.ft8_cw_rtty_setting_tab)

    note.AddPage(note.ft8_cw_rtty_setting_tab, u"FT8 CW RTTY Setting")

def ft8_setting(event):
    global config
    global devices
    global descriptions

    port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))


    for catcmd in ft8_setting_cmd:
        try:
            sndcmd = catcmd[0]+catcmd[1]+';'
            print(sndcmd)
            port.write(str.encode(sndcmd))
            data = port.read_all()
            if data != b'':
                print(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    for catcmd in ft8_cw_rtty_setting_cmd:
        try:
            sndcmd = catcmd[0]+catcmd[1]+';'
            print(sndcmd)
            port.write(str.encode(sndcmd))
            data = port.read_all()
            if data != b'':
                print(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    port.close()
    
    wx.MessageBox('設定しました', 'Setting')
    
    return

def ft8_setting_tab_set(note):
    global config

#    note.ft8_setting_tab = wx.Panel(note, wx.ID_ANY)
    note.ft8_setting_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.ft8_setting_tab.SetAutoLayout(1)
    note.ft8_setting_tab.SetupScrolling()
    note.ft8_setting_tab.layout = wx.BoxSizer(wx.VERTICAL)

    note.ft8_setting_tab.frm1 = wx.Panel(note.ft8_setting_tab, wx.ID_ANY)
    note.ft8_setting_tab.frm1.layout = wx.BoxSizer(wx.HORIZONTAL)

    note.ft8_setting_tab.frm1.button1 = wx.Button(note.ft8_setting_tab.frm1, label='Set')
    note.ft8_setting_tab.frm1.button1.Bind(wx.EVT_BUTTON, ft8_setting)
    note.ft8_setting_tab.frm1.layout.Add(note.ft8_setting_tab.frm1.button1, flag=wx.EXPAND | wx.ALL)

    note.ft8_setting_tab.frm1.SetSizer( note.ft8_setting_tab.frm1.layout)
    note.ft8_setting_tab.frm1.layout.Fit(note.ft8_setting_tab.frm1)
    note.ft8_setting_tab.layout.Add(note.ft8_setting_tab.frm1, 0, wx.GROW | wx.EXPAND | wx.ALL)


    note.ft8_setting_tab.frm2 = wx.Panel(note.ft8_setting_tab, wx.ID_ANY)
    note.ft8_setting_tab.frm2.layout = wx.GridBagSizer()

    note.ft8_setting_tab.frm2.sndcmd = []
    note.ft8_setting_tab.frm2.widget = []

    row = 0
    for catcmd in ft8_setting_cmd:
        row = ft8_cw_rtty_setting_widget_set(note.ft8_setting_tab.frm2,catcmd,row)

    row = row + 1
    for catcmd in ft8_cw_rtty_setting_cmd:
        row = ft8_cw_rtty_setting_widget_set(note.ft8_setting_tab.frm2,catcmd,row)

    note.ft8_setting_tab.frm2.SetSizer( note.ft8_setting_tab.frm2.layout)
    note.ft8_setting_tab.frm2.layout.Fit(note.ft8_setting_tab.frm2)
    note.ft8_setting_tab.layout.Add(note.ft8_setting_tab.frm2, 0, flag=wx.ALL | wx.EXPAND)

    note.ft8_setting_tab.SetSizer(note.ft8_setting_tab.layout)
    note.ft8_setting_tab.layout.Fit(note.ft8_setting_tab)

    note.AddPage(note.ft8_setting_tab, u"FT8 Setting")

def cw_setting(event):
    global config
    global devices
    global descriptions

    port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))


    for catcmd in cw_setting_cmd:
        try:
            sndcmd = catcmd[0]+catcmd[1]+';'
            print(sndcmd)
            port.write(str.encode(sndcmd))
            data = port.read_all()
            if data != b'':
                print(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    for catcmd in ft8_cw_rtty_setting_cmd:
        try:
            sndcmd = catcmd[0]+catcmd[1]+';'
            print(sndcmd)
            port.write(str.encode(sndcmd))
            data = port.read_all()
            if data != b'':
                print(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    port.close()
    
    wx.MessageBox('設定しました', 'Setting')    

    return

def cw_setting_tab_set(note):
    global config

#    note.cw_setting_tab = wx.Panel(note, wx.ID_ANY)
    note.cw_setting_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.cw_setting_tab.SetAutoLayout(1)
    note.cw_setting_tab.SetupScrolling()
    note.cw_setting_tab.layout = wx.BoxSizer(wx.VERTICAL)

    note.cw_setting_tab.frm1 = wx.Panel(note.cw_setting_tab, wx.ID_ANY)
    note.cw_setting_tab.frm1.layout = wx.BoxSizer(wx.HORIZONTAL)

    note.cw_setting_tab.frm1.button1 = wx.Button(note.cw_setting_tab.frm1, label='Set')
    note.cw_setting_tab.frm1.button1.Bind(wx.EVT_BUTTON, cw_setting)
    note.cw_setting_tab.frm1.layout.Add(note.cw_setting_tab.frm1.button1, flag=wx.EXPAND | wx.ALL)

    note.cw_setting_tab.frm1.SetSizer( note.cw_setting_tab.frm1.layout)
    note.cw_setting_tab.frm1.layout.Fit(note.cw_setting_tab.frm1)
    note.cw_setting_tab.layout.Add(note.cw_setting_tab.frm1, 0, wx.GROW | wx.EXPAND | wx.ALL)


    note.cw_setting_tab.frm2 = wx.Panel(note.cw_setting_tab, wx.ID_ANY)
    note.cw_setting_tab.frm2.layout = wx.GridBagSizer()

    note.cw_setting_tab.frm2.sndcmd = []
    note.cw_setting_tab.frm2.widget = []

    row = 0
    for catcmd in cw_setting_cmd:
        row = ft8_cw_rtty_setting_widget_set(note.cw_setting_tab.frm2,catcmd,row)

    row = row + 1
    for catcmd in ft8_cw_rtty_setting_cmd:
        row = ft8_cw_rtty_setting_widget_set(note.cw_setting_tab.frm2,catcmd,row)

    note.cw_setting_tab.frm2.SetSizer( note.cw_setting_tab.frm2.layout)
    note.cw_setting_tab.frm2.layout.Fit(note.cw_setting_tab.frm2)
    note.cw_setting_tab.layout.Add(note.cw_setting_tab.frm2, 0, flag=wx.ALL | wx.EXPAND)

    note.cw_setting_tab.SetSizer(note.cw_setting_tab.layout)
    note.cw_setting_tab.layout.Fit(note.cw_setting_tab)

    note.AddPage(note.cw_setting_tab, u"CW Setting")

def rtty_setting(event):
    global config
    global devices
    global descriptions

    port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))


    for catcmd in rtty_setting_cmd:
        try:
            sndcmd = catcmd[0]+catcmd[1]+';'
            print(sndcmd)
            port.write(str.encode(sndcmd))
            data = port.read_all()
            if data != b'':
                print(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    for catcmd in ft8_cw_rtty_setting_cmd:
        try:
            sndcmd = catcmd[0]+catcmd[1]+';'
            print(sndcmd)
            port.write(str.encode(sndcmd))
            data = port.read_all()
            if data != b'':
                print(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    port.close()
    
    wx.MessageBox('設定しました', 'Setting')    

    return

def rtty_setting_tab_set(note):
    global config

#    note.rtty_setting_tab = wx.Panel(note, wx.ID_ANY)
    note.rtty_setting_tab = wx.lib.scrolledpanel.ScrolledPanel(note, wx.ID_ANY, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
    note.rtty_setting_tab.SetAutoLayout(1)
    note.rtty_setting_tab.SetupScrolling()
    note.rtty_setting_tab.layout = wx.BoxSizer(wx.VERTICAL)

    note.rtty_setting_tab.frm1 = wx.Panel(note.rtty_setting_tab, wx.ID_ANY)
    note.rtty_setting_tab.frm1.layout = wx.BoxSizer(wx.HORIZONTAL)

    note.rtty_setting_tab.frm1.button1 = wx.Button(note.rtty_setting_tab.frm1, label='Set')
    note.rtty_setting_tab.frm1.button1.Bind(wx.EVT_BUTTON, rtty_setting)
    note.rtty_setting_tab.frm1.layout.Add(note.rtty_setting_tab.frm1.button1, flag=wx.EXPAND | wx.ALL)

    note.rtty_setting_tab.frm1.SetSizer( note.rtty_setting_tab.frm1.layout)
    note.rtty_setting_tab.frm1.layout.Fit(note.rtty_setting_tab.frm1)
    note.rtty_setting_tab.layout.Add(note.rtty_setting_tab.frm1, 0, wx.GROW | wx.EXPAND | wx.ALL)


    note.rtty_setting_tab.frm2 = wx.Panel(note.rtty_setting_tab, wx.ID_ANY)
    note.rtty_setting_tab.frm2.layout = wx.GridBagSizer()

    note.rtty_setting_tab.frm2.sndcmd = []
    note.rtty_setting_tab.frm2.widget = []

    row = 0
    for catcmd in rtty_setting_cmd:
        row = ft8_cw_rtty_setting_widget_set(note.rtty_setting_tab.frm2,catcmd,row)

    row = row + 1
    for catcmd in ft8_cw_rtty_setting_cmd:
        row = ft8_cw_rtty_setting_widget_set(note.rtty_setting_tab.frm2,catcmd,row)

    note.rtty_setting_tab.frm2.SetSizer( note.rtty_setting_tab.frm2.layout)
    note.rtty_setting_tab.frm2.layout.Fit(note.rtty_setting_tab.frm2)
    note.rtty_setting_tab.layout.Add(note.rtty_setting_tab.frm2, 0, flag=wx.ALL | wx.EXPAND)

    note.rtty_setting_tab.SetSizer(note.rtty_setting_tab.layout)
    note.rtty_setting_tab.layout.Fit(note.rtty_setting_tab)

    note.AddPage(note.rtty_setting_tab, u"RTTY Setting")

def get_geometry_info(event):
    global frame
    global config

    pos = frame.GetScreenPosition()
    size = frame.GetSize()
#    print("pos:",pos)
#    print("size:",size)

    config = configparser.ConfigParser()
    config.read_dict(default_configs)
    config.read(config_file)
    config['win'] = {}
    config['win']['winfo_width'] = str(size[0])
    config['win']['winfo_height'] = str(size[1])
    config['win']['winfo_x'] = str(pos[0])
    config['win']['winfo_y'] = str(pos[1])

    with open(config_file, 'w') as f:
        config.write(f)

    event.Skip()

def main():
    global frame
    global note
    global config
    global devices
    global descriptions
    global port
    global figure
    global peakmeter_start
    
    peakmeter_start = False
    
    config = configparser.ConfigParser()
    config.read_dict(default_configs)
    config.read(config_file)

    devices = []
    descriptions = []
    comlist(devices,descriptions)

    application = wx.App()
    frame = wx.Frame(None, wx.ID_ANY, u"FT-991 Control", pos=(int(config['win']['winfo_x']), int(config['win']['winfo_y'])), size=(int(config['win']['winfo_width']), int(config['win']['winfo_height'])))

    icon = wx.Icon(icon_file, wx.BITMAP_TYPE_ICO)
    frame.SetIcon(icon)

    note = wx.Notebook(frame, wx.ID_ANY)

    view_tab_set(note)
    dump_tab_set(note)
    auto_information_tab_set(note)
    ft8_setting_tab_set(note)
    cw_setting_tab_set(note)
    rtty_setting_tab_set(note)
    ft8_cw_rtty_setting_tab_set(note)
    com_port_setting_tab_set(note)

    frame.Show()
    note.Refresh()

    frame.Bind( wx.EVT_MOVE_END, get_geometry_info )
    frame.Bind( wx.EVT_SIZE, get_geometry_info )

#    sd.default.device = [3, 7]

#    stream = sd.InputStream(
#        channels=1,
#        dtype='float32',
#        device=3,
#        callback=sdcallback
#    )
#    stream.start()
#    ani = FuncAnimation(figure, update_plot, interval=30, blit=True)
#    pprint(stream)
#    with stream:
#        plt.show()

#    timer = wx.Timer(frame,1)
#    frame.Bind(wx.EVT_TIMER, update_graph, timer)
#    timer.Start(30)

    mtsndcmd = ['SM','PO','ALC','SWR']
    for sndcmd in mtsndcmd:
        if sndcmd in note.view_tab.frm2.sndcmd:
            widget = note.view_tab.frm2.widget[note.view_tab.frm2.sndcmd.index(sndcmd)]
            widget[3].Start(1000//1000)

#    for widget in note.view_tab.frm2.widget:
#        if widget[0] == 'SM':
#            print(widget[3].IsStarted())
#            widget[3].Start(1000//1000)
#            while widget[3].IsStarted():
#                time.sleep(0.1)
#            print(widget[3].IsStarted())
#        if widget[0] == 'PO':
#            widget[3].Start(1000//1000)
#            while widget[3].IsStarted():
#                time.sleep(0.1)
#        if widget[0] == 'ALC':
#            widget[3].Start(1000//1000)
#            while widget[3].IsStarted():
#                time.sleep(0.1)
#        if widget[0] == 'SWR':
#            widget[3].Start(1000//1000)
#            while widget[3].IsStarted():
#                time.sleep(0.1)
        
    peakmeter_start = True
    application.MainLoop()
    
if __name__ == "__main__":
    main()
