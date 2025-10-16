package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"strings"
	"unsafe"
)

type Core struct {
	key  byte
	size int
}

type Container struct {
	harmless [32]byte
	core     Core
	flag     [64]byte
}

func xorBytes(in []byte, key byte) []byte {
	out := make([]byte, len(in))
	for i := range in {
		out[i] = in[i] ^ key
	}
	return out
}

func main() {
	reader := bufio.NewReader(os.Stdin)

	fmt.Println("========================================")
	fmt.Println("PROMETHEUS FLEET TERMINAL v9.0")
	fmt.Println("\033[1;5;31m ⚠️  ANOMALY: Memory corruption detected! \033[0m")
	fmt.Println("========================================")

	rawFlag := os.Getenv("FLAG")
	if rawFlag == "" {
		rawFlag = "DEBUGFLAG123"
	}

	trueKey := byte(7*6 + 1)
	encrypted := xorBytes([]byte(rawFlag), trueKey)
	flagLen := len(encrypted)

	var container Container
	copy(container.flag[:], encrypted)

	fmt.Printf("PROMETHEUS FLEET AI: Anomaly vector emission: [%d %d %d ...]\n",
		int(trueKey^0x55), int(trueKey^0xAA), int(trueKey^0xFF))

	mem := (*[unsafe.Sizeof(container)]byte)(unsafe.Pointer(&container))

	fmt.Println("PROMETHEUS FLEET AI: Available commands: key, status, reveal, exit")

	for {
		fmt.Print("root@localhost >> ")
		line, _ := reader.ReadString('\n')
		line = strings.TrimSpace(line)
		parts := strings.Fields(line)

		switch {
		case len(parts) == 0:
			continue

		case parts[0] == "key":
			fmt.Println("Enter initialization key (up to 64 bytes):")
			input, _ := reader.ReadString('\n')

			buf := (*[64]byte)(unsafe.Pointer(&container.harmless[0]))
			copy(buf[:], []byte(input))

			fmt.Println("PROMETHEUS FLEET AI: Init complete.")

		case parts[0] == "status":
			leakLen := 16 + rand.Intn(32)
			fmt.Printf("[DUMP] %x\n", mem[:leakLen])

		case parts[0] == "reveal":
			out := xorBytes(container.flag[:flagLen], container.core.key)
			fmt.Printf("[CORE OUTPUT] %s\n", string(out))

		case parts[0] == "exit":
			fmt.Println("PROMETHEUS FLEET AI: Shutting down.")
			return

		default:
			fmt.Println("PROMETHEUS FLEET AI: Unknown command.")
		}
	}
}
