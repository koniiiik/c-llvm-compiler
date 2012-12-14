int main()
{
    return 0;
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
    for (; ; i -= 1)
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
