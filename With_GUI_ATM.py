import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib

# 
class Bank:
    def __init__(self, db_name="atm.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts
                               (acc_no INTEGER PRIMARY KEY AUTOINCREMENT,
                               username TEXT,
                               pin TEXT,
                               balance REAL)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                               (t_id INTEGER PRIMARY KEY AUTOINCREMENT,
                               acc_no INTEGER,
                               details TEXT,
                               amount REAL,
                               FOREIGN KEY(acc_no) REFERENCES accounts(acc_no))''')
        self.conn.commit()

    def create_account(self,name,pin,opening_balance=0):
        hashed_pin = hashlib.sha256(pin.encode()).hexdigest()
        self.cursor.execute("INSERT INTO accounts (username, pin, balance) VALUES (?, ?, ?)",
                            (name, hashed_pin, opening_balance))
        self.conn.commit()
        return self.cursor.lastrowid

    def verify_login(self,acc_no,pin):
        hashed_pin = hashlib.sha256(pin.encode()).hexdigest()
        self.cursor.execute("SELECT * FROM accounts WHERE acc_no=? AND pin=?", (acc_no, hashed_pin))
        return bool(self.cursor.fetchone())

    def deposit(self,acc_no,amount):
        self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE acc_no=?", (amount, acc_no))
        self.cursor.execute("INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)",
                            (acc_no, f"Deposit ₹{amount}", amount))
        self.conn.commit()

    def withdraw(self, acc_no, amount):
        self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?",(acc_no,))
        result = self.cursor.fetchone()
        if not result:
            return False, "Account not found!"
        if amount <= result[0]:
            self.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE acc_no=?", (amount, acc_no))
            self.cursor.execute("INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)",
                                (acc_no, f"Withdrew ₹{amount}", -amount))
            self.conn.commit()
            return True, f"₹{amount} withdrawn successfully!"
        else:
            return False, "Insufficient balance"

    def transfer(self,from_acc, to_acc,amount):
        self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?",(from_acc,))
        sender = self.cursor.fetchone()
        if not sender:
            return False, "Sender account not found"
        if amount > sender[0]:
            return False, "Insufficient balance"
        self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?",(to_acc,))
        if not self.cursor.fetchone():
            return False, "Receiver account not found"
        self.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE acc_no = ?",(amount,from_acc))
        self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE acc_no = ?",(amount,to_acc))
        self.cursor.execute("INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)",
                            (from_acc , f"Transferred ₹{amount} to Acc {to_acc}",-amount))
        self.cursor.execute("INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)",
                            (to_acc, f"Received ₹{amount} from Acc {from_acc}", amount))
        self.conn.commit()
        return True, f"₹{amount} transferred successfully from {from_acc} to {to_acc}"

    def get_balance(self,acc_no):
        self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?", (acc_no,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_mini_statement(self,acc_no):
        self.cursor.execute("SELECT details, amount FROM transactions WHERE acc_no=? ORDER BY t_id DESC LIMIT 5",(acc_no,))
        return self.cursor.fetchall()

    def reset_pin(self, acc_no, name, new_pin):
        self.cursor.execute("SELECT * FROM accounts WHERE acc_no=? AND username=?", (acc_no, name))
        if not self.cursor.fetchone():
            return False
        hashed_pin = hashlib.sha256(new_pin.encode()).hexdigest()
        self.cursor.execute("UPDATE accounts SET pin=? WHERE acc_no=?", (hashed_pin, acc_no))
        self.conn.commit()
        return True

# ===================== Tkinter GUI =====================
class ATMGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Colorful ATM System")
        self.root.geometry("450x500")
        self.root.config(bg="#1e1e2f")
        self.bank = Bank()
        self.current_user = None
        self.create_main_menu()

    # -------- Hover Effect --------
    def on_enter(self,e):
        e.widget['bg'] = "#ffb74d"
    def on_leave(self,e):
        e.widget['bg'] = "#4CAF50"

    # -------- Clear Window --------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # -------- Main Menu --------
    def create_main_menu(self):
        self.clear_window()
        tk.Label(self.root,text="Welcome to  SMART-ATM",fg="white",bg="#1e1e2f",
                 font=("Helvetica",16,"bold")).pack(pady=20)

        tk.Button(self.root,text="Create Account",bg="#4CAF50",fg="white",width=20,command=self.signup).pack(pady=10)
        tk.Button(self.root,text="Login",bg="#2196F3",fg="white",width=20,command=self.login).pack(pady=10)
        tk.Button(self.root,text="Reset PIN",bg="#f44336",fg="white",width=20,command=self.reset_pin_window).pack(pady=10)
        tk.Button(self.root,text="Exit",bg="#9C27B0",fg="white",width=20,command=self.root.quit).pack(pady=10)

    # =================== Signup Window ===================
    def signup(self):
        self.clear_window()
        tk.Label(self.root,text="Create Account",fg="white",bg="#1e1e2f",font=("Helvetica",16,"bold")).pack(pady=20)

        tk.Label(self.root,text="Name:",fg="white",bg="#1e1e2f").pack()
        name_entry = tk.Entry(self.root)
        name_entry.pack(pady=5)

        tk.Label(self.root,text="4-digit PIN:",fg="white",bg="#1e1e2f").pack()
        pin_entry = tk.Entry(self.root, show="*")
        pin_entry.pack(pady=5)

        tk.Label(self.root,text="Opening Balance:",fg="white",bg="#1e1e2f").pack()
        balance_entry = tk.Entry(self.root)
        balance_entry.pack(pady=5)

        def submit():
            name = name_entry.get()
            pin = pin_entry.get()
            try:
                balance = float(balance_entry.get())
            except:
                messagebox.showerror("Error","Invalid balance input")
                return
            if not name or not pin:
                messagebox.showerror("Error","All fields are required")
                return
            acc_no = self.bank.create_account(name,pin,balance)
            messagebox.showinfo("Success",f"Account Created! Your Account No: {acc_no}")
            self.create_main_menu()

        tk.Button(self.root,text="Create Account",bg="#4CAF50",fg="white",width=20,command=submit).pack(pady=10)

    # =================== Login Window ===================
    def login(self):
        self.clear_window()
        tk.Label(self.root,text="Login",fg="white",bg="#1e1e2f",font=("Helvetica",16,"bold")).pack(pady=20)

        tk.Label(self.root,text="Account Number:",fg="white",bg="#1e1e2f").pack()
        acc_entry = tk.Entry(self.root)
        acc_entry.pack(pady=5)

        tk.Label(self.root,text="PIN:",fg="white",bg="#1e1e2f").pack()
        pin_entry = tk.Entry(self.root, show="*")
        pin_entry.pack(pady=5)

        def submit():
            try:
                acc_no = int(acc_entry.get())
            except:
                messagebox.showerror("Error","Invalid account number")
                return
            pin = pin_entry.get()
            if self.bank.verify_login(acc_no,pin):
                self.current_user = acc_no
                messagebox.showinfo("Success","Login Successful!")
                self.user_menu()
            else:
                messagebox.showerror("Error","Invalid Account No/PIN")

        tk.Button(self.root,text="Login",bg="#2196F3",fg="white",width=20,command=submit).pack(pady=10)

    # =================== Reset PIN Window ===================
    def reset_pin_window(self):
        self.clear_window()
        tk.Label(self.root,text="Reset PIN",fg="white",bg="#1e1e2f",font=("Helvetica",16,"bold")).pack(pady=20)

        tk.Label(self.root,text="Account Number:",fg="white",bg="#1e1e2f").pack()
        acc_entry = tk.Entry(self.root)
        acc_entry.pack(pady=5)

        tk.Label(self.root,text="Name:",fg="white",bg="#1e1e2f").pack()
        name_entry = tk.Entry(self.root)
        name_entry.pack(pady=5)

        tk.Label(self.root,text="New PIN:",fg="white",bg="#1e1e2f").pack()
        pin_entry = tk.Entry(self.root, show="*")
        pin_entry.pack(pady=5)

        def submit():
            try:
                acc_no = int(acc_entry.get())
            except:
                messagebox.showerror("Error","Invalid account number")
                return
            name = name_entry.get()
            new_pin = pin_entry.get()
            if self.bank.reset_pin(acc_no,name,new_pin):
                messagebox.showinfo("Success","PIN Reset Successfully!")
                self.create_main_menu()
            else:
                messagebox.showerror("Error","Account not found or name incorrect")

        tk.Button(self.root,text="Reset PIN",bg="#f44336",fg="white",width=20,command=submit).pack(pady=10)

    # =================== User Menu ===================
    def user_menu(self):
        self.clear_window()
        tk.Label(self.root,text=f"Welcome User {self.current_user}",fg="white",bg="#1e1e2f",
                 font=("Helvetica",14,"bold")).pack(pady=20)

        tk.Button(self.root,text="Deposit",bg="#4CAF50",fg="white",width=20,command=self.deposit_window).pack(pady=5)
        tk.Button(self.root,text="Withdraw",bg="#f44336",fg="white",width=20,command=self.withdraw_window).pack(pady=5)
        tk.Button(self.root,text="Transfer",bg="#2196F3",fg="white",width=20,command=self.transfer_window).pack(pady=5)
        tk.Button(self.root,text="Check Balance",bg="#00BCD4",fg="white",width=20,command=self.check_balance_window).pack(pady=5)
        tk.Button(self.root,text="Mini Statement",bg="#FF9800",fg="white",width=20,command=self.mini_statement).pack(pady=5)
        tk.Button(self.root,text="Logout",bg="#9C27B0",fg="white",width=20,command=self.logout).pack(pady=5)

    # =================== Check Balance Window ===================
    def check_balance_window(self):
      balance = self.bank.get_balance(self.current_user)
      if balance is not None:
        messagebox.showinfo("Balance",f"Your current balance is: ₹{balance}")
      else:
        messagebox.showerror("Error","Account not found!")


    # =================== Deposit Window ===================
    def deposit_window(self):
        self.clear_window()
        tk.Label(self.root,text="Deposit Amount",fg="white",bg="#1e1e2f",font=("Helvetica",16,"bold")).pack(pady=20)
        tk.Label(self.root,text="Amount:",fg="white",bg="#1e1e2f").pack()
        amt_entry = tk.Entry(self.root)
        amt_entry.pack(pady=5)

        def submit():
            try:
                amount = float(amt_entry.get())
            except:
                messagebox.showerror("Error","Invalid input")
                return
            self.bank.deposit(self.current_user,amount)
            messagebox.showinfo("Success",f"₹{amount} deposited successfully!")
            self.user_menu()

        tk.Button(self.root,text="Deposit",bg="#4CAF50",fg="white",width=20,command=submit).pack(pady=10)

    # =================== Withdraw Window ===================
    def withdraw_window(self):
        self.clear_window()
        tk.Label(self.root,text="Withdraw Amount",fg="white",bg="#1e1e2f",font=("Helvetica",16,"bold")).pack(pady=20)
        tk.Label(self.root,text="Amount:",fg="white",bg="#1e1e2f").pack()
        amt_entry = tk.Entry(self.root)
        amt_entry.pack(pady=5)

        def submit():
            try:
                amount = float(amt_entry.get())
            except:
                messagebox.showerror("Error","Invalid input")
                return
            success,msg = self.bank.withdraw(self.current_user,amount)
            if success:
                messagebox.showinfo("Success",msg)
            else:
                messagebox.showerror("Error",msg)
            self.user_menu()

        tk.Button(self.root,text="Withdraw",bg="#f44336",fg="white",width=20,command=submit).pack(pady=10)

    # =================== Transfer Window ===================
    def transfer_window(self):
        self.clear_window()
        tk.Label(self.root,text="Transfer Money",fg="white",bg="#1e1e2f",font=("Helvetica",16,"bold")).pack(pady=20)

        tk.Label(self.root,text="Receiver Account Number:",fg="white",bg="#1e1e2f").pack()
        acc_entry = tk.Entry(self.root)
        acc_entry.pack(pady=5)

        tk.Label(self.root,text="Amount:",fg="white",bg="#1e1e2f").pack()
        amt_entry = tk.Entry(self.root)
        amt_entry.pack(pady=5)

        def submit():
            try:
                to_acc = int(acc_entry.get())
                amount = float(amt_entry.get())
            except:
                messagebox.showerror("Error","Invalid input")
                return
            success,msg = self.bank.transfer(self.current_user,to_acc,amount)
            if success:
                messagebox.showinfo("Success",msg)
            else:
                messagebox.showerror("Error",msg)
            self.user_menu()

        tk.Button(self.root,text="Transfer",bg="#2196F3",fg="white",width=20,command=submit).pack(pady=10)

    # =================== Mini Statement ===================
    def mini_statement(self):
        transactions = self.bank.get_mini_statement(self.current_user)
        if not transactions:
            messagebox.showinfo("Mini Statement","No transactions found")
            return
        stmt = ""
        for t in transactions:
            stmt += f"{t[0]} | ₹{t[1]}\n"
        messagebox.showinfo("Mini Statement",stmt)

    # =================== Logout ===================
    def logout(self):
        self.current_user = None
        messagebox.showinfo("Logout","Logged out successfully")
        self.create_main_menu()

# ===================== Run App =====================
if __name__ == "__main__":
    root = tk.Tk()
    app = ATMGUI(root)
    root.mainloop()
