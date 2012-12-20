int scanf(char *format, ...),
    printf(char *format, ...);

int main()
{
    int a;
    printf("type a number here: ");
    scanf("%d", &a);
    int f[10000000];
    f[0] = 0;
    f[1] = 1;
    int i;
    // TODO? i++ does not work!
    for(i = 0; i < a; i+=1) {
        f[i+2] = f[i+1] + f[i];
        printf("%Ld\n", f[i+2]);
    }
    return 0;
}
