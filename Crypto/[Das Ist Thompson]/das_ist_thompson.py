import random
import hashlib
from collections import deque
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import os

class ThompsonGroupElement:
    def __init__(self, word):
        self.word = word
    
    def __mul__(self, other):
        return ThompsonGroupElement(self.word + other.word)

    def __str__(self):
        return ''.join(f'x{i[0]}{'^-1' if not i[1] else ''}' for i in self.word)
    
    def __len__(self):
        return len(self.word)

    def letter(self, ind):
        return ThompsonGroupElement([(self.word[ind])])

    def pos(self):
        res = []

        for w in self.word:
            if w[1]:
                res.append(w[0])

        return res

    def neg(self):
        res = []

        for w in self.word:
            if not w[1]:
                res.append(w[0])

        return res

    def NF(self):
        u = self.SNF()

        s1, s2 = 0, 0
        w1, w2 = deque(), deque()
        u1, u2 = deque(u.pos()), deque(u.neg())
        S1, S2 = deque(), deque()

        while len(u1) > 0 or len(u2) > 0:
            if len(u1) > 0 and (len(u2) == 0 or u1[-1] > u2[0]):
                w1.appendleft(u1.pop())
                S1.appendleft(0)
            elif len(u2) > 0 and (len(u1) == 0 or u2[0] > u1[-1]):
                w2.append(u2.popleft())
                S2.appendleft(0)
            elif u1[-1] == u2[0]:
                if (len(w1) > 0 and len(w2) > 0 and w1[0] - S1[0] != u1[-1] and w1[0] - S1[0] != u1[-1] + 1 and w2[-1] - S2[0] != u1[-1] and w2[-1] - S2[0] != u1[-1] + 1):
                    u1.pop()
                    u2.popleft()

                    if len(S1) > 0:
                        S1[0] += 1
                    if len(S2) > 0:
                        S2[0] += 1
                elif (len(w1) > 0 and (w1[0] - S1[0] == u1[-1] or w1[0] - S1[0] == u1[-1] + 1)) or (len(w2) > 0 and (w2[-1] - S2[0] == u1[-1] or w2[-1] - S2[0] == u1[-1] + 1)):
                    w1.appendleft(u1.pop())
                    w2.append(u2.popleft())
                    S1.appendleft(0)
                    S2.appendleft(0)
                elif len(w1) == 0 or len(w2) == 0:
                    u1.pop()
                    u2.popleft()
                    S1.appendleft(1)
                    S2.appendleft(1)

        for i in range(len(w1)):
            s1 += S1.popleft()
            u1.append(w1[i] - s1)

        for i in range(len(w2) - 1, -1, -1):
            s2 += S2.popleft()
            u2.appendleft(w2[i] - s2)

        u1 = ThompsonGroupElement(list(zip(list(u1), [True] * len(u1))))
        u2 = ThompsonGroupElement(list(zip(list(u2), [False] * len(u2))))

        return u1 * u2
    
    def SNF(self):
        new_word = self.word.copy()
        changed = True

        while changed:
            changed = False

            for i in range(1, len(new_word)):
                if new_word[i][1] and new_word[i - 1][0] > new_word[i][0]:
                    temp = new_word[i]
                    new_word[i] = (new_word[i - 1][0] + 1, new_word[i - 1][1])
                    new_word[i - 1] = temp
                    changed = True
                    break
                if not new_word[i - 1][1] and new_word[i - 1][0] < new_word[i][0]:
                    temp = new_word[i - 1]
                    new_word[i - 1] = (new_word[i][0] + 1, new_word[i][1])
                    new_word[i] = temp
                    changed = True
                    break
                if new_word[i - 1][0] == new_word[i][0] and new_word[i - 1][1] != new_word[i][1]:
                    if i < len(new_word) - 1:
                        new_word = new_word[: i - 1] + new_word[i + 1 :]
                    else:
                        new_word = new_word[: i - 1]
                    changed = True
                    break
        
        return ThompsonGroupElement(new_word)

class ThompsonGroupKeyExchange:
    def __init__(self):
        self.s = random.randint(3, 8)
        self.M = random.choice(range(256, 321, 2))

    def get_public_constants(self):
        return self.s, self.M
    
    def random_element(self, generator_indices, length):
        signs = list()
        element = ThompsonGroupElement([]) 
        
        while len(element) < length:
            idx = random.choice(generator_indices)

            if random.random() < 0.5:
                new_element = ThompsonGroupElement([(idx, True)])
            else:
                new_element = ThompsonGroupElement([(idx, False)])
            
            element = element * new_element
            element = element.NF()
        
        return element
    
    def generate_w(self):
        generator_indices = list(range(self.s + 3))

        return self.random_element(generator_indices, self.M)
    
    def generate_a(self):
        element = ThompsonGroupElement([])
        
        while len(element) < self.M:
            i = random.randint(1, self.s)
            
            if random.random() < 0.5:
                new_element = ThompsonGroupElement([(0, True), (i, False)])
            else:
                new_element = ThompsonGroupElement([(i, True), (0, False)])
            
            element = element * new_element
            element = element.NF()
        
        return element
    
    def generate_b(self):
        generator_indices = list(range(self.s + 1, 2 * self.s + 1))

        return self.random_element(generator_indices, self.M)
    
    def generate_key_material(self):
        w = self.generate_w()
        
        a1 = self.generate_a()
        b1 = self.generate_b()
        a2 = self.generate_a()
        b2 = self.generate_b()
        
        A = a1 * w * b1
        A = A.NF()
        B = b2 * w * a2
        B = B.NF()
        
        K_A = a1 * B * b1
        K_B = b2 * A * a2
        
        return str(w), str(K_A.NF()), str(A), str(K_B.NF()), str(B)

def encrypt_msg(msg, key):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(msg.encode(), AES.block_size))

    return iv + ct

def decrypt_msg(encrypted, key):
    iv = encrypted[:16]
    ct = encrypted[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ct), AES.block_size)

    return plaintext.decode()

if __name__ == "__main__":
    GKE = ThompsonGroupKeyExchange()
    s, M = GKE.get_public_constants()
    w, secret_A, public_A, secret_B, public_B = GKE.generate_key_material()
    key_A = hashlib.sha256(secret_A.encode()).digest()
    key_B = hashlib.sha256(secret_B.encode()).digest()

    msg = os.environ.get('FLAG', "flag{THIS_IS_NOT_REAL_FLAG}")
    encrypted_A = encrypt_msg(msg, key_A)
    decrypted_A = decrypt_msg(encrypted_A, key_A)
    encrypted_B = encrypt_msg(msg, key_B)
    decrypted_B = decrypt_msg(encrypted_B, key_B)

    with open("out.txt", 'w') as file:
        file.write(f"s = {s}\n")
        file.write(f"M = {M}\n")
        file.write(f"w = {w}\n")

        if decrypted_A == msg:
            file.write(f"encrypted_A = {encrypted_A.hex()}\n")
            file.write(f"public_A = {public_A}\n\n")

        if decrypted_B == msg:
            file.write(f"encrypted_B = {encrypted_B.hex()}\n")
            file.write(f"public_B = {public_B}\n")