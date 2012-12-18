int printf(char *format, ...);

int main()
{
    char *hello_world;
    hello_world = "Hello world \a\b\t\n\f\r\v\"\'\\\?\n";
    printf("it wurkz! %d\n%s", 47, hello_world);
    return 0;
}
