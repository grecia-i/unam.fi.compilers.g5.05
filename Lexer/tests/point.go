package main

import "fmt"

type Point struct {
    X, Y int
}

func main() {
    p := Point{X: 3, Y: 4}
    for i := 0; i < 3; i++ {
        fmt.Println("Point:", p)
    }
}