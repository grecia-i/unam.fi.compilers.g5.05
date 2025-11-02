/*package main

import "fmt"

func main() {
	// fibonacci
	n := 10
	// number of fib numbs to generate
	a, b := 0,1
	for i := 0; i<n ; i++ {
		fmt.Println(a)
		a, b = b, a+b

	}
}*/

package main

import "fmt"

func fibonacciIterative(n int) int {
	if n <= 1 {
		return n
	}
	var n2, n1 int = 0, 1
	for i := 2; i <= n; i++ {
		temp := n1      
		n1 = n1 + n2     
		n2 = temp        
	}
	return n1
}

func main() {
	fmt.Println(fibonacciIterative(9)) // Output: 34
}