 package main

        import "fmt"

        func fibonacciIterative(n int) int {
            if n <= 1 {
                return n
            }
            var n2, n1 = 0, 1
            for i := 2; i <= n; i++ {
                n2, n1 = n1, n1+n2
            }
            return n1
        }
        
        func main() {
            fmt.Println(fibonacciIterative(9))  // Output: 34
        }
        