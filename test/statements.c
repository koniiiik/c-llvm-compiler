int main()
{
    return 0;
}

int foo1() { return 4.0; }
int foo2() {}

int bar() {
    int i;
    if(0) return 1;
    i++;
}

void statements()
{
    int i, j, k;
    if (1)
        i;
    else if (2)
        j;
    else if (3)
        k;
    while (1) ;
    do k; while(1);
    i = 10;
    for (int i; ; i -= 1)
    {
        int i;
        if(1)
            continue;
        else
            break;
    }
    switch (i+j) {
        i && j;
        case 4: {
            switch (i) {
                case 4: i+=4;
                        break;
            }
        }
        default: i++;
        case 5: i--;
    }
    switch (5) {
        case 3: ;
    }
}
