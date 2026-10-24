// =====================================================================
// Composition: Midnight Serenade in Beat It (.bi)
// =====================================================================

import from sounds.piano_notes as p
import from sounds as s

// Set optimal playback volume to 75%
volume = 75

// Define a reusable melodic phrase function with slicing
void play_verse(noteA, noteB, noteC):
    play(noteA, 0, 1200, ms)
    sleep(150, ms)
    play(noteB, 200, 1500, ms)
    sleep(150, ms)
    play(noteC, 500, 2000, ms)
    sleep(300, ms)

// Introduction: Playing progressive piano motifs
play_verse(p.note1, p.note2, p.note3)
play_verse(p.note4, p.note5, p.note6)

// Rhythm Section: Using a list and a sequential loop
accompaniment = [p.note7, p.note8, p.note9, p.note10]

for chord in accompaniment:
    play(chord, 0, 800, ms)
    sleep(100, ms)

// Bridge: Asynchronous background groove using a while loop
count = 0
while count < 4:
    play(p.note1, 1, 3, s)  // Play from 1s to 3s
    sleep(250, ms)
    play(p.note2)
    count += 1

// Outro: Range-based loop for a rhythmic finish
for i in range(4):
    play(p.note3)
    sleep(5, ms)
