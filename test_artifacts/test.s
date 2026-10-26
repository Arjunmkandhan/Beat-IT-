.intel_syntax noprefix
.extern beatit_play
.extern beatit_sleep
.extern beatit_set_volume
.text
.globl fn_play_sequence
fn_play_sequence:
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
  mov QWORD PTR [rip + var_i], rax
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_i]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  mov rax, 2
  imul rax, 1000
  push rax
  mov rax, 0
  imul rax, 1000
  push rax
  mov rax, QWORD PTR [rip + var_example]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 0
  call beatit_play
  inc QWORD PTR [rip + loop_idx_3]
  jmp for_1
endfor_2:
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl fn_song1
fn_song1:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + var_n1], rcx
  mov QWORD PTR [rip + var_n2], rdx
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_n1]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_example]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_n2]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_example]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 3
  imul rax, 1000
  mov rcx, rax
  call beatit_sleep
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
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
  mov QWORD PTR [rip + var_example], rax
  lea rax, [rip + sound_5]
  mov QWORD PTR [rip + var_n1], rax
  lea rax, [rip + sound_6]
  mov QWORD PTR [rip + var_n2], rax
  lea rax, [rip + sound_7]
  mov QWORD PTR [rip + var_n3], rax
  lea rax, [rip + sound_8]
  mov QWORD PTR [rip + var_n4], rax
  lea rax, [rip + sound_9]
  mov QWORD PTR [rip + var_n5], rax
  lea rax, [rip + sound_10]
  mov QWORD PTR [rip + var_n6], rax
  lea rax, [rip + sound_11]
  mov QWORD PTR [rip + var_n7], rax
  lea rax, [rip + sound_12]
  mov QWORD PTR [rip + var_n8], rax
  lea rax, [rip + sound_13]
  mov QWORD PTR [rip + var_n9], rax
  lea rax, [rip + sound_14]
  mov QWORD PTR [rip + var_n10], rax
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
  mov rax, QWORD PTR [rip + var_n1]
  push rax
  mov rax, QWORD PTR [rip + var_n2]
  push rax
  pop rdx
  pop rcx
  call fn_song1
  mov rax, 100
  push rax
  mov rax, 2
  push rax
  pop rdx
  pop rcx
  call fn_calculate_step_time
  mov QWORD PTR [rip + var_step], rax
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
sound_4: .asciz "sounds/example.wav"
.section .rdata,"dr"
sound_5: .asciz "sounds/piano_notes/note1.wav"
.section .rdata,"dr"
sound_6: .asciz "sounds/piano_notes/note2.wav"
.section .rdata,"dr"
sound_7: .asciz "sounds/piano_notes/note3.wav"
.section .rdata,"dr"
sound_8: .asciz "sounds/piano_notes/note4.wav"
.section .rdata,"dr"
sound_9: .asciz "sounds/piano_notes/note5.wav"
.section .rdata,"dr"
sound_10: .asciz "sounds/piano_notes/note6.wav"
.section .rdata,"dr"
sound_11: .asciz "sounds/piano_notes/note7.wav"
.section .rdata,"dr"
sound_12: .asciz "sounds/piano_notes/note8.wav"
.section .rdata,"dr"
sound_13: .asciz "sounds/piano_notes/note9.wav"
.section .rdata,"dr"
sound_14: .asciz "sounds/piano_notes/note10.wav"
.bss
list_note_sequence: .zero 40
var_adjusted: .quad 0
var_base_delay: .quad 0
var_base_ms: .quad 0
var_calculated: .quad 0
var_disco_piano: .quad 0
var_example: .quad 0
var_fm_loop: .quad 0
var_grand_piano: .quad 0
var_i: .quad 0
var_is_running: .quad 0
var_loop_limit: .quad 0
var_main_song: .quad 0
var_multiplier: .quad 0
var_n1: .quad 0
var_n10: .quad 0
var_n2: .quad 0
var_n3: .quad 0
var_n4: .quad 0
var_n5: .quad 0
var_n6: .quad 0
var_n7: .quad 0
var_n8: .quad 0
var_n9: .quad 0
var_name_str: .quad 0
var_note_sequence: .quad 0
var_project_title: .quad 0
var_ratio: .quad 0
var_solo_piano: .quad 0
var_speed_val: .quad 0
var_step: .quad 0
var_tempo_bpm: .quad 0
loop_idx_3: .quad 0
loop_limit_4: .quad 0
