# coding=utf-8
#!/usr/bin/python
# Created on 2018-03-20 10:29
# @author: Administrator
# @name: GenTextGridFromMonolab.py
# @info:  从monolab生成TextGrid

from TextGrid import TextGrid, Interval, Tier
import wave
import os
import re

def getIntervalListFromMonolab(input_monolab_file):
    fr = open(input_monolab_file, 'r', encoding = 'utf-8')
    in_list = fr.readlines()
    phon_intervals = {}
    index = 1
    for i in range(len(in_list)):
        tmp_array = re.split(" |\t", in_list[i].strip())
        tmp_array = [item for item in filter(lambda x: x != '', tmp_array)]
        try:
            phon_intervals[index] = Interval(index, tmp_array[0], tmp_array[1], tmp_array[2])
            index += 1
        except IndexError as e:
            print(str(e) + in_list[i].strip() + "\t" + input_monolab_file)
            exit(0)
    return phon_intervals

def getIntervalListFromProsodyPhonLine(prosody_phon_line):
    """韵律文本的读音行，分隔成音节和读音的序列"""
    symbols = ["(L-L%)", "silv"]
    for sym in symbols:
        prosody_phon_line = prosody_phon_line.replace(sym, "")
    prosody_phon_line = prosody_phon_line.replace("/", "]/[")
    syllables = re.split("\#|\/|\[|\]", prosody_phon_line)
    syllables = [item for item in filter(lambda x: x != '', syllables)]
    syllables_noTone = []
    for syl in syllables:
        syllables_noTone.append(syl[0:-2])
    return syllables, syllables_noTone

def getIntervalListFromProsodyWordLine(prosody_word_line):
    sarray = re.split(" |\/|\[|\]", prosody_word_line)
    sarray = [item for item in filter(lambda x: x != '', sarray)]
    biaodian = ["，", "：", "。", "、", "？", "；", "！", "【", "】", "《", "》", "", "”", "“", '—', "-", "?", ";", "…", "(", ")"]
    special_file = open(r'E:\005_others\01_ShangHai\003_News\002_Prosody_20180319_null.txt', 'r', encoding = 'utf-8')
    special_list = special_file.readlines()
    newWord = []
    i = 0
    while i < len(sarray):
        next_word = ""
        if i != len(sarray) - 1:
            next_word = sarray[i + 1]
        cur_word = sarray[i]
        if cur_word + "\n" in special_list:
            if next_word in biaodian:
                cur_word += next_word
                i = i + 1
            newWord.append(cur_word + "1")
        else:
            for j in range(len(cur_word)):
                tmp_cur_word = cur_word[j]
                if j == len(cur_word) - 1:
                    if next_word in biaodian:
                        tmp_cur_word += next_word
                        i = i + 1
                    tmp_cur_word += "1"
                newWord.append(tmp_cur_word)
        i = i + 1
    return newWord

def initialWordIntervalTime(word_interval_list, syllable_interval_list, syllable_interval_no_tone_list, input_monolab_file):
    fr = open(input_monolab_file, 'r', encoding = 'utf-8')
    input_list = fr.readlines()
    phon_intervals = []
    word_intervals = []
    break_intervals = []
    #mono_index = 1
    syll_index = 0
    tmp_mono_syl_name = ""
    break_name = ""
    tmp_word_begin = 0
    tmp_phon_end = 0
    i = 0
    while i < len(input_list):
        tmp_array = re.split(" |\t", input_list[i].strip())
        tmp_array = [item for item in filter(lambda x: x != '', tmp_array)]
        tmp_phon_end = tmp_array[1]
        tmp_next_array = []
        if i != len(input_list) - 1:
            tmp_next_array = re.split(" |\t", input_list[i + 1].strip())
            tmp_next_array = [item for item in filter(lambda x: x != '', tmp_next_array)]
        try:
            if tmp_array[2] not in ["sil", "silv"]:
                tmp_mono_syl_name += tmp_array[2] + " "
            if tmp_mono_syl_name.strip() == syllable_interval_no_tone_list[syll_index]:
                phon_intervals.append(Interval((i + 1), getFloat(tmp_array[0]), getFloat(tmp_phon_end), tmp_array[2] + syllable_interval_list[syll_index][-2:len(syllable_interval_list)]))
                if tmp_next_array[2] in ["sil", "silv"]:
                    tmp_phon_end = tmp_next_array[1]
                    if tmp_next_array[2] == "sil":
                        break_name = "4"
                    if tmp_next_array[2] == "silv":
                        break_name = "3" 
                    i += 1
                    tmp_sil_array = re.split(" |\t", input_list[i].strip())
                    tmp_sil_array = [item for item in filter(lambda x: x != '', tmp_sil_array)]
                    phon_intervals.append(Interval((i + 1), getFloat(tmp_sil_array[0]), getFloat(tmp_sil_array[1]), tmp_sil_array[2]))
                    #mono_index += 1
                cur_word_name = word_interval_list[syll_index]
                if cur_word_name[-1] == "1":
                    cur_word_name = cur_word_name[0:-1]
                    if break_name == "":
                        break_name = "1"
                word_intervals.append(Interval((syll_index + 1), getFloat(tmp_word_begin), getFloat(tmp_phon_end), cur_word_name))
                break_intervals.append(Interval((syll_index + 1), getFloat(tmp_word_begin), getFloat(tmp_phon_end), break_name))
                syll_index += 1
                tmp_word_begin = tmp_phon_end
                tmp_mono_syl_name = ""
                break_name = ""
            else:
                phon_intervals.append(Interval((i + 1), getFloat(tmp_array[0]), getFloat(tmp_phon_end), tmp_array[2]))
            #mono_index += 1
        except IndexError as e:
            print(str(e) + "\t" + input_list[i].strip() + "\t" + input_monolab_file)
            exit(0)
        i = i + 1
    return phon_intervals, word_intervals, break_intervals

def setToneInterval(phon_intervals):
    """根据第一层是否有停顿，增加边界调"""
    result_intervals = []
    for i in range(len(phon_intervals)):
        next_interval_name = ""
        if i != len(phon_intervals) - 1:
            next_interval_name = phon_intervals[i + 1].name
        if next_interval_name in ["sil", "silv"]:
            result_intervals.append(Interval(phon_intervals[i].index, phon_intervals[i].begin, phon_intervals[i].end, "L-L%"))
        else:
            result_intervals.append(Interval(phon_intervals[i].index, phon_intervals[i].begin, phon_intervals[i].end, ""))
    return result_intervals

def setBreakInterval(phon_intervals):
    """根据第一层是否有停顿，增加边界调"""
    result_intervals = []
    for i in range(len(phon_intervals)):
        next_interval_name = ""
        if i != len(phon_intervals) - 1:
            next_interval_name = phon_intervals[i + 1].name
        if next_interval_name in ["sil", "silv"]:
            result_intervals.append(Interval(phon_intervals[i].index, phon_intervals[i].begin, phon_intervals[i].end, "L-L%"))
        else:
            result_intervals.append(Interval(phon_intervals[i].index, phon_intervals[i].begin, phon_intervals[i].end, ""))
    return result_intervals

def getBlankTiers(input_intervals):
    result_intervals = []
    for i in range(len(input_intervals)):
        result_intervals.append(Interval(input_intervals[i].index, input_intervals[i].begin, input_intervals[i].end, ""))
    return result_intervals

def getFloat(input_str):
    return str(float(input_str) / 10000000)
        
input_file = r'E:\005_others\01_ShangHai\003_News\002_Prosody_20180319.txt'
wav_path = r'E:\005_others\01_ShangHai\003_News\wav'
monolab_path = r'E:\005_others\01_ShangHai\003_News\monolabInitialAlign'
textgrid_path = r'E:\005_others\01_ShangHai\003_News\TextGrid_news_Initial' #输出

# 如果目录不存在，创建输出目录
if not os.path.exists(textgrid_path):
    os.makedirs(textgrid_path)

f = open(input_file, 'r', encoding = 'utf-8')
lines = f.readlines()
lineNum = len(lines)
tones = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

for i in range(0, len(lines), 3):
    fileName = lines[i].strip()
    print('Processing ' + fileName)
    monolab_file = os.path.join(monolab_path, fileName + ".lab")
    wav_file = os.path.join(wav_path, fileName + ".wav")
    textgrid_file = os.path.join(textgrid_path, fileName + ".TextGrid")
    if os.path.exists(wav_file) and os.path.exists(monolab_file):
        #fw = open(textgrid_file, 'w', encoding = 'utf-8')
        wavefile = wave.open(wav_file, 'r')
        framerate = wavefile.getframerate()
        numframes = wavefile.getnframes()
        duration = float(numframes) / float(framerate)
        word_list = getIntervalListFromProsodyWordLine(lines[i + 1].strip())
        syllable_phons_list, syllable_phons_no_tone_list = getIntervalListFromProsodyPhonLine(lines[i + 2].strip())
        if len(word_list) != len(syllable_phons_list):
            print("hello")
            exit(0)
        phons, words, breaks = initialWordIntervalTime(word_list, syllable_phons_list, syllable_phons_no_tone_list, monolab_file)
        phons[-1].end = duration
        words[-1].end = duration
        result_tiers = {}
        result_tiers[1] = Tier(None, "Phon", phons)
        result_tiers[2] = Tier(None, "Tone", setToneInterval(phons))
        result_tiers[3] = Tier(None, "Word", words)
        result_tiers[4] = Tier(None, "Break", breaks)
        tg = TextGrid(textgrid_file)
        tg.write_new(4, duration, result_tiers)
f.close()