# -*- coding: utf-8 -*-
"""
Created on Friday April 2, 2021

@author: emmabarash
"""

# -*- coding: utf-8 -*-
"""
Created on Friday April 2, 2021

@author: emmabarash 
"""
import time
import multiprocessing as mp
import RPi.GPIO as GPIO
import os
import datetime
import random
#import pygame

class nosePoke:
        def __init__(self,light, beam, name):
                self.light = light
                self.beam = beam
                self.name = name
                self.endtime = time.time()+1200
                GPIO.setup(self.light,GPIO.OUT)
                GPIO.setup(self.beam,GPIO.IN)

        def shutdown(self):
                print("blink shutdown")
                self.exit.set()
                
        def flash_on(self):
                GPIO.output(self.light,1)
                
        def flash_off(self):
                GPIO.output(self.light,0)
                
        def flash(self, Hz, run):
                while time.time() < self.endtime:
                        if run.value == 1:
                                GPIO.output(self.light,1)
                        if run.value == 1:
                                time.sleep(2/Hz)
                                GPIO.output(self.light,0)
                        if run.value == 1:
                                time.sleep(2/Hz)
                        if run.value == 0:
                                GPIO.output(self.light,0)
                        if run.value == 2:
                                GPIO.output(self.light,1)
        
        def is_crossed(self):
                return GPIO.input(self.beam) == 0
                                
        def keep_out(self,wait):
                start = time.time()
                while time.time() < self.endtime:         
                    if self.is_crossed():
                            start = time.time()
                    elif time.time()-start > wait:
                            break                
        def kill(self):
                GPIO.output(self.light,0)
                
class trigger(nosePoke):
        def __init__(self, light, beam, name):
                nosePoke.__init__(self, light, beam, name)
                GPIO.add_event_detect(self.beam, GPIO.FALLING)
                #self.tone = pygame.mixer.Sound('pink_noise.wav')
        def playTone(self):
                os.system('omxplayer --loop pink_noise.mp3 &')
        def killTone(self):
                os.system('killall omxplayer.bin')

class taste_line:
        def __init__(self,valve,intanOut,tone):
                self.valve = valve
                self.intanOut = intanOut
                #self.tone = pygame.mixer.Sound(tone)
                self.tone = tone
                self.opentime = 0.05  
                self.endtime = time.time()+1200
                GPIO.setup(self.valve,GPIO.OUT)
                GPIO.setup(self.intanOut,GPIO.OUT)
                
        def playTone(self):
                #self.tone.play(-1)
                os.system('omxplayer --loop '+self.tone+' &')
        def killTone(self):
                os.system('killall omxplayer.bin')
        def clearout(self):
                dur = input("enter a clearout time to start clearout, or enter '0' to cancel: ")
                if dur == 0:
                        print("clearout canceled")
                        return
                GPIO.output(self.valve, 1)
                time.sleep(dur)
                GPIO.output(self.valve, 0)
                print('Tastant line clearing complete.')
                
        def calibrate(self):
                opentime = input("enter an opentime (like 0.05) to start calibration: ")
                
                while True:
                        # Open ports  
                        for rep in range(5):
                                GPIO.output(self.valve, 1)
                                time.sleep(opentime)
                                GPIO.output(self.valve, 0)
                                time.sleep(3)
        
                        ans = raw_input('keep this calibration? (y/n)')
                        if ans == 'y':
                                self.opentime = opentime
                                print("opentime saved")
                                break
                        else:
                                opentime = input('enter new opentime:')
        def deliver(self):
                GPIO.output(self.valve, 1)
                GPIO.output(self.intanOut, 1)
                time.sleep(self.opentime)
                GPIO.output(self.valve, 0)
                GPIO.output(self.intanOut, 0)
        
        def kill(self):
                GPIO.output(self.valve, 0)
                GPIO.output(self.intanOut, 0)
                
        def isOpen(self):
                return GPIO.input(self.valve)
        
def cuedtaste():
        anID = raw_input("enter animal ID: ")
        runtime = input("enter runtime in minutes: ")
        starttime = time.time()
        endtime = starttime+runtime*60
        rew.endtime = endtime
        trig.endtime = endtime
        iti = 5
        wait = 1
        Hz = 3.9
        crosstime = 10
        
        rewRun = mp.Value("i", 0)
        trigRun = mp.Value("i", 0)
        
        rewFlash = mp.Process(target = rew.flash, args = (Hz, rewRun,))
        trigFlash = mp.Process(target = trig.flash, args = (Hz, trigRun,))
        recording = mp.Process(target = record, args = (rew,trig,lines,starttime,endtime,anID,))
        
        rewFlash.start()
        trigFlash.start()
        recording.start()
        
        state = 0
        while time.time() < endtime:
                while state == 0: #state 0: initialize/prime trigger
                        rewKeep_out = mp.Process(target = rew.keep_out, args = (iti,))
                        trigKeep_out = mp.Process(target = trig.keep_out, args = (iti,))
                        rewKeep_out.start()
                        trigKeep_out.start()
                        
                        line = random.randint(0,3) #select random taste
                        rewKeep_out.join()
                        trigKeep_out.join()
                        trig.playTone()
                        trigRun.value = 1
                        state = 1
                        print("new trial")
                        
                while state == 1: #state 1: start trial/trip
                        if trig.is_crossed():
                                trig.killTone()
                                trigRun.value = 2
                                lines[line].playTone()
                                start = time.time()
                                state = 2
                                print("state 2")
                        
                while state == 2: #state 2: trigger trigger/prime reward
                        if trig.is_crossed() and time.time() > wait+start:
                                rewRun.value = 1
                                trigRun.value = 0
                                deadline = time.time()+crosstime
                                start = time.time()
                                state = 3
                                print("state 3")
                        if not trig.is_crossed():
                                trigRun.value = 0
                                lines[line].killTone()
                                state = 0
                                print("state 0")
                                
                while state == 3:
                        if not rew.is_crossed():
                                start = time.time()
                        if rew.is_crossed() and time.time() > start+wait:
                                lines[line].killTone()
                                rewRun.value = 0
                                lines[line].deliver()
                                print("reward delivered")
                                state = 0
                        if time.time() > deadline:
                                lines[line].killTone()
                                rewRun.value = 0
                                state = 0
                                
        trig.killTone()
        lines[line].killTone()
        recording.join()
        rewFlash.join()
        trigFlash.join()
        print("assay completed")

def hab1():
        hab(wait = 0.1, crosstime = 100, rewardtrigger = 1, hab_num = 1)

def hab2():
        hab(wait = 0.3, crosstime = 60, rewardtrigger = 1, hab_num = 2) # 30 iti
        
def hab3():
        hab(wait = 0.5, crosstime = 30, rewardtrigger = 1, hab_num = 3)
        
def hab4():
        hab(wait = 0.75, crosstime = 10, rewardtrigger = 1, hab_num = 4)
        
def hab5():
        hab(wait = 1, crosstime = 10, rewardtrigger = 1, hab_num = 5)
        
def hab6():
        hab(wait = 1, crosstime = 10, rewardtrigger = 0, hab_num = 6) 
        
def hab(wait,crosstime,rewardtrigger,hab_num):
        anID = raw_input("enter animal ID: ")
        runtime = input("enter runtime in minutes: ")
        iti = input('iti: ')
        starttime = time.time()
        endtime = starttime+runtime*60
        rew.endtime = endtime
        trig.endtime = endtime
        Hz = 3.9
        
        rewRun = mp.Value("i", 0)
        trigRun = mp.Value("i", 0)
        
        rewFlash = mp.Process(target = rew.flash, args = (Hz, rewRun,))
        trigFlash = mp.Process(target = trig.flash, args = (Hz, trigRun,))
        recording = mp.Process(target = record, args = (rew,trig,lines,starttime,endtime,anID,))
        
        rewFlash.start()
        trigFlash.start()
        recording.start()
        
        state = 0
        while time.time() < endtime:
                if hab_num != 1:
                        while state == 0: #state 0: initialize/prime trigger
                                rewKeep_out = mp.Process(target = rew.keep_out, args = (iti,))
                                trigKeep_out = mp.Process(target = trig.keep_out, args = (iti,))
                                rewKeep_out.start()
                                trigKeep_out.start()
                                
                                line = random.randint(0,3) #select random taste
                                rewKeep_out.join()
                                trigKeep_out.join()
                                trig.playTone()
                                print("new trial")
                                trigRun.value = 1
                                state = 1
                                
                        while state == 1: #state 1: start trial/trip
                                if trig.is_crossed():
                                        trig.killTone()
                                        lines[line].playTone()
                                        start = time.time()
                                        print("state 2")
                                        state = 2
                                
                        while state == 2: #state 2: trigger trigger/prime reward
                                if trig.is_crossed() and time.time() > wait+start or hab_num == 1: # iti variable, the hab1 session doesn't really include a complete shutdown, just reverts to the first state. 
                                        trigRun.value = 0
                                        rewRun.value = 1
                                        deadline = time.time()+crosstime
                                        start = time.time()
                                        state = 3
                                        if rewardtrigger == 1:
                                                lines[1].deliver()
                                        print("state 3")

                                if not trig.is_crossed():
                                        trigRun.value = 0
                                        lines[line].killTone()
                                        state = 0
                                        print("state 0")
                                        
                        while state == 3: 
                                if not rew.is_crossed():
                                        start = time.time()
                                if rew.is_crossed() and time.time() > start+wait:
                                        lines[line].killTone()
                                        rewRun.value = 0
                                        lines[0].deliver()
                                        print("reward delivered")
                                        state = 0
                                if time.time() > deadline:
                                        lines[line].killTone()
                                        rewRun.value = 0
                                        state = 0
                else:
                        if trig.is_crossed():
                                trigRun.value = 0
                                rewRun.value = 1
                        if rew.is_crossed():
                                trigRun.value = 0
                                rewRun.value = 1
                                
        trig.killTone()
        lines[line].killTone()
        recording.join()
        rewFlash.join()
        trigFlash.join()
        print("assay completed")

        
def record(poke1,poke2,lines,starttime,endtime,anID):
        now = datetime.datetime.now()
        d = now.strftime("%m%d%y_%Hh%Mm")
        localpath = os.getcwd()
        filepath = localpath+"/"+anID+"_"+d+".csv"
        file = open(filepath,"a")
        if os.stat(filepath).st_size == 0:
                file.write("Time,Poke1,Poke2,Line1,Line2,Line3,Line4\n")
        while time.time() < endtime:
                t = round(time.time()-starttime,2)
                file.write(str(t)+","+str(poke1.is_crossed())+","+str(poke2.is_crossed())+","+str(lines[0].isOpen())+","+str(lines[1].isOpen())+","+str(lines[2].isOpen())+","+str(lines[3].isOpen())+"\n")
                file.flush()
                time.sleep(0.1)
        file.close()
        
def killAll():
        GPIO.cleanup()
        #os.system("killall omxplayer.bin")
        
def main_menu():       ## Your menu design here
        options = ["clearout a line","calibrate a line","cuedtaste","hab1","hab2","hab3","hab4","hab5","hab6","exit"]
        print(30 * "-" , "MENU" , 30 * "-")
        for idx,item in enumerate(options):
                print(str(idx+1)+". "+item)
        print(67 * "-")
        choice = input("Enter your choice [1-8]: ")
        return choice
        
def clearout_menu():
        while True:
                for x in range(1,5):
                        print(str(x)+". clearout line "+str(x))
                print("5. main menu")
                line = input("enter your choice")
                if line in range(1,6):
                        return(line-1)
                else:
                        print("enter a valid menu option")
                        
def calibration_menu():
        while True:
                for x in range(1,5):
                        print(str(x)+". calibrate line "+str(x))
                print("5. main menu")
                line = input("enter your choice")
                if line in range(1,6):
                        return(line-1)
                else:
                        print("enter a valid menu option")

##main##

#pygame.mixer.pre_init(22100, -16, 2, 512)
#pygame.mixer.init()  
#pygame.init()
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
tasteouts = [31,33,35,37]
intanouts = [24,26,19,21]
rew = nosePoke(36,11,'reward')
trig = trigger(38,13,'trigger')
rew.flash_off()
trig.flash_off()
tones = ['1000hz_sine.mp3','3000hz_saw.mp3','5000hz_square.mp3','7000hz_unalias.mp3']
lines = [taste_line(tasteouts[i],intanouts[i],tones[i]) for i in range(4)]

while True:     
        ## While loop which will keep going until loop = False
        choice = main_menu()    ## Displays menu
        try:
                if choice ==1:
                        while True:
                                line = clearout_menu()
                                if line in range(4):
                                        lines[line].clearout()
                                elif line == 4:
                                        break
                elif choice==2:     
                        while True:
                                line = calibration_menu()
                                if line in range(4):
                                        lines[line].calibrate()
                                elif line == 4:
                                        break               
                elif choice==3:
                        print("starting cuedTaste")
                        cuedtaste()
                elif choice == 4:
                        print("starting hab1")
                        hab1()
                elif choice == 5:
                        hab2()
                elif choice == 6:
                        hab3()
                elif choice == 7:
                        hab4()
                elif choice == 8:
                        hab5()
                elif choice == 9:
                        hab6()
		elif choice == 10:
                        print("program exit")
                        GPIO.cleanup()
                        #pygame.mixer.quit()
                        os.system('killall omxplayer.bin')
                        break
                        
        except ValueError:
                print("please enter a number: ")
                
                

