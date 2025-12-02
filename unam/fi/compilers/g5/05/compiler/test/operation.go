package main

import "fmt"

func main() {
    // aritméticas
    a := 2 + 2
    b := 10 - 3
    c := 4 * 5
    d := 20 / 4
    e := 15 % 4
    fmt.Println("Aritmeticas:")
    fmt.Println(a)
    fmt.Println(b)
    fmt.Println(c)
    fmt.Println(d)
    fmt.Println(e)
    // relacionales
    x := 7
    y := 10
    fmt.Println("Relacionales:")
    fmt.Println(x == y)
    fmt.Println(x != y)
    fmt.Println(x > y)
    fmt.Println(x < y)
    fmt.Println(x >= y)
    fmt.Println(x <= y)

    // IF simple
    fmt.Println("IF simple:")
    if (a == 4) {
        fmt.Println("a es 4")
    } else {
        fmt.Println("a NO es 4")
    }

}