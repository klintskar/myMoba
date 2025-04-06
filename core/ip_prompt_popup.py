import tkinter as tk
import os

def send_ip():
    ip = entry.get().strip()
    if ip:
        with open("ip_result.txt", "w") as f:
            f.write(ip)
    root.destroy()

root = tk.Tk()
root.title("Enter IP Address")
root.geometry("300x120")

tk.Label(root, text="Enter IP:").pack(pady=10)
entry = tk.Entry(root, width=30)
entry.pack()
entry.focus()

tk.Button(root, text="Connect", command=send_ip).pack(pady=10)

root.mainloop()
