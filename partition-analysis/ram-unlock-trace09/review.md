# Attempt09 review

Attempt08 log proves a data abort at 0x8F60F888 on the first store through r4=0x82000200. The wrapper was entered; no unlock setter executed.

Attempt09 reserves the final 128 bytes of the existing aboot log data at 0x8F6986BC. Capacity becomes 3968, whose endpoint exactly matches the trace start; the trace ends at the original 4096-byte ring endpoint. Runtime preservation of the capacity still requires verification.

Image SHA256, forced MMC getter, relocated 48-byte fatal probe, and Thumb callback pointer checked. Builder bounds enforce 128-byte SBL hook within 132 and 132-byte wrapper within 156. Dual trace readers parse records independently and validate each magic. No userdata reads. Persistent unlock is unverified. Not launched yet.
