int printf(char *format, ...);

struct a {
    int i1, i2;
    char c;
};

int main()
{
    struct a s;
    s.i1 = 4;
    s.i2 = 7;
    s.c = '\\';
    printf("%d %d %c\n", s.i1, s.i2, s.c);
    return 0;
}
