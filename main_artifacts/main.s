.intel_syntax noprefix
.extern beatit_play
.extern beatit_sleep
.text
.globl main
main:
  push rbp
  mov rbp, rsp
  sub rsp, 32
  mov rax, 0
  mov QWORD PTR [rip + var_count], rax
  lea rax, [rip + sound_0]
  mov QWORD PTR [rip + var_beat1], rax
  lea rax, [rip + sound_1]
  mov QWORD PTR [rip + var_beat2], rax
  lea rax, [rip + sound_2]
  mov QWORD PTR [rip + var_beat3], rax
  lea rax, [rip + sound_3]
  mov QWORD PTR [rip + var_beat4], rax
  mov rax, QWORD PTR [rip + var_beat1]
  lea r8, [rip + list_order]
  mov QWORD PTR [r8 + 0], rax
  mov rax, QWORD PTR [rip + var_beat3]
  lea r8, [rip + list_order]
  mov QWORD PTR [r8 + 8], rax
  mov rax, QWORD PTR [rip + var_beat4]
  lea r8, [rip + list_order]
  mov QWORD PTR [r8 + 16], rax
  mov rax, QWORD PTR [rip + var_beat2]
  lea r8, [rip + list_order]
  mov QWORD PTR [r8 + 24], rax
  mov QWORD PTR [rip + loop_idx_3], 0
for_1:
  mov rax, QWORD PTR [rip + loop_idx_3]
  cmp rax, 4
  jge endfor_2
  lea r8, [rip + list_order]
  mov rdx, QWORD PTR [rip + loop_idx_3]
  mov rax, QWORD PTR [r8 + rdx*8]
  mov QWORD PTR [rip + var_i], rax
  mov rax, QWORD PTR [rip + var_i]
  mov rcx, rax
  call beatit_play
  inc QWORD PTR [rip + loop_idx_3]
  jmp for_1
endfor_2:
  xor eax, eax
  add rsp, 32
  pop rbp
  ret
.section .rdata,"dr"
sound_0: .asciz "sounds/C_OldiscoPiano_02_728.wav"
.section .rdata,"dr"
sound_1: .asciz "sounds/Fm_Musicloop_SP_07_406.wav"
.section .rdata,"dr"
sound_2: .asciz "sounds/Piano_01_112_SP.wav"
.section .rdata,"dr"
sound_3: .asciz "sounds/GrandPianoShort_12_B2_78_SP.wav"
.bss
var_beat1: .quad 0
var_beat2: .quad 0
var_beat3: .quad 0
var_beat4: .quad 0
var_count: .quad 0
var_i: .quad 0
var_order: .quad 0
list_order: .zero 32
loop_idx_3: .quad 0
loop_limit_4: .quad 0
