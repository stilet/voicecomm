#!/usr/bin/env python3

import argparse
import os
import queue
import sounddevice as sd
import vosk
import winsound
# Leo
import json
import csv
from AutoHotPy import AutoHotPy

frequency = 2500  # Set Frequency To 2500 Hertz
frequencyBad = 500  # Set Frequency To 2500 Hertz
duration = 200  # Set Duration To 1000 ms == 1 second
durationBad = 250  # Set Duration To 1000 ms == 1 second

q = queue.Queue()

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        pass
        # print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    # print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-f', '--filename', type=str, metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-m', '--model', type=str, metavar='MODEL_PATH',
    help='Path to the model')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate')
args = parser.parse_args(remaining)

try:
    if args.model is None:
        args.model = "models/vosk-model-small-ru-0.22"
    if not os.path.exists(args.model):
        print ("Please download a model for your language from https://alphacephei.com/vosk/models")
        print ("and unpack as 'model' in the current folder.")
        parser.exit(0)
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])
    # храним команды как ключи и клавиши как список
    key_dict = {}
    with open("key.csv", encoding='utf-8') as r_file:
        file_reader = csv.reader(r_file, delimiter = ";")
        for row in file_reader:
            # print(row)
            if row[0] == 'key1':
                continue
            tup = (row[0],row[1], row[2], row[3])
            # убираем двойные и тройные пробелы
            new_str = row[4].replace('\xa0', ' ').replace('  ', ' ').replace('   ', ' ').strip()
            key_dict[new_str] = tup
    
    auto = AutoHotPy()

    model = vosk.Model(args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device, dtype='int16',
                            channels=1, callback=callback):

            rec = vosk.KaldiRecognizer(model, args.samplerate)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    print('Ожидание', res['text'])
                    if res['text'] == '':
                        pass
                    else:
                        if res['text'] in key_dict:
                            winsound.Beep(frequency, duration)
                            for item in key_dict[res['text']]:
                                if item != '':
                                    # почему то добавляются пробелы
                                    new_item = item.strip()
                                    if hasattr(auto, new_item):
                                        klav = getattr(auto, new_item)
                                        klav.press()
                        else:
                            winsound.Beep(frequencyBad, durationBad)                 
                if dump_fn is not None:
                    dump_fn.write(data)

except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
