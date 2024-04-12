from PIL import Image, ImageOps, ImageEnhance, ImageGrab, ImageFilter
from pytesseract import *
import json
import time
import os, sys

# Given screenshot of EXP Region, extract current xp value
def getCurrentEXP(sc):

    path_to_tesseract = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    #Point tessaract_cmd to tessaract.exe
    pytesseract.tesseract_cmd = path_to_tesseract

    # blow up image for easier OCR
    sc = sc.resize((s*3 for s in sc.size)) # 3x image
    #sc = ImageOps.invert(sc)
    #sc = (ImageEnhance.Sharpness(sc)).enhance(5)

    # This should help with getting 8 and 9 mixed up
    thresh = 160
    fn = lambda x : 255 if x > thresh else 0
    r = sc.convert('L').point(fn, mode='1')
    r = ImageOps.invert(r)
    r.save('temp.jpg')

    #Extract text from image
    currentXP = pytesseract.image_to_string(Image.open('temp.jpg'), config="-c tessedit_char_whitelist=0123456789()[]S --psm 7")

    currentXP = currentXP.replace('S','5') # 5 and S look similar, we want numbers only
    idxParen = currentXP.find('(')
    idxBrack = currentXP.find('[')
    rawXPNumber = ''
    if idxParen != -1:
        rawXPNumber = currentXP[:idxParen]
    else:
        rawXPNumber = currentXP[:idxBrack]
    
    return rawXPNumber

def capture_screenshot():
    
    sc = ImageGrab.grab()
    scEXP = crop_screenshot(sc)
    return scEXP

def crop_screenshot(sc):

    w,h = sc.size # 2560, 1440
    # custom values below for 2k monitor, and application scaled to fullscreen
    # left, top, right, bottom
    expArea = sc.crop((w*.464 , h*.957, w*.695, h*.972))

    return expArea

def calculate(start_exp, cur_exp, timeElapsed, previousEXPGained):

    print(cur_exp)
    xp_per_hour = 0
    exp_gained = int(cur_exp) - int(start_exp)

    # Keep track of previous number
    # If new difference is at least 1 digit larger, skip calculation cause tesseract read image wrong
    if previousEXPGained == 0:
        print('First iteration ..')
    elif exp_gained > previousEXPGained*10:
        print('Ignore ..')
    else:
        xp_per_hour = exp_gained * (3600/timeElapsed)
        #print('Gained {} Total XP'.format(exp_gained))
        #print(f"Rate : {xp_per_hour:,}/hr")
    
    return exp_gained, xp_per_hour

def printInfo(secs, exp_gained, xp_per_hour, currentXP, totalXPToLvl, timeElapsed):
    for i in range(secs):
        os.system('cls')
        currentPercent = round((currentXP/totalXPToLvl)*100,2)
        rateInPercent = round((xp_per_hour/totalXPToLvl)*100,2)

        print(f"Current XP : {currentXP:,} ({currentPercent}%)")
        # print(f"Cumulative XP : {exp_gained:,}")
        print()
        print(f"Rate : {int(xp_per_hour):,}/hr ({rateInPercent}%)")
        print()
        print(f"Elapsed Time : {round(timeElapsed/60,1)} mins")
        print('Next Scan : {}'.format(secs-i))
        print()
        time.sleep(1)

def main():
    # Obtain screenshot of game
    # Crop out EXP region of SS
    # Run cropped img through OCR
    # Obtain current EXP number
    
    CURR_LVL = 119 
    POLLING_RATE = 5

    with open('./xptable.json', 'r') as f:
        xpTable = json.load(f)
        totalXPToLvl = xpTable[str(CURR_LVL)]
        f.close()

    print('Current Lvl : {} \nNeed {} Total XP to Level\n'.format(CURR_LVL, totalXPToLvl))

    time.sleep(3) # allow 3 seconds to switch windows
    
    startXP = 0
    currentXP = 0
    timeElapsed = 0
    previousEXPGained = 0
    try:
        while True:
            # Start timer
            scEXP = capture_screenshot()
            if startXP == 0 and startXP < totalXPToLvl: # Run this conditional only once at start to initialize
                startXP = getCurrentEXP(scEXP)
            else:
                currentXP = getCurrentEXP(scEXP)
                if currentXP.isdigit():
                    previousEXPGained, xp_per_hour = calculate(startXP, currentXP, timeElapsed, previousEXPGained)
                    printInfo(POLLING_RATE, previousEXPGained, xp_per_hour, int(currentXP), int(totalXPToLvl), timeElapsed)
            timeElapsed += POLLING_RATE

    except KeyboardInterrupt:
        sys.exit(0)

main()