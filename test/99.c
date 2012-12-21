int printf(char *format, ...),
    scanf(char *format, ...);

int main()
{
    int a;
    printf("Enter a positive number: ");
    scanf("%lld", &a);
    while (a)
    {
        printf("%lld\n", a);
        a -= 1;
    }
    return 0;
}
