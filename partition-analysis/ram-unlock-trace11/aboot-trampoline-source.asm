
 push {r4-r6,lr}
 ldr r4, =0x8f6986bc
 mov r0, #0x39
 str r0, [r4,#4]
 bl 0x8f609be8
 str r0, [r4,#120]
 cmp r0, #0
 blt diagnostic_stop
 mov r0, #0x1000
 mov r1, r0
 bl 0x8f645954
 movs r5, r0
 beq diagnostic_stop
 mov r1, #0
 str r1, [r5]
 mov r1, #0x1000
 bl 0x8f6293f0
 str r0, [r4,#32]
 mov r1, r5
 add r2, r4, #64
 mov r3, #8
 copy_header:
 ldr r0, [r1], #4
 str r0, [r2], #4
 subs r3, r3, #1
 bne copy_header
 mov r0, #0x42
 str r0, [r4,#4]
 dsb
 diagnostic_stop:
 ldr r0, =0x82000200
 ldr r0, [r0]
 b diagnostic_stop
