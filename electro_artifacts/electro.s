.intel_syntax noprefix
.extern beatit_play
.extern beatit_sleep
.extern beatit_set_volume
.text
.globl fn_play_verse
fn_play_verse:
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
  call beatit_play
  mov rax, 150
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  mov rax, 1500
  push rax
  mov rax, 200
  push rax
  mov rax, QWORD PTR [rip + var_noteB]
  mov rcx, rax
  pop rdx
  pop r8
  call beatit_play
  mov rax, 150
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  mov rax, 2000
  push rax
  mov rax, 500
  push rax
  mov rax, QWORD PTR [rip + var_noteC]
  mov rcx, rax
  pop rdx
  pop r8
  call beatit_play
  mov rax, 300
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.globl main
main:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov rax, 75
  mov rcx, rax
  call beatit_set_volume
  lea rax, [rip + sound_0]
  push rax
  lea rax, [rip + sound_1]
  push rax
  lea rax, [rip + sound_2]
  push rax
  pop r8
  pop rdx
  pop rcx
  call fn_play_verse
  lea rax, [rip + sound_3]
  push rax
  lea rax, [rip + sound_4]
  push rax
  lea rax, [rip + sound_5]
  push rax
  pop r8
  pop rdx
  pop rcx
  call fn_play_verse
  lea rax, [rip + sound_6]
  lea r8, [rip + list_accompaniment]
  mov QWORD PTR [r8 + 0], rax
  lea rax, [rip + sound_7]
  lea r8, [rip + list_accompaniment]
  mov QWORD PTR [r8 + 8], rax
  lea rax, [rip + sound_8]
  lea r8, [rip + list_accompaniment]
  mov QWORD PTR [r8 + 16], rax
  lea rax, [rip + sound_9]
  lea r8, [rip + list_accompaniment]
  mov QWORD PTR [r8 + 24], rax
  mov QWORD PTR [rip + loop_idx_3], 0
for_1:
  mov rax, QWORD PTR [rip + loop_idx_3]
  cmp rax, 4
  jge endfor_2
  lea r8, [rip + list_accompaniment]
  mov rdx, QWORD PTR [rip + loop_idx_3]
  mov rax, QWORD PTR [r8 + rdx*8]
  mov QWORD PTR [rip + var_chord], rax
  mov rax, 800
  push rax
  mov rax, 0
  push rax
  mov rax, QWORD PTR [rip + var_chord]
  mov rcx, rax
  pop rdx
  pop r8
  call beatit_play
  mov rax, 100
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  inc QWORD PTR [rip + loop_idx_3]
  jmp for_1
endfor_2:
  mov rax, 0
  mov QWORD PTR [rip + var_count], rax
while_5:
  mov rax, QWORD PTR [rip + var_count]
  mov r10, rax
  mov rax, 4
  xchg rax, r10
  cmp rax, r10
  setl al
  movzx rax, al
  test rax, rax
  jz endwhile_6
  mov rax, 3
  imul rax, 1000
  push rax
  mov rax, 1
  imul rax, 1000
  push rax
  lea rax, [rip + sound_0]
  mov rcx, rax
  pop rdx
  pop r8
  call beatit_play
  mov rax, 250
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  lea rax, [rip + sound_1]
  mov rcx, rax
  pop rdx
  pop r8
  call beatit_play
  mov r10, QWORD PTR [rip + var_count]
  mov rax, 1
  add rax, r10
  mov QWORD PTR [rip + var_count], rax
  jmp while_5
endwhile_6:
  mov rax, 4
  mov QWORD PTR [rip + loop_limit_10], rax
  mov QWORD PTR [rip + loop_idx_9], 0
for_7:
  mov rax, QWORD PTR [rip + loop_idx_9]
  cmp rax, QWORD PTR [rip + loop_limit_10]
  jge endfor_8
  mov QWORD PTR [rip + var_i], rax
  mov rax, 0
  push rax
  mov rax, 0
  push rax
  lea rax, [rip + sound_2]
  mov rcx, rax
  pop rdx
  pop r8
  call beatit_play
  mov rax, 500
  imul rax, 1
  mov rcx, rax
  call beatit_sleep
  inc QWORD PTR [rip + loop_idx_9]
  jmp for_7
endfor_8:
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.section .rdata,"dr"
sound_0: .asciz "sounds/piano_notes/note1.wav"
.section .rdata,"dr"
sound_1: .asciz "sounds/piano_notes/note2.wav"
.section .rdata,"dr"
sound_2: .asciz "sounds/piano_notes/note3.wav"
.section .rdata,"dr"
sound_3: .asciz "sounds/piano_notes/note4.wav"
.section .rdata,"dr"
sound_4: .asciz "sounds/piano_notes/note5.wav"
.section .rdata,"dr"
sound_5: .asciz "sounds/piano_notes/note6.wav"
.section .rdata,"dr"
sound_6: .asciz "sounds/piano_notes/note7.wav"
.section .rdata,"dr"
sound_7: .asciz "sounds/piano_notes/note8.wav"
.section .rdata,"dr"
sound_8: .asciz "sounds/piano_notes/note9.wav"
.section .rdata,"dr"
sound_9: .asciz "sounds/piano_notes/note10.wav"
.bss
var_accompaniment: .quad 0
var_chord: .quad 0
var_count: .quad 0
var_i: .quad 0
var_noteA: .quad 0
var_noteB: .quad 0
var_noteC: .quad 0
list_accompaniment: .zero 32
loop_idx_3: .quad 0
loop_limit_4: .quad 0
loop_idx_9: .quad 0
loop_limit_10: .quad 0
