0805338c push {r0, r1, r2, r3, r4, lr}
0805338e mvn r0, #0
08053392 mcr p15, #0, r0, c3, c0, #0
08053396 isb sy
0805339a ldr r0, [pc, #0x48]
0805339c movs r1, #0x34
0805339e str r1, [r0, #4]
080533a0 str r1, [r0, #0x14]
080533a2 ldr r0, [pc, #0x44]
080533a4 ldr r1, [pc, #0x44]
080533a6 movs r2, #0x84
080533a8 ldr r3, [r1], #4
080533ac str r3, [r0], #4
080533b0 subs r2, #4
080533b2 bne #0x80533a8
080533b4 ldr r0, [pc, #0x38]
080533b6 ldr r1, [pc, #0x3c]
080533b8 str r1, [r0]
080533ba ldr r0, [pc, #0x3c]
080533bc movw r1, #0xf80
080533c0 str r1, [r0]
080533c2 ldr r0, [pc, #0x38]
080533c4 movs r1, #0
080533c6 movs r2, #0x80
080533c8 str r1, [r0], #4
080533cc subs r2, #4
080533ce bne #0x80533c8
080533d0 ldr r0, [pc, #0x2c]
080533d2 ldr r1, [pc, #0x30]
080533d4 str r1, [r0]
080533d6 dsb sy
080533da pop.w {r0, r1, r2, r3, r4, lr}
080533de ldr.w ip, [pc, #0x28]
080533e2 bx ip
080533e4 lsls r0, r0, #8
080533e6 strh r0, [r0, #0x10]