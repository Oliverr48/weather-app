class ContactBook:
    def __init__(self):
        self.contacts = {}

    def add_contact(self, name, phone_number):
        if name in self.contacts:
            print(f"Contact '{name}' already exists.")
        else:
            self.contacts[name] = phone_number
            print(f"Contact '{name}' added.")

    def retrieve_contact(self, name):
        return self.contacts.get(name, "Contact not found.")

    def update_contact(self, name, new_phone_number):
        if name in self.contacts:
            self.contacts[name] = new_phone_number
            print(f"Contact '{name}' updated.")
        else:
            print(f"Contact '{name}' not found.")

    def delete_contact(self, name):
        if name in self.contacts:
            del self.contacts[name]
            print(f"Contact '{name}' deleted.")
        else:
            print(f"Contact '{name}' not found.")

    def list_contacts(self):
        if not self.contacts:
            print("No contacts found.")
        else:
            for name, phone_number in self.contacts.items():
                print(f"Name: {name}, Phone Number: {phone_number}")

# Example usage
if __name__ == "__main__":
    contact_book = ContactBook()
    contact_book.add_contact("Alice", "123-456-7890")
    contact_book.add_contact("Bob", "987-654-3210")
    print(contact_book.retrieve_contact("Alice"))
    contact_book.update_contact("Alice", "111-222-3333")
    contact_book.delete_contact("Bob")
    contact_book.list_contacts()