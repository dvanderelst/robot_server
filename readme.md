This is a cleaned up version of the client-server code used for the robot. It has been tested using python 3.

# Usage

## Setting the location of the remote computer

The following settings should be editted in ``Client.py`` to match the location and organization of the remote computer (e.g., the raspberry pi).

```
self.remote = '192.168.0.109'
self.remote_python = '/home/batman/anaconda2/bin/python'
self.remote_dir = '/home/batman/Desktop/server/'
[...]
self.user = 'batman'
self.password = 'robin'
```

## Adding functions

Adding functions that can be called by the client requires 3 steps:

(1) Add a function to the client. The function should use the ``send_command function(cmd, port)`` to communicate with the server.

``cmd``: a string sent to the server
``port``: the port the ``cmd`` is sent to



```
def test_communication(self):
    reply = self.send_command('Test communication', 10000)
    self.print_log([reply])
```

(2) Write a corrsponding function at the server side. The function should take two arguments: ``self`` and a list.

```
def test_communiction(self, args):
    if not type(args) == list: args = [args]
return 'success'
```

(3) In ``Server.py``, bind the server function to a port

```self.open_connection(10000, bind_function=self.test_communiction)```