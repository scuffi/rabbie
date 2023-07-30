
# <p align="center"><img alt="Rabbie Logo" src="https://i.imgur.com/WGK8pP1.png"></p>


<p align="center">
<img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/scuffi/rabbie"> <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/rabbie"> <img alt="GitHub" src="https://img.shields.io/github/license/scuffi/rabbie"> <a href="https://pypi.org/project/rabbie/"><img alt="PyPI" src="https://img.shields.io/pypi/v/rabbie"></a>
</p>


Rabbie is a Python package designed to provide a simple and helpful interface for interacting with AMQP message brokers, with a particular focus on RabbitMQ. This package is perfect for developers who want to build robust, scalable, and fault-tolerant messaging systems in Python without the need for extensive knowledge of AMQP protocol.

Rabbie provides a high-level API for sending and receiving messages using RabbitMQ, allowing developers to focus on their application logic rather than low-level details of AMQP. It includes features such as easy setup of exchanges, queues, and bindings, support for message publishing and consuming, automatic message acknowledgments, and easy handling of message routing.

Rabbie also provides support for various RabbitMQ features such as message persistence, TTL, priority queues, and exclusive queues. It allows developers to configure and fine-tune these features with ease using its simple and intuitive API.


## 🧐 Features    
- Multiple Workers per queue
- Multiple listeners per message broker
- Easy decorator interface
- Decoders to allow for JSON (or other) messages
- Hot reloading (COMING SOON)


## 🛠️ Installation
To install Rabbie, simply run:
```bash
pip install rabbie
```

> *You of course need a message broker instance to connect to when using Rabbie*

## 🧑🏻‍💻 Usage
The basic usage to register Listeners with a few listeners:
```python
from rabbie import consumer

@consumer.listen(queue="my_queue", workers=3)
def myfunction():
    print("I've been messaged!")

@consumer.listen(queue="my_other_queue", workers=1)
def my_other_function():
    print("I've been messaged again!")

if __name__ == "__main__":
    consumer.start()
```

The method above assumes a localhost rabbie instance with default credentials, to use custom credentials, adapt the code like so:
```python
from rabbie import Consumer

consumer = Consumer(
    host="localhost",
    port=5672,
    username="user",
    password="password",
)

@consumer.listen(queue="my_queue", workers=3)
def myfunction():
    print("I've been messaged!")

if __name__ == "__main__":
    consumer.start()
```

> ℹ️ Each Rabbie worker will be in use the entire time your custom function is running, i.e. if you have 3 workers, they can all process 1 message at a time and will not pick up anymore until the entire process has been complete. *(You can add a prefetch to allow for internal message queues)*

> ℹ️ If you're not using default connection details (Username & Password), you can provide a pika.Parameters object (such as URLParameters) into the `Consumer(connection_parameters=...)`

### 🎱 Parameters
Rabbie automatically picks up the parameters your function wants depending on the types of them:
```python
from rabbie import Consumer, Channel, Method, Properties

consumer = Consumer(
    ...
)

@consumer.listen(queue="my_queue", workers=3)
def myfunction(body: bytes, channel: Channel, method: Method, properties: Properties):
    print("I've been messaged!")

if __name__ == "__main__":
    consumer.start()
```

> ℹ️ Any parameters that don't have a defined type, or cannot be mapped will be default provided with the message body

### 🪹 Nested Consumers
If you want to have a more complex tree of consumers, you can use a 'MicroConsumer', this allows you to create your consumers anywhere in your code, which can help for readability and organisation if you have a lot of consumers:

`my_module.py`
```python
from rabbie import MicroConsumer

import my_module

nested_consumer = MicroConsumer()

@nested_consumer.listen(queue="my_queue", workers=2)
def my_function():
    print("Hello from a nested listener!")
```
`main.py`
```python
from rabbie import Consumer

import my_module

consumer = Consumer(
    ...
)

if __name__ == "__main__":
    consumer.add_consumer(my_module.nested_consumer)
    consumer.start()
```
### 💾 Encoders & Decoders
When receiving messages through Rabbie, you have the option to pass a Decoder. This acts as a preliminary step before the data passes into your function. If you received a message like: `{"hello": "world"}`, you can use the inbuilt `JSONDecoder` to automatically parse this text into a dictionary:
```python
from rabbie import Consumer, JSONDecoder

consumer = Consumer(
    host="localhost",
    port=5672,
    username="user",
    password="password",
    default_decoder=JSONDecoder()
)

@consumer.listen(queue="my_queue", workers=3, decoder=JSONDecoder())
def myfunction():
    print("I've been messaged!")

if __name__ == "__main__":
    consumer.start()
```

> ℹ️ A Consumer and an individual Listener can take a decoder. The decoder passed into the listener will always take precedence over the consumers decoder.


If you have some more complex messaging system that possibly involves encryption, you can create your own Decoder to implement custom preprocessing like so:
```python
from rabbie import Decoder

class CustomDecoder(Decoder):
    def decode(self, body: bytes):
        return # Your custom logic here

consumer = Consumer(
    ...
    default_decoder=CustomDecoder()
)
```

Encoders work in the exact same way (just to encode outgoing messages rather than decode incoming), however you have a new function `content_type()` to override when encoding the message in a particular fashion, this will be the content type sent in the request, and should reflect the bodies applicatio type. *For example the inbuilt JSONEncoder returns a 'application/json' content type*
```python
from rabbie import Encoder

class CustomEncoder(Encoder):
    def encoder(self, body: bytes):
        return # Your custom logic here

    def content_type(self):
        return "application/my_type"
```
    
### 🎫 Event Handling
If you want to add custom logic depending on whether or not your listeners are connected, or any error handling, you can use event handlers.

Event handlers allow you to create callbacks for specific events that happen, such as on start and on stop.

```python
from rabbie import Consumer, event_handler

@event_handler.register("on_start")
def on_start():
    print("I know all my listeners have started now!")

@event_handler.register("on_stop")
def on_stop():
    print("All my listeners are dead")

consumer = Consumer(
    ...
)

if __name__ == "__main__":
    consumer.start()
```
The defined functions will then get called when the given event is triggered behind the scenes.

> ℹ️ Events can have multiple callbacks associated with them, so you can have as many on_start handlers as you please!

List of current events:
| Event ID | Trigger |
|---|---|
| on_start | When the application starts and all registered listeners have successfully connected. |
| on_stop | When all active listeners have closed their connections. |

### 🖨️ Producers
Producers allow for a simple way to publish messages to exchanges. A simple example would be like so:
```python
from rabbie import Producer, JSONEncoder

producer = Producer(
    host="localhost",
    port=5672,
    username="user",
    password="password",
)

if __name__ == "__main__":
    with producer.connect() as channel:
        channel.publish("hello world!", "my_queue")
```

Producers also support encoders (same interfaces as decoders, just the opposing side) like so:
```python
from rabbie import Producer, JSONEncoder

from my_encoders import CustomEncoder

producer = Producer(
    host="localhost",
    port=5672,
    username="user",
    password="password",
)

if __name__ == "__main__":
    with producer.connect(encoder=JSONEncoder()) as channel:
        channel.publish({"hello": "world"}, "my_queue", encoder=CustomEncoder())
```
> ℹ️ Notice above two encoders are specified. Any parameters passed in to the `channel.publish()` method will take priority, so `CustomEncoder` will be used. It is sometimes easier to define a default value in `producer.connect()` if you will be publishing a lot of similar messages though.
# TODO
- Hot Reloading (Refresh listeners on file changes) 🔄


## ➤ License
Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
        
        
