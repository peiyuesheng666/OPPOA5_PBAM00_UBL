
    ldr r8, =2181038592
    mov r0, #0
    mov r1, #0
clear_trace:
    str r0, [r8, r1]
    add r1, r1, #4
    cmp r1, #128
    bne clear_trace
    ldr r0, =0xa5032010
    str r0, [r8]
    mov r0, #0x31
    str r0, [r8, #4]
    mrc p15, 0, r0, c1, c0, 0
    str r0, [r8, #64]
    ldr r0, =134738944
    mcr p15, 0, r0, c12, c0, 0
    isb
    ldr ip, =0x08008980
    blx ip
    mvn r0, #0
    mcr p15, 0, r0, c3, c0, 0
    isb
    ldr r4, =134738432
    mov r9, #0
next_segment:
    ldm r4!, {r0-r3}
    cmp r1, #0
    beq boot_sbl
    str r1, [r8, #8]
    add r9, r9, #1
    str r9, [r8, #12]
    sub r6, r3, r2
copy_loop:
    cmp r2, #0
    beq zero_start
    ldrb r7, [r0], #1
    strb r7, [r1], #1
    subs r2, r2, #1
    bne copy_loop
zero_start:
    mov r7, #0
zero_loop:
    cmp r6, #0
    beq next_segment
    strb r7, [r1], #1
    subs r6, r6, #1
    bne zero_loop
    b next_segment
boot_sbl:
    mov r1, #0x32
    str r1, [r8, #4]
    dsb
    mov r0, #0
    mcr p15, 0, r0, c7, c5, 0
    mcr p15, 0, r0, c8, c7, 0
    dsb
    isb
    ldr r0, =134230272
    ldr ip, =134250608
    bx ip
