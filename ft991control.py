#!/usr/bin/env python
import sys, time
import serial
import serial.tools.list_ports
from pprint import pprint
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkFont
from tkinter import filedialog
from tkinter import messagebox
from ttkthemes import *
import threading
import configparser

default_configs = {'win': {'geometry': '1102x586+1222+254','winfo_width': '1102','winfo_height': '586','winfo_x': '1222','winfo_y': '254'},
                   'rig': {'serialdevice': 'COM6','baudrate': '9600'},
                   'com0com': {'serialdevice': 'COM4','baudrate': '9600'}
                  }

config_file = './ft991control.ini'

baudrate = [4800,9600,19200,38400]

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
,['SH','021','3200Hz','WIDTH']
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
#        print(p)
#        print(" device       :", p.device)
#        print(" name         :", p.name)
#        print(" description  :", p.description)
#        print(" hwid         :", p.hwid)
#        print(" vid          :", p.vid)
#        print(" pid          :", p.pid)
#        print(" serial_number:", p.serial_number)
#        print(" location     :", p.location)
#        print(" manufactuer  :", p.manufacturer)
#        print(" product      :", p.product)
#        print(" interface    :", p.interface)
#        print("")
        devices.append(p.device)
        descriptions.append(p.description)

def comopen(device,baudrate):
    try:
        port = serial.Serial(port=device, baudrate=baudrate, write_timeout=0.05)
    except:
        print("Error: %s can't open." % device)
        return -1
    return port

def common():
    devices = []
    ser = {}

    comlist(devices)
    port = comopen('COM6',9600)
    ser[port] = b''

    port = comopen('COM4',19200)
    ser[port] = b''

    ports = ser.keys()

    try:
        while True:
            for p in ports:
                ser[p] = p.read_all()

                data = ser[p]
                if data != b'':
#                    pprint(data)
                    for q in ports:
                        if q != p:
                            try:
                                q.write(data)
                            except serial.serialutil.SerialTimeoutException:
                                pass
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    for p in ports:
        p.close()

def get_geometry_info(event):
    global root

    geometry = root.geometry()
    winfo_width = root.winfo_width()
    winfo_height = root.winfo_height()
    winfo_x = root.winfo_x()
    winfo_y = root.winfo_y()

    config = configparser.ConfigParser()
    config.read_dict(default_configs)
    config.read(config_file)
    config['win'] = {}
    config['win']['geometry'] = geometry
    config['win']['winfo_width'] = str(winfo_width)
    config['win']['winfo_height'] = str(winfo_height)
    config['win']['winfo_x'] = str(winfo_x)
    config['win']['winfo_y'] = str(winfo_y)

    with open(config_file, 'w') as f:
        config.write(f)

def saveconfig(note):
    global root
    global devices
    global descriptions

    geometry = root.geometry()
    winfo_width = root.winfo_width()
    winfo_height = root.winfo_height()
    winfo_x = root.winfo_x()
    winfo_y = root.winfo_y()

    config = configparser.ConfigParser()
    config.read_dict(default_configs)
    config.read(config_file)
    config['win'] = {}
    config['win']['geometry'] = geometry
    config['win']['winfo_width'] = str(winfo_width)
    config['win']['winfo_height'] = str(winfo_height)
    config['win']['winfo_x'] = str(winfo_x)
    config['win']['winfo_y'] = str(winfo_y)

    selected_value = note.com_port_setting_tab.frm1.combobox1r1.get()
    config['rig'] = {}
    config['rig']['serialdevice'] = devices[descriptions.index(selected_value)]
    config['rig']['baudrate'] = str(note.com_port_setting_tab.frm1.combobox1r2.get())

    selected_value = note.com_port_setting_tab.frm1.combobox1c1.get()
    config['com0com'] = {}
    config['com0com']['serialdevice'] = devices[descriptions.index(selected_value)]

    with open(config_file, 'w') as f:
        config.write(f)

def dump_thread(note,dummy):
    global Receiving
    global config

    com0com = note.dump_tab.frm1.checkbuttonc1var.get()
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
                    note.dump_tab.frm2.text1.insert(tk.END, 'Rig ->'+data.decode(errors='ignore')+'\n')
#                    pprint(data)
                    if com0com:
                        note.dump_tab.frm2.text1.insert(tk.END, 'com0<-'+data.decode(errors='ignore')+'\n')
                        port0.write(data)
            if com0com:
                data = port0.read_all()
                pprint('com0com:[')
                pprint(data)
                pprint(']')
                if data != b'':
                    if len(data.decode(errors='ignore')) > 0:
                        note.dump_tab.frm2.text1.insert(tk.END, 'com0->'+data.decode(errors='ignore')+'\n')
#                        pprint(data)
                        port.write(data)
                        note.dump_tab.frm2.text1.insert(tk.END, 'Rig <-'+data.decode(errors='ignore')+'\n')
            time.sleep(0.1)

#        port.write(str.encode('AI0;'))

        port.close()
        if com0com:
            port.close()

    except serial.serialutil.SerialTimeoutException:
        pass

    return

def dump(note):
    global Receiving
    
    if note.dump_tab.frm1.button1['text'] == 'Start':
        Receiving = 1
        note.dump_tab.frm1.button1['text'] = 'Stop'
        th = threading.Thread(target=dump_thread, args=(note,''), daemon=True)
        th.start()
    else:
        Receiving = 0
        note.dump_tab.frm1.button1['text'] = 'Start'

    return

def dump_tab_set(note):
    global root
    global config

    note.dump_tab = tk.Frame(note)
    note.add(note.dump_tab, text='Dump')

    note.dump_tab.frm1 = tk.Frame(note.dump_tab)
    note.dump_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.dump_tab.frm1.button1 = tk.Button(note.dump_tab.frm1, text="Start", command=lambda:dump(note))
    note.dump_tab.frm1.button1.grid(sticky=tk.N+tk.S+tk.W+tk.E,row=0, column=0, rowspan=1, ipadx=1)

    note.dump_tab.frm1.Label1 = ttk.Label(note.dump_tab.frm1, text='com0com:')
    note.dump_tab.frm1.Label1.grid(sticky=tk.N+tk.S+tk.W+tk.E,row=0, column=1, ipadx=1)

    note.dump_tab.frm1.checkbuttonc1var = tk.BooleanVar()
    note.dump_tab.frm1.checkbuttonc1 = tk.Checkbutton(note.dump_tab.frm1, text = 'Enable', variable = note.dump_tab.frm1.checkbuttonc1var )
    note.dump_tab.frm1.checkbuttonc1.grid(sticky=tk.N+tk.S+tk.W+tk.E,row=0, column=2, rowspan=1, ipadx=1)
    
    note.dump_tab.frm2 = tk.Frame(note.dump_tab)
    note.dump_tab.frm2.pack(side = tk.TOP, expand=True, fill=tk.BOTH)

    note.dump_tab.frm2.text1 = tk.Text(note.dump_tab.frm2, wrap=tk.NONE)
    ysc1 = tk.Scrollbar(note.dump_tab.frm2, orient=tk.VERTICAL, command=note.dump_tab.frm2.text1.yview)
    note.dump_tab.frm2.text1["yscrollcommand"] = ysc1.set
    ysc1.pack(side=tk.RIGHT, fill="y")
    xsc1 = tk.Scrollbar(note.dump_tab.frm2, orient=tk.HORIZONTAL, command=note.dump_tab.frm2.text1.xview)
    note.dump_tab.frm2.text1["xscrollcommand"] = xsc1.set
    xsc1.pack(side=tk.BOTTOM,fill="x")
#    note.dump_tab.frm2.text1.config(state='disabled')
    note.dump_tab.frm2.text1.pack(expand=True, fill=tk.BOTH)

    note.dump_tab.frm2.update_idletasks()
#    note.auto_information_tab.canvas.config(scrollregion=note.auto_information_tab.canvas.bbox("all"))

#def getcatdata(port,note,cmd,row)

def rig_raw2val(rawval,cal_table):
    fval = 0.0
    for i in range(len(cal_table)):
        if rawval < cal_table[i][0]:
            break
    if i <= 10:
        return i,i
    return i,((i-10)+1)*10
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
#    global style

    view_disp_thread_run  = 1
    sdata = data.split(';')
    for rdata in sdata:
        if rdata[0:2] == 'SM':
            FT991_STR_CAL = [[0, -54],[12,-48],[27,-42],[40,-36],[55,-30],[65,-24],[80,-18],[95,-12],[112,-6],[130,0],[150,10],[172,20],[190,30],[220,40],[240,50],[255,60]]
#            yaesu_default_str_cal = [[0, -54], [26, -42], [ 51, -30], [ 81, -18], [105, -9], [130, 0], [157, 12], [186, 25], [203, 35], [237, 50],[ 255, 60]]
            pi,fval = rig_raw2val(float(rdata[2:]),FT991_STR_CAL)
#            pi,fval = rig_raw2val(float(rdata[2:]),yaesu_default_str_cal)
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'SM':
                    widget[2]['text'] = str(int(fval))
#                    style=ttk.Style()
#                    style.theme_use("default")
#                    style.configure("GREEN.Horizontal.TProgressbar", background='green')
#                    widget[3].configure(value=pi/15, style='GREEN.Horizontal.TProgressbar')
                    widget[3].configure(value=pi/15)
                    break
        if rdata[0:3] == 'RM5':
            rawval = float(rdata[3:])
            FT991_RFPOWER_METER_CAL = [[0.0, 0.0], [10.0, 0.8], [50.0, 8.0], [100.0, 26.0], [150.0, 54.0], [200.0, 92.0], [250.0, 140.0]]
            fval = rig_raw2val_float(float(rdata[3:]),FT991_RFPOWER_METER_CAL)
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'PO':
                    widget[2]['text'] = str(int(fval))
#                    style=ttk.Style()
#                    style.theme_use("default")
#                    style.configure("GREEN.Horizontal.TProgressbar", background='green')
#                    widget[3].configure(value=fval/100.0, style='GREEN.Horizontal.TProgressbar')
                    widget[3].configure(value=fval/100.0)
                    break
        if rdata[0:3] == 'RM4':
            yaesu_default_alc_cal = [[0,0.0],[64,1.0]]
            fval = rig_raw2val_float(float(rdata[3:]),yaesu_default_alc_cal)
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'ALC':
                    widget[2]['text'] = ("%1.2f" % (fval))
#                    style=ttk.Style()
#                    style.theme_use("default")
#                    style.configure("GREEN.Horizontal.TProgressbar", background='green')
#                    widget[3].configure(value=fval/1.0, style='GREEN.Horizontal.TProgressbar')
                    widget[3].configure(value=fval/1.0)
                    break
        if rdata[0:3] == 'RM6':
            yaesu_default_swr_cal = [[12,1.0],[39,1.35],[65,1.5],[89,2.0],[242,5.0]]
            fval = rig_raw2val_float(float(rdata[3:]),yaesu_default_swr_cal)
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'SWR':
                    widget[2]['text'] = ("%1.2f" % (fval))
#                    if fval <= 1.5:
#                        backgroundcolor = "green"
#                    elif fval < 2.5:
#                        backgroundcolor = "yellow"
#                    else:
#                        backgroundcolor = "red"
#                    style=ttk.Style()
#                    style.theme_use("default")
#                    style.configure("SWR.Horizontal.TProgressbar", background=backgroundcolor)
#                    widget[3].configure(value=fval/10, style='SWR.Horizontal.TProgressbar')
                    widget[3].configure(value=fval/10)
                    break
        if rdata[0:2] == 'FA':
            fval = float(rdata[2:])/1000000
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'FA':
                    widget[1]['text'] = "{: >10.6f}".format(fval)
                    break
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'BS':
                    for ti in range(len(bandlists)):
                        if fval>=bandlists[ti][4] and fval<=bandlists[ti][5]:
                            widget[3].current(ti)
                            break
                    break
        if rdata[0:2] == 'PA':
            val = rdata[2:]
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'PA':
                    if val in widget[1]:
                        ti = widget[1].index(val)
                        widget[3].current(ti)
                    break
        if rdata[0:2] == 'MD':
            val = rdata[3:]
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'MD':
                    if val in widget[1]:
                        ti = widget[1].index(val)
                        widget[3].current(ti)
                    break
        if rdata[0:2] == 'PC':
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'PC':
                    val = int(rdata[2:])
                    widget[1].set(val)
                    widget[3]['text'] = "{: >5d}".format(val)
                    break
        if rdata[0:2] == 'AC':
            val = False
            if rdata[4:] == '0':
                val = False
            else:
                val = True
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'AC0':
                    widget[1].set(val)
                    break
        if rdata[0:2] == 'TX':
            val = False
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'TX':
                    if rdata[2:] == '0':
                        widget[1].config(relief=tk.SOLID, foreground="red", background="black")
                    else:
                        widget[1].config(relief=tk.SOLID, foreground="blue", background="green")
                    break
        if rdata[0:2] == 'RS':
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'RS':
                    if rdata[2:] == '0':
                        widget[1].config(relief=tk.SOLID, foreground="red", background="black")
                    else:
                        widget[1].config(relief=tk.SOLID, foreground="blue", background="green")
                    break
        if rdata[0:2] == 'BY':
            for widget in note.view_tab.frm2.widget:
                if widget[0] == 'BY':
                    if rdata[2:] == '00':
                        widget[1].config(relief=tk.SOLID, foreground="red", background="black")
                    else:
                        widget[1].config(relief=tk.SOLID, foreground="blue", background="green")
                    break
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
            th = threading.Thread(target=view_disp_thread, args=(note,ddata), daemon=True)
            th.start()
    return data

snd_cmd = ['SM0;','RM5;','RM4;','RM6;','RS;','PC;','PA0;']

def view_thread(note,dummy):
    global Receiving
    global config
    global view_disp_thread_run

    timeoutm = 0.05
    timeoutw = 0.5
    view_disp_thread_run = 0
    com0com = note.view_tab.frm1.checkbuttonc1var.get()
    try:
        port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))

        if com0com:
            port0 = comopen(config['com0com']['serialdevice'],int(config['rig']['baudrate']))
            port.write(str.encode('FA;AC;BY;SM0;RM5;RM4;RM6;RS;MD0;PC;PA0;'))
            time.sleep(timeoutm)
            view_port_read(note,port)
        else:
            port.write(str.encode('AI1;FA;AC;BY;MD0;PC;PA0;'))
            time.sleep(timeoutm)
            view_port_read(note,port)

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
                    port.write(str.encode('SM0;RM5;RM4;RM6;RS;'))
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

def view(note):
    global Receiving
    
    if note.view_tab.frm1.button1['text'] == 'Start':
        Receiving = 1
        note.view_tab.frm1.button1['text'] = 'Stop'
        th = threading.Thread(target=view_thread, args=(note,''), daemon=True)
        th.start()
    else:
        Receiving = 0
        note.view_tab.frm1.button1['text'] = 'Start'

    return

def progressbar_widget_set(frm,canvas,col,row,columnspan,rowspan,cmd):
#    global style

    val = '000'
    widget = []
    widget.append(cmd)
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=cmd))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + 1
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=val))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + 1
#    if cmd == 'SWR':
#        style.configure("SWR.Horizontal.TProgressbarr", background='green')
#        pprint(style)
#        widget.append(ttk.Progressbar(frm, length=200, mode="determinate", maximum=1, style='SWR.Horizontal.TProgressbar'))
#    else:
#        style.configure("GREEN.Horizontal.TProgressbar", background='green')
#        widget.append(ttk.Progressbar(frm, length=200, mode="determinate", maximum=1, style='GREEN.Horizontal.TProgressbar'))
    widget.append(ttk.Progressbar(frm, length=200, mode="determinate", maximum=1))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, columnspan=columnspan, rowspan=rowspan, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    return col,row

def button_widget_command(frm,no,cmd):
    return

def button_widget_set(frm,canvas,col,row,columnspan,rowspan,cmd,txt):
    widget = []
    widget.append(cmd)
    widget.append(tk.Button(frm, text=txt, command=lambda:button_widget_command(frm,len(frm.widget),cmd)))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, columnspan=columnspan, rowspan=rowspan, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    return col,row

def checkbutton_widget_set(frm,canvas,col,row,cmd,txt):
    widget = []
    widget.append(cmd)
    widget.append(tk.BooleanVar())
    widget.append(tk.Checkbutton(frm, text = txt, variable = widget[len(widget)-1]))
    widget[len(widget)-1].grid(row=row, column=col, ipadx=1)
    col = col + 1
    row = row + 1
    frm.widget.append(widget)
    return col,row

def vscale_widget_command(widget,no,cmd):
    val = widget[no][1]
    widget[no][3]['text'] = str(val.get())
    return

def vscale_widget_set(frm,canvas,col,row,columnspan,rowspan,ifrom,ito,tickinterval,length,cmd,txt):
    widget = []
    widget.append(cmd)
    widget.append(tk.IntVar())
    cno = len(frm.widget)
    widget.append(tk.Scale(frm, variable = widget[len(widget)-1] ,orient=tk.VERTICAL, showvalue=False, from_=ito, to=ifrom, tickinterval=tickinterval, length=length, command=lambda e:vscale_widget_command(frm.widget,cno,cmd)))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, columnspan=columnspan, rowspan=rowspan, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    row = row + rowspan
    widget.append(ttk.Label(frm, justify=tk.RIGHT, text=str(ifrom)))
    widget[len(widget)-1].grid(sticky=tk.E,row=row, column=col, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    row = row + 1
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=txt))
    widget[len(widget)-1].grid(sticky=tk.E,row=row, column=col, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + 1
    row = row + 1
    frm.widget.append(widget)
    return col,row

def hscale_widget_set(frm,canvas,col,row,columnspan,rowspan,cmd,txt):
    widget = []
    widget.append(cmd)
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=txt))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + 1
    widget.append(ttk.Label(frm, justify=tk.LEFT, text="000"))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + 1
    widget.append(tk.IntVar())
    widget.append(tk.Scale(frm, variable = widget[len(widget)-1] ,orient=tk.HORIZONTAL, showvalue=False))
    widget[len(widget)-1].grid(row=row, column=col, columnspan=columnspan, rowspan=rowspan, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + 1
    row = row + 1
    frm.widget.append(widget)
    return col,row

def color_label_widget_set(frm,canvas,col,row,columnspan,rowspan,cmd,txt):
    widget = []
    widget.append(cmd)
    widget.append(ttk.Label(frm, justify=tk.CENTER, anchor="center", relief=tk.SOLID, foreground="red", background="black", text=txt))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, columnspan=columnspan, rowspan=rowspan, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + columnspan
    row = row + rowspan
    frm.widget.append(widget)
    return col,row

def label_widget_set(frm,canvas,col,row,columnspan,rowspan,fontname,fontsize,cmd,txt):
    val = '  0.000000'
    widget = []
    widget.append(cmd)
    widget.append(ttk.Label(frm, justify=tk.RIGHT, anchor=tk.E, text=val, font=(fontname,fontsize)))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, columnspan=columnspan, rowspan=rowspan, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + columnspan
    if len(txt) > 0:
        widget.append(ttk.Label(frm, justify=tk.LEFT, anchor="center", text=txt, font=(fontname,fontsize)))
        widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, rowspan=rowspan, ipadx=1)
        widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
        col = col + 1
    row = row + rowspan
    frm.widget.append(widget)
    return col,row

def combobox_widget_set(frm,canvas,col,row,columnspan,rowspan,width,cmd,txt,widget_descriptions,cmd_descriptions):
    val = '  0.000000'
    widget = []
    widget.append(cmd)
    widget.append(cmd_descriptions)
    widget.append(ttk.Label(frm, justify=tk.RIGHT, anchor=tk.E, text=txt))
    widget[len(widget)-1].grid(sticky=tk.N+tk.S+tk.W+tk.E,row=row, column=col, columnspan=columnspan, rowspan=rowspan, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    col = col + columnspan
    widget.append(ttk.Combobox(frm,width=width, justify=tk.LEFT))
    widget[len(widget)-1]['values'] = widget_descriptions
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=col, ipadx=1)
    widget[len(widget)-1].current(0)
    col = col + 1
    row = row + rowspan
    frm.widget.append(widget)
    return col,row

def view_tab_set(note):
    global root
    global config

    note.view_tab = tk.Frame(note)
    note.add(note.view_tab, text='View')

    note.view_tab.frm1 = tk.Frame(note.view_tab)
    note.view_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.view_tab.frm1.button1 = tk.Button(note.view_tab.frm1, text="Start", command=lambda:view(note))
    note.view_tab.frm1.button1.grid(sticky=tk.N+tk.S+tk.W+tk.E,row=0, column=0, rowspan=1, ipadx=1)

    note.view_tab.frm1.Label1 = ttk.Label(note.view_tab.frm1, text='com0com:')
    note.view_tab.frm1.Label1.grid(sticky=tk.N+tk.S+tk.W+tk.E,row=0, column=1, ipadx=1)

    note.view_tab.frm1.checkbuttonc1var = tk.BooleanVar()
    note.view_tab.frm1.checkbuttonc1 = tk.Checkbutton(note.view_tab.frm1, text = 'Enable', variable = note.view_tab.frm1.checkbuttonc1var )
    note.view_tab.frm1.checkbuttonc1.grid(sticky=tk.N+tk.S+tk.W+tk.E,row=0, column=2, rowspan=1, ipadx=1)
    
    note.view_tab.canvas = tk.Canvas(note.view_tab)

    note.view_tab.frm2 = tk.Frame(note.view_tab.canvas)

    scrollbary = tk.Scrollbar(
        note.view_tab.canvas, orient=tk.VERTICAL, command=note.view_tab.canvas.yview
    )
    note.view_tab.canvas.configure(yscrollcommand=scrollbary.set)
    scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbarx = tk.Scrollbar(
        note.view_tab.canvas, orient=tk.HORIZONTAL, command=note.view_tab.canvas.xview
    )
    note.view_tab.canvas.configure(xscrollcommand=scrollbarx.set)
    scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)

    note.view_tab.canvas.pack(expand=True, fill=tk.BOTH)
    note.view_tab.canvas.create_window((0, 0), window=note.view_tab.frm2, anchor=tk.NW)

    note.view_tab.canvas.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.view_tab.canvas))
    note.view_tab.frm2.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.view_tab.canvas))

    note.view_tab.frm2.widget = []

    col = 0
    row = 0
    brow = row
    col,row = color_label_widget_set(note.view_tab.frm2,note.view_tab.canvas,0,brow,2,1,'TX','TX')
    col,row = color_label_widget_set(note.view_tab.frm2,note.view_tab.canvas,col,brow,1,1,'RS','MENU')
    col,row = color_label_widget_set(note.view_tab.frm2,note.view_tab.canvas,col,brow,1,1,'BY','BUSY')

    brow = row
    col,nrow = label_widget_set(note.view_tab.frm2,note.view_tab.canvas,0,brow,4,2,'Times',24,'FA','MHz')
    bcol = col
    col,wrow = combobox_widget_set(note.view_tab.frm2,note.view_tab.canvas,bcol+1,brow,1,1,15,'BS','Band',combo_bandlists,bandlists)
    col,wrow = combobox_widget_set(note.view_tab.frm2,note.view_tab.canvas,bcol+1,wrow,1,1,10,'MD','Mode',['LSB','USB','CW-U','FM','AM','RTTY-LSB','CW-R','DATA-LSB','RTTY-USB','DATA-FM','FM-N','DATA-USB','AM-N','C4FM'],['1','2','3','4','5','6','7','8','9','A','B','C','D','E'])

    col,w2row = combobox_widget_set(note.view_tab.frm2,note.view_tab.canvas,bcol+3,brow,1,1,10,'PA','Pre AMP',['IPO','AMP 1','AMP 2'],['00','01','02'])

    col,wrow = vscale_widget_set(note.view_tab.frm2,note.view_tab.canvas,bcol+1,wrow+1,1,30,5,100,10,200,'PC','Power')

    bcol = col
    col,row = checkbutton_widget_set(note.view_tab.frm2,note.view_tab.canvas,bcol+3,brow,'AC0','Enable Tune')
    col,row = button_widget_set(note.view_tab.frm2,note.view_tab.canvas,bcol+3,brow+1,2,2,'AC2','Tune')

    row = nrow
    col,row = progressbar_widget_set(note.view_tab.frm2,note.view_tab.canvas,0,row,4,1,'SM')
    col,row = progressbar_widget_set(note.view_tab.frm2,note.view_tab.canvas,0,row,4,1,'PO')
    col,row = progressbar_widget_set(note.view_tab.frm2,note.view_tab.canvas,0,row,4,1,'ALC')
    col,row = progressbar_widget_set(note.view_tab.frm2,note.view_tab.canvas,0,row,4,1,'SWR')

#    col,wrow = hscale_widget_set(note.view_tab.frm2,note.view_tab.canvas,0,row,1,1,'PC','Power')

    pprint(note.view_tab.frm2.widget)

    note.view_tab.frm2.update_idletasks()
    note.view_tab.canvas.config(scrollregion=note.view_tab.canvas.bbox("all"))

def auto_information_thread(note,dummy):
    global Receiving
    global config

    try:
        port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))
        port.write(str.encode('AI1;'))

        while 1:
            if Receiving == 0:
                break
            data = port.read_all()
            if data != b'':
                sdata = data.decode(errors='ignore').split(';')
                print(sdata)
                for rdata in sdata:
                    for widget in note.auto_information_tab.frm2.widget:
                        if widget[0] == rdata[0:2]:
                            if len(data) > 2:
                                widget[6]['text'] = rdata[2:]
            time.sleep(0.5)

        port.write(str.encode('AI0;'))
        port.close()
    except serial.serialutil.SerialTimeoutException:
        pass

    return

def auto_information(note):
    global Receiving
    
    if note.auto_information_tab.frm1.button1['text'] == 'Start':
        Receiving = 1
        note.auto_information_tab.frm1.button1['text'] = 'Stop'
        th = threading.Thread(target=auto_information_thread, args=(note,''), daemon=True)
        th.start()
    else:
        Receiving = 0
        note.auto_information_tab.frm1.button1['text'] = 'Start'

    return

def auto_information_widget_set(frm,canvas,cmd,func,description):
    val = '000'
    widget = [cmd,func,val,description]
    row = len(frm.widget)
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=cmd))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=1, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=func + ': '))
    widget[len(widget)-1].grid(sticky=tk.W, row=row, column=2, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=val))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=3, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=description))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=4, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    frm.widget.append(widget)

def mouse_y_scroll(event,canvas):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def auto_information_tab_set(note):
    global root
    global config

    note.auto_information_tab = tk.Frame(note)
    note.add(note.auto_information_tab, text='Auto Information')

    note.auto_information_tab.frm1 = tk.Frame(note.auto_information_tab)
    note.auto_information_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.auto_information_tab.frm1.button1 = tk.Button(note.auto_information_tab.frm1, text="Start", command=lambda:auto_information(note))
    note.auto_information_tab.frm1.button1.pack(side = tk.LEFT)

    note.auto_information_tab.canvas = tk.Canvas(note.auto_information_tab)

    note.auto_information_tab.frm2 = tk.Frame(note.auto_information_tab.canvas)

    scrollbary = tk.Scrollbar(
        note.auto_information_tab.canvas, orient=tk.VERTICAL, command=note.auto_information_tab.canvas.yview
    )
    note.auto_information_tab.canvas.configure(yscrollcommand=scrollbary.set)
    scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbarx = tk.Scrollbar(
        note.auto_information_tab.canvas, orient=tk.HORIZONTAL, command=note.auto_information_tab.canvas.xview
    )
    note.auto_information_tab.canvas.configure(xscrollcommand=scrollbarx.set)
    scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)

    note.auto_information_tab.canvas.pack(expand=True, fill=tk.BOTH)
    note.auto_information_tab.canvas.create_window((0, 0), window=note.auto_information_tab.frm2, anchor=tk.NW)

    note.auto_information_tab.canvas.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.auto_information_tab.canvas))
    note.auto_information_tab.frm2.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.auto_information_tab.canvas))

    note.auto_information_tab.frm2.widget = []

    for catcmd in catcmds:
#        print(catcmd)
        if catcmd[7] == 1:
            auto_information_widget_set(note.auto_information_tab.frm2,note.auto_information_tab.canvas,catcmd[0],catcmd[1],catcmd[3])

    note.auto_information_tab.frm2.update_idletasks()
    note.auto_information_tab.canvas.config(scrollregion=note.auto_information_tab.canvas.bbox("all"))

def com_port_setting_tab_set(note):
    global root
    global config
    global devices
    global descriptions

    note.com_port_setting_tab = tk.Frame(note)
    note.add(note.com_port_setting_tab, text='Com Port Setting')

    note.com_port_setting_tab.frm1 = tk.Frame(note.com_port_setting_tab)
    note.com_port_setting_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.com_port_setting_tab.frm1.label1r0 = ttk.Label(note.com_port_setting_tab.frm1, text='Rig ')
    note.com_port_setting_tab.frm1.label1r0.grid(row=0, column=1, ipadx=1)
    note.com_port_setting_tab.frm1.label1r1 = ttk.Label(note.com_port_setting_tab.frm1, text='Serial Device: ')
    note.com_port_setting_tab.frm1.label1r1.grid(row=1, column=2, ipadx=1)

    note.com_port_setting_tab.frm1.combobox1r1 = ttk.Combobox(note.com_port_setting_tab.frm1,width=40)
    note.com_port_setting_tab.frm1.combobox1r1['values'] = descriptions
    note.com_port_setting_tab.frm1.combobox1r1.grid(row=1, column=3, ipadx=1)
    rig_serialdevice = config['rig']['serialdevice']
    if rig_serialdevice in devices:
        note.com_port_setting_tab.frm1.combobox1r1.current(devices.index(rig_serialdevice))
    else:
        note.com_port_setting_tab.frm1.combobox1r1.current(0)

    note.com_port_setting_tab.frm1.label1r2 = ttk.Label(note.com_port_setting_tab.frm1, text='Baud Rate: ')
    note.com_port_setting_tab.frm1.label1r2.grid(row=1, column=5, ipadx=1)

    note.com_port_setting_tab.frm1.combobox1r2 = ttk.Combobox(note.com_port_setting_tab.frm1,width=10)
    note.com_port_setting_tab.frm1.combobox1r2['values'] = baudrate
    note.com_port_setting_tab.frm1.combobox1r2.grid(row=1, column=6, ipadx=1)
    rig_baudrate = int(config['rig']['baudrate'])
    if rig_baudrate in baudrate:
        note.com_port_setting_tab.frm1.combobox1r2.current(baudrate.index(rig_baudrate))
    else:
        note.com_port_setting_tab.frm1.combobox1r2.current(0)

    note.com_port_setting_tab.frm1.label1c0 = ttk.Label(note.com_port_setting_tab.frm1, text='com0com ')
    note.com_port_setting_tab.frm1.label1c0.grid(row=10, column=1, ipadx=1)
    
    note.com_port_setting_tab.frm1.label1c1 = ttk.Label(note.com_port_setting_tab.frm1, text='Serial Device: ')
    note.com_port_setting_tab.frm1.label1c1.grid(row=11, column=2, ipadx=1)

    note.com_port_setting_tab.frm1.combobox1c1 = ttk.Combobox(note.com_port_setting_tab.frm1,width=40)
    note.com_port_setting_tab.frm1.combobox1c1['values'] = descriptions
    note.com_port_setting_tab.frm1.combobox1c1.grid(row=12, column=3, ipadx=1)
    com0com_serialdevice = config['com0com']['serialdevice']
    if com0com_serialdevice in devices:
        note.com_port_setting_tab.frm1.combobox1c1.current(devices.index(com0com_serialdevice))
    else:
        note.com_port_setting_tab.frm1.combobox1c1.current(0)

    note.com_port_setting_tab.frm1.button1 = tk.Button(note.com_port_setting_tab.frm1, text="保存", command=lambda:saveconfig(note))
    note.com_port_setting_tab.frm1.button1.grid(row=21, column=30, ipadx=1, ipady=1)

def cw_setting(note):
    global root
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
                pprint(data)
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
                pprint(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)


    port.close()
    
    messagebox.showinfo('Setting', '設定しました')
    
    return

def cw_setting_tab_set(note):
    global root
    global config

    note.cw_setting_tab = tk.Frame(note)
    note.add(note.cw_setting_tab, text='CW Setting')

    note.cw_setting_tab.frm1 = tk.Frame(note.cw_setting_tab)
    note.cw_setting_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.cw_setting_tab.frm1.button1 = tk.Button(note.cw_setting_tab.frm1, text="Set", command=lambda:cw_setting(note))
    note.cw_setting_tab.frm1.button1.pack(side = tk.LEFT)

    note.cw_setting_tab.canvas = tk.Canvas(note.cw_setting_tab)

    note.cw_setting_tab.frm2 = tk.Frame(note.cw_setting_tab.canvas)

    scrollbary = tk.Scrollbar(
        note.cw_setting_tab.canvas, orient=tk.VERTICAL, command=note.cw_setting_tab.canvas.yview
    )
    note.cw_setting_tab.canvas.configure(yscrollcommand=scrollbary.set)
    scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbarx = tk.Scrollbar(
        note.cw_setting_tab.canvas, orient=tk.HORIZONTAL, command=note.cw_setting_tab.canvas.xview
    )
    note.cw_setting_tab.canvas.configure(xscrollcommand=scrollbarx.set)
    scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)

    note.cw_setting_tab.canvas.pack(expand=True, fill=tk.BOTH)
    note.cw_setting_tab.canvas.create_window((0, 0), window=note.cw_setting_tab.frm2, anchor=tk.NW)

    note.cw_setting_tab.canvas.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.cw_setting_tab.canvas))
    note.cw_setting_tab.frm2.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.cw_setting_tab.canvas))

    note.cw_setting_tab.frm2.widget = []

    for catcmd in cw_setting_cmd:
        ft8_cw_rtty_setting_widget_set(note.cw_setting_tab.frm2,note.cw_setting_tab.canvas,catcmd)

    widget = ['','','','']
    row = len(note.cw_setting_tab.frm2.widget)
    widget.append(ttk.Label(note.cw_setting_tab.frm2, justify=tk.LEFT, text=''))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=1, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    note.cw_setting_tab.frm2.widget.append(widget)

    for catcmd in ft8_cw_rtty_setting_cmd:
        ft8_cw_rtty_setting_widget_set(note.cw_setting_tab.frm2,note.cw_setting_tab.canvas,catcmd)

    note.cw_setting_tab.frm2.update_idletasks()
    note.cw_setting_tab.canvas.config(scrollregion=note.cw_setting_tab.canvas.bbox("all"))
    


def rtty_setting(note):
    global root
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
                pprint(data)
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
                pprint(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)
    port.close()
    
    messagebox.showinfo('Setting', '設定しました')
    
    return

def rtty_setting_tab_set(note):
    global root
    global config

    note.rtty_setting_tab = tk.Frame(note)
    note.add(note.rtty_setting_tab, text='RTTY Setting')

    note.rtty_setting_tab.frm1 = tk.Frame(note.rtty_setting_tab)
    note.rtty_setting_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.rtty_setting_tab.frm1.button1 = tk.Button(note.rtty_setting_tab.frm1, text="Set", command=lambda:rtty_setting(note))
    note.rtty_setting_tab.frm1.button1.pack(side = tk.LEFT)

    note.rtty_setting_tab.canvas = tk.Canvas(note.rtty_setting_tab)

    note.rtty_setting_tab.frm2 = tk.Frame(note.rtty_setting_tab.canvas)

    scrollbary = tk.Scrollbar(
        note.rtty_setting_tab.canvas, orient=tk.VERTICAL, command=note.rtty_setting_tab.canvas.yview
    )
    note.rtty_setting_tab.canvas.configure(yscrollcommand=scrollbary.set)
    scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbarx = tk.Scrollbar(
        note.rtty_setting_tab.canvas, orient=tk.HORIZONTAL, command=note.rtty_setting_tab.canvas.xview
    )
    note.rtty_setting_tab.canvas.configure(xscrollcommand=scrollbarx.set)
    scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)

    note.rtty_setting_tab.canvas.pack(expand=True, fill=tk.BOTH)
    note.rtty_setting_tab.canvas.create_window((0, 0), window=note.rtty_setting_tab.frm2, anchor=tk.NW)

    note.rtty_setting_tab.canvas.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.rtty_setting_tab.canvas))
    note.rtty_setting_tab.frm2.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.rtty_setting_tab.canvas))

    note.rtty_setting_tab.frm2.widget = []

    for catcmd in rtty_setting_cmd:
        ft8_cw_rtty_setting_widget_set(note.rtty_setting_tab.frm2,note.rtty_setting_tab.canvas,catcmd)

    widget = ['','','','']
    row = len(note.rtty_setting_tab.frm2.widget)
    widget.append(ttk.Label(note.rtty_setting_tab.frm2, justify=tk.LEFT, text=''))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=1, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    note.rtty_setting_tab.frm2.widget.append(widget)

    for catcmd in ft8_cw_rtty_setting_cmd:
        ft8_cw_rtty_setting_widget_set(note.rtty_setting_tab.frm2,note.rtty_setting_tab.canvas,catcmd)

    note.rtty_setting_tab.frm2.update_idletasks()
    note.rtty_setting_tab.canvas.config(scrollregion=note.rtty_setting_tab.canvas.bbox("all"))
    

def ft8_setting(note):
    global root
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
    
    messagebox.showinfo('Setting', '設定しました')
    
    return

def ft8_setting_tab_set(note):
    global root
    global config

    note.ft8_setting_tab = tk.Frame(note)
    note.add(note.ft8_setting_tab, text='FT8 Setting')

    note.ft8_setting_tab.frm1 = tk.Frame(note.ft8_setting_tab)
    note.ft8_setting_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.ft8_setting_tab.frm1.button1 = tk.Button(note.ft8_setting_tab.frm1, text="Set", command=lambda:ft8_setting(note))
    note.ft8_setting_tab.frm1.button1.pack(side = tk.LEFT)

    note.ft8_setting_tab.canvas = tk.Canvas(note.ft8_setting_tab)

    note.ft8_setting_tab.frm2 = tk.Frame(note.ft8_setting_tab.canvas)

    scrollbary = tk.Scrollbar(
        note.ft8_setting_tab.canvas, orient=tk.VERTICAL, command=note.ft8_setting_tab.canvas.yview
    )
    note.ft8_setting_tab.canvas.configure(yscrollcommand=scrollbary.set)
    scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbarx = tk.Scrollbar(
        note.ft8_setting_tab.canvas, orient=tk.HORIZONTAL, command=note.ft8_setting_tab.canvas.xview
    )
    note.ft8_setting_tab.canvas.configure(xscrollcommand=scrollbarx.set)
    scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)

    note.ft8_setting_tab.canvas.pack(expand=True, fill=tk.BOTH)
    note.ft8_setting_tab.canvas.create_window((0, 0), window=note.ft8_setting_tab.frm2, anchor=tk.NW)

    note.ft8_setting_tab.canvas.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.ft8_setting_tab.canvas))
    note.ft8_setting_tab.frm2.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.ft8_setting_tab.canvas))

    note.ft8_setting_tab.frm2.widget = []

    for catcmd in ft8_setting_cmd:
        ft8_cw_rtty_setting_widget_set(note.ft8_setting_tab.frm2,note.ft8_setting_tab.canvas,catcmd)

    widget = ['','','','']
    row = len(note.ft8_setting_tab.frm2.widget)
    widget.append(ttk.Label(note.ft8_setting_tab.frm2, justify=tk.LEFT, text=''))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=1, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    note.ft8_setting_tab.frm2.widget.append(widget)

    for catcmd in ft8_cw_rtty_setting_cmd:
        ft8_cw_rtty_setting_widget_set(note.ft8_setting_tab.frm2,note.ft8_setting_tab.canvas,catcmd)

    note.ft8_setting_tab.frm2.update_idletasks()
    note.ft8_setting_tab.canvas.config(scrollregion=note.ft8_setting_tab.canvas.bbox("all"))
    
def ft8_cw_rtty_setting(note):
    global root
    global config
    global devices
    global descriptions

    port = comopen(config['rig']['serialdevice'],int(config['rig']['baudrate']))

    for catcmd in ft8_cw_rtty_setting_cmd:
        try:
            port.write(str.encode(catcmd[0]+catcmd[1]+';'))
            data = port.read_all()
            if data != b'':
                pprint(data)
        except serial.serialutil.SerialTimeoutException:
            pass
        time.sleep(0.1)

    port.close()
    
    messagebox.showinfo('Setting', '設定しました')
    
    return

def ft8_cw_rtty_setting_widget_set(frm,canvas,catcmd):
    widget = catcmd
    row = len(frm.widget)
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=catcmd[3]))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=1, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=catcmd[0]))
    widget[len(widget)-1].grid(sticky=tk.W, row=row, column=2, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=catcmd[1]))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=3, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    widget.append(ttk.Label(frm, justify=tk.LEFT, text=catcmd[2]))
    widget[len(widget)-1].grid(sticky=tk.W,row=row, column=4, ipadx=1)
    widget[len(widget)-1].bind("<MouseWheel>", lambda event: mouse_y_scroll(event, canvas))
    frm.widget.append(widget)

def ft8_cw_rtty_setting_tab_set(note):
    global root
    global config

    note.ft8_cw_rtty_setting_tab = tk.Frame(note)
    note.add(note.ft8_cw_rtty_setting_tab, text='FT8 CW RTTY Setting')

    note.ft8_cw_rtty_setting_tab.frm1 = tk.Frame(note.ft8_cw_rtty_setting_tab)
    note.ft8_cw_rtty_setting_tab.frm1.pack(side = tk.TOP, fill=tk.BOTH)

    note.ft8_cw_rtty_setting_tab.frm1.button1 = tk.Button(note.ft8_cw_rtty_setting_tab.frm1, text="Set", command=lambda:ft8_cw_rtty_setting(note))
    note.ft8_cw_rtty_setting_tab.frm1.button1.pack(side = tk.LEFT)

    note.ft8_cw_rtty_setting_tab.canvas = tk.Canvas(note.ft8_cw_rtty_setting_tab)

    note.ft8_cw_rtty_setting_tab.frm2 = tk.Frame(note.ft8_cw_rtty_setting_tab.canvas)

    scrollbary = tk.Scrollbar(
        note.ft8_cw_rtty_setting_tab.canvas, orient=tk.VERTICAL, command=note.ft8_cw_rtty_setting_tab.canvas.yview
    )
    note.ft8_cw_rtty_setting_tab.canvas.configure(yscrollcommand=scrollbary.set)
    scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbarx = tk.Scrollbar(
        note.ft8_cw_rtty_setting_tab.canvas, orient=tk.HORIZONTAL, command=note.ft8_cw_rtty_setting_tab.canvas.xview
    )
    note.ft8_cw_rtty_setting_tab.canvas.configure(xscrollcommand=scrollbarx.set)
    scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)

    note.ft8_cw_rtty_setting_tab.canvas.pack(expand=True, fill=tk.BOTH)
    note.ft8_cw_rtty_setting_tab.canvas.create_window((0, 0), window=note.ft8_cw_rtty_setting_tab.frm2, anchor=tk.NW)

    note.ft8_cw_rtty_setting_tab.canvas.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.ft8_cw_rtty_setting_tab.canvas))
    note.ft8_cw_rtty_setting_tab.frm2.bind("<MouseWheel>", lambda event: mouse_y_scroll(event, note.ft8_cw_rtty_setting_tab.canvas))

    note.ft8_cw_rtty_setting_tab.frm2.widget = []

    for catcmd in ft8_cw_rtty_setting_cmd:
#        print(catcmd)
        ft8_cw_rtty_setting_widget_set(note.ft8_cw_rtty_setting_tab.frm2,note.ft8_cw_rtty_setting_tab.canvas,catcmd)

    note.ft8_cw_rtty_setting_tab.frm2.update_idletasks()
    note.ft8_cw_rtty_setting_tab.canvas.config(scrollregion=note.ft8_cw_rtty_setting_tab.canvas.bbox("all"))

def main():
    global root
    global config
    global devices
    global descriptions
#    global style

    devices = []
    descriptions = []
    comlist(devices,descriptions)

    config = configparser.ConfigParser()
    config.read_dict(default_configs)
    config.read(config_file)

    root = tk.Tk() 
#    root = ThemedTk() 
    root.title("FT-991 Control")
    root.geometry(config['win']['geometry'])
#    style = ttk.Style()
#    style.theme_use('arc')
#    style.configure("GREEN.Horizontal.TProgressbar", background='green')
#    style.configure("SWR.Horizontal.TProgressbar", background='green')
    note = ttk.Notebook(root)

    view_tab_set(note)
    dump_tab_set(note)
    auto_information_tab_set(note)
    ft8_setting_tab_set(note)
    cw_setting_tab_set(note)
    rtty_setting_tab_set(note)
    ft8_cw_rtty_setting_tab_set(note)
    com_port_setting_tab_set(note)

    note.pack(fill=tk.BOTH, expand=True)

    root.bind("<Configure>", get_geometry_info)
    root.mainloop()

if __name__ == "__main__":
    main()
