"""
✅ Structure Samjho Pehle
🔹 Code Ka Divide::
User class	Logic (deposit, withdraw, balance update)
ATMSystem class	:User se input lena, menu dikhana, login karwana
main.py	:Welcome screen (Create Account / Login / Exit)
"""
import sqlite3
import hashlib
class Bank:
    def __init__(self, db_name="atm.db"):
        #DB connect
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

         #variabels
        self.transactions = []
        self.create_tables()

    def create_tables(self):
         self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts
                             (acc_no INTEGER PRIMARY KEY AUTOINCREMENT,
                             username TEXT,
                             pin TEXT,
                             balance REAL)
''')
         
         self.cursor.execute(''' CREATE TABLE IF NOT EXISTS transactions
                             (t_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             acc_no INTEGER,
                             details TEXT,
                             amount REAL,
                             FOREIGN KEY(acc_no) REFERENCES accounts(acc_no)
                             )''')
         self.conn.commit()


    
    def create_account(self,name,pin,opening_balance=0):
         #hashed pin
         hashed_pin = hashlib.sha256(pin.encode()).hexdigest()

         #Db insert
         self.cursor.execute(
        "INSERT INTO accounts (username, pin, balance) VALUES (?, ?, ?)",
        (name, hashed_pin, opening_balance) )
         self.conn.commit()
         #return account no.
         acc_no = self.cursor.lastrowid
         print(f"Account created successfully! Your Account No: {acc_no}")
         return acc_no
    


    def verify_login(self,acc_no,pin):
         hashed_pin = hashlib.sha256(pin.encode()).hexdigest()
         self.cursor.execute("SELECT * FROM accounts WHERE acc_no=? AND pin=?", (acc_no, hashed_pin))
         user = self.cursor.fetchone()
         if user:
              print("login successfully")
              return True
         else:
              print("Invalid account no/pin")
              return False

    
    def deposit(self,acc_no,amount):
        self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE acc_no=?", (amount, acc_no))
        self.cursor.execute("INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)", 
                            (acc_no, f"Deposit ₹{amount}", amount))
        self.conn.commit()
        print(f"₹{amount} deposited successfully!")


    
    def withdraw(self, acc_no, amount):
        self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?",(acc_no,))
        result = self.cursor.fetchone()
        if result is None:
         print("Account not found!")
         return
        balance = result[0]
        if amount<=balance:
            self.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE acc_no=?", (amount, acc_no))
            self.cursor.execute(
            "INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)",
            (acc_no, f"Withdrew ₹{amount}", -amount)
        )
            self.conn.commit()
            print(f"₹{amount} withdrawn successfully!")
        else:
            print("You dont have enough money")


    def transfer(self,from_acc, to_acc,amount):
         #check balance
         self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?",(from_acc,))
         result = self.cursor.fetchone()
         if result is None:
              print("Account not found")
              return
         else:
              sender_balance = result[0]
         if amount > sender_balance:
              print("Dont have enough money")
              return
         self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?",(to_acc,))
         receiver = self.cursor.fetchone()
         if receiver is None:
              print("Receiver account not found")
              return
         self.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE acc_no = ?",(amount,from_acc))
         self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE acc_no = ?",(amount,to_acc))
         self.cursor.execute("INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)",(from_acc , f"Transferred ₹{amount} to Acc {to_acc}",-amount))
         self.cursor.execute("INSERT INTO transactions (acc_no, details, amount) VALUES (?, ?, ?)",(to_acc, f"Received ₹{amount} from Acc {from_acc}", amount))
         self.conn.commit()
         print(f"₹{amount} transferred successfully from {from_acc} to {to_acc}") 
    
    def get_balance(self,acc_no):
        self.cursor.execute("SELECT balance FROM accounts WHERE acc_no=?", (acc_no,))
        result = self.cursor.fetchone()
        return result[0]  if result else None
    
    
    def get_mini_statement(self,acc_no):
        self.cursor.execute("SELECT details, amount FROM transactions WHERE acc_no=? ORDER BY t_id DESC LIMIT 5",(acc_no,))
        return self.cursor.fetchall()
    

    def reset_pin(self, acc_no, name):
    # Check if account exists
      self.cursor.execute("SELECT * FROM accounts WHERE acc_no=? AND username=?", (acc_no, name))
      user = self.cursor.fetchone()
      if not user:
        print("Account not found or incorrect name!")
        return False

    # Input new PIN
      new_pin = input("Enter your new PIN: ")
      hashed_pin = hashlib.sha256(new_pin.encode()).hexdigest()

    # Update in DB
      self.cursor.execute("UPDATE accounts SET pin=? WHERE acc_no=?", (hashed_pin, acc_no))
      self.conn.commit()
      print("PIN successfully reset!")
      return True


class Atmsys:
    def __init__(self):
        self.bank = Bank(db_name="atm.db") 
        self.current_user = None
        self.main_menu()   


    def signup(self):
         user_name = input("Enter Your Name:")
         pin = input("Set of pin : ")
         balance = float(input("PLease enter your opening balance :"))
         acc_no = self.bank.create_account(user_name, pin, balance)
         print(f"Your Account Number is: {acc_no}")
         

    def login(self):
         acc_no = int(input("Enter your Account Number: "))
         pin = input("Enter your PIN: ")
         if self.bank.verify_login(acc_no,pin):
              self.current_user = acc_no
              print("Successfully login !!")
              self.user_menu()
         else:
              print("Login failed please try again!!")
              
         
    def deposit(self):
         amount = float(input("Enter the amount :"))
         self.bank.deposit(self.current_user,amount)
        
    
    def withdraw(self):
         amount =float(input("Enter the amount :"))
         self.bank.withdraw(self.current_user,amount) 
    
    def transfer(self):
          to_acc = int(input("Enter receiver account number :"))
          amount = float(input("Enter the amount :"))
          self.bank.transfer(self.current_user,to_acc,amount)

    def change_pin(self):
      acc_no = int(input("Enter your Account Number: "))
      name = input("Enter your Name: ")
      self.bank.reset_pin(acc_no, name)

    def check_balance(self):
      balance = self.bank.get_balance(self.current_user)
      if balance is not None:
        print(f"Your current balance is: ₹{balance}")
      else:
        print("Account not found!")


    def statement(self):
      transactions = self.bank.get_mini_statement(self.current_user)
    
      if not transactions:
        print("No transactions found.")
        return

      print("\n===== Mini Statement =====")
      for txn in transactions:
        details, amount = txn
        print(f"{details} | ₹{amount}")


    
    def user_menu(self):
       while True:
        print("\n===== User Menu =====")
        print("1. Deposit")
        print("2. Withdraw")
        print("3. Transfer")
        print("4. Mini Statement")
        print("5. Check Balance")   
        print("6. Logout")
        
        choice = input("Enter your choice: ")

        if choice == "1":
            self.deposit()
        elif choice == "2":
            self.withdraw()
        elif choice == "3":
            self.transfer()
        elif choice == "4":
            self.statement()
        elif choice == "5":
            self.check_balance()   # ✅ balance check call
        elif choice == "6":
          print("Logging out...")
        self.current_user = None
        break
       else:
        print("Invalid choice! Try again.")

    
    def main_menu(self):
        while True:
          print("\n===== ATM MENU =====")  
          print("1. Create Account")
          print("2. Login")
          print("3. Reset pin")
          print("4. Exit")
          choice = input("Enter your choice: ")
          if choice == "1":
                self.signup()
          elif choice == "2":
                self.login()
          elif choice =="3":
            self.change_pin()
          elif choice == "4":
            print("Thank you for using ATM!")
            exit()
          else:
            print("Invalid choice.")


if __name__ == "__main__":
    Atmsys()
                                    

    

