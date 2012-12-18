int printf(char *format, ...);

int without_args()
{
    printf("without_args called\n");
    return 47;
}

void two_args(int a, int b);

int main()
{
    char *hello_world;
    hello_world = "Hello world \a\b\t\n\f\r\v\"\'\\\?\n";
    printf("it wurkz! %d\n%s", 47, hello_world);
    without_args();
    two_args(4, 7);
    return 0;
}

void two_args(int a, int b)
{
    a + b;
}
