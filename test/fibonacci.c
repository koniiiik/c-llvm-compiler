int scanf(char *format, ...),
    printf(char *format, ...);

int main()
{
    int a;
    printf("enter a (positive) number: ");
    scanf("%Ld", &a);
    int f[1000];
    f[0] = 0;
    f[1] = 1;
    int i;
    for(i = 0; i < a; i++) {
        f[i+2] = f[i+1] + f[i];
        printf("%Ld\n", f[i+2]);
        if (i > 100)
            break;
    }
    return 0;
}
