from scapy.all import get_if_list


print("Available network interfaces:")
print("-" * 40)

for interface in get_if_list():
    print(interface)