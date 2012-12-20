int main() {
    int a;
    a = (512, 3.l, .4F, 23 + 42.5f); //, 4*7;
    double b;
    'a', '\b', '\x123432', '\134';
    b = .4;
    char c;
    c = 'e', !0.0, !0, !3, !.5, !b, !c, !a;
    a = b * c / 4.0 / 5 * 20;
    // This should fail to compile and it indeed does:
    // a = 4 % b;
    // This should fail to compile but does not: (consider it a feature)
    a = 4 % 3.0;
    a %= 3*(int)4.0;
    // FIXME: a = c % 3;
    a = b + 47 - 42, a += +3, -4, -4.0, +b, -c, -b;
    //a == b;
    //47*d ? 1 || 2 || 3 && 4 : 1 | 2 & 7 ^ 3;
    //1 != 2 == 5 % 4;
    a >>= 1 << 4 >> 512;
    a |= a ^ (int)b & 3 | 1;
    int g;
    g = (int) b;
    return 0;
}
int foo, bar;
