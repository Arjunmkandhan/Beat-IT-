.intel_syntax noprefix
.extern beatit_play
.extern beatit_sleep
.extern beatit_set_volume
.text
.globl fn_calculate_step_time
fn_calculate_step_time:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + var_base_ms], rcx
  mov QWORD PTR [rip + var_multiplier], rdx
  mov rax, QWORD PTR [rip + var_base_ms]
  mov r10, rax
  mov rax, QWORD PTR [rip + var_multiplier]
  xchg rax, r10
  imul rax, r10
  mov QWORD PTR [rip + var_calculated], rax
  mov r10, QWORD PTR [rip + var_calculated]
  mov rax, 50
  add rax, r10
  mov QWORD PTR [rip + var_calculated], rax
  mov rax, QWORD PTR [rip + var_calculated]
  mov r10, rax
  mov rax, 10
  xchg rax, r10
  sub rax, r10
  mov QWORD PTR [rip + var_adjusted], rax
  mov rax, QWORD PTR [rip + var_adjusted]
  add rsp, 32
  pop rbp
  ret
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl fn_get_tempo_scale
fn_get_tempo_scale:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + var_speed_val], rcx
  mov rax, QWORD PTR [rip + var_speed_val]
  mov r10, rax
  mov rax, 100
  xchg rax, r10
  cqo
  idiv r10
  mov QWORD PTR [rip + var_ratio], rax
  mov rax, QWORD PTR [rip + var_ratio]
  add rsp, 32
  pop rbp
  ret
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl fn_get_track_name
fn_get_track_name:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + var_name_str], rcx
  mov rax, QWORD PTR [rip + var_name_str]
  add rsp, 32
  pop rbp
  ret
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl fn_play_triad_harmony
fn_play_triad_harmony:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + var_noteA], rcx
  mov QWORD PTR [rip + var_noteB], rdx
  mov QWORD PTR [rip + var_noteC], r8
  mov rax, 1200
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_noteA]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 1200
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_noteB]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 3
  imul rax, 1000
  push rax
  mov rax, 1
  imul rax, 1000
  push rax
  mov rax, QWORD PTR [rip + var_noteC]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  mov rax, 200
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl fn_play_melody_loop
fn_play_melody_loop:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + loop_idx_3], 0
for_1:
  mov rax, QWORD PTR [rip + loop_idx_3]
  cmp rax, 5
  jge endfor_2
  lea r8, [rip + list_note_sequence]
  mov rdx, QWORD PTR [rip + loop_idx_3]
  mov rax, QWORD PTR [r8 + rdx*8]
  mov QWORD PTR [rip + var_note], rax
  mov rax, 800
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_note]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  mov rax, 100
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  inc QWORD PTR [rip + loop_idx_3]
  jmp for_1
endfor_2:
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl main
main:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov rax, 80
  mov rcx, rax
  call beatit_set_volume
  lea rax, [rip + str_5]
  mov QWORD PTR [rip + var_project_title], rax
  mov rax, 128
  mov QWORD PTR [rip + var_tempo_bpm], rax
  mov rax, 200
  mov QWORD PTR [rip + var_base_delay], rax
  mov rax, 3
  mov QWORD PTR [rip + var_loop_limit], rax
  mov rax, 1
  mov QWORD PTR [rip + var_is_running], rax
  lea rax, [rip + sound_0]
  mov QWORD PTR [rip + var_disco_piano], rax
  lea rax, [rip + sound_1]
  mov QWORD PTR [rip + var_fm_loop], rax
  lea rax, [rip + sound_2]
  mov QWORD PTR [rip + var_grand_piano], rax
  lea rax, [rip + sound_3]
  mov QWORD PTR [rip + var_solo_piano], rax
  lea rax, [rip + sound_0]
  mov QWORD PTR [rip + var_main_song], rax
  lea rax, [rip + sound_4]
  mov QWORD PTR [rip + var_n1], rax
  lea rax, [rip + sound_5]
  mov QWORD PTR [rip + var_n2], rax
  lea rax, [rip + sound_6]
  mov QWORD PTR [rip + var_n3], rax
  lea rax, [rip + sound_7]
  mov QWORD PTR [rip + var_n4], rax
  lea rax, [rip + sound_8]
  mov QWORD PTR [rip + var_n5], rax
  mov rax, QWORD PTR [rip + var_n1]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 0], rax
  mov rax, QWORD PTR [rip + var_n2]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 8], rax
  mov rax, QWORD PTR [rip + var_n3]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 16], rax
  mov rax, QWORD PTR [rip + var_n4]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 24], rax
  mov rax, QWORD PTR [rip + var_n5]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 32], rax
  mov rax, QWORD PTR [rip + var_project_title]
  push rax
  pop rcx
  call fn_get_track_name
  mov QWORD PTR [rip + var_current_track], rax
  mov rax, QWORD PTR [rip + var_base_delay]
  push rax
  mov rax, 2
  push rax
  pop rdx
  pop rcx
  call fn_calculate_step_time
  mov QWORD PTR [rip + var_step_delay], rax
  mov rax, -50
  mov QWORD PTR [rip + var_negative_offset], rax
  mov rax, QWORD PTR [rip + var_step_delay]
  mov r10, rax
  mov rax, QWORD PTR [rip + var_negative_offset]
  xchg rax, r10
  add rax, r10
  mov QWORD PTR [rip + var_final_delay], rax
  mov rax, QWORD PTR [rip + var_tempo_bpm]
  push rax
  pop rcx
  call fn_get_tempo_scale
  mov QWORD PTR [rip + var_scale_factor], rax
  mov rax, 2
  imul rax, 1000
  push rax
  mov rax, 0
  imul rax, 1000
  push rax
  mov rax, QWORD PTR [rip + var_disco_piano]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  mov rax, 1
  imul rax, 1000
  mov rcx, rax
  call beatit_sleep
  mov rax, 5
  imul rax, 1000
  push rax
  mov rax, 1
  imul rax, 1000
  push rax
  mov rax, QWORD PTR [rip + var_main_song]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 500
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  mov rax, QWORD PTR [rip + var_n1]
  push rax
  mov rax, QWORD PTR [rip + var_n3]
  push rax
  mov rax, QWORD PTR [rip + var_n5]
  push rax
  pop r8
  pop rdx
  pop rcx
  call fn_play_triad_harmony
  mov rax, 0
  lea r8, [rip + list_note_sequence]
  mov rax, QWORD PTR [r8 + rax*8]
  mov QWORD PTR [rip + var_first_note], rax
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_first_note]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  mov QWORD PTR [rip + loop_idx_8], 0
for_6:
  mov rax, QWORD PTR [rip + loop_idx_8]
  cmp rax, 5
  jge endfor_7
  lea r8, [rip + list_note_sequence]
  mov rdx, QWORD PTR [rip + loop_idx_8]
  mov rax, QWORD PTR [r8 + rdx*8]
  mov QWORD PTR [rip + var_current_note], rax
  mov rax, 500
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_current_note]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  mov rax, 100
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  inc QWORD PTR [rip + loop_idx_8]
  jmp for_6
endfor_7:
  call fn_play_melody_loop
  mov rax, 0
  mov QWORD PTR [rip + var_counter], rax
while_10:
  mov rax, QWORD PTR [rip + var_counter]
  mov r10, rax
  mov rax, QWORD PTR [rip + var_loop_limit]
  xchg rax, r10
  cmp rax, r10
  setl al
  movzx rax, al
  test rax, rax
  jz endwhile_11
  mov rax, 1000
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_fm_loop]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 1000
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  mov r10, QWORD PTR [rip + var_counter]
  mov rax, 1
  add rax, r10
  mov QWORD PTR [rip + var_counter], rax
  jmp while_10
endwhile_11:
  mov rax, 2
  mov QWORD PTR [rip + loop_limit_15], rax
  mov QWORD PTR [rip + loop_idx_14], 0
for_12:
  mov rax, QWORD PTR [rip + loop_idx_14]
  cmp rax, QWORD PTR [rip + loop_limit_15]
  jge endfor_13
  mov QWORD PTR [rip + var_idx], rax
  mov rax, 1500
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_solo_piano]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  mov rax, 250
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  inc QWORD PTR [rip + loop_idx_14]
  jmp for_12
endfor_13:
  mov rax, 1
  imul rax, 1000
  mov rcx, rax
  call beatit_sleep
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.section .rdata,"dr"
str_5: .asciz "Beat It Master Track"
.section .rdata,"dr"
sound_0: .asciz "sounds/C_OldiscoPiano_02_728.wav"
.section .rdata,"dr"
sound_1: .asciz "sounds/Fm_Musicloop_SP_07_406.wav"
.section .rdata,"dr"
sound_2: .asciz "sounds/GrandPianoShort_12_B2_78_SP.wav"
.section .rdata,"dr"
sound_3: .asciz "sounds/Piano_01_112_SP.wav"
.section .rdata,"dr"
sound_4: .asciz "sounds/piano_notes/note1.wav"
.section .rdata,"dr"
sound_5: .asciz "sounds/piano_notes/note2.wav"
.section .rdata,"dr"
sound_6: .asciz "sounds/piano_notes/note3.wav"
.section .rdata,"dr"
sound_7: .asciz "sounds/piano_notes/note4.wav"
.section .rdata,"dr"
sound_8: .asciz "sounds/piano_notes/note5.wav"
.bss
list_note_sequence: .zero 40
var_adjusted: .quad 0
var_base_delay: .quad 0
var_base_ms: .quad 0
var_calculated: .quad 0
var_counter: .quad 0
var_current_note: .quad 0
var_current_track: .quad 0
var_disco_piano: .quad 0
var_final_delay: .quad 0
var_first_note: .quad 0
var_fm_loop: .quad 0
var_grand_piano: .quad 0
var_idx: .quad 0
var_is_running: .quad 0
var_loop_limit: .quad 0
var_main_song: .quad 0
var_multiplier: .quad 0
var_n1: .quad 0
var_n2: .quad 0
var_n3: .quad 0
var_n4: .quad 0
var_n5: .quad 0
var_name_str: .quad 0
var_negative_offset: .quad 0
var_note: .quad 0
var_noteA: .quad 0
var_noteB: .quad 0
var_noteC: .quad 0
var_note_sequence: .quad 0
var_project_title: .quad 0
var_ratio: .quad 0
var_scale_factor: .quad 0
var_solo_piano: .quad 0
var_speed_val: .quad 0
var_step_delay: .quad 0
var_tempo_bpm: .quad 0
loop_idx_3: .quad 0
loop_limit_4: .quad 0
loop_idx_8: .quad 0
loop_limit_9: .quad 0
loop_idx_14: .quad 0
loop_limit_15: .quad 0
