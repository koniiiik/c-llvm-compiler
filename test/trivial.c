int i;

int main()
{
    int j, k;
    i;
    i + j + 31;
    47;
    ~i;
    k = ~j;
    i += k + (5 + 5) - j;
    k -= j;

    i || j && k;

    return 0;
}

void logical_exprs()
{
    int i, j, k;

    i || j && k;
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
    for (i = 10; i; i -= 1)
    {
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
            }
        }
        default: i++;
        case 5: i--;
    }
}
