/* Intentional incompatible-pointer aliasing: compatibility policy, not a GCC bug.
 * With strict aliasing enabled this is not valid portable C. */
typedef unsigned short u16;
typedef unsigned long u32;
_Static_assert(sizeof(u16) == 2 && sizeof(u32) == 4, "68000 data widths required");

__attribute__((noipa)) static u32 update(u16 *word, u32 *pair)
{
    *pair = 0xAABBCCDD;
    *word = 0x1234;
    return *pair;
}

int probe(void)
{
    u32 pair;
    return update((u16 *)&pair, &pair) != 0x1234CCDD;
}
