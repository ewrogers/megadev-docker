/* Character access is the portable alternative, valid with strict aliasing. */
typedef unsigned long u32;
_Static_assert(sizeof(u32) == 4, "68000 data width required");

__attribute__((noipa)) static u32 update(unsigned char *bytes, u32 *pair)
{
    *pair = 0xAABBCCDD;
    bytes[0] = 0x12;
    bytes[1] = 0x34;
    return *pair;
}

int probe(void)
{
    u32 pair;
    return update((unsigned char *)&pair, &pair) != 0x1234CCDD;
}
