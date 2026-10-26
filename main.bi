// =====================================================================
// Beat It (.bi) Language Master Demonstration File
// Showcases: Imports, Volume, Types, Functions, Returns, Synchronous & 
// Asynchronous Playback, Slicing, Time Units, Loops, Lists, Indexing,
// Unary / Binary Arithmetic, and Comparison Operators.
// =====================================================================

// 1. IMPORTS & MODULE ALIASING
import from sounds as s, sounds.piano_notes as p

// 2. COMMENTS & VOLUME CONTROL (Top-level statement)
/* 
   Multi-line Comment
   Setting system volume to 80%
*/
volume = 80

// 3. VARIABLE ASSIGNMENTS & DATA TYPES
project_title = "Beat It Master Track"   // string
tempo_bpm = 128.5                        // double / float
base_delay = 200                         // int
loop_limit = 3                           // int
is_running = 1                           // int (used as boolean)

// Sound references from sounds/ folder
disco_piano = s.C_OldiscoPiano_02_728
fm_loop = s.Fm_Musicloop_SP_07_406
grand_piano = s.GrandPianoShort_12_B2_78_SP
solo_piano = s.Piano_01_112_SP
main_song = s.C_OldiscoPiano_02_728

// Sound references from sounds/piano_notes/ subfolder
n1 = p.note1
n2 = p.note2
n3 = p.note3
n4 = p.note4
n5 = p.note5

// List literal
note_sequence = [n1, n2, n3, n4, n5]

// ---------------------------------------------------------------------
// 4. FUNCTION DEFINITIONS (Supporting int, double, string, void)
// ---------------------------------------------------------------------

// Function with 'int' return type & arithmetic operators (+, -, *, /)
int calculate_step_time(base_ms, multiplier):
    calculated = base_ms * multiplier
    calculated += 50
    adjusted = calculated - 10
    return adjusted

// Function with 'double' return type
double get_tempo_scale(speed_val):
    ratio = speed_val / 100.0
    return ratio

// Function with 'string' return type
string get_track_name(name_str):
    return name_str

// Function with 'void' return type, async audio & slicing
void play_triad_harmony(noteA, noteB, noteC):
    play_async(noteA, 0, 1200, ms)
    play_async(noteB, 0, 1200, ms)
    play(noteC, 1, 3, s)
    sleep(200, ms)

// Function iterating over a list parameter
void play_melody_loop():
    for note in note_sequence:
        play(note, 0, 800, ms)
        sleep(100, ms)

// ---------------------------------------------------------------------
// 5. MAIN PROGRAM EXECUTION & CALLS
// ---------------------------------------------------------------------

// Calling string function
current_track = get_track_name(project_title)

// Calling int function with Unary Minus operator (-base_delay)
step_delay = calculate_step_time(base_delay, 2)
negative_offset = -50
final_delay = step_delay + negative_offset

// Calling double function
scale_factor = get_tempo_scale(tempo_bpm)

// Synchronous play with different time units (s, ms, min, hr)
play(disco_piano, 0, 2, s)
sleep(1, s)

// Asynchronous play (overlapping sounds)
play_async(main_song, 1, 5, s)
sleep(500, ms)

// Standalone void function call (fixed: no assignment to a variable)
play_triad_harmony(n1, n3, n5)

// List Indexing ([0])
first_note = note_sequence[0]
play(first_note)

// Iterating over a list variable
for current_note in note_sequence:
    play(current_note, 0, 500, ms)
    sleep(100, ms)


play_melody_loop()

// While loop with comparison operators (<, !=, ==, <=, >=, >)
counter = 0
while counter < loop_limit:
    play_async(fm_loop, 0, 1000, ms)
    sleep(1000, ms)
    counter += 1

// For loop with range() function
for idx in range(2):
    play(solo_piano, 0, 1500, ms)
    sleep(250, ms)

// Final Sleep with larger time units
sleep(1, s)