8f60f87c push {r4, r5, r6, lr}
8f60f880 ldr r4, [pc, #0x50]
8f60f884 mov r0, #0x39
8f60f888 str r0, [r4, #4]
8f60f88c bl #0x8f609be8
8f60f890 str r0, [r4, #0x78]
8f60f894 cmp r0, #0
8f60f898 blt #0x8f60f8cc
8f60f89c ldr r5, [pc, #0x38]
8f60f8a0 mov r0, #0x40
8f60f8a4 str r0, [r4, #4]
8f60f8a8 mov r0, r5
8f60f8ac bl #0x8f638830
8f60f8b0 ldr r0, [r5, #0x10]
8f60f8b4 str r0, [r4, #0x28]
8f60f8b8 ldr r0, [r5, #0x18]
8f60f8bc str r0, [r4, #0x2c]
8f60f8c0 mov r0, #0x41
8f60f8c4 str r0, [r4, #4]
8f60f8c8 dsb sy
8f60f8cc ldr r0, [pc, #0xc]
8f60f8d0 ldr r0, [r0]
8f60f8d4 b #0x8f60f8cc
8f60f8d8 svchi #0x6986bc
8f60f8dc svchi #0x699a8c
8f60f8e0 andhi r0, r0, #0, #4