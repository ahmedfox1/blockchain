

import argparse
import copy
import hashlib
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--fast", action="store_true")
parser.add_argument("--difficulty", type=int, default=4)
parser.add_argument("--stage", type=int, default=1)
args = parser.parse_args()

DIFFICULTY = args.difficulty


if os.name == "nt":
    os.system("")

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
PURPLE = "\033[95m"
BOLD = "\033[1m"
GRAY = "\033[2m"
RESET = "\033[0m"


def header(text):
    print(f"\n{BOLD}{CYAN}{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}{RESET}")


def good(text):
    print(f"{GREEN}✔ {text}{RESET}")


def fail(text):
    print(f"{RED}✘ {text}{RESET}")


def note(text):
    print(f"{YELLOW}> {text}{RESET}")


def zico(text):
   
    print(f"{PURPLE}[زيكو] {text}{RESET}")


def wait():
    if not args.fast:
        input(f"{GRAY}\n[Enter]{RESET}")


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ================== Block ==================

class Block:
    def __init__(self, index, data, prev_hash, timestamp=None):
        self.index = index
        self.data = data              
        self.prev_hash = prev_hash    
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.nonce = 0               
        self.hash = self.calc_hash()

    def calc_hash(self):

        block_string = json.dumps({
            "index": self.index,
            "data": self.data,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }, sort_keys=True, ensure_ascii=False)
        return sha256(block_string)

    def mine(self, difficulty, live=False):

        target = "0" * difficulty
        start = time.time()
        self.nonce = 0
        self.hash = self.calc_hash()

        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calc_hash()

            if live and self.nonce % 25000 == 0:
                print(f"\r  {GRAY}nonce = {self.nonce:,}  ->  {self.hash[:20]}...{RESET}", end="", flush=True)

        if live:
            print("\r" + " " * 70 + "\r", end="")
        return time.time() - start

    def print_block(self):
        print(f"{BOLD}  +-- Block #{self.index}{RESET}")
        for line in self.data:
            print(f"  |   {line}")
        print(f"  |   nonce     : {self.nonce:,}")
        print(f"  |   prev_hash : {self.prev_hash[:20]}...")
        print(f"  +-- hash      : {GREEN}{self.hash[:20]}...{RESET}")


# ================== Blockchain ==================

class Blockchain:
    def __init__(self, difficulty=DIFFICULTY):
        self.difficulty = difficulty
        genesis = Block(0, ["Genesis Block"], "0" * 64, timestamp=0)
        genesis.mine(difficulty)
        self.chain = [genesis]

    def add_block(self, data, live=False):
        last = self.chain[-1]
        new_block = Block(len(self.chain), data, last.hash)
        t = new_block.mine(self.difficulty, live)
        self.chain.append(new_block)
        return new_block, t

    def is_valid(self, explain=False):

        target = "0" * self.difficulty

        for i, block in enumerate(self.chain):
            if block.hash != block.calc_hash():
                if explain:
                    fail(f"Block #{i}: الداتا اتغيرت.. البصمة مش مطابقة")
                return False

            if not block.hash.startswith(target):
                if explain:
                    fail(f"Block #{i}: مش متعدن.. البصمة مش بادئة بـ {target}")
                return False

            if i > 0 and block.prev_hash != self.chain[i - 1].hash:
                if explain:
                    fail(f"Block #{i}: السلسلة مقطوعة.. prev_hash مش بيشاور على Block #{i - 1}")
                return False

        if explain:
            good("السلسلة سليمة 100%")
        return True

    def print_chain(self):
        for block in self.chain:
            block.print_block()
            if block.index != len(self.chain) - 1:
                print("        |")
                print("        v")


transactions = [
    ["أحمد -> محمد : 10"],
    ["محمد -> سارة : 4", "سارة -> يوسف : 1"],
    ["يوسف -> أحمد : 2"],
    ["سارة -> محمد : 3"],
]


def make_chain(live=False):
    bc = Blockchain()
    for t in transactions:
        bc.add_block(t, live)
    return bc


# ================== المراحل ==================

def stage1():
    header("1) البصمة - SHA-256")

    a = "أحمد -> محمد : 10"
    b = "أحمد -> محمد : 90"

    note(f"النص: {a}")
    print(f"  {GREEN}{sha256(a)}{RESET}")

    note("نفس النص تاني:")
    print(f"  {GREEN}{sha256(a)}{RESET}")
    good("نفس الكلام = نفس البصمة")

    note(f"هغير رقم واحد بس: {b}")
    print(f"  {RED}{sha256(b)}{RESET}")

    changed = sum(1 for x, y in zip(sha256(a), sha256(b)) if x != y)
    fail(f"البصمة اتغيرت كلها.. {changed} من 64 حرف مختلفين")
    wait()


def stage2():
    header("2) السلسلة")
    note(f"ببني سلسلة من {len(transactions) + 1} بلوكات (difficulty = {DIFFICULTY})\n")

    bc = make_chain()
    bc.print_chain()

    print()
    note("كل بلوك شايل بصمة اللي قبله في prev_hash")
    bc.is_valid(explain=True)
    wait()
    return bc


def stage3():
    header("3) التعدين - Proof of Work")
    note("البلوك مش بيتقبل غير لو البصمة بتاعته بادئة بأصفار")
    note("ومفيش طريقة غير اننا نجرب nonce ورا nonce\n")

    for d in range(1, max(DIFFICULTY, 4) + 2):
        test = Block(1, ["test"], "0" * 64, timestamp=1)
        t = test.mine(d, live=True)
        zeros = "0" * d
        print(f"  difficulty {d} ({zeros:<6}) : {test.nonce + 1:>10,} محاولة  |  {t:6.2f} ثانية  |  {test.hash[:16]}...")

    print()
    good("كل صفر زيادة = شغل اكتر بحوالي 16 مرة")
    note("البيتكوين الحقيقي بيعمل مليارات المحاولات في الثانية")
    wait()


def stage4(bc=None):
    header("4) يلا نهكرها")

    if bc is None:
        note("ببني سلسلة جديدة...")
        bc = make_chain()

    target = 1

    # ---- محاولة 1: الاستيكة ----
    print(f"\n{BOLD}محاولة 1: اغير الرقم وخلاص{RESET}")
    try1 = copy.deepcopy(bc)
    before = try1.chain[target].data[0]
    try1.chain[target].data[0] = before.replace("10", "1000")
    zico(f"قبل: {before}")
    zico(f"بعد: {try1.chain[target].data[0]}")
    try1.is_valid(explain=True)
    wait()

    # ---- محاولة 2: احسب بصمة جديدة ----
    print(f"\n{BOLD}محاولة 2: اغير الرقم واحسب البصمة من جديد{RESET}")
    try2 = copy.deepcopy(try1)
    try2.chain[target].hash = try2.chain[target].calc_hash()
    zico("حسبت بصمة جديدة")
    try2.is_valid(explain=True)
    wait()

    # ---- محاولة 3: اعدن البلوك المزور ----
    print(f"\n{BOLD}محاولة 3: اعدن البلوك المزور{RESET}")
    try3 = copy.deepcopy(try1)
    t = try3.chain[target].mine(try3.difficulty, live=True)
    zico(f"عدنت Block #{target} في {t:.2f} ثانية")
    try3.is_valid(explain=True)
    note("البلوك اللي بعده لسه شايل البصمة القديمة")
    wait()

    # ---- محاولة 4: اعيد تعدين كل حاجة بعده ----
    print(f"\n{BOLD}محاولة 4: اعدن البلوك المزور وكل اللي بعده{RESET}")
    try4 = copy.deepcopy(try1)
    total = 0
    for i in range(target, len(try4.chain)):
        if i > target:
            try4.chain[i].prev_hash = try4.chain[i - 1].hash
        t = try4.chain[i].mine(try4.difficulty, live=True)
        total += t
        zico(f"عدنت Block #{i} ({t:.2f} ثانية)")

    zico(f"خلصت التزوير في {total:.2f} ثانية")
    try4.is_valid(explain=True)
    print(f"\n{YELLOW}{BOLD}  استنى.. التزوير نجح؟!{RESET}")
    wait()

    return bc, try4, target


def forge_quietly():
    # بنجهز سلسلة مزورة من غير طباعة (لو بدأنا من المرحلة 5 على طول)
    bc = make_chain()
    fake = copy.deepcopy(bc)
    fake.chain[1].data[0] = fake.chain[1].data[0].replace("10", "1000")
    for i in range(1, len(fake.chain)):
        if i > 1:
            fake.chain[i].prev_hash = fake.chain[i - 1].hash
        fake.chain[i].mine(fake.difficulty)
    return bc, fake, 1


def stage5(bc=None, fake=None, target=1):
    header("5) السر الحقيقي: الشبكة")

    if bc is None or fake is None:
        note("بجهز السلسلة الاصلية والمزورة...")
        bc, fake, target = forge_quietly()

    note("السلسلة مش على جهاز واحد.. فيه نسخة عند الاف الاجهزة")
    note("وزيكو بيزور، باقي الشبكة كملت شغل عادي:")

    real = copy.deepcopy(bc)
    for t in (["يوسف -> سارة : 5"], ["محمد -> أحمد : 1"]):
        block, sec = real.add_block(t, live=True)
        good(f"الشبكة ضافت Block #{block.index} ({sec:.2f} ثانية)")

    nodes = {
        "Node 1": copy.deepcopy(real),
        "Node 2": copy.deepcopy(real),
        "Node 3": copy.deepcopy(real),
        "Node 4": copy.deepcopy(real),
        "زيكو": fake,
    }

    print(f"\n{BOLD}  القاعدة: الكل بيصدق اطول سلسلة سليمة{RESET}")
    for name, chain in nodes.items():
        status = f"{GREEN}سليمة{RESET}" if chain.is_valid() else f"{RED}بايظة{RESET}"
        tag = f" {PURPLE}(مزورة){RESET}" if name == "زيكو" else ""
        print(f"  {name:<8} | طول السلسلة = {len(chain.chain)} | {status}{tag}")

    valid_chains = [c for c in nodes.values() if c.is_valid()]
    winner = max(valid_chains, key=lambda c: len(c.chain))
    agree = sum(1 for c in nodes.values() if c.chain[-1].hash == winner.chain[-1].hash)

    print()
    good(f"الشبكة اختارت الاطول.. {agree} من {len(nodes)} متفقين")
    fail("سلسلة زيكو اترفضت لانها اقصر")
    note(f"Block #{target} لسه فيه: {winner.chain[target].data[0]}")

    print(f"\n{YELLOW}  علشان زيكو ينجح لازم يعدن اسرع من الشبكة كلها")
    print(f"  يعني يبقى معاه اكتر من 51% من قوتها{RESET}")
    wait()


def summary():
    header("الخلاصة")
    print("  1. البصمة: اي تغيير ولو حرف بيغير البصمة كلها")
    print("  2. السلسلة: كل بلوك شايل بصمة اللي قبله فالتزوير بيبوظ اللي بعده")
    print("  3. التعدين: اعادة كتابة التاريخ محتاجة شغل كتير جدا")
    print("  4. الشبكة: لازم تسبق الاف الاجهزة مع بعض")
    print(f"\n{GRAY}  Eng. Ahmed Sameh | مشروع تعليمي، مش عملة{RESET}\n")


def main():
    print(f"\n{BOLD}{CYAN}  Blockchain from scratch | difficulty = {DIFFICULTY}{RESET}")
    print(f"{GRAY}  مشروع تعليمي بس.. مش عملة ومالوش قيمة{RESET}")

    bc = fake = None
    target = 1

    if args.stage <= 1:
        stage1()
    if args.stage <= 2:
        bc = stage2()
    if args.stage <= 3:
        stage3()
    if args.stage <= 4:
        bc, fake, target = stage4(bc)
    if args.stage <= 5:
        stage5(bc, fake, target)

    summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  bye")



