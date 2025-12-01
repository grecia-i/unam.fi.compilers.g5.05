#include <stdio.h>
#include <stdbool.h>

int fibonacciIterative(int n) {
    if ((n <= 1)) {
        return n;
    }
    int n2 = 0;
    int n1 = 1;
    {
        int i = 2;
        while ((i <= n)) {
            int temp = n1;
            n1 = (n1 + n2);
            n2 = temp;
            i++;
        }
    }
    return n1;
}
int main() {
    printf("%d\n", fibonacciIterative(9));
}