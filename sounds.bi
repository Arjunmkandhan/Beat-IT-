// This is a comment . 

/* 
This is a multi line comment 
*/ 

a = 4 
b = 2  
c = a + b 


import from sounds.piano_notes as p 

import from sounds as s 

note1 = p.note1 
note2 = p.note2 
note3 = p.note3 
note4 = p.note4 
note5 = p.note5 
note6 = p.note6 
note7 = p.note7 
note8 = p.note8 
note9 = p.note9 
note10 = p.note10 


song = s.aaj_ki_raat 


void Sound1(note1 , note2 , note3): 
    play(note1, 1, 7,s) 
    sleep(2,s) 
    play(note2, 100,110,s) 
    sleep(100,ms) 
    play(note3) 


void Sound2(note1, note2): 
    play(note1)
    play(note2)
    play(note1)
    play(note2)
    play(note1)
    play(note2)



Sound1(song ,song, note1)
//Sound2(note1, note3)   


/*
order = [note1 , note2, note3,note4]  

for note in order: 
    play(note) 

*/ 
