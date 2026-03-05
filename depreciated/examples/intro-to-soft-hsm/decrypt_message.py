import PyKCS11
import os

# --- Configuration ---
# Adjust this path if your SoftHSMv2 library is in a different location
SOFTHSM2_LIBRARY_PATH = "/usr/lib/softhsm/libsofthsm2.so"
USER_PIN = "1234"
TOKEN_LABEL = "MyToken" # Ensure this matches your token's label
KEY_LABEL = "MyKey"     # Ensure this matches your generated key pair's label

PLAINTEXT_FILE = "python_plaintext.txt" # Not used in decrypt, but for consistency
ENCRYPTED_FILE = "examples/intro-to-soft-hsm/encrypted_message.bin"
DECRYPTED_FILE = "examples/intro-to-soft-hsm/decrypted_message.txt"

# --- Main Script ---
def decrypt_data():
    try:
        # 1. Load the PKCS#11 library
        pkcs11 = PyKCS11.PyKCS11Lib()
        pkcs11.load(SOFTHSM2_LIBRARY_PATH)
        print(f"Loaded PKCS#11 library from {SOFTHSM2_LIBRARY_PATH}")

        # 2. Get the first slot with a token present
        slots = pkcs11.getSlotList(tokenPresent=True)
        if not slots:
            print("Error: No SoftHSMv2 token found. Please ensure it's initialized and present.")
            return

        # Use the first slot found
        slot = slots[0]
        print(f"Found token in slot ID: {slot}")

        # 3. Open a session and log in
        session = pkcs11.openSession(slot, PyKCS11.CKF_RW_SESSION | PyKCS11.CKF_SERIAL_SESSION)
        session.login(USER_PIN)
        print(f"Logged into token '{TOKEN_LABEL}' successfully with User PIN.")

        # 4. Read data from the encrypted file
        if not os.path.exists(ENCRYPTED_FILE):
            print(f"Error: Encrypted file '{ENCRYPTED_FILE}' not found.")
            print("Please run encrypt_message.py first to create it.")
            return

        with open(ENCRYPTED_FILE, 'rb') as f:
            encrypted_data = f.read()
        print(f"Read {len(encrypted_data)} bytes from '{ENCRYPTED_FILE}'.")

        # 5. Find the Private Key for decryption
        priv_key_attrs = [
            (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
            (PyKCS11.CKA_LABEL, KEY_LABEL)
        ]
        private_keys = session.findObjects(priv_key_attrs)
        if not private_keys:
            print(f"Error: Private Key with label '{KEY_LABEL}' not found on token.")
            return
        private_key = private_keys[0]
        print(f"Found Private Key with label '{KEY_LABEL}'.")

        # 6. Decrypt the data using RSA-PKCS-OAEP mechanism
        mechanism = PyKCS11.CKM_RSA_PKCS
        print(f"Decrypting data using mechanism: {mechanism}...")
        decrypted_data = session.decrypt(private_key, encrypted_data, PyKCS11.Mechanism(mechanism))

        with open(DECRYPTED_FILE, 'wb') as f:
            f.write(bytes(decrypted_data))
        print(f"Data decrypted and saved to '{DECRYPTED_FILE}'.")

        # --- Verification ---
        print(f"\nDecrypted message: '{bytes(decrypted_data).decode()}'")

    except PyKCS11.PyKCS11Error as e:
        print(f"PKCS#11 Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure logout and session closure even if errors occur
        if 'session' in locals() and session:
            try:
                session.logout()
                session.closeSession()
                print("\nLogged out and session closed.")
            except PyKCS11.PyKCS11Error as e:
                print(f"Error during logout/session closure: {e}")

if __name__ == "__main__":
    decrypt_data()
