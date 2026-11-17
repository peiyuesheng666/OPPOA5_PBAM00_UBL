
 push {r4-r6, lr}
 ldr r4, =0x8f6986bc
 mov r0, #0x39
 str r0, [r4, #4]
 bl 0x8f609be8
 str r0, [r4, #120]
 cmp r0, #0
 blt finish
 mov r0, #0x35
 str r0, [r4, #4]
 str r0, [r4, #24]
 ldr r5, =0x8f699a8c
 mov r0, r5
 bl 0x8f638830
 ldr r0, [r5, #16]
 str r0, [r4, #28]
 mov r0, #0
 mov r1, #1
 bl 0x8f638aa4
 str r0, [r4, #32]
 ldr r0, [r5, #16]
 str r0, [r4, #36]
 mov r0, r5
 bl 0x8f638830
 ldr r0, [r5, #16]
 str r0, [r4, #40]
 mov r0, #0x36
 str r0, [r4, #4]
 mov r0, #0
 dsb
finish:
 pop {r4-r6, pc}
