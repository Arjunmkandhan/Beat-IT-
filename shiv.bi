
play_async(kick)
play_async(c5, 250)
sleep(100, ms)

play_async(snare)
sleep(100, ms)

play_async(kick)
play_async(g4, 250)
sleep(100, ms)

play_async(snare)
sleep(100, ms)

// BAR 2 — build the melody.
play_async(kick)
play_async(f4, 250)
sleep(100, ms)

play_async(snare)
sleep(100, ms)

play_async(kick)
play_async(g4, 250)
sleep(100, ms)

play_async(snare)
play_async(b4, 1000)
sleep(100, ms)

// BAR 3 — repeat the backing phrase.
play_async(backing, 0, 4000, ms)
play_async(kick)
play_async(c5, 250)
sleep(100, ms)

play_async(snare)
sleep(100, ms)

play_async(kick)
play_async(g5)
sleep(100, ms)

play_async(snare)
sleep(100, ms)

// BAR 4 — resolve the melody.
play_async(kick)
play_async(f4, 250)
sleep(100, ms)

play_async(snare)
sleep(100, ms)

play_async(kick)
play_async(g4, 250)
sleep(100, ms)

play_async(snare)
play_async(c5, 250)
sleep(100, ms)

// Allow the final sounds to finish.
sleep(150, ms)