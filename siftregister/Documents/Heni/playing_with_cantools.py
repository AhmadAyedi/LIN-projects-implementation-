import cantools
from pprint import pprint
db = cantools.database.load_file('/home/pi/Documents/Heni/my_can_data_base.dbc')
my_messages = db.messages
my_first_message = my_messages[0]
print(db.messages[0].name)
print("type:", type(my_first_message))

#help(my_first_message)
# help(my_first_message.signals[0])
# example_message = db.get_message_by_name()
# pprint(example_message.signals)
print(cantools.__version__)
