from Crypto.Util.number import getPrime, bytes_to_long
import os

N_BITS = 10
N_PRIMES = 74
primes = []
n = 1

while len(primes) < N_PRIMES:
	p = getPrime(N_BITS)

	if not p in primes:
		primes.append(p)
		n *= primes[-1]

e = 65537

flag = os.environ.get('FLAG', "flag{THIS_IS_NOT_REAL_FLAG}")
m = bytes_to_long(flag.encode())
c = pow(m, e, n)

with open("out.txt", 'w') as f:
	f.write(f"c = {c}")
