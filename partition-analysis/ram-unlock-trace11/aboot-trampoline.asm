8f60f87c push {r4, r5, r6, lr}
8f60f880 ldr r4, [pc, #0x70]
8f60f884 mov r0, #0x39
8f60f888 str r0, [r4, #4]
8f60f88c bl #0x8f609be8
8f60f890 str r0, [r4, #0x78]
8f60f894 cmp r0, #0
8f60f898 blt #0x8f60f8ec
8f60f89c mov r0, #0x1000
8f60f8a0 mov r1, r0
8f60f8a4 bl #0x8f645954
8f60f8a8 movs r5, r0
8f60f8ac beq #0x8f60f8ec
8f60f8b0 mov r1, #0
8f60f8b4 str r1, [r5]
8f60f8b8 mov r1, #0x1000
8f60f8bc bl #0x8f6293f0
8f60f8c0 str r0, [r4, #0x20]
8f60f8c4 mov r1, r5
8f60f8c8 add r2, r4, #0x40
8f60f8cc mov r3, #8
8f60f8d0 ldr r0, [r1], #4
8f60f8d4 str r0, [r2], #4
8f60f8d8 subs r3, r3, #1
8f60f8dc bne #0x8f60f8d0
8f60f8e0 mov r0, #0x42
8f60f8e4 str r0, [r4, #4]
8f60f8e8 dsb sy
8f60f8ec ldr r0, [pc, #8]
8f60f8f0 ldr r0, [r0]
8f60f8f4 b #0x8f60f8ec
8f60f8f8 svchi #0x6986bc
8f60f8fc andhi r0, r0, #0, #4