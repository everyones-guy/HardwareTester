import unittest

class Test_test_ssh_models(unittest.TestCase):
    def test_A(self):
        self.fail("Not implemented")
        

from HardwareTester.models.ssh_models import SSHConnection
from HardwareTester.extensions import db

# Create a new connection
new_connection = SSHConnection(
    name="Test Server",
    host="192.168.1.100",
    port=22,
    username="admin"
)
new_connection.set_password("securepassword123")
db.session.add(new_connection)
db.session.commit()

# Validate the password
connection = SSHConnection.query.filter_by(name="Test Server").first()
if connection and connection.check_password("securepassword123"):
    print("Password is valid.")
else:
    print("Invalid password.")

# Update the password
connection = SSHConnection.query.filter_by(name="Test Server").first()
if connection:
    connection.set_password("newsecurepassword456")
    db.session.commit()

# Delete the connection
connection = SSHConnection.query.filter_by(name="Test Server").first()
if connection:
    db.session.delete(connection)
    db.session.commit()




if __name__ == '__main__':
    unittest.main()
