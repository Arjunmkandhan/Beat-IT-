import from sounds as s 
import from sounds.piano_notes as p 
volume = 80 


double getBase(base, ratio): 
    return base*ratio 

void play_traid(notea , noteb , notec): 
    play_async(notea) 
    play_async(noteb) 
    play_async(notec)


base = 20 
count = 0  


song1 = s.C_OldiscoPiano_02_728 
song2 = s.Fm_Musicloop_SP_07_406 
song3 = s.kick 

n1 = p.note1 
n2 = p.note2 
n3 = p.note3 
n4 = p.note4 


note_sequence = [n1,n2,n3] 

base = getBase(base,0.5)  

play_traid(n1,n2,n3)   
sleep(2,s) 

