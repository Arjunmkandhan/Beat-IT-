import from sounds as s, sounds.piano_notes as p
volume = 80


project_title = "Beat It Master Track"   // string
tempo_bpm = 128.5                        // double / float
base_delay = 200                         // int
loop_limit = 3                           // int
is_running = 1                           // int (used as boolean)


disco_piano     = s.C_OldiscoPiano_02_728
fm_loop         = s.Fm_Musicloop_SP_07_406
grand_piano     = s.GrandPianoShort_12_B2_78_SP
solo_piano      = s.Piano_01_112_SP
main_song       = s.C_OldiscoPiano_02_728
example         = s.example 

n1 = p.note1
n2 = p.note2
n3 = p.note3
n4 = p.note4
n5 = p.note5
n6 = p.note6
n7 = p.note7
n8 = p.note8
n9 = p.note9
n10 = p.note10

note_sequence = [n1, n2, n3, n4, n5]
void play_sequence(): 
    for i in note_sequence: 
        play(i) 
        play(example,0,2,s)  

//play_sequence() 

void song1(n1,n2): 
    play_async(n1)
    play_async(example)
    play_async(n2)
    play_async(example) 
    sleep(3,s) 

song1(n1,n2) 

int calculate_step_time(base_ms, multiplier):
    calculated = base_ms * multiplier
    calculated += 50
    adjusted = calculated - 10
    return adjusted

step = calculate_step_time(100,2)

double get_tempo_scale(speed_val):
    ratio = speed_val / 100.0
    return ratio


string get_track_name(name_str):
    return name_str
