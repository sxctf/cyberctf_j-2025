import hashlib
from collections import deque
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

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

    def inverse(self):
        pos = self.pos()
        neg = self.neg()

        pos.sort(reverse=True)
        neg.sort()

        neg = list(zip(neg, [True] * len(neg)))
        pos = list(zip(pos, [False] * len(pos)))

        return ThompsonGroupElement(neg + pos)

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

def parse_element(s):
    pos = []
    neg = []
    pos_s = s
    neg_s = ""
    
    neg_ind = s.find('^')

    if neg_ind > 0:
        while s[neg_ind] != 'x':
            neg_ind -= 1

        pos_s = s[: neg_ind]
        neg_s = s[neg_ind :]

    i = 0
    
    while i < len(pos_s):
        if pos_s[i] == 'x':
            i += 1
            num = 0

            while i < len(pos_s) and pos_s[i].isdigit():
                num = num * 10 + int(pos_s[i])
                i += 1

            pos.append(num)

    i = 0

    while i < len(neg_s):
        if neg_s[i] == 'x':
            i += 1
            num = 0

            while i < len(neg_s) and neg_s[i].isdigit():
                num = num * 10 + int(neg_s[i])
                i += 1

            neg.append(num)
            i += 3

    pos = list(zip(pos, [True] * len(pos)))
    neg = list(zip(neg, [False] * len(neg)))
    
    return ThompsonGroupElement(pos + neg)

def attack(w, public_A, public_B, s):
    w = parse_element(w)
    w_inv = w.inverse()

    public_A = parse_element(public_A)
    public_B = parse_element(public_B)

    z1 = public_A * w_inv
    z1 = z1.NF()
    z2 = w_inv * public_B
    z2 = z2.NF()

    az1 = get_As_Form(z1, s)
    az1 = az1.NF()
    bz1 = w_inv * az1.inverse() * public_A
    bz1 = bz1.NF()
    K_A = az1 * public_B * bz1
    K_A = K_A.NF()
    az2 = get_As_Form(z2, s)
    az2 = az2.NF()
    bz2 = public_B * az2.inverse() * w_inv
    bz2 = bz2.NF()
    K_B = bz2 * public_A * az2
    K_B = K_B.NF()
    
    key_A = hashlib.sha256(str(K_A).encode()).digest()
    key_B = hashlib.sha256(str(K_B).encode()).digest()
    
    return key_A, key_B

def get_As_Form(z, s):
    pos = z.pos()
    neg = z.neg()
    r1 = 0
    r2 = 0

    for i in range(len(pos)):
        if pos[i] - i >= s:
            r1 = i - 1
            break

    for i in range(len(neg) - 1, -1, -1):
        if neg[i] - i >= s:
            r2 = i + 1
            break

    r = min(r1, r2)

    pos = pos[: r + 1]
    pos = list(zip(pos, [True] * len(pos)))
    neg = neg[-r - 1 :]
    neg = list(zip(neg, [False] * len(neg)))

    return ThompsonGroupElement(pos + neg)

def decrypt_flag(encrypted_hex, key):
    encrypted = bytes.fromhex(encrypted_hex)
    iv = encrypted[:16]
    ct = encrypted[16:]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ct)

    return plaintext

if __name__ == "__main__":
    s, M = 0, 0
    w = ""
    encrypted_A, encrypted_B = "", ""
    public_A, public_B = "", ""

    with open("out.txt") as file:
        lines = file.readlines()
        s = int(lines[0].split("s = ")[1][: -1])
        M = int(lines[1].split("M = ")[1][: -1])
        w = lines[2].split("w = ")[1][: -1]
        encrypted_A = lines[3].split("encrypted_A = ")[1][: -1]
        public_A = lines[4].split("public_A = ")[1][: -1]
        encrypted_B = lines[6].split("encrypted_B = ")[1][: -1]
        public_B = lines[7].split("public_B = ")[1][: -1]

    key_A, key_B = attack(w, public_A, public_B, s)

    if key_A:
        flag = decrypt_flag(encrypted_A, key_A)
        print(flag)
    if key_B:
        flag = decrypt_flag(encrypted_B, key_B)
        print(flag)


