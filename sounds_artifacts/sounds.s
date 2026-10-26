.intel_syntax noprefix
.extern beatit_play
.extern beatit_sleep
.extern beatit_set_volume
.text
.globl fn_getBase
fn_getBase:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + var_base], rcx
  mov QWORD PTR [rip + var_ratio], rdx
  mov rax, QWORD PTR [rip + var_base]
  mov r10, rax
  mov rax, QWORD PTR [rip + var_ratio]
  xchg rax, r10
  imul rax, r10
  add rsp, 32
  pop rbp
  ret
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl fn_play_traid
fn_play_traid:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov QWORD PTR [rip + var_notea], rcx
  mov QWORD PTR [rip + var_noteb], rdx
  mov QWORD PTR [rip + var_notec], r8
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_notea]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_noteb]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_notec]
  mov rcx, rax
  pop rdx
  pop r8
  mov r9, 1
  call beatit_play
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
  mov rax, 20
  mov QWORD PTR [rip + var_base], rax
  mov rax, 0
  mov QWORD PTR [rip + var_count], rax
  lea rax, [rip + sound_0]
  mov QWORD PTR [rip + var_song1], rax
  lea rax, [rip + sound_1]
  mov QWORD PTR [rip + var_song2], rax
  lea rax, [rip + sound_2]
  mov QWORD PTR [rip + var_song3], rax
  lea rax, [rip + sound_3]
  mov QWORD PTR [rip + var_n1], rax
  lea rax, [rip + sound_4]
  mov QWORD PTR [rip + var_n2], rax
  lea rax, [rip + sound_5]
  mov QWORD PTR [rip + var_n3], rax
  lea rax, [rip + sound_6]
  mov QWORD PTR [rip + var_n4], rax
  mov rax, QWORD PTR [rip + var_n1]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 0], rax
  mov rax, QWORD PTR [rip + var_n2]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 8], rax
  mov rax, QWORD PTR [rip + var_n3]
  lea r8, [rip + list_note_sequence]
  mov QWORD PTR [r8 + 16], rax
  mov rax, QWORD PTR [rip + var_base]
  push rax
  mov rax, 0
  push rax
  pop rdx
  pop rcx
  call fn_getBase
  mov QWORD PTR [rip + var_base], rax
  mov rax, QWORD PTR [rip + var_n1]
  push rax
  mov rax, QWORD PTR [rip + var_n2]
  push rax
  mov rax, QWORD PTR [rip + var_n3]
  push rax
  pop r8
  pop rdx
  pop rcx
  call fn_play_traid
  mov rax, 2
  imul rax, 1000
  mov rcx, rax
  call beatit_sleep
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.section .rdata,"dr"
sound_0: .asciz "sounds/C_OldiscoPiano_02_728.wav"
.section .rdata,"dr"
sound_1: .asciz "sounds/Fm_Musicloop_SP_07_406.wav"
.section .rdata,"dr"
sound_2: .asciz "sounds/kick.wav"
.section .rdata,"dr"
sound_3: .asciz "sounds/piano_notes/note1.wav"
.section .rdata,"dr"
sound_4: .asciz "sounds/piano_notes/note2.wav"
.section .rdata,"dr"
sound_5: .asciz "sounds/piano_notes/note3.wav"
.section .rdata,"dr"
sound_6: .asciz "sounds/piano_notes/note4.wav"
.bss
list_note_sequence: .zero 24
var_base: .quad 0
var_count: .quad 0
var_n1: .quad 0
var_n2: .quad 0
var_n3: .quad 0
var_n4: .quad 0
var_note_sequence: .quad 0
var_notea: .quad 0
var_noteb: .quad 0
var_notec: .quad 0
var_ratio: .quad 0
var_song1: .quad 0
var_song2: .quad 0
var_song3: .quad 0
