
 push {r4-r6,lr}
 ldr r4, =0x8f6986bc
 mov r0, #0x39
 str r0, [r4,#4]
 bl 0x8f609be8
 str r0, [r4,#120]
 cmp r0, #0
 blt diagnostic_stop
 ldr r5, =0x8f699a8c
 mov r0, #0x40
 str r0, [r4,#4]
 mov r0, r5
 bl 0x8f638830
 ldr r0, [r5,#16]
 str r0, [r4,#40]
 ldr r0, [r5,#24]
 str r0, [r4,#44]
 mov r0, #0x41
 str r0, [r4,#4]
 dsb
 diagnostic_stop:
 ldr r0, =0x82000200
 ldr r0, [r0]
 b diagnostic_stop
