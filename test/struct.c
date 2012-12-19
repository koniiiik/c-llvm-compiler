int printf(char *format, ...);

struct a {
    int i1, i2;
    char c;
};

int main()
{
    struct a s, *p;
    s.i1 = 4;
    s.i2 = 7;
    s.c = '\\';
    p = &s;
    printf("%d %d %c\n", s.i1, p->i2, s.c);
    return 0;
}
